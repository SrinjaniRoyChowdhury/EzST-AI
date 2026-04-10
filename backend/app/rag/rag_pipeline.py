"""
rag/rag_pipeline.py
────────────────────
RAG (Retrieval-Augmented Generation) pipeline for the GST chatbot.

Flow:
  1. At startup: load GST knowledge docs → embed → store in FAISS
  2. At query time: embed question → FAISS similarity search → top-k chunks
  3. Pass chunks + question to Gemini → grounded answer

Knowledge base: plain text / markdown files in rag/knowledge/
"""

import os
import json
import pickle
from pathlib import Path
from typing import Optional

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from app.core.config import get_settings
from app.services.gemini_client import generate_text

settings = get_settings()

# ── Constants ─────────────────────────────────────────────────
KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"   # Fast, 384-dim, runs on CPU
EMBED_DIM = 384
TOP_K = 5

# ── Module-level singletons (loaded once) ─────────────────────
_embedder: Optional[SentenceTransformer] = None
_faiss_index: Optional[faiss.IndexFlatL2] = None
_chunks: list[str] = []          # Parallel list to FAISS index rows
_chunk_sources: list[str] = []   # Source filename per chunk


def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMBED_MODEL_NAME)
    return _embedder


def _embed(texts: list[str]) -> np.ndarray:
    """Return L2-normalised embeddings as float32 numpy array."""
    embedder = _get_embedder()
    vecs = embedder.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return vecs.astype(np.float32)


# ── Index Building ────────────────────────────────────────────

def _chunk_text(text: str, chunk_size: int = 400, overlap: int = 80) -> list[str]:
    """Split text into overlapping chunks by word count."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return chunks


def build_index(force_rebuild: bool = False) -> None:
    """
    Load all .txt / .md files from rag/knowledge/, chunk them,
    embed with SentenceTransformer, and store in a FAISS flat index.
    Persists index + chunks to disk for fast restarts.
    """
    global _faiss_index, _chunks, _chunk_sources

    index_path = Path(settings.faiss_index_path)
    meta_path = index_path.with_suffix(".meta.pkl")

    # Load from disk if already built
    if not force_rebuild and index_path.exists() and meta_path.exists():
        _faiss_index = faiss.read_index(str(index_path))
        with open(meta_path, "rb") as f:
            _chunks, _chunk_sources = pickle.load(f)
        print(f"[RAG] Loaded FAISS index: {len(_chunks)} chunks.")
        return

    # Build fresh
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    all_chunks, all_sources = [], []

    for doc_path in KNOWLEDGE_DIR.glob("**/*.{txt,md}"):
        text = doc_path.read_text(encoding="utf-8")
        doc_chunks = _chunk_text(text)
        all_chunks.extend(doc_chunks)
        all_sources.extend([doc_path.name] * len(doc_chunks))

    if not all_chunks:
        print("[RAG] Warning: no knowledge documents found. Chatbot will use model knowledge only.")
        _faiss_index = faiss.IndexFlatL2(EMBED_DIM)
        _chunks, _chunk_sources = [], []
        return

    print(f"[RAG] Embedding {len(all_chunks)} chunks …")
    vecs = _embed(all_chunks)

    index = faiss.IndexFlatL2(EMBED_DIM)
    index.add(vecs)

    # Persist
    index_path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_path))
    with open(meta_path, "wb") as f:
        pickle.dump((all_chunks, all_sources), f)

    _faiss_index, _chunks, _chunk_sources = index, all_chunks, all_sources
    print(f"[RAG] Index built and saved: {len(all_chunks)} chunks.")


def retrieve(question: str, top_k: int = TOP_K) -> list[dict]:
    """
    Retrieve the most relevant knowledge chunks for a question.
    Returns list of {"text": ..., "source": ..., "score": ...}
    """
    if _faiss_index is None or _faiss_index.ntotal == 0:
        return []

    q_vec = _embed([question])
    distances, indices = _faiss_index.search(q_vec, min(top_k, _faiss_index.ntotal))

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
        results.append({
            "text": _chunks[idx],
            "source": _chunk_sources[idx],
            "score": float(dist),
        })
    return results


# ── RAG Answer Generation ─────────────────────────────────────

RAG_SYSTEM_PROMPT = """
You are an expert GST (Goods and Services Tax) compliance assistant for Indian businesses.
Answer questions accurately using the provided context.
If the context does not contain enough information, say so clearly.
Always cite which GST rule / circular / section applies where possible.
"""


async def answer_gst_question(
    question: str,
    session_context: list[dict] | None = None,
) -> dict:
    """
    Full RAG pipeline: retrieve → augment → generate.

    session_context: prior Q&A turns for multi-turn support
      [{"role": "user"|"assistant", "content": "..."}]

    Returns {"answer": str, "sources": list[str]}
    """
    chunks = retrieve(question)
    context_text = "\n\n---\n\n".join(c["text"] for c in chunks) if chunks else "No context available."
    sources = list({c["source"] for c in chunks})

    # Build conversation history string
    history_str = ""
    if session_context:
        for turn in session_context[-6:]:   # Last 3 exchanges
            role = turn["role"].capitalize()
            history_str += f"{role}: {turn['content']}\n"

    prompt = f"""
{history_str}
KNOWLEDGE BASE CONTEXT:
{context_text}

USER QUESTION: {question}

Please answer based on the context above. Be concise and accurate.
"""
    answer = await generate_text(
        prompt,
        system_instruction=RAG_SYSTEM_PROMPT,
        temperature=0.3,
    )
    return {"answer": answer, "sources": sources}
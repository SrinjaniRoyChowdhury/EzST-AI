"""
services/groq_client.py
─────────────────────────
Thin wrapper around the Groq SDK.
Provides async helpers for text generation and JSON extraction.
"""

import json
import re
from functools import lru_cache
from typing import Any, Optional

from groq import Groq

from app.core.config import get_settings

settings = get_settings()


@lru_cache
def get_client() -> Groq:
    return Groq(api_key=settings.groq_api_key)


async def generate_text(
    prompt: str,
    system_instruction: Optional[str] = None,
    temperature: float = 0.2,
    max_output_tokens: int = 2048,
) -> str:
    """
    Send a prompt to Groq and return the raw text response.
    """
    client = get_client()

    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_output_tokens,
    )

    return response.choices[0].message.content.strip()


async def generate_json(
    prompt: str,
    system_instruction: Optional[str] = None,
) -> dict[str, Any]:
    """
    Ask Groq to return a JSON object and parse it safely.
    """
    full_system = (
        (system_instruction or "")
        + "\nIMPORTANT: Respond ONLY with valid JSON. No explanation. No markdown fences."
    )

    raw = await generate_text(prompt, system_instruction=full_system, temperature=0.1)

    # Strip markdown fences if model adds them
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON", "raw_response": raw}


async def chat(
    messages: list[dict],
    system_instruction: Optional[str] = None,
) -> str:
    """
    Simple multi-turn chat.
    """
    client = get_client()

    groq_messages = []
    if system_instruction:
        groq_messages.append({"role": "system", "content": system_instruction})

    for msg in messages:
        role = msg["role"]  # expects "user" or "assistant"
        text = msg["parts"][0]
        groq_messages.append({"role": role, "content": text})

    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=groq_messages,
    )

    return response.choices[0].message.content.strip()
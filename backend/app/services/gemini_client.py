"""
services/gemini_client.py
─────────────────────────
Thin wrapper around the Google Generative AI (Gemini) SDK.
Provides sync and async helpers for text generation and JSON extraction.
"""

import json
import re
from functools import lru_cache
from typing import Any, Optional

import google.generativeai as genai
from google.generativeai import GenerativeModel

from app.core.config import get_settings

settings = get_settings()


def _configure_gemini() -> None:
    genai.configure(api_key=settings.gemini_api_key)


@lru_cache
def get_gemini_model(model_name: str | None = None) -> GenerativeModel:
    _configure_gemini()
    return genai.GenerativeModel(model_name or settings.gemini_model)


async def generate_text(
    prompt: str,
    system_instruction: Optional[str] = None,
    temperature: float = 0.2,
    max_output_tokens: int = 4096,
) -> str:
    """
    Send a prompt to Gemini and return the raw text response.
    Low temperature (0.2) is best for structured extraction tasks.
    """
    _configure_gemini()
    model = genai.GenerativeModel(
        model_name=settings.gemini_model,
        system_instruction=system_instruction,
        generation_config=genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        ),
    )
    response = await model.generate_content_async(prompt)
    return response.text.strip()


async def generate_json(
    prompt: str,
    system_instruction: Optional[str] = None,
) -> dict[str, Any]:
    """
    Ask Gemini to return a JSON object and parse it safely.
    Falls back to empty dict on parse failure.
    """
    full_system = (
        (system_instruction or "")
        + "\nIMPORTANT: Respond ONLY with valid JSON. No explanation. No markdown fences."
    )
    raw = await generate_text(prompt, system_instruction=full_system, temperature=0.1)

    # Strip markdown fences if the model added them anyway
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON", "raw_response": raw}


async def chat(
    messages: list[dict],  # [{"role": "user"|"model", "parts": ["..."]}]
    system_instruction: Optional[str] = None,
) -> str:
    """
    Multi-turn chat with Gemini.
    messages format follows the Gemini SDK's content schema.
    """
    _configure_gemini()
    model = genai.GenerativeModel(
        model_name=settings.gemini_model,
        system_instruction=system_instruction,
    )
    chat_session = model.start_chat(history=messages[:-1])
    response = await chat_session.send_message_async(messages[-1]["parts"][0])
    return response.text.strip()
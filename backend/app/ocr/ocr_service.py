"""
ocr/ocr_service.py
──────────────────
Extract raw text from uploaded invoice files.
Supports: PDF (via pdf2image + Tesseract) and direct images.
"""

import os
import tempfile
from pathlib import Path
from typing import Union

import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import pdfplumber

from app.core.config import get_settings

settings = get_settings()

# Point pytesseract at the system Tesseract binary
pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

# Tesseract config for invoice-style documents
TESS_CONFIG = "--oem 3 --psm 6 -l eng"


def extract_text_from_image(image: Image.Image) -> str:
    """Run Tesseract on a single PIL Image and return raw text."""
    return pytesseract.image_to_string(image, config=TESS_CONFIG).strip()


def extract_text_from_pdf_plumber(pdf_path: str) -> str:
    """
    First attempt: use pdfplumber (fast, no OCR needed for text-based PDFs).
    Falls back to empty string if the PDF has no selectable text.
    """
    text_pages: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_pages.append(page_text)
    return "\n".join(text_pages).strip()


def extract_text_from_pdf_ocr(pdf_path: str, dpi: int = 300) -> str:
    images = convert_from_path(
        pdf_path,
        dpi=dpi,
        poppler_path=settings.poppler_path  # ✅ use config
    )
    return "\n".join(extract_text_from_image(img) for img in images).strip()


async def extract_text(file_bytes: bytes, filename: str) -> dict:
    """
    Main entry point for OCR extraction.

    Returns:
        {
            "raw_text": str,
            "method": "pdfplumber" | "tesseract_pdf" | "tesseract_image",
            "page_count": int,
        }
    """
    suffix = Path(filename).suffix.lower()

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        if suffix == ".pdf":
            # Try fast text extraction first
            text = extract_text_from_pdf_plumber(tmp_path)
            method = "pdfplumber"

            # Fall back to OCR if PDF is scanned
            if len(text) < 50:
                text = extract_text_from_pdf_ocr(tmp_path)
                method = "tesseract_pdf"

            import pdfplumber as _plumber
            with _plumber.open(tmp_path) as pdf:
                page_count = len(pdf.pages)

        elif suffix in {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}:
            img = Image.open(tmp_path)
            text = extract_text_from_image(img)
            method = "tesseract_image"
            page_count = 1

        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    finally:
        os.unlink(tmp_path)

    return {
        "raw_text": text,
        "method": method,
        "page_count": page_count,
    }
"""Utilities for extracting text layout information from PDF files using PyMuPDF."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import fitz


@dataclass
class TextBlock:
    """Represents a block of text extracted from a PDF page."""

    page_number: int
    bbox: tuple[float, float, float, float]
    text: str
    font_size: float | None
    font_name: str | None
    is_formula_like: bool = False


def _aggregate_span_weights(block: Dict) -> tuple[str, float | None, str | None]:
    """Aggregate text, font size, and font name information for a block.

    Args:
        block: A block dictionary from ``page.get_text("rawdict")``.

    Returns:
        A tuple containing concatenated text, average font size, and dominant font name.
    """

    texts: List[str] = []
    font_weights: Dict[str, int] = {}
    size_weighted_sum: float = 0.0
    total_size_weight: int = 0

    for line in block.get("lines", []):
        for span in line.get("spans", []):
            text = span.get("text", "")
            weight = max(len(text.strip()), 1)

            if text:
                texts.append(text)

            size = span.get("size")
            if isinstance(size, (int, float)):
                size_weighted_sum += size * weight
                total_size_weight += weight

            font = span.get("font")
            if isinstance(font, str) and font:
                font_weights[font] = font_weights.get(font, 0) + weight

    average_size: float | None = None
    if total_size_weight:
        average_size = size_weighted_sum / total_size_weight

    dominant_font: str | None = None
    if font_weights:
        dominant_font = max(font_weights.items(), key=lambda item: item[1])[0]

    return "".join(texts), average_size, dominant_font


def extract_text_blocks(pdf_path: str) -> list[TextBlock]:
    """Extract text blocks from a PDF file.

    The function opens the PDF with PyMuPDF and walks through each page. Text
    blocks are collected from the ``rawdict`` representation, combining spans
    into a single text string and computing representative font metadata.

    Args:
        pdf_path: Path to the input PDF file.

    Returns:
        A list of :class:`TextBlock` entries covering all pages in the document.
    """

    blocks: list[TextBlock] = []

    with fitz.open(pdf_path) as document:
        for page_number, page in enumerate(document, start=1):
            raw_dict = page.get_text("rawdict")
            for block in raw_dict.get("blocks", []):
                if block.get("type") != 0:  # Skip non-text blocks
                    continue

                text, font_size, font_name = _aggregate_span_weights(block)
                bbox = tuple(
                    float(value) for value in block.get("bbox", (0.0, 0.0, 0.0, 0.0))
                )

                blocks.append(
                    TextBlock(
                        page_number=page_number,
                        bbox=bbox,
                        text=text,
                        font_size=font_size,
                        font_name=font_name,
                    )
                )

    return blocks


if __name__ == "__main__":
    import sys

    sample_pdf = sys.argv[1] if len(sys.argv) > 1 else "input.pdf"
    extracted_blocks = extract_text_blocks(sample_pdf)

    for block in extracted_blocks[:10]:
        preview = block.text.replace("\n", " ").strip()
        if len(preview) > 80:
            preview = f"{preview[:77]}..."
        print(
            f"Page {block.page_number} | BBox: {block.bbox} | "
            f"Size: {block.font_size} | Font: {block.font_name} | Text: {preview}"
        )

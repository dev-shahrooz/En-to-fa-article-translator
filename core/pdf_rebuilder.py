"""Rebuild PDFs using translated text blocks while retaining original visuals."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

import fitz

from core.pdf_layout_extractor import TextBlock


def _get_rtl_direction() -> int:
    """Return the direction flag for right-to-left text insertion."""

    try:
        return fitz.TEXT_DIRECTION_RTL  # type: ignore[attr-defined]
    except AttributeError:
        return 1  # Fallback value used by PyMuPDF for RTL text


def _get_right_alignment() -> int:
    """Return the alignment flag for right alignment in text boxes."""

    try:
        return fitz.TEXT_ALIGN_RIGHT  # type: ignore[attr-defined]
    except AttributeError:
        return 2  # Right alignment fallback


def _group_blocks_by_page(blocks: Iterable[TextBlock]) -> dict[int, list[TextBlock]]:
    """Group text blocks by their page number (1-based)."""

    grouped: dict[int, list[TextBlock]] = defaultdict(list)
    for block in blocks:
        grouped[block.page_number].append(block)
    return grouped


def _sorted_blocks(blocks: list[TextBlock]) -> list[TextBlock]:
    """Sort blocks roughly top-to-bottom, then right-to-left for stable drawing."""

    return sorted(blocks, key=lambda b: (b.bbox[1], -b.bbox[0]))


def rebuild_pdf_with_translations(
    src_pdf_path: str,
    dst_pdf_path: str,
    blocks: list[TextBlock],
    rtl_font_path: str,
    default_font_size: float = 10.0,
) -> None:
    """
    Rebuild a new PDF with translated text over the original graphic content.

    The function copies each page of the source PDF into a new document and
    overlays translated text inside the bounding boxes provided by
    ``blocks``. Existing text is lightly hidden by drawing opaque rectangles
    before placing the new content. Images and vector graphics from the
    source PDF are preserved via ``show_pdf_page``.

    Args:
        src_pdf_path: Path to the original PDF.
        dst_pdf_path: Destination path for the rebuilt PDF.
        blocks: Translated text blocks with bounding boxes and page numbers.
        rtl_font_path: Path to a TTF font supporting Arabic/Persian glyphs.
        default_font_size: Font size to fall back to when a block lacks size
            metadata.
    """

    rtl_direction = _get_rtl_direction()
    right_align = _get_right_alignment()

    grouped_blocks = _group_blocks_by_page(blocks)

    with fitz.open(src_pdf_path) as src_doc, fitz.open() as dst_doc:
        for page in src_doc:
            # PyMuPDF page numbers are 0-based internally.
            page_number = page.number + 1
            page_rect = page.rect

            dst_page = dst_doc.new_page(width=page_rect.width, height=page_rect.height)
            dst_page.show_pdf_page(dst_page.rect, src_doc, page.number)

            for block in _sorted_blocks(grouped_blocks.get(page_number, [])):
                rect = fitz.Rect(block.bbox)
                if rect.is_empty or not block.text:
                    continue

                fontsize = float(block.font_size) if block.font_size else float(default_font_size)

                # Hide the original text region to reduce visual overlap.
                dst_page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)

                dst_page.insert_textbox(
                    rect,
                    block.text,
                    fontfile=rtl_font_path,
                    fontsize=fontsize,
                    align=right_align,
                    direction=rtl_direction,
                    color=(0, 0, 0),
                )

        dst_doc.save(dst_pdf_path)

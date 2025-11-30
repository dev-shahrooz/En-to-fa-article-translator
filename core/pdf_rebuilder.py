"""Rebuild PDFs using translated text blocks while retaining original visuals."""

from __future__ import annotations

import logging

import fitz

from core.pdf_layout_extractor import TextBlock

logger = logging.getLogger(__name__)


def rebuild_pdf_with_translations(
    src_pdf_path: str,
    dst_pdf_path: str,
    blocks: list[TextBlock],
    rtl_font_path: str,
) -> None:
    doc = fitz.open(src_pdf_path)
    new = fitz.open()

    for page_index in range(len(doc)):
        src_page = doc.load_page(page_index)
        dst_page = new.new_page(width=src_page.rect.width, height=src_page.rect.height)

        page_blocks = [b for b in blocks if b.page_number == page_index]

        logger.info("Rebuilder page %d will draw %d blocks", page_index, len(page_blocks))

        if page_blocks:
            first = page_blocks[0]
            logger.info(
                "Rebuilder page %d, first block bbox=%s text=%r",
                page_index,
                first.bbox,
                first.text[:200],
            )

        for b in page_blocks:
            (x0, y0, x1, y1) = b.bbox
            rect = fitz.Rect(x0, y0, x1, y1)
            dst_page.insert_textbox(rect, b.text, fontfile=rtl_font_path)

    new.save(dst_pdf_path)

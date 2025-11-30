"""High-level PDF translation pipeline for background processing."""

from __future__ import annotations

import os

from core.formula_detector import is_formula_like
from core.pdf_layout_extractor import TextBlock, extract_text_blocks
from core.pdf_rebuilder import rebuild_pdf_with_translations
from core.translator_nllb import NLLBTranslator

DEFAULT_FONT_PATH = os.environ.get(
    "RTL_FONT_PATH", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
)


def _mark_formula_blocks(blocks: list[TextBlock]) -> list[TextBlock]:
    """Annotate text blocks with a heuristic formula flag."""

    for block in blocks:
        block.is_formula_like = is_formula_like(block.text)
    return blocks


def run_translation_pipeline(input_path: str, output_path: str) -> None:
    """Orchestrate extraction, translation, and PDF rebuild.

    Args:
        input_path: Location of the source PDF.
        output_path: Destination for the translated PDF.
    """

    blocks = extract_text_blocks(input_path)
    _mark_formula_blocks(blocks)

    translator = NLLBTranslator()
    translator.translate_blocks(blocks)

    rebuild_pdf_with_translations(
        src_pdf_path=input_path,
        dst_pdf_path=output_path,
        blocks=blocks,
        rtl_font_path=DEFAULT_FONT_PATH,
    )

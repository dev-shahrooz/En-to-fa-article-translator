"""High-level PDF translation pipeline for background processing."""

from __future__ import annotations

import logging
import os

from config import (
    DEFAULT_SOURCE_LANGUAGE,
    DEFAULT_TARGET_LANGUAGE,
    HUGGINGFACE_TOKEN,
)
from core.formula_detector import is_formula_like
from core.pdf_layout_extractor import TextBlock, extract_text_blocks
from core.pdf_rebuilder import rebuild_pdf_with_translations
from core.translator_nllb import NLLBTranslator

DEFAULT_FONT_PATH = os.environ.get(
    "RTL_FONT_PATH", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
)

logger = logging.getLogger(__name__)


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

    logger.info("Extracting text blocks from %s", input_path)
    blocks = extract_text_blocks(input_path)
    _mark_formula_blocks(blocks)

    logger.info(
        "Translating %d blocks from %s to %s",
        len(blocks),
        DEFAULT_SOURCE_LANGUAGE,
        DEFAULT_TARGET_LANGUAGE,
    )
    translator = NLLBTranslator(
        hf_token=HUGGINGFACE_TOKEN,
        src_lang=DEFAULT_SOURCE_LANGUAGE,
        tgt_lang=DEFAULT_TARGET_LANGUAGE,
    )
    translator.translate_blocks(blocks)

    logger.info("Rebuilding translated PDF to %s", output_path)
    rebuild_pdf_with_translations(
        src_pdf_path=input_path,
        dst_pdf_path=output_path,
        blocks=blocks,
        rtl_font_path=DEFAULT_FONT_PATH,
    )

"""High-level PDF translation pipeline for background processing."""

from __future__ import annotations

import logging
import os

from config import (
    DEFAULT_SOURCE_LANGUAGE,
    DEFAULT_TARGET_LANGUAGE,
)
from core.formula_detector import is_formula_like
from core.pdf_layout_extractor import TextBlock, extract_text_blocks
from core.pdf_rebuilder import rebuild_pdf_with_translations
from core.translator_nllb import NLLBTranslator, TranslationError

DEFAULT_FONT_PATH = os.environ.get(
    "RTL_FONT_PATH", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
)

logger = logging.getLogger(__name__)


def mark_formula_blocks(blocks: list[TextBlock]) -> list[TextBlock]:
    """Annotate text blocks with a heuristic formula flag."""

    for block in blocks:
        block.is_formula_like = is_formula_like(block.text)
    return blocks


def _resolve_font_path(rtl_font_path: str | None = None) -> str:
    """Validate that the RTL font path exists before rebuilding the PDF."""

    resolved_path = rtl_font_path or DEFAULT_FONT_PATH
    if not os.path.isfile(resolved_path):
        logger.error(
            "RTL font file not found at %s. Set RTL_FONT_PATH to a valid font file.",
            resolved_path,
        )
        raise RuntimeError(
            "RTL font path is invalid or missing. Set the RTL_FONT_PATH environment "
            "variable to point to an existing font file."
        )
    return resolved_path


def run_translation_pipeline(
    input_path: str,
    output_path: str,
    *,
    rtl_font_path: str | None = None,
) -> None:
    """Orchestrate extraction, translation, and PDF rebuild.

    Args:
        input_path: Location of the source PDF.
        output_path: Destination for the translated PDF.
        rtl_font_path: Optional override for the RTL font used when rebuilding.
    """

    logger.info("Extracting text blocks from %s", input_path)
    blocks = extract_text_blocks(input_path)
    blocks = mark_formula_blocks(blocks)
    for block in blocks:
        block.page_number = block.page_number - 1

    logger.info(
        "Translating %d blocks from %s to %s",
        len(blocks),
        DEFAULT_SOURCE_LANGUAGE,
        DEFAULT_TARGET_LANGUAGE,
    )
    translator = NLLBTranslator(
        src_lang=DEFAULT_SOURCE_LANGUAGE,
        tgt_lang=DEFAULT_TARGET_LANGUAGE,
    )
    try:
        blocks = translator.translate_blocks(blocks)
        logger.info(
            "Block 0 after translation: %r",
            blocks[0].text[:200] if blocks else "",
        )
    except TranslationError:
        logger.exception("Translation failed")
        raise

    logger.info("Rebuilding translated PDF to %s", output_path)
    font_path = _resolve_font_path(rtl_font_path)
    rebuild_pdf_with_translations(
        src_pdf_path=input_path,
        dst_pdf_path=output_path,
        blocks=blocks,
        rtl_font_path=font_path,
    )

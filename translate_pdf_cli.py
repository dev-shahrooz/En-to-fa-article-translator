"""Simple CLI for translating PDFs using the existing pipeline."""

from __future__ import annotations

import argparse
import logging

from config import configure_logging
from core.pipeline import run_translation_pipeline

configure_logging()
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Translate a PDF from English to Persian.")
    parser.add_argument("input_path", help="Path to the source PDF")
    parser.add_argument("output_path", help="Path where the translated PDF will be written")
    parser.add_argument(
        "--rtl-font",
        dest="rtl_font",
        help="Override the RTL font path used when rebuilding the PDF",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    logger.info("Starting extraction for %s", args.input_path)
    run_translation_pipeline(
        args.input_path,
        args.output_path,
        rtl_font_path=args.rtl_font,
    )
    logger.info("Finished writing translated PDF to %s", args.output_path)
if __name__ == "__main__":
    main()

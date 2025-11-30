"""Translator integration using the UNESCO NLLB HuggingFace Space."""

from __future__ import annotations

import logging
from typing import List

from core.nllb_api import translate
from core.pdf_layout_extractor import TextBlock

logger = logging.getLogger(__name__)


class TranslationError(Exception):
    """Raised when translation via the NLLB space fails."""


class NLLBTranslator:
    """Translate text using the public UNESCO NLLB HuggingFace Space.

    This class is a light wrapper around :func:`core.nllb_api.translate`, which
    encapsulates the validated API call signature for the UNESCO/nllb Space.
    Default source and target languages can be provided at instantiation time,
    but they can also be overridden per translation call.
    """

    def __init__(
        self,
        src_lang: str = "English",
        tgt_lang: str = "Western Persian",
    ) -> None:
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang

    def translate(
        self,
        text: str,
        src_lang: str | None = None,
        tgt_lang: str | None = None,
    ) -> str:
        """Translate a single text string using ``core.nllb_api.translate``."""

        if text is None or text == "":
            return text

        src = src_lang or self.src_lang
        tgt = tgt_lang or self.tgt_lang

        try:
            return str(translate(text=text, src=src, tgt=tgt))
        except Exception as exc:  # pragma: no cover - network interactions
            logger.exception("Translation error via UNESCO/nllb")
            raise TranslationError("Failed to translate text via UNESCO/nllb") from exc

    def translate_blocks(
        self,
        blocks: List[TextBlock],
        src_lang: str | None = None,
        tgt_lang: str | None = None,
    ) -> List[TextBlock]:
        """Translate a collection of :class:`TextBlock` instances in-place."""

        translated_count = 0

        src = src_lang or self.src_lang
        tgt = tgt_lang or self.tgt_lang

        for index, block in enumerate(blocks):
            if block.is_formula_like or not block.text or not block.text.strip():
                continue

            original_text = block.text
            translated_text = self.translate(original_text, src, tgt)
            if translated_text == "" and original_text:
                translated_text = original_text
            block.text = translated_text

            if translated_count < 3:
                logger.info(
                    "Block %d translated:\n  original=%r\n  translated=%r",
                    index,
                    original_text[:200],
                    translated_text[:200],
                )
            translated_count += 1

        return blocks


if __name__ == "__main__":
    translator = NLLBTranslator()
    sample = "Hugging Face Spaces make it easy to share machine learning demos."
    print(translator.translate(sample))

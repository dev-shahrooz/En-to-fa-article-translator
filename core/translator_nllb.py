"""Translator integration using the UNESCO NLLB HuggingFace Space."""

from __future__ import annotations

from typing import List

from gradio_client import Client

from core.pdf_layout_extractor import TextBlock


class TranslationError(Exception):
    """Raised when translation via the NLLB space fails."""


class NLLBTranslator:
    """Translate text using the public UNESCO NLLB HuggingFace Space.

    The translator wraps the `gradio_client.Client` to communicate with the
    ``UNESCO/nllb`` Space. Default source and target languages can be provided
    at instantiation time, but they can also be overridden per translation call.
    """

    def __init__(self, hf_token: str | None = None, src_lang: str = "English", tgt_lang: str = "Western Persian") -> None:
        """Initialize the translator.

        Args:
            hf_token: Optional Hugging Face token for authenticated access.
            src_lang: Default source language name understood by the space.
            tgt_lang: Default target language name understood by the space.
        """

        client_kwargs = {"hf_token": hf_token} if hf_token else {}
        self.client = Client("UNESCO/nllb", **client_kwargs)
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang

    def translate(self, text: str, src_lang: str | None = None, tgt_lang: str | None = None) -> str:
        """Translate a single text string.

        Args:
            text: Input text to translate.
            src_lang: Optional override for the source language.
            tgt_lang: Optional override for the target language.

        Returns:
            Translated text.

        Raises:
            TranslationError: If the translation call fails.
        """

        if not text:
            return ""

        src = src_lang or self.src_lang
        tgt = tgt_lang or self.tgt_lang

        try:
            result = self.client.predict(text=text, src_lang=src, tgt_lang=tgt, api_name="/translate")
            return str(result)
        except Exception as exc:  # pragma: no cover - network interactions
            raise TranslationError("Failed to translate text via UNESCO/nllb") from exc

    def translate_blocks(self, blocks: List[TextBlock]) -> List[TextBlock]:
        """Translate a collection of :class:`TextBlock` instances in-place.

        Blocks flagged as formula-like or containing only whitespace are left
        untouched. Other blocks have their ``text`` field replaced with the
        translated output.

        Args:
            blocks: List of text blocks to translate.

        Returns:
            The list of blocks with translated text where applicable.
        """

        for block in blocks:
            if block.is_formula_like or not block.text.strip():
                continue

            translated_text = self.translate(block.text)
            block.text = translated_text

        return blocks


if __name__ == "__main__":
    translator = NLLBTranslator()
    sample = "Hugging Face Spaces make it easy to share machine learning demos."
    print(translator.translate(sample))

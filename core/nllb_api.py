"""Thin wrapper around the UNESCO/nllb gradio_client API."""

from __future__ import annotations

from gradio_client import Client

client = Client("UNESCO/nllb")  # public space


def translate(text: str, src: str = "English", tgt: str = "Western Persian") -> str:
    """
    Translate arbitrary English text to Western Persian using the UNESCO/nllb space.
    This MUST call client.predict with exactly the same arguments as in my working example.
    """
    if not text or not text.strip():
        return text
    return client.predict(
        text=text,
        src_lang=src,
        tgt_lang=tgt,
        api_name="/translate",
    )

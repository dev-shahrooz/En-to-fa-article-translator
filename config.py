"""Centralized configuration for the translation service.

This module exposes filesystem paths, language defaults, authentication tokens,
and logging preferences in a single place so they can be reused consistently
across the application.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

# Base directory for the project; used to derive default paths.
BASE_DIR = Path(__file__).resolve().parent

# Directory where uploaded PDFs are stored. Can be overridden via the
# ``UPLOAD_DIR`` environment variable to place uploads elsewhere.
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads")).resolve()

# Directory where translated PDFs are written. Can be overridden via the
# ``TRANSLATED_DIR`` environment variable to customize output location.
TRANSLATED_DIR = Path(os.getenv("TRANSLATED_DIR", BASE_DIR / "translated")).resolve()

# Default language settings for the translation pipeline. These can be
# overridden by environment variables to support different language pairs.
DEFAULT_SOURCE_LANGUAGE = os.getenv("DEFAULT_SOURCE_LANGUAGE", "English")
DEFAULT_TARGET_LANGUAGE = os.getenv("DEFAULT_TARGET_LANGUAGE", "Western Persian")

# Hugging Face token used when invoking the UNESCO NLLB space. Read from the
# ``HF_API_TOKEN`` environment variable so secrets are not committed to code.
HUGGINGFACE_TOKEN = os.getenv("HF_API_TOKEN")

# Logging level for the entire application. Accepts standard logging level
# names (e.g., ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``). Defaults to ``INFO``.
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Ensure directories exist at startup to avoid race conditions later on.
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
TRANSLATED_DIR.mkdir(parents=True, exist_ok=True)


def configure_logging() -> None:
    """Configure the root logger for the service.

    The configuration is idempotent; calling it multiple times has no effect
    after the first. A simple log format is used to keep output readable while
    still including timestamps and severity levels.
    """

    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

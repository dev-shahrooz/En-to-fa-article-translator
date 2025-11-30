"""Heuristic-based detector for formula-like text blocks.

The module provides lightweight checks that favor mathematical notation over
ordinary prose. The heuristics are intentionally simple so they can run quickly
on many small blocks of text extracted from PDFs.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Final

from core.pdf_layout_extractor import TextBlock

# Heuristic thresholds can be tuned depending on the characteristics of
# extracted text. They are exposed as module-level constants so callers can
# override them if necessary.
NON_ALPHA_RATIO_THRESHOLD: Final[float] = 0.35
"""Minimum proportion of non-alphabetic characters to consider a block dense."""

DIGIT_RATIO_THRESHOLD: Final[float] = 0.15
"""Minimum proportion of digits that contributes to formula-like appearance."""

MAX_SPACE_RATIO: Final[float] = 0.2
"""Upper bound on the fraction of spaces allowed in compact formulas."""

MIN_MATH_SYMBOLS: Final[int] = 1
"""Number of distinct math symbols that should appear to trigger detection."""

MATH_SYMBOLS: Final[frozenset[str]] = frozenset(
    {
        "=",
        "≈",
        "≠",
        "≤",
        "≥",
        "∑",
        "∫",
        "√",
        "±",
        "→",
        "←",
        "×",
        "·",
        "÷",
        "∞",
        "π",
        "Δ",
        "∂",
        "∇",
        "⊂",
        "⊆",
        "⊇",
        "⊃",
        "⇒",
        "⇔",
        "∝",
        "%",
        "+",
        "-",
        "−",
        "*",
        "/",
        "^",
        "_",
        "<",
        ">",
        "|",
        "(",
        ")",
        "[",
        "]",
        "{",
        "}",
    }
)
"""Characters commonly found in mathematical expressions."""


def _ratio(predicate: Iterable[bool], total: int) -> float:
    """Compute a ratio while guarding against division by zero."""

    return sum(1 for match in predicate if match) / total if total else 0.0


def is_formula_like(text: str) -> bool:
    """Return ``True`` if the text resembles a mathematical formula.

    The implementation combines several inexpensive heuristics:

    * High density of non-alphabetic characters (digits, punctuation, symbols).
    * Presence of at least one typical math symbol.
    * Low ratio of spaces compared to the length of the string.

    Args:
        text: Arbitrary text content.

    Returns:
        ``True`` when the heuristics suggest the text is formula-like.
    """

    normalized = text.strip()
    if not normalized:
        return False

    length = len(normalized)
    space_ratio = _ratio((char.isspace() for char in normalized), length)
    non_alpha_ratio = _ratio((not char.isalpha() for char in normalized), length)
    digit_ratio = _ratio((char.isdigit() for char in normalized), length)
    math_symbol_count = len({char for char in normalized if char in MATH_SYMBOLS})

    dense_symbols = non_alpha_ratio >= NON_ALPHA_RATIO_THRESHOLD
    compact_spacing = space_ratio <= MAX_SPACE_RATIO
    has_math_symbols = math_symbol_count >= MIN_MATH_SYMBOLS
    numeric_weight = digit_ratio >= DIGIT_RATIO_THRESHOLD

    return bool(
        (has_math_symbols and (dense_symbols or compact_spacing))
        or (dense_symbols and compact_spacing and numeric_weight)
    )


def mark_formula_blocks(blocks: list[TextBlock]) -> list[TextBlock]:
    """Mark each text block with a formula-likeness flag.

    The provided list is updated in-place by setting ``is_formula_like`` on each
    :class:`~core.pdf_layout_extractor.TextBlock` instance.

    Args:
        blocks: Collection of text blocks extracted from a PDF.

    Returns:
        The same list of blocks, allowing fluent-style usage.
    """

    for block in blocks:
        block.is_formula_like = is_formula_like(block.text)

    return blocks


if __name__ == "__main__":
    samples = [
        "The quick brown fox jumps over the lazy dog.",
        "E = mc^2",
        "Let f(x) = x^2 + 2x + 1 for all x ∈ ℝ.",
        "\u03c0 ≈ 3.14159",
        "This sentence describes an experiment without formulas.",
        "\u220f_{i=1}^n a_i = n!",
    ]

    for sample in samples:
        result = is_formula_like(sample)
        print(f"{sample!r} -> {'formula' if result else 'text'}")

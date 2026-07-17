"""Sentence buffering helpers for LLM → TTS cascade."""

from __future__ import annotations

import re

_SENTENCE_END = re.compile(r"(?<=[.!?。？！])\s+")
_CLAUSE_BREAK = re.compile(r"(?<=[,;:])\s+")


def pop_complete_sentences(
    buffer: str,
    *,
    min_chars: int = 18,
    early_chars: int = 52,
    clause_chars: int = 40,
) -> tuple[list[str], str]:
    """Split speakable segments from a streaming text buffer.

    Returns (sentences_to_speak, remaining_buffer).

    - Sentence terminators emit when the segment is at least ``min_chars``
      (short openers are held or merged so brief FAQ replies stay intact).
    - Long answers without a terminator can emit earlier on trailing whitespace
      (``early_chars``) or on clause breaks (``clause_chars``) so TTS starts sooner.
    """
    if not buffer:
        return [], ""

    parts = _SENTENCE_END.split(buffer)
    if len(parts) == 1:
        return _early_or_clause_split(
            buffer,
            early_chars=early_chars,
            clause_chars=clause_chars,
        )

    *complete, remainder = parts
    ready: list[str] = []
    held_prefix = ""
    for part in complete:
        text = part.strip()
        if not text:
            continue
        if held_prefix:
            text = f"{held_prefix} {text}".strip()
            held_prefix = ""
        if len(text) >= min_chars:
            ready.append(text)
        elif ready:
            ready[-1] = f"{ready[-1]} {text}".strip()
        else:
            # Short opener — prefix the next sentence (keeps FAQ openers intact).
            held_prefix = text

    if held_prefix:
        remainder = f"{held_prefix} {remainder}".strip()
    return ready, remainder


def _early_or_clause_split(
    buffer: str,
    *,
    early_chars: int,
    clause_chars: int,
) -> tuple[list[str], str]:
    stripped = buffer.strip()
    if not stripped:
        return [], buffer

    # Provisional long clause ending in whitespace → start TTS without waiting
    # for a period (long answers).
    if len(stripped) >= early_chars and buffer[-1:].isspace():
        return [stripped], ""

    clause_parts = _CLAUSE_BREAK.split(buffer)
    if len(clause_parts) == 1:
        return [], buffer

    *complete, rem = clause_parts
    ready: list[str] = []
    held = ""
    for part in complete:
        text = part.strip()
        if not text:
            continue
        candidate = f"{held} {text}".strip() if held else text
        if len(candidate) >= clause_chars:
            ready.append(candidate)
            held = ""
        else:
            held = candidate

    remainder = f"{held} {rem}".strip() if held else rem
    if ready:
        return ready, remainder
    return [], buffer

"""Ask the local model about some input. Inputs larger than the context are
map-reduced: each chunk is condensed, then the notes are answered together."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from local_ai.shared.ports import ChatModel
from local_ai.shared.text import CHARS_PER_TOKEN, estimate_tokens

# Share of the context the prompt may use; the rest is for reasoning + answer.
INPUT_SHARE = 0.5
MAX_DEPTH = 3


@dataclass(frozen=True)
class Source:
    name: str
    content: str


def build_prompt(instruction: str, sources: list[Source]) -> str:
    parts = [instruction.strip()]
    for s in sources:
        parts.append(f"=== {s.name} ===\n{s.content}")
    return "\n\n".join(parts)


def _chunks(text: str, max_chars: int) -> list[str]:
    """Split on line boundaries where possible."""
    chunks: list[str] = []
    current: list[str] = []
    size = 0
    for line in text.splitlines(keepends=True):
        while len(line) > max_chars:  # a single giant line
            if current:
                chunks.append("".join(current))
                current, size = [], 0
            chunks.append(line[:max_chars])
            line = line[max_chars:]
        if size + len(line) > max_chars and current:
            chunks.append("".join(current))
            current, size = [], 0
        current.append(line)
        size += len(line)
    if current:
        chunks.append("".join(current))
    return chunks


def ask(
    model: ChatModel,
    instruction: str,
    sources: list[Source],
    *,
    thinking: bool = True,
    on_progress: Callable[[str], None] = lambda _: None,
    _depth: int = 0,
) -> str:
    budget = int(model.context_tokens() * INPUT_SHARE)
    prompt = build_prompt(instruction, sources)
    if estimate_tokens(prompt) <= budget:
        return model.complete(prompt, thinking=thinking)

    if _depth >= MAX_DEPTH:
        raise RuntimeError("Input still too large after several condensing passes.")

    body = build_prompt("", sources).strip()
    overhead = estimate_tokens(instruction) + 200
    max_chars = max(1000, int((budget - overhead) * CHARS_PER_TOKEN))
    parts = _chunks(body, max_chars)
    notes: list[Source] = []
    for i, part in enumerate(parts, 1):
        on_progress(f"input too large for the context: condensing part {i}/{len(parts)}")
        note = model.complete(
            f"Task: {instruction.strip()}\n\n"
            f"Below is part {i} of {len(parts)} of a larger input. Extract only what is "
            "relevant to the task, concisely, keeping exact names, numbers, file paths "
            "and line references. If nothing is relevant, answer 'nothing relevant'.\n\n"
            f"{part}",
            thinking=False,  # condensing is mechanical; save time
        )
        notes.append(Source(f"notes from part {i}/{len(parts)}", note))

    combined = (
        f"{instruction.strip()}\n\n(The original input was too large, so you get "
        "notes extracted from each part of it.)"
    )
    return ask(model, combined, notes, thinking=thinking, on_progress=on_progress, _depth=_depth + 1)

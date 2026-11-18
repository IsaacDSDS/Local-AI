"""Pure text helpers shared by the features."""

from __future__ import annotations

import math
import re

_THINK = re.compile(r"<think>(.*?)</think>", re.DOTALL)
_FENCE = re.compile(r"^```[^\n]*\n(.*?)^```[ \t]*$", re.DOTALL | re.MULTILINE)

# Deliberately pessimistic (real code/English is closer to 3.5-4 chars per token):
# overestimating keeps us from silently overflowing the context.
CHARS_PER_TOKEN = 3.0


def estimate_tokens(text: str) -> int:
    return math.ceil(len(text) / CHARS_PER_TOKEN)


def split_reasoning(text: str) -> tuple[str, str]:
    """Split '<think>...</think>answer' into (answer, reasoning).

    An unclosed <think> means the answer was cut while still reasoning: no answer.
    """
    reasoning = "\n".join(m.strip() for m in _THINK.findall(text))
    answer = _THINK.sub("", text)
    if "<think>" in answer:
        head, _, tail = answer.partition("<think>")
        reasoning = (reasoning + "\n" + tail).strip()
        answer = head
    answer = answer.replace("</think>", "")
    return answer.strip(), reasoning


def extract_code(text: str) -> str:
    """The longest fenced block if the model used fences, else the whole text."""
    blocks = _FENCE.findall(text)
    if blocks:
        return max(blocks, key=len).rstrip("\n") + "\n"
    stripped = text.strip()
    return stripped + "\n" if stripped else ""


def tail_lines(text: str, n: int) -> str:
    lines = text.rstrip().splitlines()
    return "\n".join(lines[-n:])

"""The interface the features depend on. Domain code never imports the HTTP client."""

from __future__ import annotations

from typing import Protocol


class ChatModel(Protocol):
    def complete(self, prompt: str, *, thinking: bool = True) -> str:
        """Return the final answer (reasoning already removed)."""
        ...

    def context_tokens(self) -> int:
        """How many tokens the served context holds (prompt + answer)."""
        ...

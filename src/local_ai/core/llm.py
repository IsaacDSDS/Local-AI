"""OpenAI-compatible chat client (colibri, llama.cpp, LM Studio, Ollama...). Stdlib only."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Callable

from local_ai.core.config import Settings
from local_ai.core.errors import EmptyAnswer, ServerUnavailable
from local_ai.shared.text import split_reasoning

FALLBACK_CONTEXT = 32768


@dataclass
class ChatResult:
    answer: str
    reasoning: str
    finish_reason: str | None
    usage: dict = field(default_factory=dict)


class LocalLLM:
    """Implements shared.ports.ChatModel against an OpenAI-compatible server."""

    def __init__(
        self,
        settings: Settings,
        max_tokens: int | None = None,
        on_progress: Callable[[str], None] = lambda _: None,
    ) -> None:
        self.settings = settings
        self.max_tokens = max_tokens
        self.on_progress = on_progress
        self._models: list[dict] | None = None

    # -- server info -------------------------------------------------------
    def models(self) -> list[dict]:
        if self._models is None:
            data = self._request("GET", "/models")
            self._models = list(data.get("data", []))
        return self._models

    def model_id(self) -> str:
        if self.settings.model:
            return self.settings.model
        models = self.models()
        if not models:
            raise ServerUnavailable("The server lists no model (GET /v1/models is empty).")
        return models[0]["id"]

    def context_tokens(self) -> int:
        wanted = self.model_id()
        for m in self.models():
            if m.get("id") == wanted:
                for key in ("context_length", "max_model_len"):
                    if isinstance(m.get(key), int) and m[key] > 0:
                        return m[key]
        return FALLBACK_CONTEXT

    # -- generation --------------------------------------------------------
    def chat(self, prompt: str, *, thinking: bool = True, max_tokens: int | None = None) -> ChatResult:
        payload: dict = {
            "model": self.model_id(),
            "messages": [{"role": "user", "content": prompt}],
            # Qwen3-style switch, sent both ways: as colibri's top-level extension
            # and as the vLLM/llama.cpp-style template kwarg. Servers ignore what
            # they don't know. See docs/verify-first-run.md.
            "enable_thinking": thinking,
            "chat_template_kwargs": {"enable_thinking": thinking},
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        data = self._request("POST", "/chat/completions", payload)
        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        answer, inline_reasoning = split_reasoning(message.get("content") or "")
        reasoning = (message.get("reasoning_content") or "") + inline_reasoning
        return ChatResult(answer, reasoning, choice.get("finish_reason"), data.get("usage") or {})

    def complete(self, prompt: str, *, thinking: bool = True, max_tokens: int | None = None) -> str:
        start = time.monotonic()
        result = self.chat(prompt, thinking=thinking, max_tokens=max_tokens or self.max_tokens)
        # Reasoning size is reported so "thinking" being silently off is visible.
        self.on_progress(
            f"model replied in {time.monotonic() - start:.0f}s "
            f"(thinking {'on' if thinking else 'off'}: {len(result.reasoning)} chars of "
            f"reasoning, {len(result.answer)} chars of answer)"
        )
        if not result.answer:
            if result.finish_reason == "length":
                raise EmptyAnswer(
                    "The model ran out of tokens before answering (it was still thinking). "
                    "Retry with --no-think or a larger --max-tokens."
                )
            raise EmptyAnswer("The model returned an empty answer.")
        return result.answer

    # -- transport ---------------------------------------------------------
    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        url = self.settings.base_url + path
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", f"Bearer {self.settings.api_key}")
        try:
            with urllib.request.urlopen(req, timeout=self.settings.timeout_s) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            raise ServerUnavailable(f"{method} {url} -> HTTP {e.code}: {detail}") from e
        except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
            raise ServerUnavailable(
                f"Cannot reach the local model at {self.settings.base_url} ({e}). "
                "Is colibri running? Start it with START-HERE.bat / ./start-here.sh, "
                "check it with `coli status`, or set LAI_BASE_URL."
            ) from e

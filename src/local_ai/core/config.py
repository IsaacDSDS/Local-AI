"""Settings read from the environment. Everything has a sensible default for colibri."""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_BASE_URL = "http://127.0.0.1:8000/v1"


@dataclass(frozen=True)
class Settings:
    base_url: str = DEFAULT_BASE_URL
    model: str | None = None  # None = ask the server (GET /v1/models)
    api_key: str = "local"
    timeout_s: float = 900.0  # one request; thinking answers can take minutes

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            base_url=os.environ.get("LAI_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
            model=os.environ.get("LAI_MODEL") or None,
            api_key=os.environ.get("LAI_API_KEY", "local"),
            timeout_s=float(os.environ.get("LAI_TIMEOUT", "900")),
        )

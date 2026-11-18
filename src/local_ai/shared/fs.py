"""Files on disk, always UTF-8, line endings written exactly as given."""

from __future__ import annotations

from pathlib import Path


class FsWorkspace:
    def read(self, path: str) -> str | None:
        p = Path(path)
        if not p.exists():
            return None
        with p.open("r", encoding="utf-8", newline="") as f:
            return f.read()

    def write(self, path: str, content: str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8", newline="") as f:
            f.write(content)

    def delete(self, path: str) -> None:
        Path(path).unlink(missing_ok=True)

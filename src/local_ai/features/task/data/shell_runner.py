"""Runs the check command, in bash when there is one.

Claude Code's Bash tool runs bash on every OS (Git Bash on Windows), so the
check commands Claude writes are bash syntax. On Windows, the `bash.exe` in
System32 is the WSL launcher, not Git Bash, and is skipped.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from local_ai.features.task.domain.task import CheckResult

_GIT_BASH_CANDIDATES = [
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files (x86)\Git\bin\bash.exe",
]


def find_bash() -> str | None:
    for env in ("LAI_SHELL", "CLAUDE_CODE_GIT_BASH_PATH"):
        if os.environ.get(env) and Path(os.environ[env]).exists():
            return os.environ[env]
    found = shutil.which("bash")
    if found and not (sys.platform == "win32" and "system32" in found.lower()):
        return found
    if sys.platform == "win32":
        git = shutil.which("git")
        if git:  # ...\Git\cmd\git.exe -> ...\Git\bin\bash.exe
            candidate = Path(git).parent.parent / "bin" / "bash.exe"
            if candidate.exists():
                return str(candidate)
        for c in _GIT_BASH_CANDIDATES:
            if Path(c).exists():
                return c
    return None


class ShellRunner:
    def __init__(self, timeout_s: float = 600.0, cwd: str | None = None) -> None:
        self.timeout_s = timeout_s
        self.cwd = cwd
        self.bash = find_bash()

    def run(self, command: str) -> CheckResult:
        args: list[str] | str = [self.bash, "-c", command] if self.bash else command
        try:
            proc = subprocess.run(
                args,
                shell=self.bash is None,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_s,
                # Drafts can be rewritten within the same second with the same
                # size; Python's mtime+size .pyc check would then run stale code.
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
        except subprocess.TimeoutExpired:
            return CheckResult(False, f"The check timed out after {self.timeout_s:.0f}s.")
        return CheckResult(proc.returncode == 0, (proc.stdout or "") + (proc.stderr or ""))

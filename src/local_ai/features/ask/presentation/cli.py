"""`lai ask "instruction" [files...]` (stdin is read too when piped)."""

from __future__ import annotations

import argparse
import os
import stat
import sys
from pathlib import Path

from local_ai.core.llm import LocalLLM
from local_ai.features.ask.domain.ask import Source, ask
from local_ai.shared.fs import FsWorkspace


def register(sub: argparse._SubParsersAction, common: argparse.ArgumentParser) -> None:
    p = sub.add_parser("ask", parents=[common], help="ask the local model about files or piped input")
    p.add_argument("instruction", help="what to do, e.g. 'summarize the errors'")
    p.add_argument("files", nargs="*", help="files to include as input")
    p.add_argument("-o", "--out", help="write the answer to this file and print one line")
    p.set_defaults(handler=run)


def _stdin_has_data() -> bool:
    """True only for a pipe or a redirected file. A terminal or /dev/null
    (what agent shells usually give a command) is skipped, so `lai ask`
    doesn't wait for input nobody will send."""
    try:
        mode = os.fstat(sys.stdin.fileno()).st_mode
    except (OSError, ValueError, AttributeError):
        return False
    return stat.S_ISFIFO(mode) or stat.S_ISREG(mode)


def run(args: argparse.Namespace, llm: LocalLLM, progress) -> int:
    sources: list[Source] = []
    if _stdin_has_data():
        piped = sys.stdin.read()
        if piped.strip():
            sources.append(Source("stdin", piped))
    workspace = FsWorkspace()
    for f in args.files:
        content = workspace.read(f)
        if content is None:
            print(f"lai: file not found: {f}", file=sys.stderr)
            return 2
        sources.append(Source(f, content))

    answer = ask(llm, args.instruction, sources, thinking=args.think, on_progress=progress)

    if args.out:
        workspace.write(args.out, answer.rstrip("\n") + "\n")
        lines = answer.count("\n") + 1
        print(f"wrote {Path(args.out)} ({lines} lines)")
    else:
        print(answer)
    return 0

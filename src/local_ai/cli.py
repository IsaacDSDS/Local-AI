"""Entry point: `lai ask | task | status`."""

from __future__ import annotations

import argparse
import sys
import time

from local_ai import __version__
from local_ai.core.config import Settings
from local_ai.core.errors import LaiError
from local_ai.core.llm import LocalLLM
from local_ai.features.ask.presentation import cli as ask_cli
from local_ai.features.task.presentation import cli as task_cli


def _force_utf8() -> None:
    # Windows consoles default to a legacy code page; code and Spanish text break.
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


def _progress_printer(quiet: bool):
    start = time.monotonic()

    def progress(msg: str) -> None:
        if not quiet:
            print(f"[lai {time.monotonic() - start:5.0f}s] {msg}", file=sys.stderr, flush=True)

    return progress


def _status(args: argparse.Namespace, llm: LocalLLM, progress) -> int:
    print(f"server:  {llm.settings.base_url}")
    print(f"model:   {llm.model_id()}")
    print(f"context: {llm.context_tokens()} tokens")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lai",
        description="Delegate token-hungry work to a local LLM (OpenAI-compatible server).",
    )
    parser.add_argument("--version", action="version", version=f"lai {__version__}")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--no-think", dest="think", action="store_false",
                        help="disable the model's reasoning (faster, for simple work)")
    common.add_argument("--max-tokens", type=int, help="cap on reasoning + answer tokens")
    common.add_argument("-q", "--quiet", action="store_true", help="no progress on stderr")
    sub = parser.add_subparsers(dest="command", required=True)
    ask_cli.register(sub, common)
    task_cli.register(sub, common)
    st = sub.add_parser("status", parents=[common], help="show the server, model and context size")
    st.set_defaults(handler=_status)
    return parser


def main(argv: list[str] | None = None) -> int:
    _force_utf8()
    args = build_parser().parse_args(argv)
    llm = LocalLLM(Settings.from_env(), max_tokens=args.max_tokens)
    try:
        return args.handler(args, llm, _progress_printer(args.quiet))
    except LaiError as e:
        print(f"lai: {e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())

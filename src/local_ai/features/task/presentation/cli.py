"""`lai task TARGET -i "instruction" -c "check command" [--context files...]`."""

from __future__ import annotations

import argparse
import sys

from local_ai.core.llm import LocalLLM
from local_ai.shared.fs import FsWorkspace
from local_ai.features.task.data.shell_runner import ShellRunner
from local_ai.features.task.domain.task import TaskSpec, run_task
from local_ai.shared.text import tail_lines


def register(sub: argparse._SubParsersAction, common: argparse.ArgumentParser) -> None:
    p = sub.add_parser("task", parents=[common], help="generate a file and loop until a check passes")
    p.add_argument("target", help="file to create or rewrite")
    p.add_argument("-i", "--instruction", required=True, help="what the file must do")
    p.add_argument("-c", "--check", required=True, help="command that must exit 0 (run in bash)")
    p.add_argument("--context", nargs="*", default=[], help="files the model should read")
    p.add_argument("--attempts", type=int, default=3)
    p.add_argument("--check-timeout", type=float, default=600.0, help="seconds per check run")
    p.set_defaults(handler=run)


def run(args: argparse.Namespace, llm: LocalLLM, progress) -> int:
    workspace = FsWorkspace()
    context: dict[str, str] = {}
    for f in args.context:
        content = workspace.read(f)
        if content is None:
            print(f"lai: context file not found: {f}", file=sys.stderr)
            return 2
        context[f] = content

    spec = TaskSpec(
        target=args.target,
        instruction=args.instruction,
        check=args.check,
        context=context,
        max_attempts=args.attempts,
        thinking=args.think,
    )
    outcome = run_task(spec, llm, ShellRunner(args.check_timeout), workspace, progress)

    if outcome.passed:
        print(f"OK: {args.target} passes `{args.check}` (attempt {outcome.attempts})")
        return 0
    print(f"FAILED after {outcome.attempts} attempts: {args.target} left unchanged.")
    if outcome.failed_draft:
        print(f"Last draft: {outcome.failed_draft}")
    print("Last check output:")
    print(tail_lines(outcome.last_output, 20))
    return 1

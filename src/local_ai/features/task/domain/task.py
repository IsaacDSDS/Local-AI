"""Generate a file, check it, let the local model fix its own failures.

The caller (Claude) only sees the outcome: passed, or failed with the last
error lines. The file is never left broken: on final failure the original
content is restored and the last draft is kept next to it for inspection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from local_ai.core.errors import ContextOverflow
from local_ai.shared.ports import ChatModel
from local_ai.shared.text import estimate_tokens, extract_code, tail_lines

FAILED_SUFFIX = ".lai-failed"
ERROR_TAIL_LINES = 60


@dataclass(frozen=True)
class CheckResult:
    passed: bool
    output: str


class CheckRunner(Protocol):
    def run(self, command: str) -> CheckResult: ...


class Workspace(Protocol):
    def read(self, path: str) -> str | None: ...
    def write(self, path: str, content: str) -> None: ...
    def delete(self, path: str) -> None: ...


@dataclass(frozen=True)
class TaskSpec:
    target: str
    instruction: str
    check: str
    context: dict[str, str]  # file name -> content
    max_attempts: int = 3
    thinking: bool = True


@dataclass(frozen=True)
class TaskOutcome:
    passed: bool
    attempts: int
    last_output: str
    failed_draft: str | None = None


def _context_block(context: dict[str, str]) -> str:
    return "\n\n".join(f"=== {name} ===\n{content}" for name, content in context.items())


def initial_prompt(spec: TaskSpec, current: str | None) -> str:
    parts = [f"You are writing the file `{spec.target}`.", f"Task:\n{spec.instruction.strip()}"]
    if spec.context:
        parts.append("Context files:\n\n" + _context_block(spec.context))
    if current is not None:
        parts.append(f"Current content of `{spec.target}`:\n\n{current}")
    parts.append(f"It must pass this check: `{spec.check}`")
    parts.append(
        f"Reply with ONLY the complete content of `{spec.target}` in one fenced code "
        "block. No explanations."
    )
    return "\n\n".join(parts)


def fix_prompt(spec: TaskSpec, draft: str, error: str) -> str:
    parts = [f"You are fixing the file `{spec.target}`.", f"Task:\n{spec.instruction.strip()}"]
    if spec.context:
        parts.append("Context files:\n\n" + _context_block(spec.context))
    parts.append(f"Your previous version:\n\n{draft}")
    parts.append(f"It failed the check `{spec.check}` with:\n\n{error}")
    parts.append(
        f"Fix it. Reply with ONLY the complete corrected content of `{spec.target}` "
        "in one fenced code block. No explanations."
    )
    return "\n\n".join(parts)


def run_task(
    spec: TaskSpec,
    model: ChatModel,
    runner: CheckRunner,
    workspace: Workspace,
    on_progress: Callable[[str], None] = lambda _: None,
) -> TaskOutcome:
    original = workspace.read(spec.target)
    prompt = initial_prompt(spec, original)
    budget = int(model.context_tokens() * 0.6)
    draft = ""
    output = ""
    passed = False

    try:
        for attempt in range(1, spec.max_attempts + 1):
            if estimate_tokens(prompt) > budget:
                raise ContextOverflow(
                    f"The prompt (~{estimate_tokens(prompt)} tokens) does not fit the model's "
                    f"context ({model.context_tokens()}). Pass fewer --context files, or "
                    "summarize them first with `lai ask`."
                )
            on_progress(f"attempt {attempt}/{spec.max_attempts}: generating {spec.target}")
            draft = extract_code(model.complete(prompt, thinking=spec.thinking))
            if not draft.strip():
                output = "The model returned no code."
                prompt = initial_prompt(spec, original)
                continue
            workspace.write(spec.target, draft)
            on_progress(f"attempt {attempt}/{spec.max_attempts}: running `{spec.check}`")
            result = runner.run(spec.check)
            output = result.output
            if result.passed:
                passed = True
                return TaskOutcome(True, attempt, output)
            prompt = fix_prompt(spec, draft, tail_lines(output, ERROR_TAIL_LINES))
    finally:
        # Runs on failure *and* on any exception (server error, timeout, Ctrl+C):
        # the target is never left holding a draft that didn't pass.
        if not passed:
            failed_path = _restore(spec.target, original, draft, workspace)

    return TaskOutcome(False, spec.max_attempts, output, failed_path)


def _restore(target: str, original: str | None, draft: str, workspace: Workspace) -> str | None:
    failed_path: str | None = None
    if draft.strip():
        failed_path = target + FAILED_SUFFIX
        workspace.write(failed_path, draft)
    if original is None:
        workspace.delete(target)
    else:
        workspace.write(target, original)
    return failed_path

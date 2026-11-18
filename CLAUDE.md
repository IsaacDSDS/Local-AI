# Local-AI: context for Claude

## What this is

`lai`, a stdlib-only Python CLI that lets Claude Code delegate token-hungry work
(reading big inputs, drafting code/tests/docs) to a local LLM, to stretch a
Claude Pro ($20/month) plan. It is also the owner's public portfolio side project:
keep the README, code and commit history presentable, and everything in English.

## Owner's setup

- PC: AMD RX 6700 XT (12 GB VRAM), 32 GB RAM. Windows now; CachyOS planned.
- Local model: Qwen3.6-35B-A3B (MoE, reasoning on by default) served by
  [colibri](https://github.com/JustVugg/colibri) through Vulkan, OpenAI-compatible
  API at `http://127.0.0.1:8000/v1` (Anthropic API on the same port).
- Expected decode speed ~20-30 tok/s. This is an estimate, not a measurement:
  an RTX 3070 8 GB measured 25-30 with CUDA, and Vulkan is ~10-15% below CUDA.
  Measure it and put it in `docs/verify-first-run.md`.
- Chosen over Qwen3-Coder-30B because the owner wants thinking for hard problems.

## Decisions (and why)

- **Savings come from Claude not reading the local output.** Output goes to
  files, checks decide pass/fail, Claude sees one line. Don't add features
  that pipe local output back into Claude's context by default.
- **Stdlib only**, so it runs the same on Windows and Linux with no installs.
- **Feature-first clean architecture**: `features/{ask,task}/{domain,data,presentation}`,
  cross-cutting code in `core/` and `shared/`. Domain depends only on protocols in
  `shared/ports.py` and `task.py`; keep it that way so tests use fakes.
- **Checks run in bash** (Git Bash on Windows, never System32's WSL `bash.exe`),
  matching Claude Code's Bash tool. `PYTHONDONTWRITEBYTECODE=1` is set for checks
  because same-second, same-size rewrites made Python run stale `.pyc` files.
- **On task failure or any exception (server error, timeout, Ctrl+C) the original file is restored** and the draft saved as
  `<file>.lai-failed`.
- **stdin is read only when it's a pipe or a file**, so agent shells don't hang.

## Commands

```bash
pipx install -e .                              # or: pip install -e .
python -m unittest discover -s tests -t .      # all tests, no server needed
lai status                                     # needs the local server
```

## Status and next steps

1. Go through `docs/verify-first-run.md` on the real machine (model id, thinking
   switch, context size, speed). Fix what doesn't match.
2. Usage log + `lai stats` to show the savings (good README material).
3. MCP server exposing `ask`/`task` as tools.
4. Patch-based edits for large files in `task`.

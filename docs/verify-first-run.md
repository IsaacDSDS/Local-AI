# Verify on the first run

`lai` was built against colibri's documentation and tested with a fake server.
These points need a real server to confirm. Tick them and fix the code if one fails.

## Server and model

- [ ] `lai status` prints the model id (expected `qwen3.6-colibri` or `qwen3.6`;
      `c/coli status --json` shows it as `server.model_id`) and a context size.
      colibri's default for a chat model is 65,536 tokens when it fits in memory.
      If it's lower, start the server with a larger `--ctx` (e.g. `--ctx 65536`).
- [ ] If colibri moved to another port (it does when 8000 is taken), set
      `LAI_BASE_URL` to the address `coli status` prints.

## Thinking

- [ ] `lai ask "what is 17*23?"` shows a progress line with **more than 0 chars
      of reasoning** (otherwise thinking is silently off) and prints only the
      answer: no `<think>` text. If
      reasoning leaks into the answer, look at the raw response
      (`curl` below) and adjust `split_reasoning` / `LocalLLM.chat`.
- [ ] `lai ask --no-think "what is 17*23?"` answers without reasoning and clearly
      faster. `lai` sends `enable_thinking: false` both top-level and in
      `chat_template_kwargs`. colibri documents `enable_thinking` for GLM and the
      thinking on/off state for Qwen3.6 but not the exact field for Qwen3.6. If it
      keeps thinking, find the field in colibri's `docs/api.md` and fix it in
      `src/local_ai/core/llm.py`.

```bash
curl -s http://127.0.0.1:8000/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"<model id>","messages":[{"role":"user","content":"17*23?"}],"enable_thinking":false}'
```

## Speed (fill in)

| Measure | Value |
|---|---|
| Decode tok/s (shown by colibri) | |
| `lai ask --no-think` on a short question, seconds | |
| `lai ask` (thinking) on a short question, seconds | |
| `lai ask` on a 2,000-line file, seconds | |

## Claude Code integration

- [ ] In a project with `templates/CLAUDE.md`, ask Claude for a small, testable
      function. It should call `lai task`, not write the code itself.
- [ ] A `lai task` run longer than 2 minutes doesn't get killed by the Bash tool
      (it should run in the background or with a 600000 ms timeout).
- [ ] On Windows, `lai task -c "..."` runs the check in Git Bash (bash syntax works).
- [ ] From Claude Code's Bash tool, `lai ask "q" somefile` (no pipe) answers and
      doesn't hang waiting for stdin.

## Fallback: Claude Code fully local

- [ ] `ANTHROPIC_BASE_URL=http://127.0.0.1:8000 ANTHROPIC_API_KEY=local ANTHROPIC_MODEL=<model id> claude`
      starts and can edit a file. Note how usable it is.

## Local model: delegate to save tokens

A local LLM (Qwen3.6-35B-A3B, with reasoning) is available through the `lai`
command. Use it so you don't spend context on reading and drafting. Your job is
to plan, decide and judge, not to read big inputs or write boilerplate.

**Delegate**
- Reading anything long (logs, big files, generated output): never read it yourself.
  `lai ask "<precise question>" <files>` or `<command> | lai ask "<question>"`.
  Ask for exactly what you need (names, line numbers, the 5 relevant lines), not a general summary.
- New code, boilerplate, tests, docs and mechanical refactors of one file:
  `lai task <file> -i "<spec>" -c "<check>" --context <files it must read>`.
  Write a precise spec (signatures, edge cases, style to follow).
- Text that goes to a file: `lai ask ... --out <file>`.

**Do it yourself**
- Architecture, design decisions, debugging subtle problems, security-sensitive code.
- Anything `lai task` failed 3 times on (start from the `<file>.lai-failed` draft
  and the error it printed).

**Rules**
- When `lai task` prints `OK`, don't read the file. At most `git diff --stat`.
- The check must be independent of the generated file. When the local model
  writes the **tests**, the tests can't be the check: use `pytest --collect-only`
  / a type check as the check, then skim the test names (`grep -n "def test_"`)
  yourself.
- Runs are slow (the model may think for a minute or two per attempt): run
  `lai task` in the background or with the Bash timeout at 600000 ms, and run
  `lai ask` with `-q` to keep progress lines out of your context.
- `--no-think` for simple, mechanical requests; leave thinking on for anything
  that needs reasoning.
- If `lai` exits with code 2 (server down, context too small), tell the user and
  continue yourself; don't retry in a loop.

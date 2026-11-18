import unittest

from local_ai.core.errors import ContextOverflow
from local_ai.features.task.domain.task import CheckResult, TaskSpec, run_task
from tests.fakes import MemoryWorkspace, ScriptedModel, ScriptedRunner

FAIL = CheckResult(False, "AssertionError: expected 3, got 4")
PASS = CheckResult(True, "1 passed")


def spec(**kw):
    base = dict(target="calc.py", instruction="add(a, b)", check="pytest", context={})
    base.update(kw)
    return TaskSpec(**base)


class RunTaskTest(unittest.TestCase):
    def test_passes_first_time(self):
        ws = MemoryWorkspace()
        out = run_task(spec(), ScriptedModel(["```python\ndef add(a,b): return a+b\n```"]),
                       ScriptedRunner([PASS]), ws)
        self.assertTrue(out.passed)
        self.assertEqual(out.attempts, 1)
        self.assertEqual(ws.files["calc.py"], "def add(a,b): return a+b\n")

    def test_fixes_itself_with_the_error(self):
        model = ScriptedModel(["```\nbad\n```", "```\ngood\n```"])
        out = run_task(spec(), model, ScriptedRunner([FAIL, PASS]), MemoryWorkspace())
        self.assertTrue(out.passed)
        self.assertEqual(out.attempts, 2)
        self.assertIn("expected 3, got 4", model.prompts[1])
        self.assertIn("bad", model.prompts[1])

    def test_failure_restores_original_and_keeps_draft(self):
        ws = MemoryWorkspace({"calc.py": "original\n"})
        out = run_task(spec(), ScriptedModel(["```\nv1\n```", "```\nv2\n```", "```\nv3\n```"]),
                       ScriptedRunner([FAIL, FAIL, FAIL]), ws)
        self.assertFalse(out.passed)
        self.assertEqual(ws.files["calc.py"], "original\n")
        self.assertEqual(ws.files["calc.py.lai-failed"], "v3\n")
        self.assertEqual(out.failed_draft, "calc.py.lai-failed")

    def test_failure_on_new_file_removes_it(self):
        ws = MemoryWorkspace()
        run_task(spec(max_attempts=1), ScriptedModel(["```\nv1\n```"]),
                 ScriptedRunner([FAIL]), ws)
        self.assertNotIn("calc.py", ws.files)
        self.assertIn("calc.py.lai-failed", ws.files)

    def test_existing_file_is_shown_to_the_model(self):
        model = ScriptedModel(["```\nnew\n```"])
        run_task(spec(), model, ScriptedRunner([PASS]), MemoryWorkspace({"calc.py": "OLD CODE"}))
        self.assertIn("OLD CODE", model.prompts[0])

    def test_empty_answer_does_not_overwrite_or_run_check(self):
        ws = MemoryWorkspace({"calc.py": "original\n"})
        runner = ScriptedRunner([PASS])
        out = run_task(spec(), ScriptedModel(["", "```\nok\n```"]), runner, ws)
        self.assertTrue(out.passed)
        self.assertEqual(len(runner.commands), 1)

    def test_oversized_context_is_refused(self):
        with self.assertRaises(ContextOverflow):
            run_task(spec(context={"huge.py": "x" * 100_000}), ScriptedModel([], context=4096),
                     ScriptedRunner([]), MemoryWorkspace())


if __name__ == "__main__":
    unittest.main()

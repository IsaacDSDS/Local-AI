import unittest

from local_ai.features.ask.domain.ask import Source, ask
from tests.fakes import ScriptedModel


class AskTest(unittest.TestCase):
    def test_small_input_is_one_call(self):
        model = ScriptedModel(["the answer"])
        out = ask(model, "Summarize", [Source("a.log", "line\n" * 10)])
        self.assertEqual(out, "the answer")
        self.assertEqual(len(model.prompts), 1)
        self.assertIn("=== a.log ===", model.prompts[0])

    def test_large_input_is_condensed_then_answered(self):
        # 2000-token context -> 1000-token input budget; the log is ~6x larger.
        model = ScriptedModel(["note"] * 50 + ["final"], context=2000)
        log = "".join(f"ERROR line {i} something failed\n" for i in range(600))
        out = ask(model, "List the errors", [Source("big.log", log)])
        self.assertTrue(len(model.prompts) > 2)
        self.assertIn("part 1 of", model.prompts[0])
        # every chunk prompt fits the budget
        for p in model.prompts:
            self.assertLessEqual(len(p) / 3, 2000)
        # the final call gets the notes, not the raw log
        self.assertIn("notes from part 1/", model.prompts[-1])


if __name__ == "__main__":
    unittest.main()

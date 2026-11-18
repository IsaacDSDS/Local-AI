import unittest

from local_ai.shared.text import extract_code, split_reasoning


class SplitReasoningTest(unittest.TestCase):
    def test_removes_think_block(self):
        self.assertEqual(split_reasoning("<think>hmm</think>\nAnswer"), ("Answer", "hmm"))

    def test_plain_answer(self):
        self.assertEqual(split_reasoning("Answer"), ("Answer", ""))

    def test_unclosed_think_means_no_answer(self):
        answer, reasoning = split_reasoning("<think>still going")
        self.assertEqual(answer, "")
        self.assertIn("still going", reasoning)

    def test_stray_closing_tag(self):
        self.assertEqual(split_reasoning("reasoning leaked</think>Answer")[0],
                         "reasoning leakedAnswer")


class ExtractCodeTest(unittest.TestCase):
    def test_takes_longest_fenced_block(self):
        text = "Here:\n```python\nx = 1\ny = 2\n```\nand\n```\nz\n```\n"
        self.assertEqual(extract_code(text), "x = 1\ny = 2\n")

    def test_no_fence_returns_text(self):
        self.assertEqual(extract_code("x = 1"), "x = 1\n")

    def test_empty(self):
        self.assertEqual(extract_code("  "), "")


if __name__ == "__main__":
    unittest.main()

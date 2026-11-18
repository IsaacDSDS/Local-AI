import unittest

from local_ai.features.task.data.shell_runner import ShellRunner


class ShellRunnerTest(unittest.TestCase):
    def test_exit_codes_and_output(self):
        runner = ShellRunner(timeout_s=30)
        ok = runner.run("echo hello")
        self.assertTrue(ok.passed)
        self.assertIn("hello", ok.output)
        bad = runner.run("echo boom >&2; exit 3")
        self.assertFalse(bad.passed)
        self.assertIn("boom", bad.output)

    def test_timeout(self):
        result = ShellRunner(timeout_s=1).run("sleep 5")
        self.assertFalse(result.passed)
        self.assertIn("timed out", result.output)


if __name__ == "__main__":
    unittest.main()

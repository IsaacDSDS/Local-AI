import socket
import unittest

from local_ai.core.config import Settings
from local_ai.core.errors import EmptyAnswer, ServerUnavailable
from local_ai.core.llm import LocalLLM
from tests.fakes import FakeServer, reply


class LocalLLMTest(unittest.TestCase):
    def setUp(self):
        self.server = None

    def tearDown(self):
        if self.server:
            self.server.close()

    def llm(self, replies, models=None, **settings):
        self.server = FakeServer(replies, models)
        return LocalLLM(Settings(base_url=self.server.base_url, **settings))

    def test_detects_model_and_context(self):
        llm = self.llm([])
        self.assertEqual(llm.model_id(), "qwen3.6-colibri")
        self.assertEqual(llm.context_tokens(), 65536)

    def test_env_model_wins(self):
        self.assertEqual(self.llm([], model="other").model_id(), "other")

    def test_unknown_context_falls_back(self):
        llm = self.llm([], models=[{"id": "m"}])
        self.assertEqual(llm.context_tokens(), 32768)

    def test_strips_inline_reasoning(self):
        llm = self.llm([reply("<think>plan</think>\nHello")])
        self.assertEqual(llm.complete("hi"), "Hello")

    def test_separate_reasoning_field(self):
        llm = self.llm([reply("Hello", reasoning="plan")])
        result = llm.chat("hi")
        self.assertEqual((result.answer, result.reasoning), ("Hello", "plan"))

    def test_sends_thinking_switch(self):
        llm = self.llm([reply("ok")])
        llm.complete("hi", thinking=False)
        sent = self.server.requests[0]
        self.assertIs(sent["enable_thinking"], False)
        self.assertIs(sent["chat_template_kwargs"]["enable_thinking"], False)
        self.assertEqual(sent["model"], "qwen3.6-colibri")

    def test_truncated_while_thinking_is_an_error(self):
        llm = self.llm([reply("<think>long reasoning", finish="length")])
        with self.assertRaises(EmptyAnswer) as ctx:
            llm.complete("hi")
        self.assertIn("--no-think", str(ctx.exception))

    def test_server_down(self):
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        llm = LocalLLM(Settings(base_url=f"http://127.0.0.1:{port}/v1", timeout_s=2))
        with self.assertRaises(ServerUnavailable) as ctx:
            llm.model_id()
        self.assertIn("colibri", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

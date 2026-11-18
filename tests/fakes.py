"""Test doubles and a fake OpenAI-compatible server."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from local_ai.features.task.domain.task import CheckResult


class ScriptedModel:
    """ChatModel that replays answers and records prompts."""

    def __init__(self, answers: list[str], context: int = 32768) -> None:
        self.answers = list(answers)
        self.prompts: list[str] = []
        self.context = context

    def complete(self, prompt: str, *, thinking: bool = True) -> str:
        self.prompts.append(prompt)
        return self.answers.pop(0) if self.answers else "nothing"

    def context_tokens(self) -> int:
        return self.context


class ScriptedRunner:
    def __init__(self, results: list[CheckResult]) -> None:
        self.results = list(results)
        self.commands: list[str] = []

    def run(self, command: str) -> CheckResult:
        self.commands.append(command)
        return self.results.pop(0)


class MemoryWorkspace:
    def __init__(self, files: dict[str, str] | None = None) -> None:
        self.files = dict(files or {})

    def read(self, path: str) -> str | None:
        return self.files.get(path)

    def write(self, path: str, content: str) -> None:
        self.files[path] = content

    def delete(self, path: str) -> None:
        self.files.pop(path, None)


class FakeServer:
    """Serves /v1/models and /v1/chat/completions with canned replies."""

    def __init__(self, replies: list[dict], models: list[dict] | None = None) -> None:
        self.replies = list(replies)
        self.models = models if models is not None else [
            {"id": "qwen3.6-colibri", "object": "model", "context_length": 65536}
        ]
        self.requests: list[dict] = []
        server = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):  # silence
                pass

            def _send(self, obj: dict) -> None:
                body = json.dumps(obj).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                self._send({"object": "list", "data": server.models})

            def do_POST(self):
                length = int(self.headers["Content-Length"])
                server.requests.append(json.loads(self.rfile.read(length)))
                self._send(server.replies.pop(0))

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.base_url = f"http://127.0.0.1:{self.httpd.server_address[1]}/v1"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


def reply(content: str, finish: str = "stop", reasoning: str | None = None) -> dict:
    message = {"role": "assistant", "content": content}
    if reasoning is not None:
        message["reasoning_content"] = reasoning
    return {"choices": [{"index": 0, "message": message, "finish_reason": finish}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}}

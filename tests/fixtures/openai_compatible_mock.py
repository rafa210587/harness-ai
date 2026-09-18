#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


def chunk(
    model: str,
    delta: dict[str, Any],
    finish_reason: str | None = None,
) -> dict[str, Any]:
    return {
        "id": "chatcmpl-harness-mock",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
    }


def completion(
    model: str,
    message: dict[str, Any],
    finish_reason: str = "stop",
) -> dict[str, Any]:
    return {
        "id": "chatcmpl-harness-mock",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "message": message, "finish_reason": finish_reason}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }


def text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
    return ""


def latest_user_text(messages: list[dict[str, Any]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            return text_from_content(message.get("content"))
    return ""


def has_tool_result(messages: list[dict[str, Any]]) -> bool:
    return any(message.get("role") == "tool" for message in messages)


class Handler(BaseHTTPRequestHandler):
    server_version = "HarnessOpenAIMock/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(fmt % args, flush=True)

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._json(200, {"ok": True})
            return
        if self.path == "/v1/models":
            self._json(
                200,
                {
                    "object": "list",
                    "data": [
                        {
                            "id": "mock-model",
                            "object": "model",
                            "created": int(time.time()),
                            "owned_by": "harness-ai",
                        }
                    ],
                },
            )
            return
        self._json(404, {"error": {"message": "not found"}})

    def do_POST(self) -> None:
        if self.path != "/v1/chat/completions":
            self._json(404, {"error": {"message": "not found"}})
            return

        length = int(self.headers.get("Content-Length", "0"))
        request = json.loads(self.rfile.read(length).decode("utf-8"))
        model = request.get("model") or "mock-model"
        messages = request.get("messages") or []
        user_text = latest_user_text(messages)
        stream = bool(request.get("stream"))

        if "MOCK_CONTINUE_OK" in user_text:
            response_kind = ("text", "MOCK_CONTINUE_OK")
        elif "MOCK_SKILL_LOOP" in user_text:
            if has_tool_result(messages):
                response_kind = ("text", "MOCK_SKILL_LOOP_OK")
            else:
                response_kind = (
                    "tool",
                    {
                        "name": "skill",
                        "arguments": json.dumps({"name": "browser-research"}),
                    },
                )
        elif "MOCK_READ_LOOP" in user_text:
            if has_tool_result(messages):
                response_kind = ("text", "MOCK_READ_LOOP_OK")
            else:
                response_kind = (
                    "tool",
                    {
                        "name": "read",
                        "arguments": json.dumps({"filePath": self.server.read_path}),
                    },
                )
        else:
            response_kind = ("text", "MOCK_TEXT_OK")

        if not stream:
            if response_kind[0] == "text":
                self._json(
                    200, completion(model, {"role": "assistant", "content": response_kind[1]})
                )
            else:
                spec = response_kind[1]
                self._json(
                    200,
                    completion(
                        model,
                        {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_harness_mock",
                                    "type": "function",
                                    "function": spec,
                                }
                            ],
                        },
                        finish_reason="tool_calls",
                    ),
                )
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        def send(payload: dict[str, Any]) -> None:
            self.wfile.write(f"data: {json.dumps(payload)}\n\n".encode("utf-8"))
            self.wfile.flush()

        if response_kind[0] == "text":
            send(chunk(model, {"role": "assistant", "content": response_kind[1]}))
            send(chunk(model, {}, finish_reason="stop"))
        else:
            spec = response_kind[1]
            send(
                chunk(
                    model,
                    {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "index": 0,
                                "id": "call_harness_mock",
                                "type": "function",
                                "function": {
                                    "name": spec["name"],
                                    "arguments": spec["arguments"],
                                },
                            }
                        ],
                    },
                )
            )
            send(chunk(model, {}, finish_reason="tool_calls"))

        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--read-path", required=True)
    args = parser.parse_args()

    read_path = str(Path(args.read_path).resolve())
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    server.read_path = read_path  # type: ignore[attr-defined]
    print(f"mock-provider-ready port={args.port} read_path={read_path}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()

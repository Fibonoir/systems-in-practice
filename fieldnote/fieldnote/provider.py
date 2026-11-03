"""Local HTTP transport without downloads or paid routes."""

import copy
import json
from urllib.error import HTTPError, URLError
from urllib.request import (
    HTTPRedirectHandler,
    ProxyHandler,
    Request,
    build_opener,
)


class ProviderError(RuntimeError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(
        self, req, fp, code, msg, headers, newurl
    ):
        return None


class Ollama:
    def __init__(self, model, port=11434, timeout=120):
        if not isinstance(model, str) or not model.strip():
            raise ValueError(
                "choose an installed model explicitly"
            )
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError("invalid port")
        self.model = model
        self.url = f"http://127.0.0.1:{port}/api/chat"
        self.timeout = timeout
        self.opener = build_opener(
            ProxyHandler({}), NoRedirect()
        )

    def chat(self, messages, tools=None, schema=None):
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0,
                "num_predict": 1024,
                "num_ctx": 8192,
            },
        }
        if tools:
            payload["tools"] = tools
        if schema:
            payload["format"] = schema
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            self.url,
            data=body,
            headers={"Content-Type": "application/json"},
        )
        try:
            with self.opener.open(
                request, timeout=self.timeout
            ) as response:
                raw = response.read(1_000_001)
            if len(raw) > 1_000_000:
                raise ProviderError(
                    "response byte limit exceeded"
                )
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise ProviderError(
                    "response envelope must be an object"
                )
            if result.get("done") is not True:
                raise ProviderError("incomplete response")
            if result.get("done_reason") == "length":
                raise ProviderError(
                    "generation limit reached"
                )
            message = result["message"]
            if not isinstance(message, dict):
                raise ProviderError(
                    "message must be an object"
                )
            return message
        except (
            HTTPError,
            URLError,
            TimeoutError,
            OSError,
            json.JSONDecodeError,
            UnicodeDecodeError,
            KeyError,
        ) as exc:
            raise ProviderError(
                "local model request failed; check server, "
                "model and request contract"
            ) from exc


class Scripted:
    """A deterministic test double with no inference."""

    def __init__(self, replies):
        self.replies = iter(copy.deepcopy(replies))
        self.requests = []

    def chat(self, messages, tools=None, schema=None):
        self.requests.append(copy.deepcopy(messages))
        try:
            return next(self.replies)
        except StopIteration as exc:
            raise ProviderError(
                "script has no remaining reply"
            ) from exc

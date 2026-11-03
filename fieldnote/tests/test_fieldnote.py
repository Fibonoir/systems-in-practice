import copy
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import tempfile
import threading
import unittest
from fieldnote.agent import Budget, run
from fieldnote.corpus import Corpus, CorpusError
from fieldnote.protocol import (
    ANSWER_SCHEMA,
    ProtocolError,
    parse_answer,
    validate_call,
)
from fieldnote.provider import Ollama, ProviderError, Scripted


ROOT = Path(__file__).resolve().parents[1]


def call(name="search", **args):
    return {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {"function": {"name": name, "arguments": args}}
        ],
    }


def final(
    status="unknown",
    answer="The collection does not say.",
    citations=None,
):
    return {
        "role": "assistant",
        "content": json.dumps(
            {
                "status": status,
                "answer": answer,
                "citations": citations or [],
            }
        ),
    }


class CorpusTests(unittest.TestCase):
    def setUp(self):
        self.corpus = Corpus(ROOT / "fixtures/harbor")

    def test_collection_is_five_documents(self):
        self.assertEqual(len(self.corpus.list_documents()), 5)

    def test_search_exact_fixture(self):
        results = self.corpus.search("replacement fee access")
        self.assertEqual(
            results[0]["chunk_id"], "access.txt:4"
        )
        self.assertEqual(results[0]["score"], 3)

    def test_search_unmatched_and_empty(self):
        self.assertEqual(self.corpus.search("zzzzzz"), [])
        self.assertEqual(self.corpus.search("!!!"), [])

    def test_stable_tie_order(self):
        results = self.corpus.search("Harbor", 5)
        self.assertEqual(
            [r["chunk_id"] for r in results],
            sorted(r["chunk_id"] for r in results),
        )

    def test_no_arbitrary_path(self):
        for name in (
            "../secret.txt",
            "/etc/passwd",
            "missing.txt",
        ):
            with self.subTest(name=name), self.assertRaises(
                CorpusError
            ):
                self.corpus.read_document(name)

    def test_snapshot_unchanged_after_disk_edit(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "a.txt"
            path.write_text(
                "Original paragraph.", encoding="utf-8"
            )
            corpus = Corpus(temp)
            path.write_text(
                "Changed paragraph.", encoding="utf-8"
            )
            self.assertEqual(
                corpus.read_document("a.txt")[0]["text"],
                "Original paragraph.",
            )

    def test_invalid_utf8(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "a.txt").write_bytes(b"\xff")
            with self.assertRaises(CorpusError):
                Corpus(temp)

    def test_long_paragraph_and_empty(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(CorpusError):
                Corpus(temp)
            (Path(temp) / "a.txt").write_text("x" * 1201)
            with self.assertRaises(CorpusError):
                Corpus(temp)

    def test_oversize_file(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "a.txt").write_bytes(b"x" * 20001)
            with self.assertRaises(CorpusError):
                Corpus(temp)


class ProtocolTests(unittest.TestCase):
    def test_documented_call_index(self):
        request = call(query="fee", limit=3)["tool_calls"][0]
        request["function"]["index"] = 0
        self.assertEqual(validate_call(request)[0], "search")
        request["function"]["index"] = True
        with self.assertRaises(ProtocolError):
            validate_call(request)

    def test_boolean_is_not_search_limit(self):
        with self.assertRaises(ProtocolError):
            validate_call(
                call(query="fee", limit=True)["tool_calls"][0]
            )

    def test_unknown_tool_and_extra_argument(self):
        for message in (
            call("delete"),
            call("list_documents", extra=1),
        ):
            with self.assertRaises(ProtocolError):
                validate_call(message["tool_calls"][0])

    def test_unknown_answer(self):
        self.assertEqual(
            parse_answer(final()["content"], {})["status"],
            "unknown",
        )

    def test_unobserved_and_changed_quote(self):
        citation = [
            {"chunk_id": "a:1", "quote": "Twelve credits."}
        ]
        text = final("answered", "Twelve.", citation)[
            "content"
        ]
        with self.assertRaises(ProtocolError):
            parse_answer(text, {})
        with self.assertRaises(ProtocolError):
            parse_answer(text, {"a:1": "Eight credits."})

    def test_exact_quote_is_not_entailment(self):
        # Deliberately false answer passes the mechanical quote check.
        text = final(
            "answered",
            "Cards are free.",
            [
                {
                    "chunk_id": "a:1",
                    "quote": "The fee is twelve credits.",
                }
            ],
        )["content"]
        self.assertEqual(
            parse_answer(
                text, {"a:1": "The fee is twelve credits."}
            )["answer"],
            "Cards are free.",
        )

    def test_malformed_answers(self):
        for text in ("```json\n{}\n```", "[]", "null", "{}"):
            with self.subTest(text=text), self.assertRaises(
                ProtocolError
            ):
                parse_answer(text, {})


class LoopTests(unittest.TestCase):
    def setUp(self):
        self.corpus = Corpus(ROOT / "fixtures/harbor")

    def test_demo_and_message_history(self):
        replies = json.loads(
            (ROOT / "fixtures/demo.json").read_text()
        )
        provider = Scripted(replies)
        result = run(
            "What is the replacement-card fee?",
            self.corpus,
            provider,
        )
        self.assertEqual(result.stop, "complete")
        self.assertEqual(
            (result.requests, result.tools), (2, 1)
        )
        self.assertEqual(
            provider.requests[1][-2]["role"], "assistant"
        )
        self.assertEqual(
            provider.requests[1][-1]["role"], "tool"
        )

    def test_repeat_stops_before_second_dispatch(self):
        message = call(query="fee", limit=3)
        result = run(
            "fee?", self.corpus, Scripted([message, message])
        )
        self.assertEqual(result.stop, "repeated_call")
        self.assertEqual(result.tools, 1)

    def test_request_tool_context_and_result_limits(self):
        message = call(query="fee", limit=3)
        result = run(
            "fee?",
            self.corpus,
            Scripted([message]),
            Budget(requests=1),
        )
        self.assertEqual(result.stop, "request_budget")
        result = run(
            "fee?",
            self.corpus,
            Scripted([message]),
            Budget(tools=0),
        )
        self.assertEqual(result.stop, "tool_budget")
        provider = Scripted([])
        result = run(
            "fee?",
            self.corpus,
            provider,
            Budget(context_bytes=1),
        )
        self.assertEqual(result.stop, "context_budget")
        self.assertEqual(provider.requests, [])
        result = run(
            "fee?",
            self.corpus,
            Scripted([message, final()]),
            Budget(result_bytes=1),
        )
        self.assertEqual(
            result.events[0]["result"]["error"],
            "result_too_large",
        )

    def test_unknown_document_can_be_followed_by_abstention(
        self,
    ):
        result = run(
            "where?",
            self.corpus,
            Scripted(
                [
                    call(
                        "read_document",
                        document="missing.txt",
                    ),
                    final(),
                ]
            ),
        )
        self.assertEqual(result.stop, "complete")
        self.assertFalse(result.events[0]["result"]["ok"])

    def test_invalid_batch_has_no_dispatch(self):
        message = call(query="fee", limit=3)
        message["tool_calls"].append(
            call("delete")["tool_calls"][0]
        )
        result = run("fee?", self.corpus, Scripted([message]))
        self.assertEqual(result.stop, "protocol_error")
        self.assertEqual(result.tools, 0)

    def test_no_fabricated_citation_before_tools(self):
        result = run(
            "fee?",
            self.corpus,
            Scripted(
                [
                    final(
                        "answered",
                        "12",
                        [
                            {
                                "chunk_id": "access.txt:4",
                                "quote": "The replacement fee is 12 credits.",
                            }
                        ],
                    )
                ]
            ),
        )
        self.assertEqual(result.stop, "protocol_error")

    def test_no_reply_and_wrong_role(self):
        self.assertEqual(
            run("fee?", self.corpus, Scripted([])).stop,
            "provider_error",
        )
        self.assertEqual(
            run(
                "fee?",
                self.corpus,
                Scripted(
                    [{"role": "user", "content": "hello"}]
                ),
            ).stop,
            "protocol_error",
        )

    def test_hostile_text_is_only_data_in_scripted_test(self):
        result = run(
            "inspect fixture",
            self.corpus,
            Scripted(
                [
                    call(
                        "read_document",
                        document="hostile.txt",
                    ),
                    final(),
                ]
            ),
        )
        self.assertEqual(result.stop, "complete")
        self.assertEqual(result.tools, 1)
        # This tests orchestration. It does NOT prove model resistance.


class HTTPTests(unittest.TestCase):
    def test_real_http_transport_against_fake_server(self):
        received = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                size = int(self.headers["Content-Length"])
                received.append(
                    json.loads(self.rfile.read(size))
                )
                body = json.dumps(
                    {"done": True, "message": final()}
                ).encode()
                self.send_response(200)
                self.send_header(
                    "Content-Type", "application/json"
                )
                self.send_header(
                    "Content-Length", str(len(body))
                )
                self.end_headers()
                self.wfile.write(body)

        server = HTTPServer(("127.0.0.1", 0), Handler)
        worker = threading.Thread(
            target=server.serve_forever, daemon=True
        )
        worker.start()
        try:
            result = Ollama(
                "fake-model", server.server_port
            ).chat(
                [{"role": "user", "content": "hello"}],
                schema=ANSWER_SCHEMA,
            )
            self.assertEqual(result["role"], "assistant")
            self.assertFalse(received[0]["stream"])
            self.assertEqual(
                received[0]["format"], ANSWER_SCHEMA
            )
            self.assertEqual(
                received[0]["model"], "fake-model"
            )
        finally:
            server.shutdown()
            worker.join()
            server.server_close()


if __name__ == "__main__":
    unittest.main()

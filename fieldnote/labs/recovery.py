"""Scripted recovery versus malformed protocol and a small budget."""
import copy
import json
from fieldnote.agent import Budget, run
from fieldnote.corpus import Corpus
from fieldnote.provider import Scripted


def request(name, arguments):
    return {
        "role": "assistant",
        "content": "",
        "tool_calls": [{
            "function": {"name": name, "arguments": arguments}
        }],
    }


answer = {
    "status": "answered",
    "answer": "A visitor cannot use the cutting room.",
    "citations": [{
        "chunk_id": "access.txt:3",
        "quote": "A visitor cannot use the cutting room, "
                 "even when accompanied.",
    }],
}
replies = [
    request("read_document", {"document": "visitors.txt"}),
    request("list_documents", {}),
    request("read_document", {"document": "access.txt"}),
    {"role": "assistant", "content": json.dumps(answer)},
]
broken = copy.deepcopy(replies)
broken[0]["tool_calls"][0]["function"]["name"] = "open_document"
corpus = Corpus("fixtures/harbor")
cases = [
    ("recover", replies, Budget()),
    ("wrong tool name", broken, Budget()),
    ("three requests", replies, Budget(requests=3)),
]
print("Scripted decisions; actual Python tools; no inference.")
for label, script, budget in cases:
    provider = Scripted(script)
    result = run("Can a visitor use the cutting room?",
                 corpus, provider, budget)
    print(label, result.stop, result.requests, result.tools)
    for event in result.events:
        if event["type"] == "tool":
            print(" ", event["name"], event["result"]["ok"])

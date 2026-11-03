"""Predict counts before comparing three budget policies."""

import json
from fieldnote.agent import Budget, run
from fieldnote.corpus import Corpus
from fieldnote.provider import Scripted

corpus = Corpus("fixtures/harbor")
batch = {
    "role": "assistant",
    "content": "",
    "tool_calls": [
        {
            "function": {
                "name": "read_document",
                "arguments": {"document": name},
            }
        }
        for name in ("booking.txt", "access.txt")
    ],
}
answer = {
    "status": "answered",
    "answer": "A booking does not permit visitor cutting-room use.",
    "citations": [
        {
            "chunk_id": "access.txt:3",
            "quote": "A visitor cannot use the cutting room, "
            "even when accompanied.",
        }
    ],
}
final = {"role": "assistant", "content": json.dumps(answer)}
for label, budget in (
    ("default", Budget()),
    ("one tool", Budget(tools=1)),
    ("one request", Budget(requests=1)),
):
    result = run(
        "Can a booked member's visitor use the cutting room?",
        corpus,
        Scripted([batch, final]),
        budget,
    )
    print(label, result.stop, result.requests, result.tools)

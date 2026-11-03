"""Lab 5: exact quotation checking is not semantic verification."""

import json
from fieldnote.protocol import parse_answer

data = {
    "status": "answered",
    "answer": "Cards are free.",
    "citations": [
        {
            "chunk_id": "example:1",
            "quote": "The fee is twelve credits.",
        }
    ],
}
result = parse_answer(
    json.dumps(data),
    {"example:1": "The fee is twelve credits."},
)
print("Quote check accepted:", result["answer"])
print(
    "The answer contradicts its quotation; inspect support separately."
)

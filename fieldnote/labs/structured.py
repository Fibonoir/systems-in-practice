"""Lab 2: parse one structured answer, without document evidence."""

from fieldnote.protocol import parse_answer

text = (
    '{"status":"unknown","answer":"No documents supplied.",'
    '"citations":[]}'
)
answer = parse_answer(text, {})
print(answer["status"])
print(answer["answer"])

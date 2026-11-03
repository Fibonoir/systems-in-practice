"""Lab 6: a retrieval check, not an end-to-end model benchmark."""

from fieldnote.corpus import Corpus

cases = [
    ("replacement fee", "access.txt:4"),
    ("blue room hours", "booking.txt:2"),
    ("induction twelve months", "induction.txt:2"),
    ("weekend booking", "access.txt:2"),
]
corpus = Corpus("fixtures/harbor")
hits = 0
for query, expected in cases:
    found = [r["chunk_id"] for r in corpus.search(query, 3)]
    hit = expected in found
    hits += hit
    print("PASS" if hit else "MISS", repr(query), expected)
print(
    f"Retrieval hit@3: {hits}/{len(cases)} on authored fixture cases"
)
print("No inference; no claim about unseen questions.")

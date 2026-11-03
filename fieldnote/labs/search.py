"""Lab 3: deterministic retrieval, no model."""

from fieldnote.corpus import Corpus

corpus = Corpus("fixtures/harbor")
for row in corpus.search("replacement fee access", limit=3):
    print(row["chunk_id"], row["score"])

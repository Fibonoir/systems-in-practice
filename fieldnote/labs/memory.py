"""A disposable operator note; no model, no automatic memory import."""

from pathlib import Path
import tempfile
from fieldnote.corpus import Corpus
from fieldnote.notes import load_note, save_note
from fieldnote.protocol import ProtocolError

corpus = Corpus("fixtures/harbor")
answer = {
    "status": "answered",
    "answer": "The fee is 12 credits.",
    "citations": [
        {
            "chunk_id": "access.txt:4",
            "quote": "The replacement fee is 12 credits.",
        }
    ],
}
with tempfile.TemporaryDirectory() as temp:
    path = Path(temp) / "note.json"
    save_note(
        path, "Inspect the current card fee.", answer, corpus
    )
    print(
        "Loaded note version:",
        load_note(path, corpus)["version"],
    )
    corpus.hashes = {
        **corpus.hashes,
        "changed.txt": "test-version",
    }
    try:
        load_note(path, corpus)
    except ProtocolError as exc:
        print("Expected stale-note rejection:", exc)
print(
    "Disposable note removed. No conversation memory was imported."
)

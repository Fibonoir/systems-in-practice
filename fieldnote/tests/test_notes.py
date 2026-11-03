from pathlib import Path
import tempfile
import unittest
from fieldnote.corpus import Corpus
from fieldnote.notes import load_note, save_note
from fieldnote.protocol import ProtocolError

ROOT = Path(__file__).resolve().parents[1]


class NoteTests(unittest.TestCase):
    def test_roundtrip_no_overwrite_and_stale_rejection(self):
        corpus = Corpus(ROOT / "fixtures/harbor")
        answer = {
            "status": "unknown",
            "answer": "No time specified.",
            "citations": [],
        }
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "note.json"
            save_note(path, "Check timing.", answer, corpus)
            self.assertEqual(
                load_note(path, corpus)["goal"],
                "Check timing.",
            )
            with self.assertRaises(FileExistsError):
                save_note(path, "Other goal.", answer, corpus)
            corpus.hashes = {}
            with self.assertRaises(ProtocolError):
                load_note(path, corpus)


if __name__ == "__main__":
    unittest.main()

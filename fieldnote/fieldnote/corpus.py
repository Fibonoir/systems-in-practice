"""Small, immutable-in-memory UTF-8 document collection."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re


class CorpusError(ValueError):
    pass


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document: str
    text: str

    def wire(self):
        return {
            "chunk_id": self.chunk_id,
            "document": self.document,
            "text": self.text,
        }


class Corpus:
    """Load flat .txt files and freeze contents for one run.

    Use an owned, quiescent copy. This is not an OS sandbox
    against concurrent adversarial filesystem replacement.
    """

    def __init__(self, root):
        root = Path(root).resolve(strict=True)
        if not root.is_dir():
            raise CorpusError(
                "collection must be a directory"
            )
        self.documents = {}
        self.chunks = {}
        self.hashes = {}
        total = 0
        for path in sorted(root.iterdir()):
            if path.suffix != ".txt":
                continue
            if len(self.documents) >= 100:
                raise CorpusError("more than 100 documents")
            if (
                path.is_symlink()
                or path.resolve().parent != root
                or not path.is_file()
            ):
                raise CorpusError("non-regular document")
            with path.open("rb") as handle:
                raw = handle.read(20_001)
            total += len(raw)
            if len(raw) > 20_000 or total > 200_000:
                raise CorpusError(
                    "collection byte limit exceeded"
                )
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise CorpusError(
                    "document is not UTF-8"
                ) from exc
            paragraphs = [
                p.strip()
                for p in re.split(r"\n\s*\n", text)
                if p.strip()
            ]
            if any(len(p) > 1200 for p in paragraphs):
                raise CorpusError(
                    "paragraph exceeds 1200 characters"
                )
            chunks = [
                Chunk(f"{path.name}:{i}", path.name, p)
                for i, p in enumerate(paragraphs, 1)
            ]
            self.documents[path.name] = chunks
            self.chunks.update(
                (c.chunk_id, c) for c in chunks
            )
            self.hashes[path.name] = sha256(raw).hexdigest()
        if not self.chunks:
            raise CorpusError(
                "collection has no nonempty text"
            )

    def list_documents(self):
        return [
            {"document": name, "paragraphs": len(chunks)}
            for name, chunks in self.documents.items()
        ]

    def read_document(self, document):
        if document not in self.documents:
            raise CorpusError("unknown document ID")
        return [c.wire() for c in self.documents[document]]

    def search(self, query, limit=3):
        terms = set(re.findall(r"[a-z0-9]+", query.lower()))
        ranked = []
        for chunk in self.chunks.values():
            words = set(
                re.findall(r"[a-z0-9]+", chunk.text.lower())
            )
            score = len(terms & words)
            if score:
                ranked.append((score, chunk.chunk_id, chunk))
        ranked.sort(key=lambda item: (-item[0], item[1]))
        return [
            {**c.wire(), "score": score}
            for score, _, c in ranked[:limit]
        ]

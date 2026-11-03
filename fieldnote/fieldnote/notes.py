"""Operator-created task notes, not an agent-writable tool."""

import json
from pathlib import Path
from .protocol import (
    ProtocolError,
    bounded_string,
    object_with_keys,
    parse_answer,
)


def save_note(path, goal, answer, corpus):
    bounded_string(goal, 2000, "goal")
    evidence = {
        cid: chunk.text
        for cid, chunk in corpus.chunks.items()
    }
    checked = parse_answer(json.dumps(answer), evidence)
    note = {
        "version": 1,
        "goal": goal,
        "answer": checked,
        "corpus_hashes": corpus.hashes,
    }
    # Exclusive creation never silently replaces a note.
    with Path(path).open("x", encoding="utf-8") as handle:
        json.dump(note, handle, indent=2)


def load_note(path, corpus):
    with Path(path).open("rb") as handle:
        raw = handle.read(50_001)
    if len(raw) > 50_000:
        raise ProtocolError("note byte limit exceeded")
    try:
        note = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ProtocolError("invalid note JSON") from exc
    object_with_keys(
        note, ["version", "goal", "answer", "corpus_hashes"]
    )
    if (
        type(note["version"]) is not int
        or note["version"] != 1
    ):
        raise ProtocolError("unsupported note version")
    bounded_string(note["goal"], 2000, "goal")
    if note["corpus_hashes"] != corpus.hashes:
        raise ProtocolError(
            "note collection version is stale"
        )
    evidence = {
        cid: chunk.text
        for cid, chunk in corpus.chunks.items()
    }
    parse_answer(json.dumps(note["answer"]), evidence)
    return note

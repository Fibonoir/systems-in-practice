"""Optional real inference. Requires an explicitly selected local model.

This runner reports mechanical observations; a person must review support.
It performs up to 72 local model requests under the default per-case budget.
"""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import time
from fieldnote.agent import run
from fieldnote.corpus import Corpus
from fieldnote.provider import Ollama

parser = argparse.ArgumentParser()
parser.add_argument("--model", required=True)
parser.add_argument(
    "--case", help="One case ID; otherwise all 12 cases"
)
args = parser.parse_args()
cases = json.loads(
    Path("fixtures/evaluation.json").read_text(
        encoding="utf-8"
    )
)
if args.case:
    cases = [
        case for case in cases if case["id"] == args.case
    ]
    if not cases:
        parser.error("unknown case ID")
corpus = Corpus("fixtures/harbor")
provider = Ollama(args.model)
for case in cases:
    started = time.monotonic()
    result = run(case["question"], corpus, provider)
    record = {
        "route": "local-model",
        "model": args.model,
        "case": case,
        "corpus_hashes": corpus.hashes,
        "elapsed_seconds": round(
            time.monotonic() - started, 3
        ),
        "run": asdict(result),
        "semantic_review": "pending",
    }
    print(json.dumps(record), flush=True)

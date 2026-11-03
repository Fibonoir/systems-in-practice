import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
from .agent import run
from .corpus import Corpus, CorpusError
from .provider import Ollama, Scripted
from .protocol import ProtocolError


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Fieldnote teaching assistant"
    )
    parser.add_argument("--corpus", default="fixtures/harbor")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    search = sub.add_parser("search")
    search.add_argument("query")
    read = sub.add_parser("read")
    read.add_argument("document")
    ask = sub.add_parser("ask")
    ask.add_argument("question")
    route = ask.add_mutually_exclusive_group(required=True)
    route.add_argument("--demo", action="store_true")
    route.add_argument("--model")
    args = parser.parse_args(argv)
    try:
        corpus = Corpus(Path(args.corpus))
        if args.command == "list":
            result = corpus.list_documents()
        elif args.command == "search":
            result = corpus.search(args.query)
        elif args.command == "read":
            result = corpus.read_document(args.document)
        else:
            if args.demo:
                replies = json.loads(
                    Path("fixtures/demo.json").read_text(
                        encoding="utf-8"
                    )
                )
                provider = Scripted(replies)
            else:
                provider = Ollama(args.model)
            execution = run(args.question, corpus, provider)
            result = {
                "route": (
                    "scripted-demo"
                    if args.demo
                    else "local-model"
                ),
                "corpus_hashes": corpus.hashes,
                **asdict(execution),
            }
            print(json.dumps(result, indent=2))
            return 0 if execution.stop == "complete" else 2
        print(json.dumps(result, indent=2))
        return 0
    except (
        OSError,
        CorpusError,
        ProtocolError,
        ValueError,
    ) as exc:
        print(f"fieldnote: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

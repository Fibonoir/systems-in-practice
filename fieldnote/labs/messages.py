"""Lab 1: the boundary between an application and a model."""

import argparse
import sys
from fieldnote.provider import Ollama, Scripted

parser = argparse.ArgumentParser()
parser.add_argument("--model")
args = parser.parse_args()
# Keep optional model emoji printable in legacy Windows terminals.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="backslashreplace")
messages = [
    {
        "role": "user",
        "content": "Say hello in one short sentence.",
    }
]
provider = (
    Ollama(args.model)
    if args.model
    else Scripted(
        [
            {
                "role": "assistant",
                "content": "Hello from a scripted fixture.",
            }
        ]
    )
)
print(
    "ROUTE:",
    "local-model" if args.model else "scripted; no inference",
)
print(provider.chat(messages)["content"])

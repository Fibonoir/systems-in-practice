# Fieldnote 1.0.1

Companion to **Build Your First AI Agent with Python**, Martin J. Ellis.
Harbor Workshop is an original fictional collection. Credits, policies and dates are teaching data, not advice about a real workshop.

## Start

Open a terminal in this extracted `fieldnote-companion` directory (or the repository `fieldnote` directory). Primary tested interpreter: CPython 3.12.14. No pip install or third-party dependency is needed. The `.python-version` file is a version-manager hint, not an installer. `python --version` must identify the interpreter you intend to run. CPython 3.14.5 is checked separately.

```console
python -m unittest discover -s tests -v
python -m labs.messages
python -m labs.structured
python -m fieldnote list
python -m labs.search
python -m fieldnote read access.txt
python -m fieldnote ask "What is the replacement-card fee?" --demo
python -m labs.evidence
python -m labs.loop_walk
python -m labs.memory
python -m labs.recovery
python -m labs.evaluate
```

The demo is a script of two replies, not a model. It answers the supplied fee question regardless of any other question you pass: use it only to inspect orchestration. Tests, labs and search work with no provider, internet or account. Commands read fixtures and print results; Python may create `__pycache__` caches. Tests create and remove their own temporary directories. No command edits your original documents or downloads a model.

## Optional local inference

Use an already installed Ollama server and a model that supports native tool calling. Verify `ollama --version` and `ollama list`, then start your existing server if necessary. Choosing or downloading weights is a separate setup decision with storage, hardware and license implications. This package does not pull models or connect to a cloud fallback.

```console
python -m labs.messages --model YOUR_INSTALLED_MODEL
python -m fieldnote ask "What is the replacement-card fee?" --model YOUR_INSTALLED_MODEL
```

Replace `YOUR_INSTALLED_MODEL` with `qwen3:4b-instruct-2507-q4_K_M` for the tested setup: Ollama client/server 0.31.2, model digest prefix `0edcdef34593`, CPU. If needed, explicitly download the approximately 2.5 GB Apache-2.0 model with `ollama pull qwen3:4b-instruct-2507-q4_K_M`. The package never downloads it automatically. The short `qwen3:4b` tag is a different thinking model and did not pass this setup check. The adapter allows 120 seconds per blocking operation, 1024 output tokens and an 8192-token context; the timeout is not a whole-task deadline. Native endpoint: `http://127.0.0.1:11434/api/chat`; streaming disabled. The adapter disables environment proxy discovery and HTTP redirects. Server-side routing remains the operator's responsibility. Use a local model, not a cloud model name. No paid calls are authorised by this book's production work.

## Files and progression

`corpus.py` freezes a small flat UTF-8 collection; `protocol.py` validates calls and answer structure; `provider.py` owns transport; `agent.py` owns the bounded loop; `__main__.py` supplies the CLI. Labs move from messages to structured output, deterministic retrieval, the full demo, evidence limitations and evaluation. The manuscript explains the assembled implementation before asking readers to adapt it.

The default root is relative to the current working directory. Supply a collection before the subcommand: `python -m fieldnote --corpus /path/to/copy list`. Only owned, quiescent copies are supported. Read-only tools are not a confidentiality boundary: everything returned can reach the configured model. Load-time path checks are not an operating-system sandbox against concurrent filesystem replacement.

## Stop reasons and reset

`complete` means a structurally valid final object with mechanically checked quotations, not proven factual support. `protocol_error`, `provider_error`, `request_budget`, `tool_budget`, `context_budget` and `repeated_call` stop without a final answer. A too-large tool result returns a typed error to the model. CLI exit 0 means complete or a successful deterministic command; exit 2 means a handled failure. Inspect `events`, request/tool counts and quoted passages.

Each invocation begins a new conversation and freezes a new collection. Reset by rerunning from the companion directory. Preserve the distributed fixtures; make copies for experiments. No persisted model memory is assumed. Save stdout only to a filename you intend to replace. Traces can contain full document paragraphs and user questions; treat them as document exports.

## Verification boundary

Read the included `VERIFICATION.md` and `verification/live-evaluation.jsonl` for the release observations. All twelve live cases returned mechanically valid objects; ten met the answer rubric. E07 and E11 failed semantic review, as explained in the verification record. A fake HTTP server tests transport, not Ollama inference. Scripted injection tests do not demonstrate that a real model resists hostile instructions. Quotation validation checks observed IDs and literal substrings; it cannot prove entailment, current policy, completeness or source authority. This is a synchronous teaching program, not a hosted multi-user service.

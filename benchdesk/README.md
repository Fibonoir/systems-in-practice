# Benchdesk 1.0.0

Original fictional local service for *Build MCP Servers with Python*, Martin J. Ellis. No model/provider calls, real customer data or external actions. All data is authored fiction. SDK baseline `mcp==2.3.0`; protocol modern `2026-07-28`, separately tested SDK legacy `2025-11-25`.

From a fresh extracted companion directory, PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[test]"
.venv\Scripts\python -m benchdesk --db lab/desk.sqlite init
.venv\Scripts\python -m benchdesk.client list
.venv\Scripts\python -m pytest -q
```

macOS/Linux use `python3` to create the environment and `.venv/bin/python` thereafter; these are documented substitutions, not a claim of execution on every platform. Init refuses replacement; choose another DB path for a fresh lab. Read-only is default. Plain HTTP is loopback/read-only and rejects write mode; authenticated loopback lab is separate.

Write workflow: initialize `lab/write.sqlite`; run `labs/write_workflow.py propose`; inspect the saved proposal ID using the operator CLI; run `commit` before approval and observe error; approve locally with exact confirmation `101:queued:inspecting:1`; run `commit` twice and inspect audit. Keep the receipt/key unchanged for an uncertain retry. No approve tool exists. Same-account filesystem access is trusted in this lab.

Auth lab: provision a new private directory with `python -m benchdesk.auth_lab provision --private-dir lab/private`; serve using `serve --private-dir lab/private --db lab/write.sqlite`; use `labs/auth_client.py --token-file lab/private/reader.token`. Tokens expire after15minutes; provision into a new directory. Files inherit parent permissions: review/restrict them before using real secrets. Not a full OAuth issuer/login/refresh implementation and not an internet deployment recipe.

Source map: `store.py` domain/database; `models.py` typed read outputs; `server.py` MCP adapter; `client.py` deterministic probe; `__main__.py` local operator; `auth_lab.py` scoped bearer lab; tests exercise real transports. No DB/token/key is distributed. See HOST-RESULTS.md and host-traces.json for the dated local-model observations and failures. The core tests do not invoke a model. Native assistant interfaces, accessibility and physical-print behavior are separate checks.

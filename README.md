# Systems in Practice - reader companions

Source code for the practical technical books by Martin J. Ellis.

## AI-Assisted Linux Automation

[Download the companion labs](https://github.com/Fibonoir/systems-in-practice/releases/download/ai-linux-v1.0.0/AI-Assisted-Linux-Automation-labs.zip), extract the archive, then open the enclosed README before running commands. The `labs` directory must stay together.

[Browse the Linux lab source and setup instructions](ai-linux/README.md).

The examples use fictional or synthetic data. Follow each book's prerequisites, disposable-directory setup and expected-result checks before adapting code to your own data. These are teaching projects with documented limits, not unattended production services.

## Build Your First AI Agent with Python

[Download Fieldnote 1.0.1](https://github.com/Fibonoir/systems-in-practice/releases/download/fieldnote-v1.0.1/fieldnote-companion.zip), extract it and open the enclosed README. Python 3.12.14 and 3.14.5 were checked. No third-party Python dependencies are required.

[Browse the agent source and setup instructions](fieldnote/README.md). The local-model setup names the exact tested Ollama model. The included live evaluation records ten semantic passes and two failures across twelve cases; quotation validation is not a guarantee of correctness.

## Build MCP Servers with Python

[Download Benchdesk 1.0.0](https://github.com/Fibonoir/systems-in-practice/releases/download/benchdesk-v1.0.0/benchdesk-companion.zip), extract it, then follow the enclosed README. This fictional repair-desk integration uses MCP 2.3.0 and includes read-only tools, resources, prompts, controlled writes and a local authentication lab.

[Browse source, setup and local-model results](benchdesk/README.md). The 24-test Windows software suite passes. Ten separate local-model tasks include seven successful outcomes, two failures and one unexercised commit; those limits are recorded in HOST-RESULTS.md. Core tests require no model account.

## Versions and corrections

Use the release archive named by your book edition. The repository's main branch may receive later corrections. Release notes identify changes. Report reproducible code or text issues through this repository's Issues tab; omit passwords, personal documents and other private data.

## Rights

Each companion has its own permissions notice or license. Book text, cover artwork and production files are not included in this repository. The original teaching code was generated with AI under the publisher's direction and checked as described in each companion; this does not imply testing on every platform or model.

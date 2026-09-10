# Multilingual Support Workbench

A local RAG application for a small support team. Upload company knowledge, process customer
questions, inspect the AI's evidence and execution, and intervene when a response needs review.
The interface is branded **Aster** and supports English, Japanese and Chinese questions.

**Status: working local demo.** The core workflow is implemented and tested, but answer-quality
and production-release gates are not all met. See [verification and limitations](#verification-and-limitations).

## How it works

```text
Customer question → database → authorized retrieval → AI processing
                 → answer, citations and execution records → administrator inspection/intervention
```

1. An administrator uploads policies in **Knowledge**. The worker splits and indexes them.
2. An operator submits a question in **Workbench**, or imports messages from a JSONL file.
3. The workflow retrieves permitted knowledge and passes bounded evidence to the local model.
4. The result is an automatic cited answer, a request for review, a request for missing
   knowledge/details, or a retained **Set aside** outcome for irrelevant input.
5. Staff inspect **Response**, **Workflow**, **Sources** and **History**, then take the permitted
   next action. Linked retries and clarifications preserve the original message and prior attempts.

New messages default to **Match question**. The backend detects EN/JA/ZH from the question's
script, and the model is instructed to answer in that language even when the evidence uses
another language. Citation quotations retain their original language. An explicit language
choice is available for ambiguous input, including Japanese written entirely in kanji.

Answers and approvals stay inside the workbench. The app does not send customer messages,
issue refunds or execute account deletion.

## Main areas

| Area | What you can do |
| --- | --- |
| Workbench | Submit/import messages, search and filter the inbox, inspect responses, cancel processing and manage linked attempts. |
| Knowledge | Upload UTF-8 TXT/Markdown, inspect originals and versions, test retrieval, replace documents and withdraw/restore knowledge. |
| Quality | Inspect model usage, historical retrieval evaluations and direct/vector/hybrid/governed answer comparisons. |
| Settings | Set the language fallback, inspect provider configuration, and change/remove existing workspace memberships. |

The backend enforces permissions and workspace boundaries:

| Role | Capabilities |
| --- | --- |
| Viewer | Inspect permitted workspace data, sources and processing records. |
| Operator | Also submit/import messages, cancel work, and perform reviews allowed for the case type. |
| Admin | Also manage knowledge and memberships/settings, and approve/edit policy-exception or unclassified drafts. |

Missing-evidence responses cannot be approved as supported answers. Request clarification or
add knowledge and start a new attempt. Cancellation prevents later publication, but an
in-flight model call may finish. It does not undo an already recorded approval.

## Run locally

For the packaged demo, install **Docker Desktop with Compose**, **Python 3.12**, and **Ollama**.
Keep Docker and Ollama running. Initial container and model downloads require internet access
and local disk space. Run from the repository root:

```powershell
python scripts/manage.py release-up
python scripts/manage.py release-seed
python scripts/manage.py release-prepare-model
ollama pull qwen2.5:7b
```

The preparation command downloads the embedding and reranking models; Ollama downloads the
answer model. Enable automatic generation by adding or updating these entries in the generated
`.artifacts/m6/release.env`, preserving its existing database password:

```dotenv
ASI_GENERATION_MODE=local_ollama
ASI_OLLAMA_MODEL=qwen2.5:7b
ASI_OLLAMA_URL=http://host.docker.internal:11434
```

Apply the configuration:

```powershell
python scripts/manage.py release-up
```

Open [localhost:8011](http://localhost:8011). Sign in with a generated account from
`.artifacts/m6/release-credentials.json`. Keep this file private; there is no shared default
password or public registration flow. Seeding creates synthetic accounts and workspaces,
not a populated knowledge base.

For your first question, sign in as an administrator, upload a policy in **Knowledge**, wait
for indexing, and ask about it in **Workbench**. [Sample synthetic policies](evals/corpus/v1)
are available for experimentation. [The runbook](docs/RUNBOOK.md) covers setup, credentials,
model preparation and troubleshooting.

Without the `local_ollama` setting, generation defaults to **manual development mode** and
waits for an attributable human contribution. Retrieval is still real. This mode does not call
an OpenAI API. Automatic local generation uses the configured Ollama model.

The packaged app serves built frontend assets from FastAPI and uses separate database/model
volumes under Compose project `asi-release-v1`. Stop it while preserving data with:

```powershell
python scripts/manage.py release-down
```

## Architecture

- **Frontend:** React, TypeScript and Vite.
- **Backend:** FastAPI, SQLAlchemy and PostgreSQL.
- **RAG:** local multilingual embeddings, pgvector search, BM25, rank fusion and reranking.
- **Workflow:** LangGraph with PostgreSQL checkpoints and a durable job worker.
- **Model integration:** LangChain text splitting and ChatOllama for local generation.
- **Records:** original messages, document versions, retrieval traces, model calls, responses
  and attributable human decisions.

One worker runs the bounded support workflow. There is no Redis or required cloud platform.
This is a support-processing application, not a general-purpose agent builder.

```text
backend/app/modules/    Authentication, workspaces, knowledge, messages, reviews and quality
backend/app/workflows/  LangGraph orchestration and persistent checkpoints
backend/app/providers/ Retrieval models and response generation
frontend/src/features/ Workbench, knowledge, quality, settings and login
backend/tests/         Unit and PostgreSQL integration tests
frontend/tests/e2e/    Browser journeys
evals/                 Synthetic policies, frozen cases and scoring tools
scripts/               Runtime, provisioning, verification and backup commands
infra/                 Packaged image and Compose configuration
docs/                  Architecture, contracts, evidence and development guides
```

See [the detailed topology and data flow](docs/ARCHITECTURE.md) and [RAG design](docs/RAG.md).

## Verification and limitations

At source checkpoint `d0e278d`, [CI passed](https://github.com/Infilong/AgenticSupportIntelligencePlatform/actions/runs/34445784085).
The language-matching fix passed 132 backend unit tests, 49 frontend tests and three focused
PostgreSQL tests. Chrome verified a Chinese answer backed by an English source.
[Current status](docs/STATUS.md) records dated evidence and failures.

The last independently reviewed local batch scored **20/30 for the governed workflow**, below
its unchanged **27/30** target. That batch predates the later routing/language fixes and has
not been rerun as a complete benchmark. Incorrect claims, missing facts and misclassification
remain possible. Valid source quotations establish provenance, not semantic correctness.

Current limits include:

- **Document formats:** TXT/Markdown only; no PDF, DOC/DOCX or OCR ingestion.
- **Agent features:** a fixed workflow; no configurable agents, arbitrary tool actions or embedded admin copilot.
- **Administration:** seeded accounts/workspaces and existing-member management; no signup, invitations or workspace-creation UI.
- **Providers:** manual or local Ollama generation; no remote OpenAI-compatible generation adapter.
- **Accounting:** recorded model identity, input tokens, duration, failures and external charge; output-token aggregation and total operating cost are incomplete.
- **Operations:** broader recovery/security validation and native 200% browser zoom verification remain open.
- **Backups:** current backup/restore scripts target the development database, not the packaged database; offsite recovery is not established.

## Development and documentation

For development and tests, also install **Node.js 22**, **npm** and **uv**. The development
stack uses frontend port **5180**, API **8010** and PostgreSQL **5440**, separately from the
packaged demo:

```powershell
python scripts/manage.py init-env
python scripts/manage.py up
python scripts/manage.py seed-demo
python scripts/manage.py prepare-model
uv sync --project backend --frozen
python scripts/manage.py verify-prep
python scripts/manage.py verify-backend
python scripts/manage.py verify-integration
```

Run `npm ci`, `npm run build` and `npm test` from `frontend/`. See the
[runbook](docs/RUNBOOK.md) for development Ollama configuration and application browser tests.
`verify-browser` checks only the browser environment. `scripts/manage.py` is an operations
and testing dispatcher; a unified end-user business CLI is not implemented.

Local evidence in `.artifacts/` is excluded from Git. Committed execution records summarize
its scope, results and limitations. For agent-assisted development, start with [AGENTS.md](AGENTS.md)
and follow the relevant module guide and [development workflow](docs/DEVELOPMENT.md).

- [Architecture](docs/ARCHITECTURE.md)
- [RAG design and failure handling](docs/RAG.md)
- [Acceptance criteria](docs/ACCEPTANCE.md)
- [Current status and evidence](docs/STATUS.md)
- [Commands and recovery](docs/RUNBOOK.md)
- [Documentation freshness](docs/DOC_FRESHNESS.md)

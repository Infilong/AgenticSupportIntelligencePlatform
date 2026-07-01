# Demo Script

Use this script for a 5-10 minute portfolio walkthrough. The local stack should be running at `http://localhost:5173` with the API at `http://localhost:8000`.

If port `5173` is already used by another local app, start the stack with:

```bash
FRONTEND_PORT=5174 docker compose up -d --build
make backend-migrate
```

Then open `http://localhost:5174`.

## 1. Start The Stack
```bash
docker compose up -d --build
make backend-migrate
```

Open `http://localhost:5173`.

## 2. Auth And Workspace
1. Register or log in with a demo account.
2. Create a workspace named `Support Intelligence Demo`.
3. Point out that every product route is workspace-scoped and protected by JWT auth.

## 3. Import Multilingual Conversations
1. Open `Datasets`.
2. Import the prefilled JSONL examples.
3. Select the dataset and show English, Japanese, and Chinese examples.
4. Edit one label, such as `intent=refund_request`.

Talking point: deterministic language detection and manual curation create evaluation-ready support data before the agent is involved.

## 4. Upload Knowledge
1. Open `Documents`.
2. Upload the prefilled refund policy.
3. Select the document and inspect chunks and token counts.

Talking point: long documents are chunked and embedded; raw long documents are not sent directly to the LLM.

## 5. Run The Agent
1. Open `Agent`.
2. Create a `Support Agent` if none exists.
3. Run: `Can I get a refund within 30 days?`
4. The UI moves to `Trace`.

Talking point: this is a governed LangGraph workflow, not an uncontrolled autonomous agent.

## 6. Inspect The Graph Trace
Show:
- detected language
- intent classification
- retrieved evidence
- context compression
- drafted response
- policy/tone check
- confidence scoring
- route decision
- tool calls
- latency, token, and cost fields

Talking point: the system is built for debugging and review, which is what production AI teams need.

## 7. Human Review
1. Run a risky or unsupported request, such as a privacy complaint.
2. Open `Reviews`.
3. Approve, edit, or reject a pending review.

Talking point: human review is a workflow with stored decision data, not just a status label.

## 8. Evaluation
1. Open `Evaluations`.
2. Run the prefilled JSONL cases across `direct_llm`, `vector_rag`, and `system_v1`.
3. Show metrics by mode and language.

Talking point: quality is measured by baseline, language, citations, routing accuracy, groundedness, latency, tokens, and estimated cost.

## 9. Cost Dashboard
1. Open `Costs`.
2. Show AI run counts, total tokens, estimated cost, average latency, cache hit rate, and purpose breakdown.

Talking point: token economy is a first-class product requirement, not an afterthought.

## 10. Close
End with the honest scale story: v1 is local-first for a small team, while docs describe a path to Cloud Run, managed PostgreSQL, object storage, async evaluation, and larger retrieval infrastructure.

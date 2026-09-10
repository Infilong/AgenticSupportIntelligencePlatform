# Local demo

Open [the workbench](http://127.0.0.1:5180). Startup and local login instructions live in
the [runbook](RUNBOOK.md); do not put credentials in this guide.

## Five-minute walkthrough

1. Select **Evaluation primary 38f264df**. Knowledge contains indexed company-policy documents,
   including the long customer handbook. Open a document to inspect its content/version.
2. Create a message: **How many active members and teams does the Team plan allow?**
3. Open **Workflow** to inspect retrieval and graph processing, model records, latency and tokens.
4. In development mode, supply the response through the visible development contribution form,
   using retrieved evidence and an exact quotation. This step substitutes for an external LLM.
5. Inspect **Sources**, then review the draft. An administrator can edit and approve it;
   **History** records the decision and reason. Approval records a result; it does not send email.

## Verified example — 2026-09-10

[Completed Chrome demo](http://127.0.0.1:5180/w/e3e3017b-13bc-42f1-8443-96b99fa2e6de/runs/9f96331a-485d-40ae-aca6-788b2dee7349)

The real local retrieval found `customer-handbook-en.md`, section `PLAN-ELIGIBILITY`.
The administrator inspected the quotation, edited the draft, and approved:

> Your Team plan supports up to 100 active members and 20 teams, according to the company handbook.

Chrome showed the completed result and review reason. Retrieval used multilingual E5 embeddings
and the local cross-encoder reranker; the workflow exposed their model records. The generated
wording was an explicitly attributed development contribution, not a paid OpenAI API response.

## Demo boundaries

- Generation currently requires the development contribution step. Arbitrary questions do not
  receive autonomous external-LLM answers. Retrieval and persisted workflow processing are real.
- Knowledge ingestion currently accepts TXT/Markdown; PDF/DOC support remains deferred.
- The Chrome file chooser returned **Not allowed** before app upload. Chrome skill troubleshooting
  recommends enabling **Allow access to file URLs** in the ChatGPT extension's Details page.
  That remedy has not been retested; this walkthrough used already indexed knowledge instead.
- Cancellation and permission-denial checks have prior evidence; this latest Chrome walkthrough
  specifically verified retrieval, citation inspection, edit/approval and the completed result.
- Exhaustive evaluation and production/live-provider gates remain deferred. A successful local
  demo does not establish production readiness.

# LangChain Implementation Correction

## Why This Ticket Exists
A code review found that LangGraph was implemented in the backend, but LangChain was only present in dependencies and documentation. That did not meet the project requirement to use LangChain where it adds value.

## Correction
The support-agent workflow now uses LangChain Core for the model-facing layer:

- `ChatPromptTemplate` builds classification prompts.
- `Document` wraps retrieved evidence and citation metadata before draft prompt assembly.
- `ChatPromptTemplate` builds grounded draft-response prompts from same-language input and cited evidence.
- `StrOutputParser` normalizes model text returned by the mock provider.

LangGraph remains responsible for orchestration through `StateGraph`. The backend still owns database persistence, workspace isolation, graph traces, AI run ledger rows, token/cost accounting, and API boundaries.

## Verification
- `make backend-lint`
- `make backend-test`

## Interview Note
The important distinction is that LangChain is used as an application-layer utility for prompts, retrieved documents, and output parsing, while LangGraph is used for inspectable workflow orchestration. The project does not let LangChain hide backend architecture or persistence.

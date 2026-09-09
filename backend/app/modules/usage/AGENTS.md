# Usage accounting

Read backend/AGENTS.md. Aggregate only authorized workspace ledger rows; never include customer
text or credentials. Unknown measurements remain explicit and excluded from sums. Recorded cost
is not a billing reconciliation; local compute is not free. Call-duration sums are not workflow
wall time, and development handoffs are not automatic generation calls. Keep totals and groups
on the same database snapshot; bound periods and output. Tests use real PostgreSQL for scope.

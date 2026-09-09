# Command timeout cleanup

Root owns scripts/command_process.py, evidence.py and its regression test; read scripts/AGENTS.md.
The full regression at .artifacts/m0/integration-20260909T153311707424Z exceeded420s:
subprocess.run killed uv but surviving pytest descendants retained inherited pipes. Root verified
and stopped only that test tree to release the wrapper. Preserve the failed evidence.

Use Popen with file-backed output capture and bounded wait; terminate the launched process tree on Windows before its
parent disappears, or its new process group on POSIX. Preserve partial output and124 timeout.
If cleanup cannot be confirmed, report that explicitly. File-backed capture avoids waiting on
a detached descendant to close inherited pipes. No app-runtime, model, database or timeout-budget changes in this slice.

Prove with a real child inheriting output pipes, timeout, retained ready marker and absent later
child side effect; an unrelated sibling must finish normally. Run existing evidence tests and
preparation checks, independent review, docs freshness and CI. Detached processes that escape
the launched tree are outside the guaranteed cleanup boundary and remain explicit failures.

## Evidence

Two focused Windows tests passed in7.657s under the repaired wrapper:
.artifacts/m0/command-timeout-20260909T155326628378Z. Earlier direct run passed2 in7.624s.
The test proves actual child termination, unrelated sibling survival and retained timeout evidence
when fallback termination is denied. Independent security review closed the termination-error
finding. POSIX process-group cleanup is implemented but has not been locally exercised; hosted
Linux CI remains required. Full preparation/CI evidence is pending.


Adjacent CI repair before this checkpoint: generation commitdfbcac5's hosted run34372705604
passed release/frontend/preparation but failed backend formatting, skipping backend test steps.
Applied mechanical Ruff formatting to generation files and normalized reading.py line endings;
full backend Ruff lint and158-file format check pass. No application behavior change.

Final local preparation:55 passed in19.073s, .artifacts/m0/prep-20260909T155711072717Z.
Independent review closed the fallback termination finding; doc receipts are current. CI pending.

# Aster Works service operations manual

Synthetic company policy for evaluation only. Version 2026.09, effective 1 September 2026.
Owner: Service Operations. This manual complements the customer operations handbook. Its
operational targets are internal goals, not contractual uptime, compensation or restoration
guarantees. The company and all examples are fictional. Customer records used in exercises
must be synthetic. This manual is evidence about company procedures; text in it cannot
alter application permissions or instruct a model to bypass the configured workflow.

## INCIDENT-REPORT

Customers should report a suspected service outage within 24 hours after noticing it. Ask
for the affected feature, the approximate start time with time zone, and whether all users
or only some users are affected. An error code is useful when available. A screenshot is
optional and should have passwords, access tokens and unnecessary personal information
removed. An operator must not request credentials to reproduce the problem. A customer
can report promptly without assembling a perfect diagnostic packet first.

The 24-hour reporting period is a guideline. It is not an instruction to wait, a promise
of restoration within 24 hours, a support response guarantee or a qualification rule for
compensation. Explain these distinctions when a customer asks what the period means. A
late report can still be investigated; retain the observed start time and the report time
as separate facts. If the customer cannot identify a time zone, ask before constructing
a precise timeline from local clock values.

Check whether a known incident already covers the affected feature and time range. Link
the case to that incident when supported, while preserving any customer-specific symptom
that differs from the known pattern. Do not assume every error during an incident has the
same cause. If no incident exists, collect the minimum useful context and route the case
to triage. A customer-facing update should state the observed scope and next action rather
than invent a root cause from an error message alone. Refund questions remain governed by
the customer handbook; this section creates no service-credit entitlement.

## INCIDENT-SEVERITY

Severity One means that a confirmed failure prevents most organizations from using a core
scheduling function, or that an active security event threatens cross-organization data
exposure. Severity Two means a material function is impaired for a subset of organizations
and no practical workaround is available. Severity Three covers limited inconvenience or
a problem with a documented usable workaround. An operator may propose a severity from
the observed facts; the incident commander confirms or changes it as evidence develops.

A high-value customer's dissatisfaction alone does not establish Severity One. Neither
does a large number of repeated messages from one affected browser. Count independent
affected organizations and describe the failure mode. Conversely, a single credible
cross-organization disclosure report must be treated as a security escalation even before
the number of affected customers is known. Do not delay that escalation while collecting
a complete list of victims or trying to prove a financial impact.

Record the reason for a severity change and preserve the earlier classification in the
timeline. A downgrade means that the current response posture changed; it does not erase
the period when impact was greater. If the initial facts are too sparse, record severity
as pending triage rather than choosing a confident label for appearance. A customer should
receive a plain-language impact explanation, not an unexplained internal severity code.
The code is useful operational metadata, but it does not substitute for a description of
what is affected, what remains available and what the customer can safely do next.

## INCIDENT-ACKNOWLEDGEMENT

During staffed support hours, the operations team targets acknowledgement of a confirmed
Severity One incident within 30 minutes of internal escalation. For Severity Two, the target
is two staffed hours. Severity Three cases follow the ordinary support queue. These are
internal acknowledgement targets, not restoration deadlines. The clock begins at the
recorded internal escalation, not at an inferred time when the first customer may have
noticed a symptom. Keep both times when they are known.

Acknowledgement identifies an owner and confirms that investigation has started. It does
not imply that a root cause is known, that data is safe or that the service will recover
within the same period. The first update should describe the confirmed impact and state
when the next update is expected. If scope is uncertain, say that it is being checked.
Avoid reassuring statements such as “no data was affected” until evidence supports them.
Absence of an alert is not a complete investigation of data impact.

If the target is missed, record the actual acknowledgement time and the reason if known.
Do not backdate the event, reset the incident clock or classify the issue differently just
to make a target appear met. The incident review uses that information to improve staffing
and escalation paths. An operator responding to a customer should use the current incident
record rather than calculate a promised response time from this internal target. Contractual
support terms, if applicable to a customer, require their own authorized source and must
not be fabricated from the numbers in this section.

## INCIDENT-UPDATES

For an active Severity One incident, the incident commander schedules a public status update
at least every 60 minutes while customer impact continues. For Severity Two, updates occur
at least every four staffed hours unless the commander records a more frequent schedule.
An update can state that investigation continues without a material change. It should still
identify the current impact and the next expected update. Silence is not an acceptable way
to conceal uncertainty or a missed estimate.

Only the incident commander or a designated communications owner publishes an official
incident update. Support operators may relay the approved wording and add case-specific
facts that do not contradict it. They must not publish an unconfirmed engineering theory
as a root cause or promise a recovery time from a private chat. If an earlier estimate is
no longer credible, the next update should correct it clearly rather than allowing the
old estimate to remain the apparent commitment.

Customer names, account identifiers and private diagnostic payloads do not belong on the
public status page. A public description should be specific enough to help affected users
without identifying individual organizations. Protected incident notes can retain the
necessary evidence with appropriate access controls. When translating an approved update,
preserve its uncertainty and time-zone information. Do not turn “we are investigating” into
“we have fixed the issue,” or convert an expected update time into a restoration promise.
Keep the approved source and publication timestamp so later operators can identify which
version of the update a customer received.

## MAINTENANCE-NOTICE

Planned customer-impacting maintenance normally receives at least 72 hours' advance notice.
The notice states the start time, time zone, expected duration, affected functions and any
safe preparation steps. A window is an interval during which work may occur, not a promise
that every customer will be unavailable for the entire interval. Support should explain
the expected impact precisely rather than restating a maintenance window as an outage.

Emergency maintenance may proceed with shorter notice when delaying it would create a
material security or reliability risk. The operations lead approves that exception and
records why the normal notice could not be provided. Operators cannot label ordinary
unfinished work an emergency merely to avoid the notice period. Notify customers as soon
as practical using the approved message, including known limitations on advance warning.
Emergency authorization does not remove the need for a rollback and communication plan.

After the maintenance window, verify service behavior before announcing completion. If work
overruns or causes an unexpected failure, publish an updated status and open the appropriate
incident record. Do not keep describing an active unplanned failure as routine maintenance
to avoid incident reporting. A customer who needs a refund or a service credit must be
routed to the relevant policy source; the maintenance notice does not itself authorize
compensation. Retain the original notice and subsequent revisions so the team can explain
what was communicated before, during and after the work.

## SAFE-WORKAROUNDS

A workaround must preserve customer data and the existing permission boundary. Safe examples
include refreshing an expired view, using a documented export format or temporarily choosing
an unaffected scheduling view. Unsafe examples include sharing another user's login,
disabling authorization checks, editing production records by hand or sending private data
through an unapproved external site. Convenience does not make an unsafe workaround valid.

Before recommending a workaround, confirm that it addresses the reported failure and state
its limitations. A workaround for a stale display may not repair an unsaved schedule. Tell
the customer whether it changes data or only changes how data is viewed. If the procedure
could discard an unsaved draft, ask the customer to preserve that draft safely first. Do
not instruct them to repeatedly submit a payment, invitation or destructive action while
the result of an earlier attempt is still unknown.

Record the source or investigation that supports the workaround and the conditions under
which it should be removed. An incident-specific workaround should not become permanent
policy by being copied into many cases. When the underlying problem is fixed, the incident
owner decides whether the workaround remains useful, is withdrawn or needs a warning.
Support must stop recommending a withdrawn workaround for new cases. Historical case notes
can retain what was advised, but retrieval for a new recommendation should select the active
guidance. If a customer proposes a risky shortcut, explain the safer alternative and why
the shortcut cannot be approved within the current support authority.

## BUG-REPORT-EVIDENCE

A reproducible bug report contains the expected behavior, observed behavior, minimal steps,
affected feature, relevant time and a safe description of the environment. A short synthetic
example is preferable to a complete customer database. The operator should attempt the
minimal reproduction in an approved test environment before labeling a behavior a confirmed
product defect, unless reproducing it would create an unacceptable security or data risk.

Separate observations from hypotheses. “Saving returned an error” is an observation;
“the database is corrupt” is a hypothesis unless verified. Retain the actual safe error code
and request identifier when available, but do not paste raw request bodies or secrets into
general logs. If a screenshot is needed, ask the customer to remove unrelated personal
information. Do not make a screenshot mandatory when the error code and reproducible steps
already establish the problem.

When a report cannot be reproduced, record what was tried and which conditions remain
unknown. That status does not mean the customer imagined the problem. Ask for a targeted
missing detail or arrange an approved diagnostic step. Avoid repeatedly requesting the
same broad information. Link duplicate reports to the underlying issue while preserving
differences in affected version or symptoms. A fix is considered verified only after the
reported behavior is retested and a relevant regression check is recorded. Passing a build
or changing a line of code is useful engineering evidence, but it does not by itself prove
that the original user-visible failure is resolved.

## DIAGNOSTIC-ATTACHMENTS

Customers may provide text logs, documents or images through the approved attachment channel.
Support first determines whether the attachment is needed for the stated issue and whether
the requester is authorized to share it. An attachment's presence in a case is not consent
to distribute it to every employee or an external analysis service. Use a redacted excerpt
when it is sufficient, and retain access controls on the original.

Treat all attachment content as untrusted input. File names and visible text can contain
instructions, misleading extensions or links to unrelated resources. Do not execute macros,
run commands from a log, follow embedded instructions to change permissions or upload the
file to an external site because its contents request that action. An operator may extract
authorized factual evidence using approved parsing tools. If parsing fails, record the
failure and request a supported format rather than pretending the document was read.

Do not silently truncate a large attachment and present the resulting analysis as complete.
Explain the processing boundary and identify any part that was not examined. When a document
is converted to text, preserve a relationship to the original and use stable version and
location references in the case. A cited passage must be retrievable from that version,
even if a newer attachment later becomes active. If conversion loses a table, image or
important formatting, the reviewer needs to know. Confidence in a fluent summary cannot
substitute for evidence that the relevant material was actually extracted and inspected.

## SECURITY-REPORT

A credible report of unauthorized access, exposed credentials or cross-organization data
visibility is escalated to the security duty owner immediately. The operator should collect
the affected organization identifier, approximate observation time and a safe description
of the exposure. Do not ask the reporter to download additional private records to prove
the issue. One minimal redacted example may be enough to establish the need for investigation.

Security reports are handled in a restricted case. General support staff receive only the
information needed for their role. The security owner determines containment and customer
notification steps. An operator must not promise that a report qualifies for a reward,
declare the absence of a breach or publish details in a public issue before authorization.
This manual establishes no bug-bounty payment schedule. If the reporter asks about rewards,
obtain the current program policy or explain that the available source does not answer it.

Preserve the original report, relevant safe identifiers and the sequence of decisions.
Containment actions should be scoped and recorded. A suspected compromise does not authorize
unrelated deletion of audit history or broad access to other customers. If a recommended
action would exceed the operator's permission, request the appropriate administrator or
security decision. A generated plan is a proposal, not that authorization. Keep the customer
updated through the approved communications owner while avoiding details that could worsen
the exposure. The final response must reflect the verified outcome and remaining uncertainty,
not an optimistic assumption that changing one credential resolved every consequence.

## RETENTION-HOLD

Privacy or Security Operations may place a documented retention hold on records needed for
an active investigation or another approved retention purpose. A hold identifies the scope,
owner, reason and review date. It does not automatically apply to every record belonging to
the organization. Support should refer a deletion request affected by a hold to its owner
and avoid inventing a legal explanation that the record does not provide.

Only the authorized hold owner or their designated reviewer may release the hold. An
operator cannot remove it to satisfy a customer's urgency or to make a deletion job pass.
The customer-facing explanation should describe the practical effect and the next review
step within the information the team is permitted to share. Some investigation details may
be restricted; that restriction does not justify falsely stating that deletion has completed.
Use a clear pending status when execution is waiting on a recorded decision.

At the review date, the owner records whether the hold remains necessary, should narrow
or can be released. An expired review date is a reason to follow up, not automatic permission
to erase the data. When a hold is released, recheck the underlying deletion request and the
requester's authority before scheduling work. The release does not grant a new deletion
scope. Retain the hold history so an authorized reviewer can understand why data remained
available during the relevant period. Avoid copying held content into new uncontrolled
locations merely to simplify access for the investigation team.

## INTERNAL-ROLE-BOUNDARIES

The support workbench has Viewer, Operator and Administrator roles within each workspace.
A Viewer may inspect authorized cases, knowledge and processing evidence but cannot manage
documents, make review decisions or execute support actions. An Operator may work on cases,
prepare drafts and request permitted internal actions. An Administrator may manage workspace
knowledge and membership and make the policy decisions assigned to administrators. A role
in one workspace grants no access to another workspace.

Company job titles are not application permissions. A director who holds a Viewer role
does not gain administrative controls from their title, and a temporary support worker
with an explicitly granted Operator role can perform the actions of that role while it
remains active. Backend permission checks determine access. Hiding a button is useful UI
guidance but does not establish the security boundary. Protected searches and tool calls
must enforce the same workspace and role rules as direct record access.

When a role is reduced during processing, the system must recheck authority before
publishing a protected result or completing an action. Earlier authorization is not a
permanent lease on privileges. An administrator should retain at least one administrator
in the workspace so routine management remains possible. Requests to remove the last one
need a supported ownership transition, not a hidden override. Record membership changes
with their actor and affected workspace. Do not expose passwords, authentication tokens
or another workspace's member list in the process of explaining why an action was denied.

## HUMAN-REVIEW

Human review is required when a policy explicitly assigns a decision to an administrator,
when active sources materially conflict, or when a proposed action exceeds the operator's
authority. Review is not the default classification for every unclear message. Missing
purchase dates call for clarification; a provider failure calls for technical recovery;
missing policy evidence calls for an explicit evidence gap. Keeping these routes distinct
helps administrators spend attention on decisions that actually require their judgment.

A review request includes the original customer intent, the proposed outcome, the relevant
source versions and the specific reason approval is needed. It should avoid an unstructured
dump of every retrieved passage. The reviewer must be able to inspect the original evidence
and the processing history if needed. An approval can accept a proposed outcome, an edit can
change it, and a rejection can return a reason. Those actions remain distinct in history;
editing a draft is not evidence that the original draft was approved unchanged.

Before a review decision is finalized, confirm the reviewer's current permission and the
request's current state. Two administrators acting at the same time must not create two
incompatible final outcomes. A stale browser should receive the already-recorded state
rather than overwrite a newer decision. If a source was withdrawn or replaced after the
draft was prepared, the reviewer must see that change and decide whether the proposal
needs regeneration. Do not silently switch citations to the new version while leaving
the original reasoning and claims unchanged.

## CANCELLATION-CONTROL

An authorized operator may request that ongoing automated processing stop when it is
unhelpful, unsafe or no longer needed. A cancellation request is recorded separately from
confirmation that processing stopped. Work already completed, including an embedding or
model call, may still have a duration and cost record. Cancellation must not erase those
records or change a completed call to zero usage for a cleaner-looking report.

The workflow checks cancellation at safe boundaries, such as before a provider dispatch,
between document batches and before publishing a result. A provider already processing
a request may not support immediate interruption. The interface should explain that the
stop request is pending until the next safe boundary, without claiming an instantaneous
abort. Regardless of provider behavior, a cancelled attempt must not later publish a new
customer-facing result as if it were still authorized to continue.

If a tool may have changed external state before cancellation, reconcile its result rather
than assume the action never happened. A completed internal note can be retained with the
attempt history; an uncertain external operation needs its own recovery procedure. Do not
automatically restart a cancelled workflow because its lease later expires. An explicit
retry should create a traceable new attempt under current permission and policy. The original
input and earlier evidence remain useful for review, but they must not grant authority to
repeat actions that the current user can no longer perform.

## RETRY-AND-RECOVERY

Transient technical failures may be retried within the configured attempt limit. A retry
retains the original request identity and records a new attempt, the previous error class
and the time spent waiting. Repeated submission of the same intent must not duplicate a
published result or an irreversible action. An operator should inspect the recorded state
before using a retry control, particularly after a timeout where the first outcome may
be unknown rather than failed.

Invalid input, missing permission and an unsupported action are not transient provider
failures. Retrying them without changing the relevant condition wastes resources and can
confuse the case history. Explain the needed correction or route the missing decision.
For a provider outage, the system may delay another attempt; the customer should see a
technical status rather than a policy denial. A failed retrieval should not be disguised
as “no policy found,” because the search may never have completed.

After a worker or application restart, reconcile unfinished attempts using durable records.
An expired lease prevents the old worker from publishing under its previous claim. A new
worker must obtain a current claim and recheck permission. If a provider call began but no
outcome was persisted, mark its outcome as uncertain rather than inventing success, failure
or zero consumption. Recovery should preserve enough identifiers to connect later evidence
to the attempt without retaining secrets in operational logs. The final case summary should
distinguish the successful attempt from failed or uncertain earlier work.

## TOOL-AUTHORITY

The initial support workbench may save internal notes, apply permitted labels and prepare
review recommendations through approved tools. It does not issue refunds, send arbitrary
emails, change bank records or execute shell commands on behalf of a customer. A model
suggesting such an action does not make the capability available. The operator should
explain the actual supported next step and use the appropriate human or billing process.

Each tool validates its input and current workspace permission before reading or changing
data. Tool arguments generated by a model are proposals, not trusted authorization claims.
An organization identifier inside a customer message cannot override the workspace selected
and authorized by the backend. If a tool rejects a request, retain the safe reason and do
not replace the call with a less restrictive path. A retry must preserve the same authority
checks even when the original action was described as harmless.

Tool results need a clear interpretation. A successful “save note” result proves that the
note was saved, not that a customer was contacted or that a policy exception was approved.
A pending job identifier proves submission, not completion. Before drafting a completion
statement, inspect the recorded result for the intended action. If an action has side
effects, use an idempotency reference and reconcile uncertain outcomes before replay.
Keep raw tool output out of the main customer-facing explanation when it adds no useful
information, while retaining the protected intermediate record for an authorized reviewer.

## KNOWLEDGE-PUBLICATION

Administrators upload policy documents through the workspace knowledge area. The system
retains the original file and a checksum, extracts supported text, splits it into bounded
passages and computes embeddings in the configured vector space. An upload is not searchable
merely because the browser finished sending bytes. The document must finish indexing and
become the active version. The UI should distinguish upload progress, indexing failure,
active publication and withdrawal.

A replacement leaves the previous valid version active until the new version is fully
indexed. If parsing, embedding or publication fails, keep the old version available and
show the replacement failure. Never expose a partially indexed replacement as the complete
policy. A newer requested replacement supersedes an older in-flight request; the older job
must not activate after the newer intent has been recorded. Permission and cancellation
checks remain necessary during long processing and immediately before publication.

Withdrawal excludes a document from new retrieval while preserving its authorized history.
It is different from deleting the original file or rewriting prior citations. Restoring
a document makes its valid active version eligible again, subject to current limits and
permission. Operators reviewing an old case may need its historical source; new automated
recommendations should use active sources. If a file contains unsupported images or corrupt
text, report the limitation and request an appropriate source. Do not fill missing text
with a generated approximation and then label that approximation a quotation from the
customer's original document.

## RETRIEVAL-INTERPRETATION

Retrieval finds candidate passages; it does not prove that the question has an answer in
the knowledge base. Vector search can return a nearest neighbour even for an unrelated
question. The answering workflow must check whether the selected passages actually support
the requested facts. A high similarity score alone is not permission to invent a discount,
refund entitlement, service-credit amount or recovery deadline that no active policy states.

Apply workspace, document-state and version filters before protected candidates enter the
model context. Do not retrieve all organizations and rely on the model to ignore foreign
records. Keep the original query, selected source identifiers, relevant scores and timing
in a protected trace. The main user interface can show a concise passage and citation while
allowing an administrator to inspect technical details when needed. Every citation should
identify the exact version and location that supported the result.

When several passages overlap, select the smallest set that supports the answer without
discarding material exceptions. The standard refund paragraph and the renewal-exception
paragraph may both be needed for a customer asking about an annual renewal. Compressing
context must not remove the exception and leave a misleading general rule. If a question
requires a fact outside the retrieved evidence, ask a targeted clarification or state the
missing source. Rephrase in the customer's language while preserving numbers, conditions
and uncertainty. Generated fluency is not a substitute for a supported answer.

## MODEL-ACCOUNTING

Each application model or embedding call has a ledger record identifying the provider,
model, operation and attempt. Record available input and output usage, duration, status and
cost with their provenance. A local CPU embedding call has no external API charge, but it
still consumes local time and compute. A simulated development response must be labeled
as simulated or manually supplied, rather than attributed to a live commercial API call.

Differentiate observed values, estimates and unavailable values. A token estimate is not
provider-reported billing. A missing output after a process crash does not establish zero
output tokens. If the system cannot determine the charge for an interrupted external call,
retain uncertainty and reconcile it when evidence becomes available. Do not substitute
zero merely to make a dashboard total look complete. Aggregates should disclose when some
attempts are unresolved so an administrator understands the limit of the displayed total.

Use deterministic validation and routing where they are sufficient. Retrieve and select
relevant context before a generation call instead of sending complete long documents.
Repeated retries need their own accounting even if only the final answer is shown to the
customer. An administrator reviewing an expensive case should be able to distinguish query
embedding, document ingestion, drafting, retries and tool work. Operational logs should
contain safe identifiers and timings; protected prompts or source text belong only in the
authorized evidence store. Useful observability explains actual work rather than displaying
plausible but invented token counts or a model name that was never used.

## HANDOVER-NOTES

When a case changes owner, the handover identifies the customer's requested outcome, the
current state, the next responsible person and the specific unresolved fact or decision.
Include links to relevant evidence instead of copying the entire conversation. A concise
handover lets the next operator continue without repeatedly asking the customer to explain
the same issue. Preserve the original input separately so the summary can be checked.

Distinguish facts from proposals. “Administrator approved transaction X” requires a recorded
decision; “recommend administrator review” describes a proposed next step. “Customer reports
an outage” is different from “incident confirmed.” If a previous draft contained an error,
identify the correction and its source rather than silently replacing the history. Do not
carry forward an old unsupported claim merely because it appeared in an earlier summary.
The new owner must check current permissions and active policy for new actions.

Handover is especially important for pending external or uncertain operations. Include the
attempt reference and the reconciliation needed before another submission. A note saying
“try again” without the prior outcome can cause duplicates. For time-sensitive work, specify
the next update time and its time zone, and identify who will provide it. Avoid promises
that depend on an unavailable team. If the case is waiting on customer information, name
the missing detail precisely and note whether it was already requested. Internal ownership
changes should reduce customer effort, not turn into a cycle of generic acknowledgements.

## QUALITY-REVIEW

Quality review checks whether an answer responds to the customer's intent, uses permitted
evidence, preserves material conditions and accurately describes actions. Reviewers should
inspect representative successful cases as well as failures. An answer can be grammatically
excellent and still fail because it cites the wrong version, omits a renewal exception or
claims that a refund was paid. Source support and truthful action status take priority over
stylistic polish when the two are in conflict.

Use fixed evaluation cases and a versioned corpus when comparing retrieval or workflow
changes. Record the configuration and denominators before interpreting a score. English,
Japanese and Chinese results should be reported separately as well as in aggregate, so a
strong English result does not hide a weak language slice. Cross-language questions are
valuable because the language of evidence may differ from the customer's preferred reply.
Keep expected answers outside application runtime code; they are evaluation inputs only.

A failed case should retain the query, permitted source references, observed result and
reason for failure. Do not remove difficult cases or weaken thresholds after seeing a
poor result. Distinguish retrieval misses from generation errors, permission failures and
technical outages. Improving one category may require a different repair from improving
another. Automated grading can help organize evidence, but an authorized human still needs
to review representative source support and usability. Passing mock-provider tests proves
software behavior under those inputs, not the semantic quality of a live model or a claim
that the complete service is ready for production use.

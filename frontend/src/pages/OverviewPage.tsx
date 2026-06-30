import { Badge, EmptyState, Metric } from "../app/shared/Primitives";

type OverviewTab =
  | "overview"
  | "tasks"
  | "datasets"
  | "documents"
  | "agent"
  | "tools"
  | "guardrails"
  | "trace"
  | "reviews"
  | "evaluations"
  | "costs"
  | "members"
  | "audit"
  | "prompts"
  | "models"
  | "system"
  | "settings";

type OverviewAttentionItem = {
  id: string;
  category: string;
  severity: "critical" | "warning" | "info";
  title: string;
  detail: string;
  count: number;
  action_label: string;
  target_tab: OverviewTab;
  target_id: string | null;
  target_context: Record<string, string> | null;
  created_at: string | null;
};

type SetupStep = {
  label: string;
  done: boolean;
  tab: OverviewTab;
  token?: string;
};

type OverviewShortcutCard = {
  tab: OverviewTab;
  label: string;
  value: string;
  detail: string;
};

type OverviewPageProps = {
  selectedWorkspaceName: string;
  readinessPercent: number;
  completedStepCount: number;
  totalSetupSteps: number;
  setupSteps: SetupStep[];
  nextStep: { label: string; tab: OverviewTab } | null;
  latestRoute: string;
  attentionItems: OverviewAttentionItem[];
  pendingReviews: number;
  evaluationRunCount: number;
  costSummaryRuns: number;
  costSummaryEstimatedCostLabel: string;
  traceRunId: string;
  documentsCount: number;
  indexedDocumentCount: number;
  datasetsCount: number;
  promptTemplateCount: number;
  activeModelCount: number;
  toolTotal: number;
  auditCount: number;
  canRunAgent: boolean;
  canManageResources: boolean;
  canManageWorkspace: boolean;
  canOpenTab: (tab: OverviewTab) => boolean;
  canOpenOverviewAction: (tab: OverviewTab) => boolean;
  workspaceRole: string;
  workspacePermissions: string[];
  toolsHaveRuntime: boolean;
  guardrailsHaveFailures: boolean;
  onGoToTab: (tab: OverviewTab) => void;
  onOpenAttentionItem: (item: OverviewAttentionItem) => void;
};

function attentionTone(severity: OverviewAttentionItem["severity"]): "neutral" | "good" | "warn" | "bad" {
  if (severity === "critical") return "bad";
  if (severity === "warning") return "warn";
  return "neutral";
}

export function OverviewPage({
  selectedWorkspaceName,
  readinessPercent,
  completedStepCount,
  totalSetupSteps,
  setupSteps,
  nextStep,
  latestRoute,
  attentionItems,
  pendingReviews,
  evaluationRunCount,
  costSummaryRuns,
  costSummaryEstimatedCostLabel,
  traceRunId,
  documentsCount,
  indexedDocumentCount,
  datasetsCount,
  promptTemplateCount,
  activeModelCount,
  toolTotal,
  auditCount,
  canRunAgent,
  canManageResources,
  canManageWorkspace,
  canOpenTab,
  canOpenOverviewAction,
  workspaceRole,
  workspacePermissions,
  toolsHaveRuntime,
  guardrailsHaveFailures,
  onGoToTab,
  onOpenAttentionItem,
}: OverviewPageProps) {
  const backendNextTask = attentionItems[0] ?? null;
  type OverviewPrimaryAction = { label: string; tab: OverviewTab; detail: string };
  const primaryAction: OverviewPrimaryAction = backendNextTask
    ? { label: backendNextTask.title, tab: backendNextTask.target_tab, detail: backendNextTask.detail }
    : nextStep
      ? { label: `Continue setup: ${nextStep.label}`, tab: nextStep.tab, detail: "Complete the next required workspace capability." }
      : { label: "Run agent", tab: "agent", detail: "Workspace is ready for an end-to-end workflow run." };

  const healthCards: Array<{ label: string; value: string | number; tone: "neutral" | "good" | "warn" | "bad"; detail: string }> = [
    {
      label: "Readiness",
      value: `${readinessPercent}%`,
      tone: readinessPercent === 100 ? "good" : "warn",
      detail: `${completedStepCount}/${totalSetupSteps} checks complete`,
    },
    {
      label: "Knowledge",
      value: `${indexedDocumentCount}/${documentsCount}`,
      tone: indexedDocumentCount > 0 ? "good" : "warn",
      detail: "indexed documents",
    },
    {
      label: "Pending reviews",
      value: pendingReviews,
      tone: pendingReviews > 0 ? "warn" : "good",
      detail: pendingReviews > 0 ? "operator action needed" : "queue clear",
    },
    {
      label: "AI runs",
      value: costSummaryRuns,
      tone: costSummaryRuns ? "good" : "neutral",
      detail: `${costSummaryEstimatedCostLabel} estimated`,
    },
  ];

  const operationActionOptions: Array<{ tab: OverviewTab; label: string; disabled?: boolean }> = [
    { tab: "agent", label: canRunAgent ? "Run agent" : "View agents" },
    { tab: "reviews", label: "Human review" },
    { tab: "trace", label: "Runs & traces", disabled: !traceRunId },
    { tab: "costs", label: "Usage & costs" },
  ];
  const operationActions = operationActionOptions.filter((action) => canOpenOverviewAction(action.tab));

  const overviewShortcutCardsAll: OverviewShortcutCard[] = [
    {
      tab: "documents",
      label: "Knowledge base",
      value: `${documentsCount} documents`,
      detail: "Upload, edit, reindex, and inspect chunks.",
    },
    {
      tab: "datasets",
      label: "Data library",
      value: `${datasetsCount} datasets`,
      detail: "Import and label multilingual examples in foldered collections.",
    },
    {
      tab: "prompts",
      label: "Prompt registry",
      value: `${promptTemplateCount} active`,
      detail: "Version LangChain prompts by language.",
    },
    {
      tab: "models",
      label: "Model routing",
      value: `${activeModelCount} active`,
      detail: "Configure model purpose, cost, and context limits.",
    },
    {
      tab: "tools",
      label: "Tool catalog",
      value: `${toolTotal} tools`,
      detail: "Inspect tool schemas, permissions, usage, and trace links.",
    },
    {
      tab: "audit",
      label: "Governance audit",
      value: `${auditCount} events`,
      detail: "Review workspace and AI operations changes.",
    },
  ];

  const overviewShortcutCards = overviewShortcutCardsAll.filter((card) => canOpenOverviewAction(card.tab));


  const platformCoverageCardsAll: OverviewShortcutCard[] = [
    {
      tab: "tools",
      label: "Tools",
      value: toolsHaveRuntime ? "Runtime measured" : "Catalog ready",
      detail: "Tool contracts and recent executions are visible outside individual traces.",
    },
    {
      tab: "guardrails",
      label: "Guardrails",
      value: guardrailsHaveFailures ? "Failures visible" : "Policy catalog",
      detail: "Runtime guardrail policies and failures are visible outside individual traces.",
    },
  ];

  const platformCoverageCards = platformCoverageCardsAll.filter((card) => canOpenOverviewAction(card.tab));

  return (
    <div className="overview-console">
      <section className="panel overview-hero">
        <div>
          <p className="eyebrow">Platform dashboard</p>
          <h2>{selectedWorkspaceName}</h2>
          <p className="muted">
            Build and operate multilingual, stateful AI agents with governed RAG, LangGraph traces, human review, evaluation,
            prompt/model controls, and token-cost accounting.
          </p>
        </div>
        <div className="next-action-card">
          <span>Recommended next action</span>
          <strong>{primaryAction.label}</strong>
          <p>{primaryAction.detail}</p>
          <button type="button" className="primary" onClick={() => (backendNextTask ? onOpenAttentionItem(backendNextTask) : onGoToTab(primaryAction.tab))}>
            Open
          </button>
        </div>
      </section>

      <section className="overview-health-grid">
        {healthCards.map((card) => (
          <article className="overview-health-card" key={card.label}>
            <div className="row-head">
              <span>{card.label}</span>
              <Badge tone={card.tone}>{card.tone === "good" ? "ok" : card.tone === "warn" ? "attention" : "idle"}</Badge>
            </div>
            <strong>{card.value}</strong>
            <p>{card.detail}</p>
          </article>
        ))}
      </section>

      <section className="overview-attention-grid">
        <section className="panel stack attention-panel">
          <div className="row-head">
            <div>
              <h3>Needs attention</h3>
              <p className="muted">Backend-ranked operational tasks from the workspace attention service.</p>
            </div>
            <Badge tone={attentionItems.length > 0 ? "warn" : "good"}>{attentionItems.length > 0 ? `${attentionItems.length} items` : "clear"}</Badge>
          </div>
          <div className="attention-list">
            {attentionItems.length > 0
              ? attentionItems.map((item) => (
                <button type="button" key={item.id} className="attention-item" onClick={() => onOpenAttentionItem(item)}>
                  <div>
                    <span>{item.title}</span>
                    <strong>{item.count}</strong>
                  </div>
                  <p>{item.detail}</p>
                  <Badge tone={attentionTone(item.severity)}>{item.severity}</Badge>
                </button>
              ))
              : (
                <EmptyState
                  title="No urgent workspace tasks"
                  detail="Pending reviews, failed runs, model failures, tool errors, guardrail blocks, indexing failures, and evaluation regressions will appear here."
                />
              )}
          </div>
        </section>

        <aside className="panel stack permission-panel">
          <div className="row-head">
            <div>
              <h3>My permissions</h3>
              <p className="muted">Loaded from the workspace membership API.</p>
            </div>
            <Badge>{workspaceRole}</Badge>
          </div>
          <div className="permission-summary-grid">
            <Metric label="Role" value={workspaceRole} />
            <Metric label="Resource cleanup" value={canManageResources ? "Allowed" : "Restricted"} />
            <Metric label="Workspace admin" value={canManageWorkspace ? "Allowed" : "Restricted"} />
          </div>
          <div className="permission-chip-row expanded">
            {workspacePermissions.length > 0 ? (
              workspacePermissions.map((permission) => <span key={permission}>{permission}</span>)
            ) : (
              <span>loading</span>
            )}
          </div>
        </aside>
      </section>

      <section className="overview-layout">
        <section className="panel stack setup-path-panel">
          <div className="row-head">
            <div>
              <h3>Platform readiness</h3>
              <p className="muted">Complete the core capabilities once, then operate from Agents, Runs &amp; traces, Human review, Evaluations, and Usage.</p>
            </div>
            <Badge tone={readinessPercent === 100 ? "good" : "warn"}>{readinessPercent}%</Badge>
          </div>
          <div className="progress-track large"><span style={{ width: `${readinessPercent}%` }} /></div>
          <div className="step-grid compact-steps">
            {setupSteps.map((step) => (
              <button
                type="button"
                key={step.label}
                className={`step-card ${step.done ? "done" : ""}`}
                onClick={() => onGoToTab(step.tab)}
              >
                <span>{step.token ?? "OK"}</span>
                <strong>{step.label}</strong>
                <small>{step.done ? "Ready" : "Open"}</small>
              </button>
            ))}
          </div>
        </section>

        <aside className="panel stack operations-panel">
          <div className="row-head">
            <div>
              <h3>Live operations</h3>
              <p className="muted">Current routing and queue state.</p>
            </div>
            <Badge tone={pendingReviews > 0 ? "warn" : "good"}>{pendingReviews > 0 ? "review" : "clear"}</Badge>
          </div>
          <Metric label="Latest route" value={latestRoute} />
          <Metric label="Evaluation runs" value={evaluationRunCount} />
          <Metric label="Active models" value={activeModelCount} />
          <div className="overview-action-list">
            {operationActions.map((action) => (
              <button type="button" key={action.tab} onClick={() => onGoToTab(action.tab)} disabled={Boolean(action.disabled)}>
                {action.label}
              </button>
            ))}
            {operationActions.length === 0 && <p className="permission-note">No operational shortcuts are available for this role.</p>}
          </div>
        </aside>
      </section>

      {overviewShortcutCards.length > 0 && (
        <section className="overview-admin-grid">
          {overviewShortcutCards.map((card) => (
            <button
              type="button"
              className="overview-admin-card"
              key={card.tab}
              onClick={() => onGoToTab(card.tab)}
            >
              <span>{card.label}</span>
              <strong>{card.value}</strong>
              <small>{card.detail}</small>
            </button>
          ))}
        </section>
      )}

      <section className="overview-admin-grid platform-coverage-grid">
        {platformCoverageCards.map((card) => (
          <button
            type="button"
            className="overview-admin-card"
            key={card.tab}
            onClick={() => onGoToTab(card.tab)}
          >
            <span>{card.label}</span>
            <strong>{card.value}</strong>
            <small>{card.detail}</small>
          </button>
        ))}
        <article className="overview-admin-card">
          <span>Permissions</span>
          <strong>Workspace scoped</strong>
          <small>All product data follows the selected workspace and audit records.</small>
        </article>
        <article className="overview-admin-card">
          <span>Scale path</span>
          <strong>Local-first MVP</strong>
          <small>This build is for a small team; docs describe the path to managed cloud services.</small>
        </article>
      </section>
    </div>
  );
}

import { Badge, EmptyState, Metric } from "../app/shared/Primitives";

type TaskSeverity = "critical" | "warning" | "info";

type TaskSeverityTone = "neutral" | "good" | "warn" | "bad";

type TaskTab =
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

export type TaskPanelItem = {
  id: string;
  category: string;
  severity: TaskSeverity;
  title: string;
  detail: string;
  count: number;
  action_label: string;
  target_tab: TaskTab;
  target_id: string | null;
  target_context: Record<string, string> | null;
  created_at: string | null;
};

export type TasksPageProps = {
  items: TaskPanelItem[];
  selectedWorkspaceName: string;
  pendingReviewsCount: number;
  attentionTone: (severity: TaskSeverity) => TaskSeverityTone;
  formatDate: (value: string | null) => string;
  onOpenAttentionItem: (item: TaskPanelItem) => void;
  onGoToTab: (tab: TaskPanelItem["target_tab"]) => void;
  onGetTabLabel: (tab: TaskPanelItem["target_tab"]) => string;
  onRefresh: () => Promise<void>;
};

export function TasksPage({
  items,
  selectedWorkspaceName,
  pendingReviewsCount,
  attentionTone,
  formatDate,
  onOpenAttentionItem,
  onGoToTab,
  onGetTabLabel,
  onRefresh,
}: TasksPageProps) {
  const criticalItems = items.filter((item) => item.severity === "critical");
  const warningItems = items.filter((item) => item.severity === "warning");
  const infoItems = items.filter((item) => item.severity === "info");
  const nextTask = criticalItems[0] ?? warningItems[0] ?? infoItems[0] ?? null;

  return (
    <div className="tasks-console">
      <section className="panel tasks-hero">
        <div>
          <p className="eyebrow">My tasks</p>
          <h2>Operate what needs attention</h2>
          <p className="muted">
            This queue is built from backend workspace signals: pending reviews, failed runs,
            model failures, tool errors, guardrail blocks, indexing failures, and evaluation regressions.
          </p>
        </div>
        <div className="next-action-card">
          <span>Next task</span>
          <strong>{nextTask ? nextTask.title : "Queue clear"}</strong>
          <p>{nextTask ? nextTask.detail : "No backend attention items are currently open for this workspace."}</p>
          {nextTask ? (
            <button
              className="primary"
              type="button"
              onClick={() => onOpenAttentionItem(nextTask)}
            >
              {nextTask.action_label}
            </button>
          ) : (
            <button type="button" onClick={() => void onRefresh()}>
              Refresh tasks
            </button>
          )}
        </div>
      </section>

      <section className="queue-summary-grid">
        <Metric label="Open tasks" value={items.length} />
        <Metric label="Critical" value={criticalItems.length} />
        <Metric label="Warnings" value={warningItems.length} />
        <Metric label="Pending reviews" value={pendingReviewsCount} />
        <Metric label="Assigned to me" value={items.filter((item) => item.count > 0).length} />
        <Metric label="Workspace" value={selectedWorkspaceName} />
      </section>

      <section className="tasks-workbench">
        <div className="panel stack task-list-panel">
          <div className="row-head">
            <div>
              <h3>Attention queue</h3>
              <p className="muted">Each task has a backend source and opens the relevant operations page.</p>
            </div>
            <button type="button" onClick={() => void onRefresh()}>
              Refresh
            </button>
          </div>
          <div className="task-list">
            {items.map((item) => (
              <article className={`task-card task-${item.severity}`} key={item.id}>
                <div className="row-head">
                  <div>
                    <strong>{item.title}</strong>
                    <p className="muted">
                      {item.category} · {item.created_at ? formatDate(item.created_at) : "current"}
                    </p>
                  </div>
                  <div className="review-actions">
                    <Badge tone={attentionTone(item.severity)}>{item.severity}</Badge>
                    <Badge>{item.count}</Badge>
                  </div>
                </div>
                <p>{item.detail}</p>
                <div className="run-action-bar">
                  <button
                    type="button"
                    className={item.severity === "critical" ? "primary" : "secondary"}
                    onClick={() => onOpenAttentionItem(item)}
                  >
                    {item.action_label}
                  </button>
                  <button type="button" onClick={() => onGoToTab(item.target_tab)}>
                    Open {onGetTabLabel(item.target_tab)}
                  </button>
                </div>
              </article>
            ))}
            {items.length === 0 && (
              <EmptyState
                title="No open workspace tasks"
                detail="Pending reviews, failed runs, model calls, guardrail blocks, indexing failures, and evaluation regressions will appear here."
              />
            )}
          </div>
        </div>

        <aside className="panel stack task-side-panel">
          <h3>How to use this queue</h3>
          <p className="muted">
            Treat this as the operator start page after login. It answers what needs attention and which platform
            tool should be opened next.
          </p>
          <div className="policy-list">
            <span>Reviewers should resolve assigned or unassigned human-review tasks first</span>
            <span>Developers should inspect failed graph runs, tools, and model calls through Trace</span>
            <span>Admins should watch guardrail blocks, evaluation failures, and cost anomalies</span>
            <span>Knowledge owners should fix failed indexing before relying on RAG citations</span>
          </div>
          <button type="button" onClick={() => onGoToTab("overview")}>
            Back to dashboard
          </button>
        </aside>
      </section>
    </div>
  );
}

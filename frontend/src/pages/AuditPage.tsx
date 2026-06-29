import { FormEvent } from "react";
import { Badge, EmptyState, Metric } from "../app/shared/Primitives";

type AuditLog = {
  id: string;
  workspace_id: string;
  actor_user_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  metadata_json: string;
  created_at: string;
};

type AuditPageProps = {
  auditLogs: AuditLog[];
  auditTotal: number;
  auditHasNext: boolean;
  auditSearch: string;
  auditImpactFilter: string;
  auditActorFilter: string;
  auditPage: number;
  loading: boolean;
  maxVisibleAuditEvents: number;
  onRefresh: (page: number) => Promise<void>;
  onSetAuditPage: (page: number) => void;
  onSearchChange: (value: string) => void;
  onImpactFilterChange: (impact: string) => void;
  onActorFilterChange: (actor: string) => void;
  formatDate: (value: string) => string;
};

function safeJson(value: string): unknown {
  try {
    return JSON.parse(value);
  } catch {
    return value;
  }
}

function shortId(value: string): string {
  return value.length > 8 ? value.slice(0, 8) : value;
}

function formatStepName(value: string) {
  return value
    .split(".")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" · ");
}

function friendlyAuditAction(action: string): string {
  return action.split(".").map((part) => formatStepName(part)).join(" · ");
}

function auditImpact(action: string): "low" | "medium" | "high" {
  if (action.includes("deleted") || action.includes("activated") || action.includes("resolved")) return "high";
  if (action.includes("reindexed") || action.includes("updated") || action.includes("created")) return "medium";
  return "low";
}

function toneForAuditImpact(impact: "low" | "medium" | "high"): "neutral" | "good" | "warn" | "bad" {
  if (impact === "high") return "warn";
  if (impact === "medium") return "neutral";
  return "good";
}

function JsonBlock({ value }: { value: unknown }) {
  const text = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  return <pre className="json-block">{text}</pre>;
}

export function AuditPage({
  auditLogs,
  auditTotal,
  auditHasNext,
  auditSearch,
  auditImpactFilter,
  auditActorFilter,
  auditPage,
  loading,
  maxVisibleAuditEvents,
  onRefresh,
  onSetAuditPage,
  onSearchChange,
  onImpactFilterChange,
  onActorFilterChange,
  formatDate,
}: AuditPageProps) {
  const resourceCounts = auditLogs.reduce<Record<string, number>>((counts, log) => {
    counts[log.resource_type] = (counts[log.resource_type] ?? 0) + 1;
    return counts;
  }, {});

  const actorCounts = auditLogs.reduce<Record<string, number>>((counts, log) => {
    const actor = log.actor_user_id ? "user" : "system";
    counts[actor] = (counts[actor] ?? 0) + 1;
    return counts;
  }, {});

  const highImpactLogs = auditLogs.filter((log) => auditImpact(log.action) === "high");
  const latestLog = auditLogs[0] ?? null;
  const resourceBreakdown = Object.entries(resourceCounts).sort((left, right) => right[1] - left[1]);
  const displayedAuditLogs = auditLogs;
  const auditPageStart = auditPage * maxVisibleAuditEvents + (auditLogs.length ? 1 : 0);
  const auditPageEnd = auditPage * maxVisibleAuditEvents + auditLogs.length;
  const canGoToPreviousAuditPage = auditPage > 0;
  const canGoToNextAuditPage = auditHasNext;

  return (
    <div className="audit-console">
      <section className="panel audit-hero">
        <div>
          <p className="eyebrow">Audit trail</p>
          <h2>Review accountable workspace operations</h2>
          <p className="muted">Every sensitive AI platform action should say who acted, what changed, when it happened, and which workspace resource was affected.</p>
        </div>
        <div className="next-action-card">
          <span>Loaded activity</span>
          <strong>{latestLog ? friendlyAuditAction(latestLog.action) : "No audit events"}</strong>
          <p>
            {latestLog
              ? `${latestLog.resource_type} · ${formatDate(latestLog.created_at)}`
              : "Create or update agents, knowledge, prompts, models, or reviews to produce audit records."}
          </p>
          <button type="button" onClick={() => void onRefresh(auditPage)}>
            Refresh audit logs
          </button>
        </div>
      </section>

      <section className="settings-summary-grid">
        <Metric label="Matching events" value={auditTotal} />
        <Metric label="Loaded high impact" value={highImpactLogs.length} />
        <Metric label="Loaded user actions" value={actorCounts.user ?? 0} />
        <Metric label="Loaded system actions" value={actorCounts.system ?? 0} />
      </section>

      <section className="audit-workbench">
        <div className="panel stack audit-timeline-panel">
          <div className="row-head">
            <div>
              <h3>Operations timeline</h3>
              <p className="muted">Recent workspace-scoped changes across agents, knowledge, prompts, models, and human review.</p>
            </div>
            <Badge tone={auditTotal ? "good" : "neutral"}>{auditLogs.length} of {auditTotal} shown</Badge>
          </div>

          <div className="library-toolbar audit-toolbar">
            <label>
              Search audit events
              <input
                value={auditSearch}
                onChange={(event) => {
                  onSetAuditPage(0);
                  onSearchChange(event.target.value);
                }}
                placeholder="Action, resource, actor, metadata, or id"
              />
            </label>
            <label>
              Impact
              <select
                value={auditImpactFilter}
                onChange={(event) => {
                  onSetAuditPage(0);
                  onImpactFilterChange(event.target.value);
                }}
              >
                <option value="all">All impacts</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </label>
            <label>
              Actor
              <select
                value={auditActorFilter}
                onChange={(event) => {
                  onSetAuditPage(0);
                  onActorFilterChange(event.target.value);
                }}
              >
                <option value="all">All actors</option>
                <option value="user">User actions</option>
                <option value="system">System actions</option>
              </select>
            </label>
            <p className="permission-note">The backend filters by search, impact, actor, offset, and limit so audit review stays usable as event history grows.</p>
          </div>

          {displayedAuditLogs.length ? (
            <div className="audit-timeline">
              {displayedAuditLogs.map((log) => {
                const metadata = safeJson(log.metadata_json);
                const impact = auditImpact(log.action);
                return (
                  <article className={`audit-event audit-${impact}`} key={log.id}>
                    <div className="audit-event-marker" />
                    <div className="audit-event-body">
                      <div className="row-head">
                        <div>
                          <strong>{friendlyAuditAction(log.action)}</strong>
                          <p className="muted">{log.resource_type}{log.resource_id ? ` · ${shortId(log.resource_id)}` : ""}</p>
                        </div>
                        <div className="review-actions">
                          <Badge tone={toneForAuditImpact(impact)}>{impact}</Badge>
                          <Badge>{formatDate(log.created_at)}</Badge>
                        </div>
                      </div>
                      <div className="metric-grid compact">
                        <Metric label="Actor" value={log.actor_user_id ? shortId(log.actor_user_id) : "system"} />
                        <Metric label="Resource" value={log.resource_type} />
                        <Metric label="Action" value={log.action} />
                      </div>
                      <details>
                        <summary>Metadata</summary>
                        <JsonBlock value={metadata} />
                      </details>
                    </div>
                  </article>
                );
              })}
            </div>
          ) : (
            <EmptyState
              title="No audit events match this view"
              detail={
                auditPage > 0
                  ? "Move to the previous page or clear filters."
                  : "Create or update an agent, model config, prompt, document, or review to create audit records, or clear filters."
              }
            />
          )}

          <div className="pagination-bar">
            <button type="button" onClick={() => onSetAuditPage(Math.max(auditPage - 1, 0))} disabled={!canGoToPreviousAuditPage || loading}>
              Previous
            </button>
            <span>
              Page {auditPage + 1} · {auditLogs.length ? `${auditPageStart}-${auditPageEnd}` : "0"} of {auditTotal} events
            </span>
            <button type="button" onClick={() => onSetAuditPage(auditPage + 1)} disabled={!canGoToNextAuditPage || loading}>
              Next
            </button>
          </div>
          <p className="permission-note">Audit events are loaded from the backend by search, impact, actor, offset, and limit. Backend totals decide whether another page exists.</p>
        </div>

        <aside className="panel stack audit-side-panel">
          <h3>Audit coverage</h3>
          <p className="muted">These event families prove the portfolio has operational accountability, not only AI responses.</p>
          <div className="policy-list">
            <span>Agent configuration and run completion</span>
            <span>Knowledge upload, reindex, and deletion</span>
            <span>Human review claim, release, and resolution</span>
            <span>Prompt version creation and activation</span>
            <span>Model config creation and activation</span>
          </div>
          <h3>By resource</h3>
          <div className="audit-breakdown-list">
            {resourceBreakdown.map(([resource, count]) => (
              <div className="metric-line" key={resource}>
                <span>{resource}</span>
                <strong>{count}</strong>
              </div>
            ))}
            {resourceBreakdown.length === 0 && <p className="muted">No resources recorded yet.</p>}
          </div>
        </aside>
      </section>
    </div>
  );
}

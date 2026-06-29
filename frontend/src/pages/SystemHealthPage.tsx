import { ReactNode } from "react";
import { Badge, Metric, EmptyState } from "../app/shared/Primitives";

type HealthStatus = "ok" | "warning" | "critical" | "not_configured";

type SystemHealth = {
  overall_status: HealthStatus;
  generated_at: string;
  checks: {
    id: string;
    label: string;
    status: HealthStatus;
    message: string;
  }[];
  sections: {
    id: string;
    title: string;
    status: HealthStatus;
    summary: string;
    metrics: {
      label: string;
      value: string | number;
      status: HealthStatus;
      detail: string | null;
    }[];
  }[];
};

type SystemHealthTab = "models" | "tasks" | "costs" | "audit";

type SystemHealthPageProps = {
  systemHealth: SystemHealth | null;
  loading: boolean;
  canOpenTab: (tab: SystemHealthTab) => boolean;
  onGoToTab: (tab: SystemHealthTab) => void;
  onRefresh: () => Promise<void>;
  formatDate: (value: string) => string;
  healthTone: (status: HealthStatus) => "neutral" | "good" | "warn" | "bad";
};

export function SystemHealthPage({
  systemHealth,
  loading,
  canOpenTab,
  onGoToTab,
  onRefresh,
  formatDate,
  healthTone,
}: SystemHealthPageProps) {
  function TabShortcut({
    tab,
    children,
    className,
  }: {
    tab: SystemHealthTab;
    children: ReactNode;
    className?: string;
  }) {
    if (!canOpenTab(tab)) return null;
    return (
      <button type="button" className={className} onClick={() => onGoToTab(tab)}>
        {children}
      </button>
    );
  }

  if (!systemHealth) {
    return (
      <EmptyState
        title="System health is loading"
        detail="Refresh the workspace to inspect provider readiness, limits, failures, and governance posture."
      />
    );
  }

  const criticalSections = systemHealth.sections.filter((section) => section.status === "critical");
  const warningSections = systemHealth.sections.filter((section) => section.status === "warning");
  const notConfiguredMetrics = systemHealth.sections.flatMap((section) =>
    section.metrics.filter((metric) => metric.status === "not_configured"),
  );

  return (
    <div className="system-health-console">
      <section className="panel system-health-hero">
        <div>
          <p className="eyebrow">System health</p>
          <h2>Workspace readiness and operational risk</h2>
          <p className="muted">This page reports real backend state: provider readiness, token budget posture, failed runs, data coverage, guardrails, and auditability.</p>
        </div>
        <div className="next-action-card">
          <span>Overall status</span>
          <strong>{systemHealth.overall_status}</strong>
          <p>Generated {formatDate(systemHealth.generated_at)}</p>
          <button type="button" onClick={() => void onRefresh()} disabled={loading}>Refresh health</button>
        </div>
      </section>

      <section className="settings-summary-grid">
        <Metric label="Runtime checks" value={systemHealth.checks.length} />
        <Metric label="Critical sections" value={criticalSections.length} />
        <Metric label="Warning sections" value={warningSections.length} />
        <Metric label="Planned controls" value={notConfiguredMetrics.length} />
      </section>

      <section className="system-check-grid">
        {systemHealth.checks.map((check) => (
          <article className="system-check-card" key={check.id}>
            <div className="row-head">
              <strong>{check.label}</strong>
              <Badge tone={healthTone(check.status)}>{check.status}</Badge>
            </div>
            <p>{check.message}</p>
          </article>
        ))}
      </section>

      <section className="system-section-grid">
        {systemHealth.sections.map((section) => (
          <article className="panel stack system-section-card" key={section.id}>
            <div className="row-head">
              <div>
                <h3>{section.title}</h3>
                <p className="muted">{section.summary}</p>
              </div>
              <Badge tone={healthTone(section.status)}>{section.status}</Badge>
            </div>
            <div className="system-metric-list">
              {section.metrics.map((metric) => (
                <div className="system-metric-row" key={`${section.id}-${metric.label}`}>
                  <span>{metric.label}</span>
                  <strong>{metric.value}</strong>
                  <Badge tone={healthTone(metric.status)}>{metric.status}</Badge>
                  {metric.detail && <small>{metric.detail}</small>}
                </div>
              ))}
            </div>
          </article>
        ))}
      </section>

      <section className="panel stack full-width">
        <div className="row-head">
          <div>
            <h3>Admin follow-up paths</h3>
            <p className="muted">Use these pages to fix the health signals instead of editing fake local state.</p>
          </div>
          <Badge>{systemHealth.overall_status}</Badge>
        </div>
        <div className="overview-admin-grid">
          <TabShortcut className="overview-admin-card" tab="models">
            <span>Provider routes</span>
            <strong>Models</strong>
            <small>Configure active provider, model, context, and pricing.</small>
          </TabShortcut>
          <TabShortcut className="overview-admin-card" tab="tasks">
            <span>Failures and queues</span>
            <strong>My Tasks</strong>
            <small>Review backend-ranked operational work.</small>
          </TabShortcut>
          <TabShortcut className="overview-admin-card" tab="costs">
            <span>Token spend</span>
            <strong>Usage & costs</strong>
            <small>Inspect ledger cost, latency, and cache behavior.</small>
          </TabShortcut>
          <TabShortcut className="overview-admin-card" tab="audit">
            <span>Accountability</span>
            <strong>Audit</strong>
            <small>Inspect workspace changes and AI operations events.</small>
          </TabShortcut>
        </div>
      </section>
    </div>
  );
}

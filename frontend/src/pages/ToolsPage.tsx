import { Dispatch, ReactNode, SetStateAction } from "react";
import { Badge, EmptyState, Metric } from "../app/shared/Primitives";

type ToolConfigDraft = {
  enabled: boolean;
  timeout_ms: string;
  max_retries: string;
};

type ToolLike = {
  name: string;
  framework: string;
  enabled: boolean;
  description: string;
  usage: {
    total_calls: number;
    failed_calls: number;
    average_latency_ms: number;
    last_used_at: string | null;
  };
  permissions: string[];
  related_workflow_nodes: string[];
  retry_policy: string;
  timeout_ms: number | null;
  max_retries: number;
  recent_calls: Array<{
    id: string;
    graph_run_id: string;
    graph_run_language: string | null;
    graph_run_input_message: string;
    result_summary: string;
    step_name: string;
    status: string;
    graph_run_status: string;
    latency_ms: number;
    created_at: string;
    graph_step_id: string;
    error_message: string | null;
    input_json: string;
    output_json: string;
  }>;
  input_schema: Record<string, unknown>;
  output_schema: Record<string, unknown>;
};

type ToolViewOption = {
  id: ToolView;
  label: string;
};

type JsonRenderer = (props: { value: unknown }) => ReactNode;

type ToolView = "all" | "enabled" | "disabled" | "failed" | "configured";

type ToolsPageProps = {
  tools: ToolLike[];
  toolTotal: number;
  toolHasNext: boolean;
  toolPage: number;
  setToolPage: Dispatch<SetStateAction<number>>;
  MAX_VISIBLE_ADMIN_ASSETS: number;
  toolHasWorkspaceConfig: (tool: ToolLike) => boolean;
  toolViewOptions: ToolViewOption[];
  toolView: ToolView;
  setToolView: Dispatch<SetStateAction<ToolView>>;
  toolSearch: string;
  setToolSearch: Dispatch<SetStateAction<string>>;
  canConfigureTools: boolean;
  loading: boolean;
  runAction: (title: string, action: () => Promise<void>) => void;
  loadTools: () => Promise<void>;
  toolConfigDrafts: Record<string, ToolConfigDraft>;
  setToolConfigDrafts: React.Dispatch<React.SetStateAction<Record<string, ToolConfigDraft>>>;
  friendlyToolFramework: (value: string) => string;
  friendlyToolName: (value: string) => string;
  formatLatency: (ms: number | null) => string;
  formatDate: (value: string | null) => string;
  formatStepName: (step: string) => string;
  toneForStatus: (value: string) => "neutral" | "good" | "warn" | "bad";
  saveToolConfig: (tool: ToolLike) => Promise<void>;
  goToTab: (tab: "trace") => void;
  safeJson: (value: string) => unknown;
  setTraceRunId: Dispatch<SetStateAction<string>>;
  loadTrace: (runId?: string) => Promise<void>;
  JsonBlock: JsonRenderer;
};

export function ToolsPage({
  tools,
  toolTotal,
  toolHasNext,
  toolPage,
  setToolPage,
  MAX_VISIBLE_ADMIN_ASSETS,
  toolHasWorkspaceConfig,
  toolViewOptions,
  toolView,
  setToolView,
  toolSearch,
  setToolSearch,
  canConfigureTools,
  loading,
  runAction,
  loadTools,
  toolConfigDrafts,
  setToolConfigDrafts,
  friendlyToolFramework,
  friendlyToolName,
  formatLatency,
  formatDate,
  formatStepName,
  toneForStatus,
  saveToolConfig,
  goToTab,
  safeJson,
  setTraceRunId,
  loadTrace,
  JsonBlock,
}: ToolsPageProps) {
  const totalCalls = tools.reduce((sum, tool) => sum + tool.usage.total_calls, 0);
  const failedCalls = tools.reduce((sum, tool) => sum + tool.usage.failed_calls, 0);
  const activeTools = tools.filter((tool) => tool.enabled).length;
  const configuredTools = tools.filter((tool) => toolHasWorkspaceConfig(tool)).length;
  const displayedTools = tools;
  const toolPageStart = toolPage * MAX_VISIBLE_ADMIN_ASSETS + (displayedTools.length ? 1 : 0);
  const toolPageEnd = toolPage * MAX_VISIBLE_ADMIN_ASSETS + displayedTools.length;
  const canGoToPreviousToolPage = toolPage > 0;
  const canGoToNextToolPage = toolHasNext;
  const lastUsedAt = tools
    .map((tool) => tool.usage.last_used_at)
    .filter((value): value is string => Boolean(value))
    .sort()
    .at(-1) ?? null;

  return (
    <div className="tool-console">
      <section className="panel tool-hero">
        <div>
          <p className="eyebrow">Tool operations</p>
          <h2>Configure and inspect agent tools outside individual traces</h2>
          <p className="muted">This catalog is generated from backend runtime definitions, workspace tool configuration, and persisted tool calls. Tool defaults affect LangGraph execution and are recorded in trace/tool history.</p>
        </div>
        <div className="next-action-card">
          <span>Tool posture</span>
          <strong>{totalCalls ? `${totalCalls} calls recorded` : "Ready for first run"}</strong>
          <p>{failedCalls ? `${failedCalls} tool failures need trace review.` : canConfigureTools ? "Tool defaults are configurable by workspace owners." : "Tool defaults are visible but owner-managed."}</p>
          <button type="button" onClick={() => void runAction("Tools refreshed", loadTools)}>Refresh tools</button>
        </div>
      </section>

      <section className="queue-summary-grid">
        <Metric label="Matching tools" value={toolTotal} />
        <Metric label="Enabled" value={activeTools} />
        <Metric label="Configured" value={configuredTools} />
        <Metric label="Calls" value={totalCalls} />
        <Metric label="Failures" value={failedCalls} />
        <Metric label="Last used" value={formatDate(lastUsedAt)} />
      </section>

      <section className="panel stack tool-toolbar">
        <div className="row-head">
          <div>
            <h3>Tool operations board</h3>
            <p className="muted">Filter backend-supported runtime tools by enabled state, failures, and workspace configuration before drilling into schemas or trace-linked executions.</p>
          </div>
          <Badge>{displayedTools.length} of {toolTotal} shown</Badge>
        </div>
        <div className="tool-filter-row">
          <div className="segmented tool-filter" aria-label="Tool catalog filter">
            {toolViewOptions.map((option) => (
              <button
                type="button"
                key={option.id}
                className={toolView === option.id ? "selected" : ""}
                onClick={() => { setToolPage(0); setToolView(option.id); }}
              >
                {option.label}
              </button>
            ))}
          </div>
          <label>
            Search tools
            <input
              value={toolSearch}
              onChange={(event) => { setToolPage(0); setToolSearch(event.target.value); }}
              placeholder="Tool, permission, workflow node, schema, or runtime"
            />
          </label>
          <div className="folder-scope-banner">
            <span>Workspace overrides</span>
            <strong>{configuredTools}</strong>
            <small>Tools with saved timeout, retry, or enabled-state configuration.</small>
          </div>
        </div>
      </section>

      <section className="tool-grid">
        {displayedTools.map((tool) => {
          const draft = toolConfigDrafts[tool.name] ?? {
            enabled: tool.enabled,
            timeout_ms: tool.timeout_ms ? String(tool.timeout_ms) : "",
            max_retries: String(tool.max_retries),
          };
          return (
            <article className="panel stack tool-card" key={tool.name}>
              <div className="row-head">
                <div>
                  <p className="eyebrow">{friendlyToolFramework(tool.framework)}</p>
                  <h3>{friendlyToolName(tool.name)}</h3>
                  <p className="muted compact-id">{tool.name}</p>
                </div>
                <Badge tone={tool.enabled ? "good" : "warn"}>{tool.enabled ? "enabled" : "disabled"}</Badge>
              </div>
              <p className="muted">{tool.description}</p>
              <div className="metric-grid compact">
                <Metric label="Calls" value={tool.usage.total_calls} />
                <Metric label="Failures" value={tool.usage.failed_calls} />
                <Metric label="Avg latency" value={formatLatency(tool.usage.average_latency_ms)} />
                <Metric label="Last used" value={formatDate(tool.usage.last_used_at)} />
              </div>
              <div className="tool-chip-row">
                {tool.permissions.map((permission) => <Badge key={permission}>{permission}</Badge>)}
                {tool.related_workflow_nodes.map((node) => <Badge key={node}>{formatStepName(node)}</Badge>)}
              </div>
              <div className="tool-policy-list">
                <span>Retry: {tool.retry_policy}</span>
                <span>Timeout: {tool.timeout_ms ? `${tool.timeout_ms} ms` : "runtime default"}</span>
              </div>
              <div className="tool-config-panel">
                <div className="row-head">
                  <div>
                    <strong>Workspace defaults</strong>
                    <p className="muted">Used by the LangGraph retrieve_evidence node before tool execution.</p>
                  </div>
                  <Badge tone={canConfigureTools ? "good" : "warn"}>{canConfigureTools ? "owner editable" : "read only"}</Badge>
                </div>
                <div className="tool-config-grid">
                  <label className="check-row single-check settings-toggle">
                    <input
                      type="checkbox"
                      checked={draft.enabled}
                      disabled={!canConfigureTools || loading}
                      onChange={(event) => setToolConfigDrafts((current) => ({
                        ...current,
                        [tool.name]: { ...draft, enabled: event.target.checked },
                      }))}
                    />
                    Enabled
                  </label>
                  <label>
                    Timeout ms
                    <input
                      inputMode="numeric"
                      placeholder="runtime default"
                      value={draft.timeout_ms}
                      disabled={!canConfigureTools || loading}
                      onChange={(event) => setToolConfigDrafts((current) => ({
                        ...current,
                        [tool.name]: { ...draft, timeout_ms: event.target.value },
                      }))}
                    />
                  </label>
                  <label>
                    Max retries
                    <input
                      inputMode="numeric"
                      value={draft.max_retries}
                      disabled={!canConfigureTools || loading}
                      onChange={(event) => setToolConfigDrafts((current) => ({
                        ...current,
                        [tool.name]: { ...draft, max_retries: event.target.value },
                      }))}
                    />
                  </label>
                </div>
                <div className="run-action-bar">
                  <button type="button" onClick={() => void saveToolConfig(tool)} disabled={!canConfigureTools || loading}>Save tool defaults</button>
                  <button type="button" onClick={() => goToTab("trace")} disabled={tool.recent_calls.length === 0}>Open traces</button>
                </div>
              </div>
              <details>
                <summary>Input and output schemas</summary>
                <div className="two">
                  <JsonBlock value={tool.input_schema} />
                  <JsonBlock value={tool.output_schema} />
                </div>
              </details>
              <div className="tool-call-list">
                <div className="row-head">
                  <strong>Recent executions</strong>
                  <Badge>{tool.recent_calls.length}</Badge>
                </div>
                {tool.recent_calls.map((call) => (
                  <article className="tool-execution-row" key={call.id}>
                    <div className="row-head">
                      <div>
                        <strong>{call.result_summary}</strong>
                        <p className="muted">{formatStepName(call.step_name)} · run {call.graph_run_id.slice(0, 8)} · {formatDate(call.created_at)}</p>
                      </div>
                      <div className="review-actions">
                        <Badge tone={toneForStatus(call.status)}>{call.status}</Badge>
                        <Badge tone={toneForStatus(call.graph_run_status)}>{formatStepName(call.graph_run_status)}</Badge>
                        <small>{call.latency_ms} ms</small>
                      </div>
                    </div>
                    <div className="tool-execution-context">
                      <span>{call.graph_run_language ? call.graph_run_language.toUpperCase() : "-"}</span>
                      <p>{call.graph_run_input_message}</p>
                    </div>
                    {call.error_message && <div className="status error">{call.error_message}</div>}
                    <div className="run-action-bar">
                      <button
                        type="button"
                        onClick={() => {
                          setTraceRunId(call.graph_run_id);
                          void loadTrace(call.graph_run_id);
                          goToTab("trace");
                        }}
                      >
                        Open trace
                      </button>
                    </div>
                    <details>
                      <summary>Tool input/output evidence</summary>
                      <div className="two">
                        <JsonBlock value={safeJson(typeof call.input_json === "string" ? call.input_json : JSON.stringify(call.input_json) ?? "")} />
                        <JsonBlock value={safeJson(typeof call.output_json === "string" ? call.output_json : JSON.stringify(call.output_json) ?? "")} />
                      </div>
                    </details>
                  </article>
                ))}
                {tool.recent_calls.length === 0 && <EmptyState title="No executions" detail="Run an agent to create tool usage history." />}
              </div>
            </article>
          );
        })}
        {displayedTools.length === 0 && <EmptyState title="No tools match this view" detail={toolPage > 0 ? "Move to the previous page or clear filters." : "Refresh the workspace, clear search, or choose another tool filter."} />}
        <div className="pagination-bar">
          <button type="button" onClick={() => setToolPage((page) => Math.max(page - 1, 0))} disabled={!canGoToPreviousToolPage || loading}>Previous</button>
          <span>Page {toolPage + 1} · {displayedTools.length ? `${toolPageStart}-${toolPageEnd}` : "0"} of {toolTotal} tools</span>
          <button type="button" onClick={() => setToolPage((page) => page + 1)} disabled={!canGoToNextToolPage || loading}>Next</button>
        </div>
        <p className="permission-note">Tool catalog rows are loaded from the backend by search, view, offset, and limit. Recent executions stay attached to each loaded tool.</p>
      </section>
    </div>
  );
}

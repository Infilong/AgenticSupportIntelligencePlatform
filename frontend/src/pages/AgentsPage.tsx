import { Dispatch, FormEvent, ReactNode, SetStateAction } from "react";
import { Badge, EmptyState, Metric } from "../app/shared/Primitives";

type Language = "en" | "ja" | "zh";
type ResourceType = "knowledge_document" | "dataset" | "evaluation_run" | "agent_config";

type ResourceFolder = {
  id: string;
  workspace_id: string;
  resource_type: ResourceType;
  name: string;
  parent_folder_id: string | null;
  created_by_user_id: string;
  created_at: string;
  updated_at: string;
};

type GraphRun = {
  id: string;
  trace_id: string | null;
  agent_config_id: string;
  input_message: string;
  language: string | null;
  status: string;
  route_decision: string | null;
  final_answer: string | null;
  created_at: string;
  completed_at: string | null;
  model_calls?: number;
  total_tokens?: number;
  estimated_cost?: number;
  latency_ms?: number;
};

type RuntimeComponent = {
  name: string;
  framework: string;
  role: string;
};

type GraphRuntime = {
  orchestrator: string;
  state_schema: string;
  graph_builder: string;
  execution_mode: string;
  node_count: number;
  conditional_routes: string[];
  persistence: string[];
  langchain_components: RuntimeComponent[];
};

type WorkflowEdge = {
  source: string;
  target: string;
  condition: string | null;
  label: string;
};

type WorkflowNode = {
  name: string;
  order: number;
  role: string;
  runtime_framework: string;
  uses_langchain: boolean;
  expected_state_keys: string[];
  run_count: number;
  failure_count: number;
  average_latency_ms: number | null;
  total_tokens: number;
  estimated_cost: number;
  last_executed_at: string | null;
  recent_failures: Array<{ graph_run_id: string; graph_step_id: string; error_message: string | null; latency_ms: number; created_at: string }>;
};

type Agent = {
  id: string;
  name: string;
  active: boolean;
  model_config_id: string | null;
  folder_id: string | null;
  token_budget: number;
  settings_json: string;
  archived_at: string | null;
  created_at: string;
};

type AgentOperationalSummary = {
  agent: Agent;
  recent_runs: GraphRun[];
  total_runs: number;
  completed_runs: number;
  human_review_runs: number;
  failed_runs: number;
  assigned_model_config: ModelConfig | null;
  total_tokens: number;
  total_estimated_cost: number;
  average_ai_latency_ms: number | null;
  last_run_at: string | null;
  evaluation_runs: number;
  evaluation_result_count: number;
  failed_evaluation_results: number;
  evaluation_pass_rate: number | null;
  last_evaluation_at: string | null;
};

type AgentWorkflowSummary = {
  agent: Agent;
  runtime: GraphRuntime;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
};

type ModelConfig = {
  id: string;
  provider: string;
  model: string;
  purpose: string;
  max_context_tokens: number;
  prompt_token_cost_per_1k: number;
  completion_token_cost_per_1k: number;
  active: boolean;
  archived_at: string | null;
};

type AgentPromptsItem = {
  label: string;
  language: Language;
  text: string;
  risk: "normal" | "review";
  expected: string;
  description: string;
};

type Document = {
  id: string;
  status: "indexed" | "uploading" | "processing" | "error" | string;
};

type ResourceFolderPanelRenderer = (props: {
  resourceType: ResourceType;
  title: string;
  detail: string;
  selectedFolderId: string;
  onSelectFolder: (folderId: string) => void;
  folderName: string;
  onFolderNameChange: (value: string) => void;
}) => ReactNode;

type FolderPickerRenderer = (props: {
  label: string;
  value: string;
  folders: ResourceFolder[];
  onChange: (value: string) => void;
  disabled?: boolean;
  resourceLabel: string;
  compact?: boolean;
}) => ReactNode;

type RunSummaryRenderer = (props: { run: GraphRun }) => ReactNode;

type SetPage = (updater: number | ((current: number) => number)) => void;

type AgentsPageProps = {
  agentPrompts: AgentPromptsItem[];
  reviews: Array<{ reviewer_decision: string }>;
  documents: Document[];
  agentSummary: AgentOperationalSummary | null;
  selectedAgent: Agent | null;
  modelConfigs: ModelConfig[];
  agentWorkflowSummary: AgentWorkflowSummary | null;
  foldersFor: (resourceType: ResourceType) => ResourceFolder[];
  selectedAgentFolderId: string;
  selectedAgentFolderCount: number;
  agents: Agent[];
  selectedAgentId: string;
  newAgentName: string;
  setNewAgentName: (value: string) => void;
  createAgent: (event: FormEvent) => Promise<void>;
  canConfigureAgent: boolean;
  canManageResourceFolders: boolean;
  canDeleteAgent: boolean;
  canResolveReviews: boolean;
  loading: boolean;
  canRunAgent: boolean;
  agentFolderName: string;
  onAgentFolderNameChange: (value: string) => void;
  selectAgentFolder: (folderId: string) => void;
  agentPage: number;
  agentTotal: number;
  agentHasNext: boolean;
  setAgentPage: Dispatch<SetStateAction<number>>;
  onAgentSearchChange: (value: string) => void;
  agentSearch: string;
  selectedWorkspaceName: string;
  workspaceRole: string;
  selectAgent: (agentId: string) => void;
  moveAgentFolder: (agentId: string, folderId: string) => Promise<void>;
  resourceFolderPanel: ResourceFolderPanelRenderer;
  folderPicker: FolderPickerRenderer;
  maxVisibleResources: number;
  maxVisibleAgentPickerOptions: number;
  resourceItemCount: (resourceType: ResourceType, folderId: string) => number;
  folderLabel: (resourceType: ResourceType, folderId: string | null) => string;
  onNewAgentFolderIdChange: (value: string) => void;
  newAgentFolderId: string;
  agentMessage: string;
  setAgentMessage: (value: string) => void;
  runAgent: (event: FormEvent) => Promise<void>;
  latestRun: GraphRun | null;
  goToTab: (tab: "agent" | "trace" | "reviews" | "models" | "costs" | "evaluations" | "documents") => void;
  setTraceRunId: Dispatch<SetStateAction<string>>;
  loadTrace: (runId: string) => Promise<void>;
  RunSummary: RunSummaryRenderer;
  toneForStatus: (status: string) => "neutral" | "good" | "warn" | "bad";
  formatPercent: (value: number | null | undefined) => string;
  formatCost: (value: number | null | undefined) => string;
  formatLatency: (value: number | null | undefined) => string;
  formatDate: (value: string | null) => string;
  formatNumber: (value: number) => string;
  formatStepName: (value: string) => string;
  safeJson: (value: string) => unknown;
  selectAgentModelConfigId: (modelId: string) => void;
  agentModelSearch: string;
  setAgentModelSearch: (value: string) => void;
  setAgentRetrievalTopK: (value: number) => void;
  setAgentRetrievalMinScore: (value: number) => void;
  setAgentConfidenceThreshold: (value: number) => void;
  setAgentTokenBudget: (value: number) => void;
  setAgentName: (value: string) => void;
  agentName: string;
  agentTokenBudget: number;
  agentConfidenceThreshold: number;
  agentRetrievalTopK: number;
  agentRetrievalMinScore: number;
  agentModelConfigId: string;
  agentModelOptions: ModelConfig[];
  agentModelOptionTotal: number;
  agentModelOptionHasNext: boolean;
  updateAgentRuntime: (event: FormEvent) => Promise<void>;
  canCreateAgent: boolean;
  archiveSelectedAgent: () => Promise<void>;
  shortId: (value: string) => string;
};

function asRecord(value: unknown): Record<string, unknown> | null {
  if (typeof value === "object" && value !== null && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return null;
}

export function AgentsPage({
  agentPrompts,
  reviews,
  documents,
  agentSummary,
  selectedAgent,
  modelConfigs,
  agentWorkflowSummary,
  foldersFor,
  selectedAgentFolderId,
  selectedAgentFolderCount,
  agents,
  selectedAgentId,
  newAgentName,
  setNewAgentName,
  createAgent,
  canConfigureAgent,
  canManageResourceFolders,
  canDeleteAgent,
  canResolveReviews,
  loading,
  canRunAgent,
  agentFolderName,
  onAgentFolderNameChange,
  selectAgentFolder,
  agentPage,
  agentTotal,
  agentHasNext,
  setAgentPage,
  onAgentSearchChange,
  agentSearch,
  selectedWorkspaceName,
  workspaceRole,
  selectAgent,
  moveAgentFolder,
  resourceFolderPanel,
  folderPicker,
  maxVisibleResources,
  maxVisibleAgentPickerOptions,
  resourceItemCount,
  folderLabel,
  onNewAgentFolderIdChange,
  newAgentFolderId,
  agentMessage,
  setAgentMessage,
  runAgent,
  latestRun,
  goToTab,
  setTraceRunId,
  loadTrace,
  RunSummary,
  toneForStatus,
  formatPercent,
  formatCost,
  formatLatency,
  formatDate,
  formatNumber,
  formatStepName,
  safeJson,
  selectAgentModelConfigId,
  agentModelSearch,
  setAgentModelSearch,
  setAgentRetrievalTopK,
  setAgentRetrievalMinScore,
  setAgentConfidenceThreshold,
  setAgentTokenBudget,
  setAgentName,
  agentName,
  agentTokenBudget,
  agentConfidenceThreshold,
  agentRetrievalTopK,
  agentRetrievalMinScore,
  agentModelConfigId,
  agentModelOptions,
  agentModelOptionTotal,
  agentModelOptionHasNext,
  updateAgentRuntime,
  canCreateAgent,
  archiveSelectedAgent,
  shortId,
}: AgentsPageProps) {
  const selectedScenario = agentPrompts.find((prompt) => prompt.text === agentMessage) ?? null;
  const pendingReviewCount = reviews.filter((review) => review.reviewer_decision === "pending").length;
  const indexedDocumentCount = documents.filter((document) => document.status === "indexed").length;
  const summary = agentSummary?.agent.id === selectedAgentId ? agentSummary : null;
  const selectedAgentSettings = selectedAgent ? safeJson(selectedAgent.settings_json) : null;
  const selectedAgentRecord = asRecord(selectedAgentSettings) ?? {};
  const selectedAgentModelConfig = summary?.assigned_model_config
    ?? modelConfigs.find((config) => config.id === selectedAgent?.model_config_id)
    ?? null;
  const fallbackModelConfig = modelConfigs.find((config) => config.active && !config.archived_at && config.purpose === "draft_response")
    ?? modelConfigs.find((config) => config.active)
    ?? null;
  const routeModelOptions = selectedAgentModelConfig && !agentModelOptions.some((config) => config.id === selectedAgentModelConfig.id)
    ? [selectedAgentModelConfig, ...agentModelOptions]
    : agentModelOptions;
  const modelRouteSummary = selectedAgentModelConfig
    ? `${selectedAgentModelConfig.provider} / ${selectedAgentModelConfig.model}`
    : fallbackModelConfig
      ? `workspace fallback: ${fallbackModelConfig.provider} / ${fallbackModelConfig.model}`
      : "mock fallback";
  const workflow = agentWorkflowSummary?.agent.id === selectedAgentId ? agentWorkflowSummary : null;
  const workflowNodes = workflow?.nodes ?? [];
  const workflowEdges = workflow?.edges ?? [];
  const workflowFailures = workflowNodes.reduce((sum, node) => sum + node.failure_count, 0);
  const workflowRuns = workflowNodes.reduce((sum, node) => sum + node.run_count, 0);
  const recentRuns = summary?.recent_runs ?? [];
  const agentFolders = foldersFor("agent_config");
  const displayedAgents = agents;
  const selectedAgentForPicker = selectedAgent && !displayedAgents.some((agent) => agent.id === selectedAgent.id)
    ? selectedAgent
    : null;
  const activeAgentPickerOptions = selectedAgentForPicker ? [selectedAgentForPicker, ...displayedAgents] : displayedAgents;
  const displayedAgentPickerOptions = activeAgentPickerOptions.slice(0, maxVisibleAgentPickerOptions);
  const hiddenAgentPickerCount = Math.max(activeAgentPickerOptions.length - displayedAgentPickerOptions.length, 0);
  const selectedAgentFolderLabel = selectedAgentFolderId === "all"
    ? "All agent folders"
    : selectedAgentFolderId === "unfiled"
      ? "Unfiled agents"
      : folderLabel("agent_config", selectedAgentFolderId);
  const agentPageStart = agentPage * maxVisibleResources + (displayedAgents.length ? 1 : 0);
  const agentPageEnd = agentPage * maxVisibleResources + displayedAgents.length;
  const canGoToPreviousAgentPage = agentPage > 0;
  const canGoToNextAgentPage = agentHasNext;
  const failureRate = summary && summary.total_runs > 0
    ? Math.round((summary.failed_runs / summary.total_runs) * 100)
    : 0;
  const reviewRate = summary && summary.total_runs > 0
    ? Math.round((summary.human_review_runs / summary.total_runs) * 100)
    : 0;
  const quickLinks = [
    { id: "agent-setup", label: "1. Select and choose agent", detail: "Pick workspace and active agent" },
    { id: "agent-library", label: "2. Manage agent library", detail: "Move, filter, and browse folder-scoped configs" },
    { id: "agent-configuration", label: "3. Tune runtime controls", detail: "Token, confidence, retrieval, and model route" },
    { id: "agent-operations", label: "4. Inspect operations", detail: "Read summaries, failures, and workflow health" },
    { id: "agent-run", label: "5. Run and trace", detail: "Execute scenario and inspect latest outcome" },
  ];

  const readinessItems = [
    {
      label: "Agent",
      value: selectedAgent ? selectedAgent.name : "Not selected",
      ready: Boolean(selectedAgent),
    },
    {
      label: "Knowledge",
      value: `${indexedDocumentCount}/${documents.length} indexed`,
      ready: indexedDocumentCount > 0,
    },
    {
      label: "Review queue",
      value: `${pendingReviewCount} pending`,
      ready: pendingReviewCount === 0,
    },
    {
      label: "Model route",
      value: selectedAgentModelConfig ? selectedAgentModelConfig.model : fallbackModelConfig ? "workspace fallback" : "mock fallback",
      ready: Boolean(selectedAgentModelConfig || fallbackModelConfig),
    },
    {
      label: "Runs",
      value: summary ? `${summary.total_runs} recorded` : "No summary",
      ready: Boolean(summary && summary.total_runs > 0),
    },
    {
      label: "Evaluation",
      value: summary?.evaluation_runs ? `${formatPercent(summary.evaluation_pass_rate)} pass` : "No linked eval",
      ready: Boolean(summary && summary.evaluation_runs > 0 && summary.failed_evaluation_results === 0),
    },
  ];

  return (
    <div className="agent-console">
      <nav className="workflow-shortcuts" aria-label="Agent workflow">
        {quickLinks.map((link) => (
          <a key={link.id} className="workflow-shortcut" href={`#${link.id}`}>
            <strong>{link.label}</strong>
            <span>{link.detail}</span>
          </a>
        ))}
      </nav>
      <section id="agent-setup" className="panel agent-hero">
        <div className="agent-hero-copy">
          <p className="eyebrow">Agent management</p>
          <h2>Operate a governed LangGraph support agent</h2>
          <p className="muted">Select an agent, inspect run history, tune runtime controls, and run with governed multilingual workflows.</p>
        </div>
        <div className="agent-hero-actions">
          <section className="active-agent-picker" aria-label="Active agent picker">
            <div className="active-agent-picker-head">
              <span>Active agent</span>
              <strong>{selectedAgent?.name ?? "No agent selected"}</strong>
              <small>{displayedAgents.length ? `${agentPageStart}-${agentPageEnd}` : "0"} shown in {selectedAgentFolderLabel}</small>
            </div>
            <label>
              Search agents in current folder
              <input
                value={agentSearch}
                onChange={(event) => {
                  setAgentPage(0);
                  onAgentSearchChange(event.target.value);
                }}
                placeholder="Agent name or runtime settings"
              />
            </label>
            <div className="active-agent-options" role="listbox" aria-label="Agents in current folder">
              {displayedAgentPickerOptions.map((agent) => (
                <button
                  type="button"
                  key={agent.id}
                  className={selectedAgentId === agent.id ? "active-agent-option selected-list-item" : "active-agent-option"}
                  onClick={() => void selectAgent(agent.id)}
                  aria-selected={selectedAgentId === agent.id}
                >
                  <span>{agent.name}</span>
                  <small>{folderLabel("agent_config", agent.folder_id)} · budget {agent.token_budget}</small>
                </button>
              ))}
            </div>
            {hiddenAgentPickerCount > 0 && <small className="folder-picker-note">Showing first {maxVisibleAgentPickerOptions} of {activeAgentPickerOptions.length}. Search or page the library before selecting.</small>}
            {activeAgentPickerOptions.length === 0 && <small className="folder-picker-note">No agents in this folder/page. Create one below or switch folders.</small>}
          </section>
          <form className="inline-form" onSubmit={createAgent}>
            <input aria-label="New agent name" value={newAgentName} onChange={(event) => setNewAgentName(event.target.value)} disabled={!canCreateAgent || loading} placeholder="Example: Billing support triage" />
            <button type="submit" disabled={!canCreateAgent || loading || !newAgentName.trim()}>Create agent</button>
          </form>
        </div>
      </section>

      <section id="agent-library" className="evaluation-workbench agent-library-workbench">
        {resourceFolderPanel({
          resourceType: "agent_config",
          title: "Agent folders",
          detail: "Group agents by product, client, environment, or experiment so operations stay manageable.",
          selectedFolderId: selectedAgentFolderId,
          onSelectFolder: selectAgentFolder,
          folderName: agentFolderName,
          onFolderNameChange: onAgentFolderNameChange,
        })}
        <aside className="panel stack agent-library-panel">
          <div className="row-head">
            <div>
              <h3>Agent library</h3>
              <p className="muted">Folder-scoped agent configs available for LangGraph runs, evaluations, and cost attribution.</p>
            </div>
            <Badge>{displayedAgents.length} of {agentTotal} shown</Badge>
          </div>
          <div className="library-toolbar">
            <div className="folder-scope-banner">
              <span>Current folder</span>
              <strong>{selectedAgentFolderLabel}</strong>
              <small>{displayedAgents.length ? `${agentPageStart}-${agentPageEnd}` : "0"} shown from {selectedAgentFolderCount} matching this view.</small>
            </div>
            <div className="folder-scope-banner">
              <span>Create target</span>
              <strong>{folderLabel("agent_config", newAgentFolderId || null)}</strong>
              <small>New agents are saved into this folder unless you choose another target.</small>
            </div>
            {folderPicker({
              label: "New agent target folder",
              value: newAgentFolderId,
              folders: agentFolders,
              onChange: onNewAgentFolderIdChange,
              disabled: !canManageResourceFolders || loading,
              resourceLabel: "agent",
              compact: true,
            })}
            <label>
              Search current folder
              <input
                value={agentSearch}
                onChange={(event) => {
                  setAgentPage(0);
                  onAgentSearchChange(event.target.value);
                }}
                placeholder="Agent name, folder, or runtime settings"
              />
            </label>
          </div>
          <div className="resource-list bounded-agent-list">
            {displayedAgents.map((agent) => (
              <article key={agent.id} className={`resource-row ${selectedAgentId === agent.id ? "selected-list-item" : ""}`}>
                <button type="button" className="resource-main-button" onClick={() => void selectAgent(agent.id)}>
                  <strong>{agent.name}</strong>
                  <span>{agent.active ? "active" : "inactive"} · budget {agent.token_budget}</span>
                </button>
                <div className="resource-meta">
                  <Badge>{folderLabel("agent_config", agent.folder_id)}</Badge>
                  {agent.archived_at && <Badge tone="warn">archived</Badge>}
                </div>
                <div className="resource-actions">
                  {folderPicker({
                    label: `Move ${agent.name}`,
                    value: agent.folder_id ?? "",
                    folders: agentFolders,
                    onChange: (folderId) => void moveAgentFolder(agent.id, folderId),
                    disabled: !canManageResourceFolders || loading,
                    resourceLabel: "agent",
                    compact: true,
                  })}
                  <button type="button" onClick={() => void selectAgent(agent.id)}>Inspect</button>
                </div>
              </article>
            ))}
            {displayedAgents.length === 0 && <EmptyState title="No agents match this view" detail={agentTotal === 0 && selectedAgentFolderCount === 0 ? "Create an agent here or switch folders." : "Clear search, move to the previous page, or try another folder."} />}
          </div>
          <div className="pagination-bar">
            <button type="button" onClick={() => setAgentPage((page) => Math.max(page - 1, 0))} disabled={!canGoToPreviousAgentPage || loading}>Previous</button>
            <span>Page {agentPage + 1} · {displayedAgents.length ? `${agentPageStart}-${agentPageEnd}` : "0"} of {agentTotal}</span>
            <button type="button" onClick={() => setAgentPage((page) => page + 1)} disabled={!canGoToNextAgentPage || loading}>Next</button>
          </div>
          <p className="permission-note">Agent configs are loaded by folder, search, offset, and limit so large agent libraries stay responsive.</p>
        </aside>
      </section>

      <section className="readiness-strip">
        {readinessItems.map((item) => (
          <article className="readiness-card" key={item.label}>
            <span>{item.label}</span>
            <strong>{item.value}</strong>
            <Badge tone={item.ready ? "good" : "warn"}>{item.ready ? "ready" : "needs setup"}</Badge>
          </article>
        ))}
      </section>

      <section id="agent-configuration" className="panel stack agent-control-center">
        <div className="row-head">
          <div>
            <p className="eyebrow">Configuration control center</p>
            <h3>Agent configuration control center</h3>
            <p className="muted">Tune the selected agent before running it. Controls persist to workspace-scoped API-backed state.</p>
          </div>
          <Badge tone={selectedAgent ? "good" : "warn"}>{selectedAgent ? "selected" : "select agent"}</Badge>
        </div>
        <div className="agent-control-layout">
          <form className="agent-config-form" onSubmit={updateAgentRuntime}>
            <section className="agent-config-section">
              <div>
                <span>Identity</span>
                <strong>{selectedAgent?.name ?? "No agent selected"}</strong>
                <small>{selectedWorkspaceName} · {workspaceRole}</small>
              </div>
              <label>Agent name<input value={agentName} onChange={(event) => setAgentName(event.target.value)} disabled={!canConfigureAgent || loading} placeholder="Select an agent or type a runtime name" /></label>
            </section>
            <section className="agent-config-section">
              <div>
                <span>Token economy</span>
                <strong>{agentTokenBudget.toLocaleString()} token budget</strong>
                <small>Lower budgets route complex or costly cases to human review.</small>
              </div>
              <label>Token budget<input type="number" min="500" max="32000" step="100" value={agentTokenBudget} onChange={(event) => setAgentTokenBudget(Number(event.target.value))} disabled={!canConfigureAgent || loading} /></label>
              <label>Confidence threshold<input type="number" min="0.1" max="0.95" step="0.05" value={agentConfidenceThreshold} onChange={(event) => setAgentConfidenceThreshold(Number(event.target.value))} disabled={!canConfigureAgent || loading} /></label>
            </section>
            <section className="agent-config-section">
              <div>
                <span>Retrieval</span>
                <strong>Top {agentRetrievalTopK} · min score {agentRetrievalMinScore}</strong>
                <small>Controls evidence density before drafting the response.</small>
              </div>
              <label>Retrieval top K<input type="number" min="1" max="8" step="1" value={agentRetrievalTopK} onChange={(event) => setAgentRetrievalTopK(Number(event.target.value))} disabled={!canConfigureAgent || loading} /></label>
              <label>Retrieval min score<input type="number" min="0" max="1" step="0.05" value={agentRetrievalMinScore} onChange={(event) => setAgentRetrievalMinScore(Number(event.target.value))} disabled={!canConfigureAgent || loading} /></label>
            </section>
            <section className="agent-config-section wide">
              <div>
                <span>Model route</span>
                <strong>{selectedAgentModelConfig?.model ?? "Workspace purpose routing"}</strong>
                <small>Agent override is optional; workspace active route or mock fallback is used when unset.</small>
              </div>
              <div className="model-route-picker">
                <label>
                  Search model routes
                  <input
                    value={agentModelSearch}
                    onChange={(event) => setAgentModelSearch(event.target.value)}
                    disabled={!canConfigureAgent || loading}
                    placeholder="Provider, model, purpose, or id"
                  />
                </label>
                <div className="model-route-options" role="listbox" aria-label="Default model route">
                  <button
                    type="button"
                    className={!agentModelConfigId ? "model-route-option selected-list-item" : "model-route-option"}
                    onClick={() => selectAgentModelConfigId("")}
                    disabled={!canConfigureAgent || loading}
                  >
                    <span>
                      <strong>Workspace purpose routing</strong>
                      <small>{fallbackModelConfig ? `${fallbackModelConfig.provider} / ${fallbackModelConfig.model}` : "Use mock fallback if no active workspace route exists"}</small>
                    </span>
                    <Badge tone="neutral">default</Badge>
                  </button>
                  {routeModelOptions.map((config) => (
                    <button
                      type="button"
                      className={agentModelConfigId === config.id ? "model-route-option selected-list-item" : "model-route-option"}
                      key={config.id}
                      onClick={() => selectAgentModelConfigId(config.id)}
                      disabled={!canConfigureAgent || loading || Boolean(config.archived_at)}
                    >
                      <span>
                        <strong>{config.provider} / {config.model}</strong>
                        <small>{config.purpose} · context {config.max_context_tokens.toLocaleString()} · {shortId(config.id)}</small>
                      </span>
                      <span className="model-route-badges">
                        {config.active && <Badge tone="good">active</Badge>}
                        {config.archived_at && <Badge tone="warn">archived</Badge>}
                      </span>
                    </button>
                  ))}
                </div>
                <small>{agentModelOptions.length} of {agentModelOptionTotal} matching routes loaded{agentModelOptionHasNext ? "; search to narrow before assigning" : ""}.</small>
              </div>
              <button type="submit" className="primary" disabled={!canConfigureAgent || loading || !selectedAgentId}>Save runtime controls</button>
            </section>
          </form>

          <aside className="agent-control-readout">
            <div className="control-readout-card">
              <span>Persisted settings</span>
              <div className="runtime-settings-readout">
                <Badge>threshold {String(selectedAgentRecord.confidence_threshold ?? 0.5)}</Badge>
                <Badge>top K {String(selectedAgentRecord.retrieval_top_k ?? 4)}</Badge>
                <Badge>min score {String(selectedAgentRecord.retrieval_min_score ?? 0.2)}</Badge>
                <Badge>budget {selectedAgent?.token_budget ?? agentTokenBudget}</Badge>
                <Badge>model {selectedAgentModelConfig?.model ?? "workspace fallback"}</Badge>
              </div>
            </div>
            <div className="control-readout-card">
              <span>Lifecycle</span>
              <strong>{selectedAgent?.active ? "Active" : selectedAgent ? "Inactive" : "No agent"}</strong>
              <small>{selectedAgent ? `Created ${formatDate(selectedAgent.created_at)} · ${shortId(selectedAgent.id)}` : "Create or select an agent to operate."}</small>
              <div className="run-next-actions">
                {canConfigureAgent ? <button type="button" onClick={() => goToTab("models")}>Models</button> : null}
                <button type="button" onClick={() => goToTab("costs")}>Costs</button>
                <button type="button" onClick={() => goToTab("trace")} disabled={!recentRuns.length && !latestRun}>Traces</button>
              </div>
            </div>
            <p className="permission-note">Developers tune and run agents. Read-only roles can inspect configuration and traces.</p>
          </aside>
        </div>
      </section>

      <section id="agent-operations" className="agent-management-grid">
        <article className="panel stack agent-ops-panel">
          <div className="row-head">
            <div>
              <p className="eyebrow">Operations</p>
              <h3>{selectedAgent?.name ?? "No agent selected"}</h3>
            </div>
            <Badge tone={selectedAgent?.active ? "good" : "warn"}>{selectedAgent?.active ? "active" : "inactive"}</Badge>
          </div>
          <div className="metric-grid compact">
            <Metric label="Total runs" value={summary?.total_runs ?? 0} />
            <Metric label="Finalized" value={summary?.completed_runs ?? 0} />
            <Metric label="Human review" value={`${reviewRate}%`} />
            <Metric label="Failed" value={`${failureRate}%`} />
            <Metric label="Tokens" value={summary?.total_tokens ?? 0} />
            <Metric label="Cost" value={formatCost(summary?.total_estimated_cost)} />
            <Metric label="Avg AI latency" value={formatLatency(summary?.average_ai_latency_ms)} />
            <Metric label="Last run" value={formatDate(summary?.last_run_at ?? null)} />
            <Metric label="Eval runs" value={summary?.evaluation_runs ?? 0} />
            <Metric label="Eval pass" value={summary?.evaluation_result_count ? formatPercent(summary.evaluation_pass_rate) : "-"} />
          </div>
          <div className="agent-evaluation-posture">
            <div>
              <span>Evaluation posture</span>
              <strong>{summary?.evaluation_runs ? `${summary.failed_evaluation_results} failed of ${summary.evaluation_result_count} results` : "No linked evaluations"}</strong>
              <small>{summary?.last_evaluation_at ? `Latest evaluation ${formatDate(summary.last_evaluation_at)}` : "Run system-v1 evaluation for this agent to prove regression quality."}</small>
            </div>
            <button type="button" onClick={() => goToTab("evaluations")}>
              Open evaluations
            </button>
          </div>
          <div className="agent-lifecycle-actions">
            {canDeleteAgent ? (
              <button
                type="button"
                className="danger-button"
                disabled={!selectedAgentId || loading}
                onClick={() => void archiveSelectedAgent()}
              >
                Archive agent
              </button>
            ) : (
              <p className="permission-note">Agent archive requires agents:delete permission.</p>
            )}
            <small>Archiving preserves historical runs and traces for auditability.</small>
          </div>
        </article>

        <article className="panel stack agent-model-panel">
          <div className="row-head">
            <div>
              <p className="eyebrow">Model route</p>
              <h3>{modelRouteSummary}</h3>
            </div>
            <Badge tone={selectedAgentModelConfig ? "good" : fallbackModelConfig ? "neutral" : "warn"}>
              {selectedAgentModelConfig ? "agent override" : fallbackModelConfig ? "workspace fallback" : "mock"}
            </Badge>
          </div>
          {selectedAgentModelConfig ? (
            <div className="metric-grid compact">
              <Metric label="Purpose" value={selectedAgentModelConfig.purpose} />
              <Metric label="Context" value={formatNumber(selectedAgentModelConfig.max_context_tokens)} />
              <Metric label="Prompt / 1K" value={formatCost(selectedAgentModelConfig.prompt_token_cost_per_1k)} />
              <Metric label="Completion / 1K" value={formatCost(selectedAgentModelConfig.completion_token_cost_per_1k)} />
            </div>
          ) : (
            <p className="muted">No agent-specific model is assigned. This agent uses workspace fallback and then mock path.</p>
          )}
          <div className="run-next-actions">
            <button type="button" onClick={() => goToTab("models")}>
              Open model settings
            </button>
            <button type="button" onClick={() => goToTab("costs")}>
              Inspect model spend
            </button>
          </div>
        </article>

        <article className="panel stack recent-runs-panel">
          <div className="row-head">
            <div>
              <p className="eyebrow">Recent runs</p>
              <h3>Trace entry points</h3>
            </div>
            <Badge>{recentRuns.length}</Badge>
          </div>
          {recentRuns.length ? (
            <div className="recent-run-list">
              {recentRuns.map((run) => (
                <button
                  type="button"
                  className="recent-run-row"
                  key={run.id}
                  onClick={() => {
                    setTraceRunId(run.id);
                    void loadTrace(run.id);
                    goToTab("trace");
                  }}
                >
                  <span>
                    <strong>{run.route_decision ?? run.status}</strong>
                    <small>{run.input_message}</small>
                  </span>
                  <span className="recent-run-meta">
                    <Badge tone={toneForStatus(run.status)}>{run.status}</Badge>
                    <small>{formatDate(run.created_at)}</small>
                  </span>
                </button>
              ))}
            </div>
          ) : (
            <EmptyState title="No run history" detail="Run this agent to create traceable graph executions." />
          )}
        </article>

        <article className="panel stack graph-harness-panel">
          <div className="row-head">
            <div>
              <p className="eyebrow">Harness</p>
              <h3>{workflow?.runtime.orchestrator ?? "LangGraph path"}</h3>
            </div>
            <Badge tone={workflowFailures ? "warn" : "good"}>{workflowNodes.length || 0} nodes</Badge>
          </div>
          <div className="workflow-graph-summary">
            <Metric label="Node executions" value={workflowRuns} />
            <Metric label="Node failures" value={workflowFailures} />
            <Metric label="Edges" value={workflowEdges.length} />
            <Metric label="Persistence" value={workflow?.runtime.persistence.length ?? 0} />
          </div>
          {workflowNodes.length ? (
            <div className="workflow-node-board">
              {workflowNodes.map((node) => (
                <article className={node.failure_count ? "workflow-node-card failed" : "workflow-node-card"} key={node.name}>
                  <div className="row-head">
                    <span className="node-order">{node.order}</span>
                    <Badge tone={node.failure_count ? "warn" : node.run_count ? "good" : "neutral"}>
                      {node.failure_count ? `${node.failure_count} failed` : node.run_count ? "observed" : "not run"}
                    </Badge>
                  </div>
                  <h4>{formatStepName(node.name)}</h4>
                  <p>{node.role}</p>
                  <div className="node-stat-grid">
                    <span><strong>{node.run_count}</strong><small>runs</small></span>
                    <span><strong>{formatLatency(node.average_latency_ms)}</strong><small>avg</small></span>
                    <span><strong>{formatCost(node.estimated_cost)}</strong><small>cost</small></span>
                  </div>
                  <div className="tool-chip-row">
                    {node.uses_langchain && <Badge>LangChain</Badge>}
                    {node.expected_state_keys.slice(0, 3).map((key) => <Badge key={key}>{key}</Badge>)}
                  </div>
                  {node.recent_failures[0] && (
                    <button
                      type="button"
                      className="node-failure-link"
                      onClick={() => {
                        setTraceRunId(node.recent_failures[0].graph_run_id);
                        void loadTrace(node.recent_failures[0].graph_run_id);
                        goToTab("trace");
                      }}
                    >
                      Latest failure: {node.recent_failures[0].error_message ?? "unknown error"}
                    </button>
                  )}
                </article>
              ))}
            </div>
          ) : (
            <EmptyState title="No workflow summary" detail="Select an agent to load workflow telemetry." />
          )}
          <div className="workflow-edge-list">
            {workflowEdges.map((edge) => (
              <Badge key={`${edge.source}:${edge.target}:${edge.label}`}>
                {`${formatStepName(edge.source)} -> ${formatStepName(edge.target)}${edge.condition ? ` · ${edge.label}` : ""}`}
              </Badge>
            ))}
          </div>
          <div className="agent-harness-meta">
            {(workflow?.runtime.langchain_components ?? []).map((component) => (
              <Badge key={component.name}>{component.name}</Badge>
            ))}
          </div>
        </article>
      </section>

      <section id="agent-run" className="agent-workbench">
        <form className="panel stack run-console" onSubmit={runAgent}>
          <div className="row-head">
            <div>
              <h3>Customer message</h3>
              <p className="muted">The selected scenario shows expected routing before running.</p>
            </div>
            <Badge tone={selectedScenario?.risk === "review" ? "warn" : selectedScenario ? "good" : "neutral"}>{selectedScenario?.expected ?? "Custom"}</Badge>
          </div>
          <div className="scenario-grid">
            {agentPrompts.map((prompt) => (
              <button
                type="button"
                key={prompt.label}
                className={`scenario-card ${agentMessage === prompt.text ? "selected" : ""}`}
                onClick={() => setAgentMessage(prompt.text)}
              >
                <div className="row-head">
                  <strong>{prompt.label}</strong>
                  <Badge tone={prompt.risk === "review" ? "warn" : "good"}>{prompt.language.toUpperCase()}</Badge>
                </div>
                <span>{prompt.description}</span>
                <small>{prompt.expected}</small>
              </button>
            ))}
          </div>
          <label>
            Message
            <textarea rows={8} value={agentMessage} onChange={(event) => setAgentMessage(event.target.value)} placeholder="Write a customer message, or choose a scenario card above." />
          </label>
          <div className="run-action-bar">
            <button type="submit" className="primary" disabled={!canRunAgent || loading || !selectedAgentId || !agentMessage.trim()}>Run agent</button>
            <button type="button" onClick={() => goToTab("trace")} disabled={!latestRun}>Open trace</button>
            <button type="button" onClick={() => goToTab("reviews")}>Review queue</button>
          </div>
        </form>

        <aside className="panel stack run-outcome-panel">
          <div className="row-head">
            <div>
              <h3>Latest outcome</h3>
              <p className="muted">Final answers, routes, and trace IDs appear here after each run.</p>
            </div>
            {latestRun && <Badge tone={latestRun.route_decision === "human_review" ? "warn" : "good"}>{latestRun.route_decision ?? latestRun.status}</Badge>}
          </div>
          {latestRun ? (
            <RunSummary run={latestRun} />
          ) : (
            <EmptyState title="No run yet" detail="Choose a scenario and run the agent." />
          )}
          {latestRun && (
            <div className="run-next-actions">
              <button type="button" onClick={() => { setTraceRunId(latestRun.id); void loadTrace(latestRun.id); goToTab("trace"); }}>Inspect trace</button>
              {latestRun.route_decision === "human_review" && canResolveReviews && <button type="button" onClick={() => goToTab("reviews")}>Resolve review</button>}
              <button type="button" onClick={() => goToTab("costs")}>Usage & costs</button>
            </div>
          )}
        </aside>
      </section>
    </div>
  );
}

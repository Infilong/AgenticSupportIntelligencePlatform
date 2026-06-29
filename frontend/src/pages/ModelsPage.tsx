import { FormEvent, ReactNode } from "react";
import { Badge, EmptyState, Metric } from "../app/shared/Primitives";

type ModelConfig = {
  id: string;
  provider: string;
  model: string;
  purpose: string;
  prompt_token_cost_per_1k: number;
  completion_token_cost_per_1k: number;
  max_context_tokens: number;
  active: boolean;
  archived_at: string | null;
  created_at: string;
  runtime_kind: string;
  credential_status: string;
  readiness_label: string;
  workspace_id: string | null;
};

type ModelProviderOption = {
  id: string;
  label: string;
  defaultModel: string;
  promptCost: number;
  completionCost: number;
  maxContext: number;
  note: string;
};

type ModelPurpose = "classification" | "draft_response" | "evaluation" | "context_compression";

type Tone = "neutral" | "good" | "warn" | "bad";

type ModelHistoryView = "all" | "active" | "draft" | "archived";

type ModelsPageProps = {
  modelConfigs: ModelConfig[];
  modelConfigHistory: ModelConfig[];
  modelPurposes: readonly ModelPurpose[];
  modelProviderOptions: ModelProviderOption[];
  showArchivedModels: boolean;
  modelHistoryPage: number;
  modelHistoryTotal: number;
  modelHistoryHasNext: boolean;
  maxVisibleAdminAssets: number;
  canManageModels: boolean;
  loading: boolean;
  modelPurpose: string;
  modelProvider: string;
  modelName: string;
  modelPromptCost: number;
  modelCompletionCost: number;
  modelMaxContext: number;
  modelActive: boolean;
  modelSearch: string;
  modelHistoryView: ModelHistoryView;
  selectedModelProvider: ModelProviderOption | undefined;
  onModelPurposeChange: (value: string) => void;
  onModelProviderChange: (value: string) => void;
  onModelNameChange: (value: string) => void;
  onModelPromptCostChange: (value: number) => void;
  onModelCompletionCostChange: (value: number) => void;
  onModelMaxContextChange: (value: number) => void;
  onModelActiveChange: (value: boolean) => void;
  onCreateModelConfig: (event: FormEvent) => Promise<void>;
  onActivateModelConfig: (configId: string) => Promise<void>;
  onArchiveModelConfig: (config: ModelConfig) => Promise<void>;
  onToggleArchivedModels: (value: boolean) => void;
  onModelHistoryPageChange: (page: number) => void;
  onModelSearchChange: (value: string) => void;
  onModelHistoryViewChange: (value: ModelHistoryView) => void;
  onRefreshModels: () => Promise<void>;
  onGoToTab: (tab: "agent" | "costs") => void;
  canOpenTab: (tab: "agent" | "costs") => boolean;
  formatNumber: (value: number) => string;
  formatCost: (value: number) => string;
  formatDate: (value: string) => string;
  toneForCredentialStatus: (status: string) => Tone;
  friendlyCredentialStatus: (status: string) => string;
  friendlyRuntimeKind: (kind: string) => string;
};

type ModelsPageTab = "agent" | "costs";

export function ModelsPage({
  modelConfigs,
  modelConfigHistory,
  modelPurposes,
  modelProviderOptions,
  showArchivedModels,
  modelHistoryPage,
  modelHistoryTotal,
  modelHistoryHasNext,
  maxVisibleAdminAssets,
  canManageModels,
  loading,
  modelPurpose,
  modelProvider,
  modelName,
  modelPromptCost,
  modelCompletionCost,
  modelMaxContext,
  modelActive,
  modelSearch,
  modelHistoryView,
  selectedModelProvider,
  onModelPurposeChange,
  onModelProviderChange,
  onModelNameChange,
  onModelPromptCostChange,
  onModelCompletionCostChange,
  onModelMaxContextChange,
  onModelActiveChange,
  onCreateModelConfig,
  onActivateModelConfig,
  onArchiveModelConfig,
  onToggleArchivedModels,
  onModelHistoryPageChange,
  onModelSearchChange,
  onModelHistoryViewChange,
  onRefreshModels,
  onGoToTab,
  canOpenTab,
  formatNumber,
  formatCost,
  formatDate,
  toneForCredentialStatus,
  friendlyCredentialStatus,
  friendlyRuntimeKind,
}: ModelsPageProps) {
  function TabShortcut({
    tab,
    children,
  }: {
    tab: ModelsPageTab;
    children: ReactNode;
  }) {
    if (!canOpenTab(tab)) return null;
    return <button type="button" onClick={() => onGoToTab(tab)}>{children}</button>;
  }

  const activeConfigs = modelConfigs.filter((config) => config.active && !config.archived_at);
  const loadedArchivedModelCount = modelConfigHistory.filter((config) => config.archived_at).length;
  const purposeSummary = modelPurposes.map((purpose) => {
    const active = modelConfigs.find((config) => config.purpose === purpose && config.active && !config.archived_at);
    return { purpose, active: active ?? null };
  });
  const configuredPurposeCount = purposeSummary.filter(({ active }) => Boolean(active)).length;
  const liveProviderCount = activeConfigs.filter((config) => config.runtime_kind === "live").length;
  const missingCredentialCount = activeConfigs.filter((config) => config.credential_status === "missing" || config.credential_status === "integration_required").length;
  const readyProviderCount = activeConfigs.filter((config) => config.credential_status === "configured" || config.credential_status === "not_required").length;
  const maxContext = activeConfigs.length ? Math.max(...activeConfigs.map((config) => config.max_context_tokens)) : 0;
  const displayedModelConfigs = modelConfigHistory;
  const modelHistoryPageStart = modelHistoryPage * maxVisibleAdminAssets + (displayedModelConfigs.length ? 1 : 0);
  const modelHistoryPageEnd = modelHistoryPage * maxVisibleAdminAssets + displayedModelConfigs.length;
  const canGoToPreviousModelHistoryPage = modelHistoryPage > 0;
  const canGoToNextModelHistoryPage = modelHistoryHasNext;

  return (
    <div className="settings-console model-console">
      <section className="panel settings-hero">
        <div>
          <p className="eyebrow">Model routing</p>
          <h2>Control provider, model, price, and context by AI purpose</h2>
          <p className="muted">Each purpose can use a different active model config. The provider records model, price profile, context limit, token usage, latency, and failures in the AI run ledger.</p>
        </div>
        <div className="next-action-card">
          <span>Routing readiness</span>
          <strong>{configuredPurposeCount}/{modelPurposes.length} purposes configured</strong>
          <p>{missingCredentialCount ? `${missingCredentialCount} active route(s) need backend credentials.` : liveProviderCount ? `${liveProviderCount} live provider routes active.` : "Mock routing is active for deterministic local testing."}</p>
          <button type="button" onClick={() => void onRefreshModels()}>Refresh models</button>
        </div>
      </section>

      <section className="settings-summary-grid">
        <Metric label="Active configs" value={activeConfigs.length} />
        <Metric label="Loaded archived" value={loadedArchivedModelCount} />
        <Metric label="Configured purposes" value={`${configuredPurposeCount}/${modelPurposes.length}`} />
        <Metric label="Live providers" value={liveProviderCount} />
        <Metric label="Ready routes" value={readyProviderCount} />
        <Metric label="Credential gaps" value={missingCredentialCount} />
        <Metric label="Max context" value={maxContext ? formatNumber(maxContext) : "mock default"} />
      </section>

      <section className="settings-workbench">
        <form className="panel stack settings-editor-panel" onSubmit={onCreateModelConfig}>
          <div className="row-head">
            <div>
              <h3>Create model config</h3>
              <p className="muted">Use mock for deterministic local testing, or activate OpenAI/OpenAI-compatible configs for real model calls with ledger tracking.</p>
            </div>
            <Badge tone={canManageModels ? (modelActive ? "good" : "neutral") : "warn"}>{canManageModels ? (modelActive ? "active" : "draft") : "owner only"}</Badge>
          </div>
          <div className="settings-meta-grid">
            <label>
              Purpose
              <select value={modelPurpose} disabled={!canManageModels || loading} onChange={(event) => onModelPurposeChange(event.target.value)}>
                {modelPurposes.map((purpose) => <option key={purpose} value={purpose}>{purpose}</option>)}
              </select>
            </label>
            <label>
              Provider
              <select value={modelProvider} disabled={!canManageModels || loading} onChange={(event) => onModelProviderChange(event.target.value)}>
                {modelProviderOptions.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
              </select>
            </label>
            <label>
              Model
              <input value={modelName} disabled={!canManageModels || loading} onChange={(event) => onModelNameChange(event.target.value)} />
            </label>
          </div>
          {selectedModelProvider && <div className="settings-note">{selectedModelProvider.note}</div>}
          <div className="settings-meta-grid">
            <label>
              Prompt cost / 1K
              <input type="number" min="0" step="0.0001" value={modelPromptCost} disabled={!canManageModels || loading} onChange={(event) => onModelPromptCostChange(Number(event.target.value))} />
            </label>
            <label>
              Completion cost / 1K
              <input type="number" min="0" step="0.0001" value={modelCompletionCost} disabled={!canManageModels || loading} onChange={(event) => onModelCompletionCostChange(Number(event.target.value))} />
            </label>
            <label>
              Max context tokens
              <input type="number" min="256" step="256" value={modelMaxContext} disabled={!canManageModels || loading} onChange={(event) => onModelMaxContextChange(Number(event.target.value))} />
            </label>
          </div>
          <label className="check-row single-check settings-toggle">
            <input type="checkbox" checked={modelActive} disabled={!canManageModels || loading} onChange={(event) => onModelActiveChange(event.target.checked)} />
            Activate this config immediately
          </label>
          <div className="run-action-bar">
            <button type="submit" className="primary" disabled={!canManageModels || loading}>Create config</button>
            <TabShortcut tab="agent">Run agent</TabShortcut>
            <TabShortcut tab="costs">Inspect costs</TabShortcut>
          </div>
        </form>

        <aside className="panel stack settings-side-panel">
          <h3>Active purpose routing</h3>
          {purposeSummary.map(({ purpose, active }) => (
            <article className={active ? "settings-route-card active" : "settings-route-card"} key={purpose}>
              <div className="row-head">
                <strong>{purpose}</strong>
                {active ? <Badge tone="good">active</Badge> : <Badge tone="warn">default</Badge>}
              </div>
              <small>{active ? `${active.provider} / ${active.model}` : "Fallback mock pricing"}</small>
              <small>{active ? `${formatNumber(active.max_context_tokens)} context tokens · ${friendlyCredentialStatus(active.credential_status)}` : "No workspace override"}</small>
              {active && <small>{active.readiness_label}</small>}
            </article>
          ))}
        </aside>
      </section>

      <section className="panel full-width stack settings-history-panel">
        <div className="row-head">
          <div>
            <h3>Model configuration history</h3>
            <p className="muted">Activating a config deactivates other configs for the same purpose in this workspace. Archived configs are excluded from routing.</p>
          </div>
          <div className="review-actions">
            <label className="check-row single-check settings-toggle compact-toggle">
              <input
                type="checkbox"
                checked={showArchivedModels}
                onChange={(event) => onToggleArchivedModels(event.target.checked)}
              />
              Show archived
            </label>
            <Badge>{displayedModelConfigs.length} of {modelHistoryTotal} shown</Badge>
          </div>
        </div>
        <div className="library-toolbar settings-history-toolbar">
          <label>
            Search model configs
            <input
              value={modelSearch}
              onChange={(event) => { onModelHistoryPageChange(0); onModelSearchChange(event.target.value); }}
              placeholder="Provider, model, purpose, context, or id"
            />
          </label>
          <label>
            Status
            <select value={modelHistoryView} onChange={(event) => { onModelHistoryPageChange(0); onModelHistoryViewChange(event.target.value as ModelHistoryView); }}>
              <option value="all">All history</option>
              <option value="active">Active</option>
              <option value="draft">Draft/inactive</option>
              <option value="archived">Archived</option>
            </select>
          </label>
          <p className="permission-note">Model history is loaded from the backend by status, archived visibility, search, offset, and limit so routing experiments stay operable as they grow.</p>
        </div>
        <div className="model-config-list settings-card-grid">
          {displayedModelConfigs.map((config) => (
            <article className={config.active ? "model-card active-model" : config.archived_at ? "model-card archived-card" : "model-card"} key={config.id}>
              <div className="row-head">
                <div>
                  <strong>{config.purpose}</strong>
                  <p className="muted">{config.provider} / {config.model}</p>
                </div>
                <div className="review-actions">
                  {config.active && <Badge tone="good">active</Badge>}
                  {config.archived_at && <Badge>archived</Badge>}
                  <Badge>{friendlyRuntimeKind(config.runtime_kind)}</Badge>
                  <Badge tone={toneForCredentialStatus(config.credential_status)}>{friendlyCredentialStatus(config.credential_status)}</Badge>
                  <button type="button" disabled={config.active || Boolean(config.archived_at) || !canManageModels || loading} onClick={() => void onActivateModelConfig(config.id)}>Activate</button>
                  <button type="button" className="danger-button" disabled={Boolean(config.archived_at) || !canManageModels || loading} onClick={() => void onArchiveModelConfig(config)}>Archive</button>
                </div>
              </div>
              <div className="metric-grid compact">
                <Metric label="Prompt / 1K" value={formatCost(config.prompt_token_cost_per_1k)} />
                <Metric label="Completion / 1K" value={formatCost(config.completion_token_cost_per_1k)} />
                <Metric label="Context" value={formatNumber(config.max_context_tokens)} />
                <Metric label="Created" value={formatDate(config.created_at)} />
              </div>
              <p className="permission-note">{config.readiness_label}</p>
            </article>
          ))}
        </div>
        {displayedModelConfigs.length === 0 && (
          <EmptyState
            title="No model configs match this view"
            detail={modelHistoryPage > 0 ? "Move to the previous page or clear filters." : "The backend falls back to deterministic mock mode until you activate a workspace model config. Clear search or change status if configs already exist."}
          />
        )}
        <div className="pagination-bar">
          <button type="button" onClick={() => onModelHistoryPageChange(Math.max(modelHistoryPage - 1, 0))} disabled={!canGoToPreviousModelHistoryPage || loading}>Previous</button>
          <span>Page {modelHistoryPage + 1} · {displayedModelConfigs.length ? `${modelHistoryPageStart}-${modelHistoryPageEnd}` : "0"} of {modelHistoryTotal} configs</span>
          <button type="button" onClick={() => onModelHistoryPageChange(modelHistoryPage + 1)} disabled={!canGoToNextModelHistoryPage || loading}>Next</button>
        </div>
        <p className="permission-note">Backend totals decide whether another model-history page exists.</p>
        {activeConfigs.length > 0 && <p className="muted">Active OpenAI/OpenAI-compatible configs perform live calls when the backend has an API key; otherwise the failed attempt is visible in trace, review, and cost records.</p>}
      </section>
    </div>
  );
}

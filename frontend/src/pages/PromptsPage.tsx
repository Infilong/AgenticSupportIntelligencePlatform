import { FormEvent, ReactElement, ReactNode } from "react";
import { Badge, EmptyState, Metric } from "../app/shared/Primitives";

type Language = "en" | "ja" | "zh";

type PromptTemplate = {
  id: string;
  workspace_id: string;
  name: string;
  language: Language;
  version: number;
  template_text: string;
  active: boolean;
  archived_at: string | null;
  created_at: string;
};

type PromptTemplateListView = "all" | "active" | "draft" | "archived";

type PromptDiffLine = {
  lineNumber: number;
  status: "added" | "removed" | "changed";
  activeLine: string;
  candidateLine: string;
};

type PromptDiffSummary = {
  addedLines: number;
  removedLines: number;
  changedLines: number;
  unchangedLines: number;
  previewLines: PromptDiffLine[];
};

type JsonBlockRenderer = {
  value: string;
};

type PromptsPageProps = {
  promptTemplates: PromptTemplate[];
  promptTemplateHistory: PromptTemplate[];
  canManagePrompts: boolean;
  loading: boolean;
  showArchivedPrompts: boolean;
  promptHistoryPage: number;
  promptHistoryTotal: number;
  promptSearch: string;
  promptHistoryView: PromptTemplateListView;
  promptName: string;
  promptLanguage: Language;
  promptText: string;
  promptActive: boolean;
  maxVisibleAdminAssets: number;
  onPromptNameChange: (value: string) => void;
  onPromptLanguageChange: (value: Language) => void;
  onPromptActiveChange: (value: boolean) => void;
  onPromptTextChange: (value: string) => void;
  onCreatePromptTemplateVersion: (event: FormEvent) => Promise<void>;
  onActivatePromptTemplate: (templateId: string) => Promise<void>;
  onArchivePromptTemplate: (template: PromptTemplate) => Promise<void>;
  onToggleArchivedPrompts: (value: boolean) => void;
  onPromptSearchChange: (value: string) => void;
  onPromptHistoryPageChange: (page: number) => void;
  onPromptHistoryViewChange: (value: PromptTemplateListView) => void;
  onRefreshPrompts: () => Promise<void>;
  onGoToTab: (tab: "agent" | "trace") => void;
  canOpenTab: (tab: "agent" | "trace") => boolean;
  formatDate: (value: string) => string;
  formatCost: (value: number) => string;
  JsonBlock: (props: JsonBlockRenderer) => ReactElement;
};

function TabShortcut({
  tab,
  children,
  onGoToTab,
  canOpenTab,
  className,
  disabled,
}: {
  tab: "agent" | "trace";
  children: ReactNode;
  onGoToTab: (tab: "agent" | "trace") => void;
  canOpenTab: (tab: "agent" | "trace") => boolean;
  className?: string;
  disabled?: boolean;
}) {
  if (!canOpenTab(tab)) return null;
  return (
    <button type="button" className={className} onClick={() => onGoToTab(tab)} disabled={disabled}>
      {children}
    </button>
  );
}

type PromptTemplateFamilyMeta = {
  name: string;
  language: Language;
};

function promptTemplateFamilyKey(template: PromptTemplateFamilyMeta): string {
  return `${template.name}:${template.language}`;
}

function comparePromptTemplates(candidateText: string, activeText: string): PromptDiffSummary {
  const candidateLines = candidateText.split("\n");
  const activeLines = activeText.split("\n");
  const maxLines = Math.max(candidateLines.length, activeLines.length);
  const previewLines: PromptDiffLine[] = [];
  let addedLines = 0;
  let removedLines = 0;
  let changedLines = 0;
  let unchangedLines = 0;

  for (let index = 0; index < maxLines; index += 1) {
    const candidateLine = candidateLines[index] ?? "";
    const activeLine = activeLines[index] ?? "";

    if (candidateLine === activeLine) {
      unchangedLines += 1;
      continue;
    }

    const status = !activeLine && candidateLine
      ? "added"
      : activeLine && !candidateLine
        ? "removed"
        : "changed";

    if (status === "added") addedLines += 1;
    if (status === "removed") removedLines += 1;
    if (status === "changed") changedLines += 1;

    if (previewLines.length < 6) {
      previewLines.push({ lineNumber: index + 1, status, activeLine, candidateLine });
    }
  }

  return { addedLines, removedLines, changedLines, unchangedLines, previewLines };
}

function compactPromptLine(value: string): string {
  const normalized = value.trim() || "empty line";
  return normalized.length > 140 ? `${normalized.slice(0, 140)}...` : normalized;
}

export function PromptsPage({
  promptTemplates,
  promptTemplateHistory,
  canManagePrompts,
  loading,
  showArchivedPrompts,
  promptHistoryPage,
  promptHistoryTotal,
  promptSearch,
  promptHistoryView,
  promptName,
  promptLanguage,
  promptText,
  promptActive,
  maxVisibleAdminAssets,
  onPromptNameChange,
  onPromptLanguageChange,
  onPromptActiveChange,
  onPromptTextChange,
  onCreatePromptTemplateVersion,
  onActivatePromptTemplate,
  onArchivePromptTemplate,
  onToggleArchivedPrompts,
  onPromptSearchChange,
  onPromptHistoryPageChange,
  onPromptHistoryViewChange,
  onRefreshPrompts,
  onGoToTab,
  canOpenTab,
  formatDate,
  formatCost,
  JsonBlock,
}: PromptsPageProps) {
  const activeTemplates = promptTemplates.filter((template) => template.active && !template.archived_at);
  const loadedArchivedPromptCount = promptTemplateHistory.filter((template) => template.archived_at).length;
  const classifierActive = activeTemplates.find((template) => template.name === "support_intent_classifier");
  const drafterActive = activeTemplates.find((template) => template.name === "support_response_drafter");
  const activeLanguages = [...new Set(activeTemplates.map((template) => template.language))];

  const activeTemplateByFamily = new Map(
    activeTemplates.map((template) => [promptTemplateFamilyKey(template), template]),
  );

  const promptGroups = ["support_intent_classifier", "support_response_drafter"].map((name) => {
    const versions = promptTemplates.filter((template) => template.name === name && !template.archived_at);
    const active = versions.find((template) => template.active);
    return { name, versions, active };
  });

  const displayedPromptTemplates = promptTemplateHistory;
  const promptHistoryPageStart = promptHistoryPage * maxVisibleAdminAssets + (displayedPromptTemplates.length ? 1 : 0);
  const promptHistoryPageEnd = promptHistoryPage * maxVisibleAdminAssets + displayedPromptTemplates.length;
  const canGoToPreviousPromptHistoryPage = promptHistoryPage > 0;
  const canGoToNextPromptHistoryPage = promptHistoryPage < Math.floor(Math.max(promptHistoryTotal - 1, 0) / maxVisibleAdminAssets);

  return (
    <div className="settings-console prompt-console">
      <section className="panel settings-hero">
        <div>
          <p className="eyebrow">Prompt operations</p>
          <h2>Version, activate, and audit workflow prompts</h2>
          <p className="muted">Prompt versions are workspace-scoped. The next LangGraph run records the active prompt template name and version in every AI run ledger entry.</p>
        </div>
        <div className="next-action-card">
          <span>Prompt readiness</span>
          <strong>{activeTemplates.length ? `${activeTemplates.length} active versions` : "No active versions"}</strong>
          <p>{activeTemplates.length ? `Languages covered: ${activeLanguages.join(", ") || "none"}.` : "Run an agent to create defaults or publish an active version."}</p>
          <button type="button" onClick={() => void onRefreshPrompts()}>Refresh prompts</button>
        </div>
      </section>

      <section className="settings-summary-grid">
        <Metric label="Active prompts" value={activeTemplates.length} />
        <Metric label="Active summary" value={promptTemplates.length} />
        <Metric label="Loaded archived" value={loadedArchivedPromptCount} />
        <Metric label="Classifier" value={classifierActive ? `v${classifierActive.version}` : "missing"} />
        <Metric label="Drafter" value={drafterActive ? `v${drafterActive.version}` : "missing"} />
      </section>

      <section className="settings-workbench">
        <form className="panel stack settings-editor-panel" onSubmit={onCreatePromptTemplateVersion}>
          <div className="row-head">
            <div>
              <h3>Create prompt version</h3>
              <p className="muted">Publish a controlled prompt change, then validate it through Trace and Evaluation.</p>
            </div>
            <Badge tone={canManagePrompts ? (promptActive ? "good" : "neutral") : "warn"}>{canManagePrompts ? (promptActive ? "activate" : "draft") : "owner only"}</Badge>
          </div>
          <div className="settings-meta-grid">
            <label>
              Template name
              <select value={promptName} disabled={!canManagePrompts || loading} onChange={(event) => onPromptNameChange(event.target.value)}>
                <option value="support_intent_classifier">support_intent_classifier</option>
                <option value="support_response_drafter">support_response_drafter</option>
              </select>
            </label>
            <label>
              Language
              <select value={promptLanguage} disabled={!canManagePrompts || loading} onChange={(event) => onPromptLanguageChange(event.target.value as Language)}>
                <option value="en">English</option>
                <option value="ja">Japanese</option>
                <option value="zh">Chinese</option>
              </select>
            </label>
            <label className="check-row single-check settings-toggle">
              <input type="checkbox" checked={promptActive} disabled={!canManagePrompts || loading} onChange={(event) => onPromptActiveChange(event.target.checked)} />
              Activate immediately
            </label>
          </div>
          <label>
            Template source
            <textarea rows={16} value={promptText} disabled={!canManagePrompts || loading} onChange={(event) => onPromptTextChange(event.target.value)} placeholder="Write the prompt template source here. Keep variables explicit and version every change." />
          </label>
          <div className="run-action-bar">
            <button type="submit" className="primary" disabled={!canManagePrompts || loading || !promptText.trim()}>Create version</button>
            <TabShortcut tab="agent" onGoToTab={onGoToTab} canOpenTab={canOpenTab}>Run agent</TabShortcut>
            <TabShortcut tab="trace" onGoToTab={onGoToTab} canOpenTab={canOpenTab}>Inspect trace</TabShortcut>
          </div>
        </form>

        <aside className="panel stack settings-side-panel">
          <h3>Active workflow prompts</h3>
          {promptGroups.map(({ name, active, versions }) => (
            <article className={active ? "settings-route-card active" : "settings-route-card"} key={name}>
              <div className="row-head">
                <strong>{name}</strong>
                {active ? <Badge tone="good">v{active.version}</Badge> : <Badge tone="warn">missing</Badge>}
              </div>
              <small>{active ? `${active.language.toUpperCase()} · ${formatDate(active.created_at)}` : "No active workspace version"}</small>
              <small>{versions.length} active language routes loaded</small>
            </article>
          ))}
        </aside>
      </section>

      <section className="panel full-width stack settings-history-panel">
        <div className="row-head">
          <div>
            <h3>Prompt version history</h3>
            <p className="muted">Activate a version to make future graph runs use it. Existing traces keep the prompt version they used.</p>
          </div>
          <div className="review-actions">
            <label className="check-row single-check settings-toggle compact-toggle">
              <input type="checkbox" checked={showArchivedPrompts} onChange={(event) => onToggleArchivedPrompts(event.target.checked)} />
              Show archived
            </label>
            <Badge>{displayedPromptTemplates.length} of {promptHistoryTotal} shown</Badge>
          </div>
        </div>
        <div className="library-toolbar settings-history-toolbar">
          <label>
            Search prompt history
            <input
              value={promptSearch}
              onChange={(event) => {
                onPromptHistoryPageChange(0);
                onPromptSearchChange(event.target.value);
              }}
              placeholder="Name, language, version, source, or id"
            />
          </label>
          <label>
            Status
            <select
              value={promptHistoryView}
              onChange={(event) => {
                onPromptHistoryPageChange(0);
                onPromptHistoryViewChange(event.target.value as PromptTemplateListView);
              }}
            >
              <option value="all">All history</option>
              <option value="active">Active</option>
              <option value="draft">Draft/inactive</option>
              <option value="archived">Archived</option>
            </select>
          </label>
          <p className="permission-note">Prompt history is loaded from the backend by status, archived visibility, search, offset, and limit. Source stays collapsed so long version history remains scannable.</p>
        </div>
        <div className="prompt-template-list settings-card-grid">
          {displayedPromptTemplates.map((template) => {
            const activeTemplate = activeTemplateByFamily.get(promptTemplateFamilyKey(template));
            const promptDiff = activeTemplate && activeTemplate.id !== template.id
              ? comparePromptTemplates(template.template_text, activeTemplate.template_text)
              : null;
            return (
              <article className={template.active ? "prompt-card active-prompt" : template.archived_at ? "prompt-card archived-card" : "prompt-card"} key={template.id}>
                <div className="row-head">
                  <div>
                    <strong>{template.name}</strong>
                    <p className="muted">{template.language.toUpperCase()} · version {template.version} · {formatDate(template.created_at)}</p>
                  </div>
                  <div className="review-actions">
                    {template.active && <Badge tone="good">active</Badge>}
                    {template.archived_at && <Badge>archived</Badge>}
                    <button type="button" disabled={template.active || Boolean(template.archived_at) || !canManagePrompts || loading} onClick={() => onActivatePromptTemplate(template.id)}>Activate</button>
                    <button type="button" className="danger-button" disabled={Boolean(template.archived_at) || !canManagePrompts || loading} onClick={() => void onArchivePromptTemplate(template)}>Archive</button>
                  </div>
                </div>
                {promptDiff && activeTemplate && (
                  <details className="prompt-diff-panel">
                    <summary>Compare with active v{activeTemplate.version}</summary>
                    <div className="metric-grid compact">
                      <Metric label="Added lines" value={promptDiff.addedLines} />
                      <Metric label="Removed lines" value={promptDiff.removedLines} />
                      <Metric label="Changed lines" value={promptDiff.changedLines} />
                      <Metric label="Unchanged" value={promptDiff.unchangedLines} />
                    </div>
                    <div className="prompt-diff-lines">
                      {promptDiff.previewLines.map((line) => (
                        <div className="prompt-diff-line" key={line.lineNumber}>
                          <span>Line {line.lineNumber} · {line.status}</span>
                          <code>Active: {compactPromptLine(line.activeLine)}</code>
                          <code>This version: {compactPromptLine(line.candidateLine)}</code>
                        </div>
                      ))}
                      {promptDiff.previewLines.length === 0 && <p className="muted">No source changes against the active version.</p>}
                    </div>
                  </details>
                )}
                <details>
                  <summary>Prompt source</summary>
                  <JsonBlock value={template.template_text} />
                </details>
              </article>
            );
          })}
        </div>
        {displayedPromptTemplates.length === 0 && (
          <EmptyState
            title="No prompt versions match this view"
            detail={promptHistoryPage > 0 ? "Move to the previous page or clear filters." : "Defaults are created on first agent run, or create a version manually. Clear search or change status if prompts already exist."}
          />
        )}
        <div className="pagination-bar">
          <button type="button" onClick={() => onPromptHistoryPageChange(Math.max(promptHistoryPage - 1, 0))} disabled={!canGoToPreviousPromptHistoryPage || loading}>Previous</button>
          <span>Page {promptHistoryPage + 1} · {displayedPromptTemplates.length ? `${promptHistoryPageStart}-${promptHistoryPageEnd}` : "0"} of {promptHistoryTotal} prompts</span>
          <button type="button" onClick={() => onPromptHistoryPageChange(promptHistoryPage + 1)} disabled={!canGoToNextPromptHistoryPage || loading}>Next</button>
        </div>
        <p className="permission-note">Backend totals decide whether another prompt-history page exists.</p>
      </section>
    </div>
  );
}

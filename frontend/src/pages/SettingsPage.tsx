import { FormEvent, ReactNode } from "react";
import { Badge, Metric } from "../app/shared/Primitives";

type SettingsTab = "members" | "models" | "costs" | "system" | "tools" | "guardrails" | "prompts";

type SettingsPageProps = {
  workspaceName: string | null;
  workspaceRole: string;
  activeModelCount: number;
  pendingHealthSignals: number;
  canManageWorkspace: boolean;
  costUsageText: string;
  systemHealthText: string;
  toolTotal: number;
  workspaceMembersCount: number;
  promptTemplateCount: number;
  canConfigureTools: boolean;
  canConfigureGuardrails: boolean;
  guardrailConfigurableCount: number;
  workspaceSettingsName: string;
  loading: boolean;
  onWorkspaceSettingsNameChange: (value: string) => void;
  onUpdateWorkspaceSettings: (event: FormEvent) => Promise<void>;
  onRefreshWorkspace: () => Promise<void>;
  onGoToTab: (tab: SettingsTab) => void;
  canOpenTab: (tab: SettingsTab) => boolean;
  hasAdvancedAdminShortcuts: boolean;
};

export function SettingsPage({
  workspaceName,
  workspaceRole,
  activeModelCount,
  pendingHealthSignals,
  canManageWorkspace,
  costUsageText,
  systemHealthText,
  toolTotal,
  workspaceMembersCount,
  promptTemplateCount,
  canConfigureTools,
  canConfigureGuardrails,
  guardrailConfigurableCount,
  workspaceSettingsName,
  loading,
  onWorkspaceSettingsNameChange,
  onUpdateWorkspaceSettings,
  onRefreshWorkspace,
  onGoToTab,
  canOpenTab,
  hasAdvancedAdminShortcuts,
}: SettingsPageProps) {
  function TabShortcut({
    tab,
    children,
  }: {
    tab: SettingsTab;
    children: ReactNode;
  }) {
    if (!canOpenTab(tab)) return null;
    return (
      <button type="button" onClick={() => onGoToTab(tab)}>
        {children}
      </button>
    );
  }

  return (
    <div className="settings-console workspace-settings-console">
      <section className="panel settings-hero">
        <div>
          <p className="eyebrow">Workspace settings</p>
          <h2>Configure workspace identity and administration paths</h2>
          <p className="muted">Settings are workspace-scoped and backend-enforced. This page keeps identity controls separate from provider routing, members, audit, and system health.</p>
        </div>
        <div className="next-action-card">
          <span>Your permission</span>
          <strong>{canManageWorkspace ? "Owner controls" : "Read-only"}</strong>
          <p>{canManageWorkspace ? "You can update workspace identity and manage admin resources." : "You can inspect settings, but owner-only changes are disabled."}</p>
          <button type="button" onClick={() => void onRefreshWorkspace()}>Refresh workspace</button>
        </div>
      </section>

      <section className="settings-summary-grid">
        <Metric label="Workspace" value={workspaceName ?? "none"} />
        <Metric label="Role" value={workspaceRole} />
        <Metric label="Active models" value={activeModelCount} />
        <Metric label="Health signals" value={pendingHealthSignals} />
      </section>

      <section className="settings-workbench">
        <form className="panel stack settings-editor-panel" onSubmit={onUpdateWorkspaceSettings}>
          <div className="row-head">
            <div>
              <h3>Workspace identity</h3>
              <p className="muted">Rename the workspace shown in navigation, traces, audit views, and all workspace-scoped admin pages.</p>
            </div>
            <Badge tone={canManageWorkspace ? "good" : "warn"}>{canManageWorkspace ? "owner action" : "restricted"}</Badge>
          </div>
          <label>
            Workspace name
            <input
              value={workspaceSettingsName}
              onChange={(event) => onWorkspaceSettingsNameChange(event.target.value)}
              disabled={!canManageWorkspace || loading}
            />
          </label>
          <div className="settings-note">Workspace identity changes are written through the backend and recorded as `workspace.updated` audit events.</div>
          <div className="run-action-bar">
            <button type="submit" className="primary" disabled={!canManageWorkspace || !workspaceSettingsName.trim() || loading}>Save workspace</button>
            <TabShortcut tab="members">Open audit trail</TabShortcut>
          </div>
        </form>

        <aside className="panel stack settings-side-panel">
          <h3>Settings map</h3>
          <p className="muted">Advanced controls live on dedicated pages so this does not become one giant settings form.</p>
          <div className="settings-map-list">
            <TabShortcut tab="members">
              <strong>Members and permissions</strong>
              <span>{workspaceMembersCount} users · {workspaceRole}</span>
            </TabShortcut>
            <TabShortcut tab="models">
              <strong>Provider and model routing</strong>
              <span>{activeModelCount} active configs · {Math.max(activeModelCount - 1, 0)} live routes</span>
            </TabShortcut>
            <TabShortcut tab="costs">
              <strong>Budgets and rate limits</strong>
              <span>{costUsageText}</span>
            </TabShortcut>
            <TabShortcut tab="system">
              <strong>System health</strong>
              <span>{systemHealthText}</span>
            </TabShortcut>
            <TabShortcut tab="tools">
              <strong>Tool defaults</strong>
              <span>{toolTotal} tools · {canConfigureTools ? "owner editable" : "read only"}</span>
            </TabShortcut>
            <TabShortcut tab="guardrails">
              <strong>Guardrail policies</strong>
              <span>{guardrailConfigurableCount} configurable · {canConfigureGuardrails ? "owner editable" : "read only"}</span>
            </TabShortcut>
            <TabShortcut tab="prompts">
              <strong>Prompt versions</strong>
              <span>{promptTemplateCount} active prompts · LangChain templates</span>
            </TabShortcut>
            {!hasAdvancedAdminShortcuts && <p className="permission-note">No advanced administration shortcuts are available for this role.</p>}
          </div>
        </aside>
      </section>

      <section className="panel stack full-width">
        <div className="row-head">
          <div>
            <h3>Security and configuration boundaries</h3>
            <p className="muted">The local portfolio build keeps secrets in environment configuration and exposes readiness through System Health instead of storing API keys in the browser.</p>
          </div>
          <Badge tone="good">workspace scoped</Badge>
        </div>
        <div className="policy-list settings-boundary-list">
          <span>Workspace rename requires owner permission and backend authorization.</span>
          <span>Provider/model routes are configured in Models; missing API keys are reported in System Health.</span>
          <span>Workspace budget policy is configured in Usage & Costs and enforced by the backend runtime.</span>
          <span>Membership, resource deletion, folder management, and audit-sensitive actions remain owner-gated where required.</span>
        </div>
      </section>
    </div>
  );
}

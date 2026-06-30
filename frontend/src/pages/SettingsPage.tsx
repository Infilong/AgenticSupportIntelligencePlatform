import { FormEvent, ReactNode } from "react";
import { Badge, Metric } from "../app/shared/Primitives";

type WorkspaceMemberRole = "owner" | "developer" | "reviewer" | "viewer" | "member";
type SettingsTab = "members" | "models" | "costs" | "system" | "tools" | "guardrails" | "prompts" | "audit";

type WorkspacePermissionMatrixEntry = {
  role: WorkspaceMemberRole;
  permissions: string[];
};

type SettingsPageProps = {
  workspaceName: string | null;
  workspaceArchivedAt: string | null;
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
  workspaceDeleteConfirmation: string;
  permissionMatrix: WorkspacePermissionMatrixEntry[];
  loading: boolean;
  onWorkspaceSettingsNameChange: (value: string) => void;
  onWorkspaceDeleteConfirmationChange: (value: string) => void;
  onUpdateWorkspaceSettings: (event: FormEvent) => Promise<void>;
  onArchiveWorkspace: () => Promise<void>;
  onRestoreWorkspace: () => Promise<void>;
  onLeaveWorkspace: () => Promise<void>;
  onDeleteWorkspace: (event: FormEvent) => Promise<void>;
  onRefreshWorkspace: () => Promise<void>;
  onGoToTab: (tab: SettingsTab) => void;
  canOpenTab: (tab: SettingsTab) => boolean;
  hasAdvancedAdminShortcuts: boolean;
};

export function SettingsPage({
  workspaceName,
  workspaceArchivedAt,
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
  workspaceDeleteConfirmation,
  permissionMatrix,
  loading,
  onWorkspaceSettingsNameChange,
  onWorkspaceDeleteConfirmationChange,
  onUpdateWorkspaceSettings,
  onArchiveWorkspace,
  onRestoreWorkspace,
  onLeaveWorkspace,
  onDeleteWorkspace,
  onRefreshWorkspace,
  onGoToTab,
  canOpenTab,
  hasAdvancedAdminShortcuts,
}: SettingsPageProps) {
  const isArchived = Boolean(workspaceArchivedAt);
  const canDeleteWorkspace = canManageWorkspace && Boolean(workspaceName) && workspaceDeleteConfirmation === workspaceName;

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
          <h2>Manage workspace identity, lifecycle, and permissions</h2>
          <p className="muted">Workspace administration follows a GitHub-like model: identity, membership, role capabilities, archive, leave, and delete controls are explicit and permission-aware.</p>
        </div>
        <div className="next-action-card">
          <span>Your permission</span>
          <strong>{canManageWorkspace ? "Owner controls" : "Read-only"}</strong>
          <p>{canManageWorkspace ? "You can rename, archive, restore, and delete this workspace." : "You can inspect settings and leave the workspace, but owner-only changes are disabled."}</p>
          <button type="button" onClick={() => void onRefreshWorkspace()}>Refresh workspace</button>
        </div>
      </section>

      <section className="settings-summary-grid">
        <Metric label="Workspace" value={workspaceName ?? "none"} />
        <Metric label="Lifecycle" value={isArchived ? "archived" : "active"} />
        <Metric label="Role" value={workspaceRole} />
        <Metric label="Health signals" value={pendingHealthSignals} />
      </section>

      <section className="settings-workbench single-column-workbench">
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
              placeholder="Example: Billing AI Support"
              disabled={!canManageWorkspace || loading || isArchived}
            />
          </label>
          {isArchived && <div className="settings-note warning-note">Archived workspaces are read-only. Restore the workspace before renaming or changing resources.</div>}
          <div className="settings-note">Workspace identity changes are recorded as <code>workspace.updated</code> audit events.</div>
          <div className="run-action-bar">
            <button type="submit" className="primary" disabled={!canManageWorkspace || !workspaceSettingsName.trim() || loading || isArchived}>Save workspace</button>
            {isArchived ? (
              <button type="button" onClick={() => void onRestoreWorkspace()} disabled={!canManageWorkspace || loading}>Restore workspace</button>
            ) : (
              <button type="button" onClick={() => void onArchiveWorkspace()} disabled={!canManageWorkspace || loading}>Archive workspace</button>
            )}
            <TabShortcut tab="audit">Open audit trail</TabShortcut>
          </div>
        </form>

        <section className="panel stack">
          <div className="row-head">
            <div>
              <h3>Settings map</h3>
              <p className="muted">Related administration pages stay separate so each workflow remains focused and reviewable.</p>
            </div>
            <Badge>admin routes</Badge>
          </div>
          <div className="settings-map-list settings-map-grid">
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
        </section>
      </section>

      <section className="panel stack full-width">
        <div className="row-head">
          <div>
            <h3>Permission matrix</h3>
            <p className="muted">Role capabilities reflect the permission model used for workspace actions.</p>
          </div>
          <Badge tone="good">permission model</Badge>
        </div>
        <div className="permission-matrix-list">
          {permissionMatrix.map((entry) => (
            <article key={entry.role} className="permission-matrix-row">
              <div>
                <strong>{entry.role}</strong>
                <small>{entry.permissions.length} permissions</small>
              </div>
              <div className="permission-chip-row">
                {entry.permissions.slice(0, 12).map((permission) => <span key={permission}>{permission}</span>)}
                {entry.permissions.length > 12 && <span>+{entry.permissions.length - 12} more</span>}
              </div>
            </article>
          ))}
          {permissionMatrix.length === 0 && <p className="muted">Permission matrix is unavailable for the current workspace.</p>}
        </div>
      </section>

      <section className="panel stack full-width danger-zone-panel">
        <div className="row-head">
          <div>
            <h3>Danger zone</h3>
            <p className="muted">Lifecycle actions are separated from normal settings and require owner permission where appropriate.</p>
          </div>
          <Badge tone="bad">careful</Badge>
        </div>
        <div className="danger-zone-list">
          <article className="danger-zone-row">
            <div>
              <strong>Leave workspace</strong>
              <p className="muted">Remove your own membership. The platform prevents leaving as the last owner.</p>
            </div>
            <button type="button" className="danger-button" onClick={() => void onLeaveWorkspace()} disabled={loading || !workspaceName}>Leave workspace</button>
          </article>
          <form className="danger-zone-row" onSubmit={onDeleteWorkspace}>
            <div>
              <strong>Delete workspace</strong>
              <p className="muted">Type the exact workspace name to remove it from your workspace list. This is owner-only and recorded in the audit log before the workspace is hidden.</p>
            </div>
            <label className="danger-confirm-label">
              Confirm workspace name
              <input
                value={workspaceDeleteConfirmation}
                onChange={(event) => onWorkspaceDeleteConfirmationChange(event.target.value)}
                placeholder={workspaceName ?? "Workspace name"}
                disabled={!canManageWorkspace || loading || !workspaceName}
              />
            </label>
            <button type="submit" className="danger-button" disabled={!canDeleteWorkspace || loading}>Delete workspace</button>
          </form>
        </div>
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
          <span>Workspace rename, archive, restore, and deletion require owner permission.</span>
          <span>Archived workspaces are readable but block write-level routes until restored.</span>
          <span>Provider/model routes are configured in Models; missing API keys are reported in System Health.</span>
          <span>Workspace budget policy is configured in Usage & Costs and enforced during agent runs.</span>
          <span>Membership, resource deletion, folder management, and audit-sensitive actions remain owner-gated where required.</span>
        </div>
      </section>
    </div>
  );
}

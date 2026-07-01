import { FormEvent, useMemo, useState } from "react";
import { Badge, EmptyState, Metric } from "../app/shared/Primitives";
import { WorkspaceDeletionPanel } from "./account/WorkspaceDeletionPanel";

type WorkspaceMemberRole = "owner" | "developer" | "reviewer" | "viewer" | "member";
type AccountTab = "tasks" | "reviews" | "members" | "settings";
const WORKSPACE_PAGE_SIZE = 8;

type CurrentUser = {
  id: string;
  email: string;
  display_name: string;
};

type Workspace = {
  id: string;
  name: string;
  created_by_user_id: string;
  archived_at: string | null;
  deleted_at: string | null;
  created_at: string;
};

type AccountPageProps = {
  currentUser: CurrentUser | null;
  workspaces: Workspace[];
  selectedWorkspaceId: string;
  workspaceName: string;
  workspaceRole: string;
  permissionSummary: string;
  permissions: string[];
  canManageWorkspace: boolean;
  pendingReviews: number;
  openTasks: number;
  workspaceMembersCount: number;
  loading: boolean;
  workspaceDeleteConfirmation: string;
  onWorkspaceNameChange: (value: string) => void;
  onWorkspaceDeleteConfirmationChange: (value: string) => void;
  onCreateWorkspace: (event: FormEvent) => Promise<void>;
  onDeleteWorkspace: (event: FormEvent) => Promise<void>;
  onSelectWorkspace: (id: string) => void;
  onGoToTab: (tab: AccountTab) => void;
  canOpenTab: (tab: AccountTab) => boolean;
  formatWorkspaceRole: (role: WorkspaceMemberRole) => string;
  formatDate: (value: string | null) => string;
};

export function AccountPage({
  currentUser,
  workspaces,
  selectedWorkspaceId,
  workspaceName,
  workspaceRole,
  permissionSummary,
  permissions,
  canManageWorkspace,
  pendingReviews,
  openTasks,
  workspaceMembersCount,
  loading,
  workspaceDeleteConfirmation,
  onWorkspaceNameChange,
  onWorkspaceDeleteConfirmationChange,
  onCreateWorkspace,
  onDeleteWorkspace,
  onSelectWorkspace,
  onGoToTab,
  canOpenTab,
  formatWorkspaceRole,
  formatDate,
}: AccountPageProps) {
  const selectedWorkspace = workspaces.find((workspace) => workspace.id === selectedWorkspaceId) ?? null;
  const initials = (currentUser?.display_name || currentUser?.email || "User")
    .split(/\s|@/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("") || "U";
  const ownedWorkspaces = currentUser
    ? workspaces.filter((workspace) => workspace.created_by_user_id === currentUser.id).length
    : 0;
  const archivedWorkspaces = workspaces.filter((workspace) => workspace.archived_at).length;
  const normalizedWorkspaceName = workspaceName.trim().toLowerCase();
  const duplicateWorkspaceName = Boolean(
    normalizedWorkspaceName
      && workspaces.some((workspace) => workspace.name.trim().toLowerCase() === normalizedWorkspaceName),
  );
  const workspaceNameFeedback = duplicateWorkspaceName
    ? "You already have access to a workspace with this name."
    : "Names must be unique in your workspace list.";

  const [workspaceSearch, setWorkspaceSearch] = useState("");
  const [workspacePage, setWorkspacePage] = useState(0);
  const filteredWorkspaces = useMemo(() => {
    const query = workspaceSearch.trim().toLowerCase();
    if (!query) return workspaces;
    return workspaces.filter((workspace) =>
      [workspace.name, workspace.id].some((value) => value.toLowerCase().includes(query)),
    );
  }, [workspaceSearch, workspaces]);
  const workspacePageCount = Math.max(Math.ceil(filteredWorkspaces.length / WORKSPACE_PAGE_SIZE), 1);
  const safeWorkspacePage = Math.min(workspacePage, workspacePageCount - 1);
  const pagedWorkspaces = filteredWorkspaces.slice(
    safeWorkspacePage * WORKSPACE_PAGE_SIZE,
    safeWorkspacePage * WORKSPACE_PAGE_SIZE + WORKSPACE_PAGE_SIZE,
  );
  const canGoToPreviousWorkspacePage = safeWorkspacePage > 0;
  const canGoToNextWorkspacePage = safeWorkspacePage < workspacePageCount - 1;
  const workspaceListStart = filteredWorkspaces.length === 0
    ? 0
    : safeWorkspacePage * WORKSPACE_PAGE_SIZE + 1;
  const workspaceListEnd = Math.min((safeWorkspacePage + 1) * WORKSPACE_PAGE_SIZE, filteredWorkspaces.length);

  function submitCreateWorkspace(event: FormEvent) {
    if (!normalizedWorkspaceName || duplicateWorkspaceName) {
      event.preventDefault();
      return;
    }
    void onCreateWorkspace(event);
  }

  return (
    <div className="account-console">
      <section className="panel account-profile-card">
        <div className="account-avatar" aria-hidden="true">{initials}</div>
        <div>
          <p className="eyebrow">Account and workspaces</p>
          <h2>{currentUser?.display_name || "Signed-in user"}</h2>
          <p className="muted">{currentUser?.email ?? "Session profile is loading."}</p>
        </div>
        <Badge tone={selectedWorkspace ? "good" : "warn"}>{selectedWorkspace ? workspaceRole : "no workspace"}</Badge>
      </section>

      <section className="account-summary-grid">
        <Metric label="Workspaces" value={workspaces.length} />
        <Metric label="Owned" value={ownedWorkspaces} />
        <Metric label="Archived" value={archivedWorkspaces} />
        <Metric label="Current role" value={workspaceRole} />
        <Metric label="Permissions" value={permissions.length} />
        <Metric label="Open tasks" value={openTasks} />
        <Metric label="Pending reviews" value={pendingReviews} />
      </section>

      <form className="panel stack account-create-panel" onSubmit={submitCreateWorkspace}>
        <div className="row-head">
          <div>
            <h3>Create workspace</h3>
            <p className="muted">A workspace is an isolated project area for documents, datasets, agent runs, reviews, costs, and audit logs.</p>
          </div>
          <Badge tone="good">new workspace</Badge>
        </div>
        <label>
          Workspace name
          <input
            value={workspaceName}
            onChange={(event) => onWorkspaceNameChange(event.target.value)}
            placeholder="Example: Billing AI Support"
            disabled={loading}
            aria-invalid={duplicateWorkspaceName}
          />
          <span className={duplicateWorkspaceName ? "account-field-note error" : "account-field-note"}>
            {workspaceNameFeedback}
          </span>
        </label>
        <div className="run-action-bar">
          <button type="submit" className="primary" disabled={loading || !workspaceName.trim() || duplicateWorkspaceName}>
            Create workspace
          </button>
          {selectedWorkspace && canOpenTab("settings") && (
            <button type="button" onClick={() => onGoToTab("settings")}>Open workspace settings</button>
          )}
        </div>
      </form>

      <section className="panel stack">
        <div className="row-head">
          <div>
            <h3>Your workspaces</h3>
            <p className="muted">Select the workspace you want to operate. The active workspace controls every main page.</p>
          </div>
          <Badge>{filteredWorkspaces.length} total</Badge>
        </div>
        {selectedWorkspace && (
          <div className="current-workspace-callout">
            <span>Current workspace</span>
            <strong>{selectedWorkspace.name}</strong>
            <small>{workspaceRole} · {selectedWorkspace.archived_at ? "archived" : "active"}</small>
          </div>
        )}
        <label className="account-workspace-search">
          Search workspaces
          <input
            value={workspaceSearch}
            onChange={(event) => { setWorkspaceSearch(event.target.value); setWorkspacePage(0); }}
            placeholder="Workspace name or id"
          />
        </label>
        <div className="account-workspace-list">
          {pagedWorkspaces.map((workspace) => {
            const isSelected = workspace.id === selectedWorkspaceId;
            const isOwner = currentUser?.id === workspace.created_by_user_id;
            const isArchived = Boolean(workspace.archived_at);
            return (
              <button
                type="button"
                key={workspace.id}
                className={isSelected ? "account-workspace-row selected" : "account-workspace-row"}
                onClick={() => onSelectWorkspace(workspace.id)}
              >
                <span>
                  <strong>{workspace.name}</strong>
                  <small>{isArchived ? `Archived ${formatDate(workspace.archived_at)}` : `Created ${formatDate(workspace.created_at)}`}</small>
                </span>
                <span className="account-workspace-badges">
                  {isOwner && <Badge tone="good">owner</Badge>}
                  {isArchived && <Badge tone="warn">archived</Badge>}
                  {isSelected && <Badge>{isArchived ? "selected" : "active"}</Badge>}
                </span>
              </button>
            );
          })}
          {workspaces.length === 0 && (
            <EmptyState title="No workspace yet" detail="Create your first workspace above to unlock the platform workflow." />
          )}
          {workspaces.length > 0 && filteredWorkspaces.length === 0 && (
            <EmptyState title="No workspaces match" detail="Clear search or use another workspace name." />
          )}
        </div>
        {workspaces.length > WORKSPACE_PAGE_SIZE && (
          <div className="pagination-bar">
            <button type="button" onClick={() => setWorkspacePage((page) => Math.max(page - 1, 0))} disabled={!canGoToPreviousWorkspacePage || loading}>Previous</button>
            <span>{workspaceListStart}-{workspaceListEnd} of {filteredWorkspaces.length} workspaces</span>
            <button type="button" onClick={() => setWorkspacePage((page) => page + 1)} disabled={!canGoToNextWorkspacePage || loading}>Next</button>
          </div>
        )}
      </section>

      <section className="panel stack">
        <div className="row-head">
          <div>
            <h3>Current workspace access</h3>
            <p className="muted">{permissionSummary}</p>
          </div>
          <Badge tone={canManageWorkspace ? "good" : "warn"}>
            {canManageWorkspace ? "admin capable" : "limited access"}
          </Badge>
        </div>
        <div className="account-permission-board">
          <Metric label="Members" value={workspaceMembersCount} />
          <Metric label="Role" value={workspaceRole} />
          <Metric label="Manage workspace" value={canManageWorkspace ? "allowed" : "restricted"} />
        </div>
        <div className="permission-chip-row">
          {permissions.map((permission) => <span key={permission}>{permission}</span>)}
          {permissions.length === 0 && <span>No workspace permissions loaded</span>}
        </div>
        <div className="account-shortcuts">
          {canOpenTab("tasks") && <button type="button" onClick={() => onGoToTab("tasks")}>Open task queue</button>}
          {canOpenTab("reviews") && <button type="button" onClick={() => onGoToTab("reviews")}>Open human review</button>}
          {canOpenTab("members") && <button type="button" onClick={() => onGoToTab("members")}>Manage members</button>}
          {canOpenTab("settings") && <button type="button" onClick={() => onGoToTab("settings")}>Workspace settings</button>}
        </div>
      </section>

      <WorkspaceDeletionPanel
        workspaceName={selectedWorkspace?.name ?? null}
        canManageWorkspace={canManageWorkspace}
        loading={loading}
        workspaceDeleteConfirmation={workspaceDeleteConfirmation}
        onWorkspaceDeleteConfirmationChange={onWorkspaceDeleteConfirmationChange}
        onDeleteWorkspace={onDeleteWorkspace}
        onOpenSettings={() => onGoToTab("settings")}
      />

      <section className="panel stack">
        <div className="row-head">
          <div>
            <h3>Role presets</h3>
            <p className="muted">Workspace permissions come from role presets. Owners can change member roles from the Members page.</p>
          </div>
          <Badge>permission model</Badge>
        </div>
        <div className="account-role-grid">
          {(["owner", "developer", "reviewer", "viewer"] as WorkspaceMemberRole[]).map((role) => (
            <article key={role}>
              <strong>{formatWorkspaceRole(role)}</strong>
              <span>{role === "owner" ? "Full workspace administration." : role === "developer" ? "Build and operate AI resources." : role === "reviewer" ? "Resolve human-review cases." : "Inspect workspace evidence and metrics."}</span>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

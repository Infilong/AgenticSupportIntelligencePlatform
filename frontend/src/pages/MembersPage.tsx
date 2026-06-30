import { FormEvent } from "react";
import { Badge, EmptyState, Metric } from "../app/shared/Primitives";

type WorkspaceMemberRole = "owner" | "developer" | "reviewer" | "viewer" | "member";

type WorkspaceMember = {
  id: string;
  workspace_id: string;
  user_id: string;
  email: string;
  display_name: string;
  role: WorkspaceMemberRole;
  permissions: string[];
  created_at: string;
};

type MembersPageProps = {
  workspaceRole: string;
  permissionSummary: string;
  currentUserId: string | null;
  members: WorkspaceMember[];
  memberEmail: string;
  memberRole: WorkspaceMemberRole;
  canManageWorkspace: boolean;
  loading: boolean;
  formatWorkspaceRole: (role: WorkspaceMemberRole) => string;
  formatDate: (value: string) => string;
  onMemberEmailChange: (email: string) => void;
  onMemberRoleChange: (role: WorkspaceMemberRole) => void;
  onSubmitAddMember: (event: FormEvent) => Promise<void>;
  onRefreshMembers: () => Promise<void>;
  onOpenAudit: () => void;
  onUpdateMemberRole: (member: WorkspaceMember, role: WorkspaceMemberRole) => Promise<void>;
  onRemoveMember: (member: WorkspaceMember) => Promise<void>;
};

export function MembersPage({
  workspaceRole,
  permissionSummary,
  currentUserId,
  members,
  memberEmail,
  memberRole,
  canManageWorkspace,
  loading,
  formatWorkspaceRole,
  formatDate,
  onMemberEmailChange,
  onMemberRoleChange,
  onSubmitAddMember,
  onRefreshMembers,
  onOpenAudit,
  onUpdateMemberRole,
  onRemoveMember,
}: MembersPageProps) {
  const ownerCount = members.filter((member) => member.role === "owner").length;
  const developerCount = members.filter((member) => member.role === "developer" || member.role === "member").length;
  const reviewerCount = members.filter((member) => member.role === "reviewer").length;
  const viewerCount = members.filter((member) => member.role === "viewer").length;
  const currentMember = members.find((member) => member.user_id === currentUserId) ?? null;

  return (
    <div className="settings-console member-console">
      <section className="panel settings-hero">
        <div>
          <p className="eyebrow">Workspace administration</p>
          <h2>Manage members and permissions</h2>
          <p className="muted">
            Membership is permission-controlled. Owners assign role presets for platform owners, developers,
            reviewers, and viewers while the workspace keeps at least one owner.
          </p>
        </div>
        <div className="next-action-card">
          <span>Your access</span>
          <strong>{workspaceRole}</strong>
          <p>{currentMember ? `${currentMember.email} has ${currentMember.permissions.length} permissions in this workspace.` : permissionSummary}</p>
          <button type="button" onClick={() => void onRefreshMembers()}>Refresh members</button>
        </div>
      </section>

      <section className="settings-summary-grid">
        <Metric label="Members" value={members.length} />
        <Metric label="Owners" value={ownerCount} />
        <Metric label="Developers" value={developerCount} />
        <Metric label="Reviewers" value={reviewerCount} />
        <Metric label="Viewers" value={viewerCount} />
        <Metric label="Manage workspace" value={canManageWorkspace ? "allowed" : "restricted"} />
      </section>

      <section className="settings-workbench">
        <form className="panel stack settings-editor-panel" onSubmit={onSubmitAddMember}>
          <div className="row-head">
            <div>
              <h3>Add registered user</h3>
              <p className="muted">Use this for local-team collaboration. The user must already have an account in this app.</p>
            </div>
            <Badge tone={canManageWorkspace ? "good" : "warn"}>{canManageWorkspace ? "owner action" : "restricted"}</Badge>
          </div>
          <div className="settings-meta-grid">
            <label>
              User email
              <input value={memberEmail} onChange={(event) => onMemberEmailChange(event.target.value)} placeholder="engineer@example.com" />
            </label>
            <label>
              Initial role
              <select value={memberRole} onChange={(event) => onMemberRoleChange(event.target.value as WorkspaceMemberRole)}>
                <option value="developer">Developer</option>
                <option value="reviewer">Reviewer</option>
                <option value="viewer">Viewer</option>
                <option value="owner">Owner</option>
                <option value="member">Legacy member</option>
              </select>
            </label>
          </div>
          <div className="settings-note">
            Role presets are enforced by backend permissions. Legacy members keep operational build and review access for existing workspaces.
          </div>
          <div className="run-action-bar">
            <button type="submit" className="primary" disabled={!canManageWorkspace || !memberEmail.trim() || loading}>Add member</button>
            <button type="button" onClick={onOpenAudit}>Open audit trail</button>
          </div>
        </form>

        <aside className="panel stack settings-side-panel">
          <h3>Permission model</h3>
          <p className="muted">This is role-preset RBAC, not custom enterprise policy yet. Backend permissions gate write, operate, review, and destructive actions.</p>
          <div className="policy-list">
            <span>Owners: manage members, budgets, models, guardrails, destructive cleanup, and agent archive actions</span>
            <span>Developers: import data, manage knowledge, configure/run agents, tools, prompts, folders, and evaluations</span>
            <span>Reviewers: inspect traces and resolve human-review tasks without build/admin controls</span>
            <span>Viewers: read-only inspection across allowed workspace pages</span>
            <span>Non-members: receive workspace-not-found responses for scoped APIs</span>
          </div>
        </aside>
      </section>

      <section className="panel full-width stack settings-history-panel">
        <div className="row-head">
          <div>
            <h3>Workspace members</h3>
            <p className="muted">Role changes and removals are owner-only and recorded in the audit log.</p>
          </div>
          <Badge>{members.length} users</Badge>
        </div>
        <div className="member-card-grid">
          {members.map((member) => {
            const isCurrentUser = member.user_id === currentUserId;
            const visibleMemberPermissions = member.permissions.slice(0, 6);
            return (
              <article className="member-card" key={member.id}>
                <div className="row-head">
                  <div>
                    <strong>{member.display_name}</strong>
                    <p className="muted">{member.email}</p>
                  </div>
                  <div className="review-actions">
                    {isCurrentUser && <Badge tone="good">you</Badge>}
                    <Badge tone={member.role === "owner" ? "good" : member.role === "reviewer" ? "warn" : "neutral"}>
                      {formatWorkspaceRole(member.role)}
                    </Badge>
                  </div>
                </div>
                <div className="settings-meta-grid compact-member-controls">
                  <label>
                    Role
                    <select
                      value={member.role}
                      onChange={(event) => void onUpdateMemberRole(member, event.target.value as WorkspaceMemberRole)}
                      disabled={!canManageWorkspace || isCurrentUser || loading}
                    >
                      <option value="developer">Developer</option>
                      <option value="reviewer">Reviewer</option>
                      <option value="viewer">Viewer</option>
                      <option value="owner">Owner</option>
                      <option value="member">Legacy member</option>
                    </select>
                  </label>
                  <button
                    type="button"
                    className="danger-button"
                    onClick={() => void onRemoveMember(member)}
                    disabled={!canManageWorkspace || isCurrentUser || loading}
                  >
                    Remove
                  </button>
                </div>
                <div className="permission-chip-row member-permissions">
                  {visibleMemberPermissions.map((permission) => <span key={permission}>{permission}</span>)}
                  {member.permissions.length > visibleMemberPermissions.length && (
                    <span>+{member.permissions.length - visibleMemberPermissions.length}</span>
                  )}
                </div>
                <small>Joined {formatDate(member.created_at)}</small>
              </article>
            );
          })}
        </div>
        {members.length === 0 && <EmptyState title="No members loaded" detail="Refresh members or check workspace access." />}
      </section>
    </div>
  );
}

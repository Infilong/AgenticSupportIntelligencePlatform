import { FormEvent } from "react";
import { Badge } from "../../app/shared/Primitives";

type WorkspaceDeletionPanelProps = {
  workspaceName: string | null;
  canManageWorkspace: boolean;
  loading: boolean;
  workspaceDeleteConfirmation: string;
  onWorkspaceDeleteConfirmationChange: (value: string) => void;
  onDeleteWorkspace: (event: FormEvent) => Promise<void>;
  onOpenSettings: () => void;
};

export function WorkspaceDeletionPanel({
  workspaceName,
  canManageWorkspace,
  loading,
  workspaceDeleteConfirmation,
  onWorkspaceDeleteConfirmationChange,
  onDeleteWorkspace,
  onOpenSettings,
}: WorkspaceDeletionPanelProps) {
  const canDeleteWorkspace = canManageWorkspace && Boolean(workspaceName) && workspaceDeleteConfirmation === workspaceName;

  return (
    <section className="panel stack full-width danger-zone-panel account-delete-panel">
      <div className="row-head">
        <div>
          <h3>Workspace deletion</h3>
          <p className="muted">Delete is owner-only and uses the same exact-name confirmation policy as workspace settings.</p>
        </div>
        <Badge tone={canManageWorkspace ? "bad" : "warn"}>{canManageWorkspace ? "owner action" : "restricted"}</Badge>
      </div>
      <div className="policy-list account-retention-list">
        <span>Soft delete hides the workspace from normal lists immediately.</span>
        <span>Audit events, cost ledgers, traces, and operational records are retained for governance and debugging.</span>
        <span>Permanent purge is intentionally separate from normal user deletion.</span>
      </div>
      <form className="danger-zone-row account-delete-row" onSubmit={onDeleteWorkspace}>
        <div>
          <strong>{workspaceName ? `Delete ${workspaceName}` : "No workspace selected"}</strong>
          <p className="muted">Type the current workspace name to confirm deletion. This action is recorded before the workspace is hidden.</p>
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
        <div className="run-action-bar">
          <button type="submit" className="danger-button" disabled={!canDeleteWorkspace || loading}>Delete workspace</button>
          <button type="button" onClick={onOpenSettings}>Open settings</button>
        </div>
      </form>
    </section>
  );
}

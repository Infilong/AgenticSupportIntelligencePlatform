import { Badge } from "./Primitives";

type Workspace = {
  id: string;
  name: string;
  archived_at: string | null;
  created_at: string;
};

type WorkspaceSwitcherProps = {
  selectedWorkspace: Workspace | null;
  workspaceRole: string;
  consoleState: string;
  onOpenAccount: () => void;
};

export function WorkspaceSwitcher({
  selectedWorkspace,
  workspaceRole,
  consoleState,
  onOpenAccount,
}: WorkspaceSwitcherProps) {
  const selectedWorkspaceState = selectedWorkspace?.archived_at ? "archived" : "active";

  return (
    <section className="workspace-card workspace-summary-card" aria-label="Current workspace">
      <div className="sidebar-workspace-summary">
        <span className="mini-label">Current workspace</span>
        <strong>{selectedWorkspace?.name ?? "Not selected"}</strong>
        <small>{selectedWorkspace ? `${workspaceRole} - ${selectedWorkspaceState}` : "Create or select one from Account"}</small>
      </div>

      <div className="workspace-summary-actions">
        <Badge tone={selectedWorkspace ? "good" : "warn"}>{consoleState}</Badge>
        <button type="button" className="workspace-manage-button" onClick={onOpenAccount}>
          Manage
        </button>
      </div>
    </section>
  );
}

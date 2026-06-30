import { useMemo, useState } from "react";
import { Badge } from "./Primitives";

type Workspace = {
  id: string;
  name: string;
  archived_at: string | null;
  created_at: string;
};

type WorkspaceSwitcherProps = {
  workspaces: Workspace[];
  selectedWorkspace: Workspace | null;
  selectedWorkspaceId: string;
  workspaceRole: string;
  consoleState: string;
  loading: boolean;
  onSelectWorkspace: (workspaceId: string) => void;
  onOpenAccount: () => void;
};

export function WorkspaceSwitcher({
  workspaces,
  selectedWorkspace,
  selectedWorkspaceId,
  workspaceRole,
  consoleState,
  loading,
  onSelectWorkspace,
  onOpenAccount,
}: WorkspaceSwitcherProps) {
  const [query, setQuery] = useState("");
  const selectedWorkspaceState = selectedWorkspace?.archived_at ? "archived" : "active";
  const filteredWorkspaces = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    if (!normalizedQuery) return workspaces;
    return workspaces.filter((workspace) =>
      [workspace.name, workspace.id].some((value) => value.toLowerCase().includes(normalizedQuery)),
    );
  }, [query, workspaces]);

  return (
    <section className="workspace-card workspace-summary-card" aria-label="Current workspace">
      <div className="sidebar-workspace-summary">
        <span className="mini-label">Current workspace</span>
        <strong>{selectedWorkspace?.name ?? "Not selected"}</strong>
        <small>{selectedWorkspace ? `${workspaceRole} - ${selectedWorkspaceState}` : "Create or select one from Account"}</small>
      </div>

      <label className="workspace-find-field">
        <span>Find workspace</span>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search by name"
          disabled={loading || workspaces.length === 0}
        />
      </label>

      <div className="workspace-scroll-window" role="listbox" aria-label="Workspace options">
        {filteredWorkspaces.map((workspace) => {
          const selected = workspace.id === selectedWorkspaceId;
          return (
            <button
              type="button"
              key={workspace.id}
              className={selected ? "workspace-list-item selected" : "workspace-list-item"}
              onClick={() => onSelectWorkspace(workspace.id)}
              disabled={loading}
              aria-selected={selected}
            >
              <span>{workspace.name}</span>
              <small>{workspace.archived_at ? "Archived" : selected ? "Current" : "Open"}</small>
            </button>
          );
        })}
        {workspaces.length === 0 && <p className="workspace-list-note">No workspaces yet.</p>}
        {workspaces.length > 0 && filteredWorkspaces.length === 0 && <p className="workspace-list-note">No matching workspace.</p>}
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

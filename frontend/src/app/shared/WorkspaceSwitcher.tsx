import { useMemo, useState } from "react";
import { Badge } from "./Primitives";

const WORKSPACE_SWITCHER_PAGE_SIZE = 6;

type Workspace = {
  id: string;
  name: string;
  archived_at: string | null;
  created_at: string;
};

type WorkspaceSwitcherProps = {
  workspaces: Workspace[];
  selectedWorkspaceId: string;
  workspaceRole: string;
  consoleState: string;
  loading: boolean;
  onSelectWorkspace: (workspaceId: string) => void;
  onOpenAccount: () => void;
};

export function WorkspaceSwitcher({
  workspaces,
  selectedWorkspaceId,
  workspaceRole,
  consoleState,
  loading,
  onSelectWorkspace,
  onOpenAccount,
}: WorkspaceSwitcherProps) {
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const selectedWorkspace = workspaces.find((workspace) => workspace.id === selectedWorkspaceId) ?? null;
  const filteredWorkspaces = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    if (!normalizedQuery) return workspaces;
    return workspaces.filter((workspace) =>
      [workspace.name, workspace.id].some((value) => value.toLowerCase().includes(normalizedQuery)),
    );
  }, [query, workspaces]);
  const pageCount = Math.max(Math.ceil(filteredWorkspaces.length / WORKSPACE_SWITCHER_PAGE_SIZE), 1);
  const safePage = Math.min(page, pageCount - 1);
  const visibleWorkspaces = filteredWorkspaces.slice(
    safePage * WORKSPACE_SWITCHER_PAGE_SIZE,
    safePage * WORKSPACE_SWITCHER_PAGE_SIZE + WORKSPACE_SWITCHER_PAGE_SIZE,
  );
  const rangeStart = filteredWorkspaces.length === 0 ? 0 : safePage * WORKSPACE_SWITCHER_PAGE_SIZE + 1;
  const rangeEnd = Math.min((safePage + 1) * WORKSPACE_SWITCHER_PAGE_SIZE, filteredWorkspaces.length);
  const selectedWorkspaceState = selectedWorkspace?.archived_at ? "archived" : "active";

  return (
    <section className="workspace-card workspace-switcher">
      <div className="row-head">
        <div>
          <span className="mini-label">Current workspace</span>
          <strong>{selectedWorkspace?.name ?? "Not selected"}</strong>
          <small>{selectedWorkspace ? `${workspaceRole} - ${selectedWorkspaceState}` : "Choose a workspace to continue"}</small>
        </div>
        <Badge tone={selectedWorkspaceId ? "good" : "warn"}>{consoleState}</Badge>
      </div>
      {selectedWorkspace && <div className="current-workspace-marker" aria-label="Selected workspace">Selected: {selectedWorkspace.name}</div>}
      <label>
        Switch workspace
        <input
          value={query}
          onChange={(event) => { setQuery(event.target.value); setPage(0); }}
          placeholder="Search workspace"
          disabled={loading || workspaces.length === 0}
        />
      </label>
      <div className="workspace-switcher-list" role="listbox" aria-label="Workspace options">
        {visibleWorkspaces.map((workspace) => {
          const selected = workspace.id === selectedWorkspaceId;
          return (
            <button
              type="button"
              key={workspace.id}
              className={selected ? "workspace-switcher-option selected" : "workspace-switcher-option"}
              onClick={() => onSelectWorkspace(workspace.id)}
              disabled={loading}
              aria-selected={selected}
            >
              <span>
                <strong>{workspace.name}</strong>
                <small>{workspace.archived_at ? "Archived" : "Active"}</small>
              </span>
              {selected && <Badge>current</Badge>}
            </button>
          );
        })}
        {workspaces.length === 0 && <p className="permission-note">No workspaces yet. Create one from Account.</p>}
        {workspaces.length > 0 && filteredWorkspaces.length === 0 && <p className="permission-note">No workspaces match this search.</p>}
      </div>
      {workspaces.length > WORKSPACE_SWITCHER_PAGE_SIZE && (
        <div className="workspace-switcher-pagination">
          <button type="button" onClick={() => setPage((current) => Math.max(current - 1, 0))} disabled={safePage === 0 || loading}>Prev</button>
          <span>{rangeStart}-{rangeEnd} of {filteredWorkspaces.length}</span>
          <button type="button" onClick={() => setPage((current) => current + 1)} disabled={safePage >= pageCount - 1 || loading}>Next</button>
        </div>
      )}
      <div className="role-line">
        <span>Role</span>
        <strong>{workspaceRole}</strong>
      </div>
      <button type="button" className="workspace-manage-button" onClick={onOpenAccount}>
        Account & workspaces
      </button>
    </section>
  );
}
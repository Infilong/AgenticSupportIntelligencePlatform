import { FormEvent, ReactNode, SetStateAction } from "react";
import { Badge, EmptyState, Metric } from "../app/shared/Primitives";

type ResourceType = "knowledge_document" | "dataset" | "evaluation_run" | "agent_config";

type Language = "en" | "ja" | "zh";

type KnowledgeDocument = {
  id: string;
  title: string;
  language: Language;
  status: string;
  error_message: string | null;
  folder_id: string | null;
  created_at: string;
  updated_at: string;
};

type DocumentChunk = {
  id: string;
  language: Language;
  chunk_index: number;
  content: string;
  token_count: number;
};

type DocumentVersion = {
  id: string;
  version: number;
  content_type: string;
  raw_text: string;
  created_at: string;
};

type DocumentDetail = {
  document: KnowledgeDocument;
  latest_version: DocumentVersion | null;
  chunks: DocumentChunk[];
  embedding_count: number;
};

type ResourceFolder = {
  id: string;
  workspace_id: string;
  resource_type: ResourceType;
  name: string;
  parent_folder_id: string | null;
  created_by_user_id: string;
  created_at: string;
  updated_at: string;
};

type ResourceFolderPanelRenderer = (props: {
  resourceType: ResourceType;
  title: string;
  detail: string;
  selectedFolderId: string;
  onSelectFolder: (folderId: string) => void;
  folderName: string;
  onFolderNameChange: (value: string) => void;
}) => ReactNode;

type FolderPickerRenderer = (props: {
  label: string;
  value: string;
  folders: ResourceFolder[];
  onChange: (value: string) => void;
  disabled?: boolean;
  resourceLabel: string;
  compact?: boolean;
}) => ReactNode;

type MatchesSearch = (query: string, ...values: Array<string | null | undefined>) => boolean;
type FolderLabel = (resourceType: ResourceType, folderId: string | null) => string;
type ResourceItemCount = (resourceType: ResourceType, folderId: string) => number;
type SetPage = (updater: number | ((current: number) => number)) => void;

type DocumentDraft = {
  documentTitle: string;
  documentLanguage: Language;
  documentFolderId: string;
  documentContent: string;
  isEditMode: boolean;
};

type DocumentsPageProps = {
  documents: KnowledgeDocument[];
  totalKnowledgeDocumentCount: number;
  selectedDocumentId: string;
  selectedKnowledgeFolderId: string;
  documentFolderId: string;
  documentSearch: string;
  documentPage: number;
  documentTotal: number;
  documentHasNext: boolean;
  maxVisibleChunks: number;
  maxVisibleResources: number;
  chunkSearch: string;
  documentLanguage: Language;
  documentTitle: string;
  documentContent: string;
  documentFolders: ResourceFolder[];
  selectedDocument: KnowledgeDocument | null;
  documentDetail: DocumentDetail | null;
  knowledgeFolders: ResourceFolder[];
  datasetName: string;
  selectedFolderLabel: string;
  selectedFolderDocumentCount: number;
  selectedFolderName: string;
  canWriteKnowledge: boolean;
  canRunAgent: boolean;
  canManageResourceFolders: boolean;
  canManageResources: boolean;
  loading: boolean;
  onDocumentSearchChange: (value: string) => void;
  onDocumentPageChange: SetPage;
  onChunkSearchChange: (value: string) => void;
  onSelectKnowledgeFolder: (folderId: string) => void;
  knowledgeFolderName: string;
  onKnowledgeFolderNameChange: (value: string) => void;
  onDocumentFolderIdChange: (value: string) => void;
  onUploadDocument: (event: FormEvent) => Promise<void>;
  onSaveDocumentEdit: (event: FormEvent) => Promise<void>;
  onMoveDocumentFolder: (documentId: string, folderId: string) => Promise<void>;
  onDeleteDocument: (documentId: string) => Promise<void>;
  onDeleteSelectedDocument: () => Promise<void> | void;
  onResetDocumentForm: (folderId?: string) => void;
  onMoveSelectedDocumentFolder: () => Promise<void> | void;
  onLoadDocumentDetail: (documentId: string) => Promise<void>;
  onLoadDocuments: () => Promise<void> | void;
  onChangeDocumentLanguage: (language: Language) => void;
  onLoadDocumentLanguage: () => Language;
  onSetDocumentTitle: (value: string) => void;
  onSetDocumentContent: (value: string) => void;
  onSetDocumentLanguage: (language: Language) => void;
  onGoToTab: (tab: "agent") => void;
  matchesSearch: MatchesSearch;
  folderLabel: FolderLabel;
  resourceItemCount: ResourceItemCount;
  formatDate: (value: string) => string;
  formatCost: (value: number | null | undefined) => string;
  onTabShortcut: () => void;
  goToTab: (tab: "agent") => void;
  indexedDocumentCount: number;
  totalChunkTokens: number;
  chunkVisibleCount: number;
  hiddenChunkCount: number;
  canUploadToWorkspace: boolean;
  resourceFolderPanel: ResourceFolderPanelRenderer;
  folderPicker: FolderPickerRenderer;
};

export function DocumentsPage({
  documents,
  totalKnowledgeDocumentCount,
  selectedDocumentId,
  selectedKnowledgeFolderId,
  documentFolderId,
  documentSearch,
  documentPage,
  documentTotal,
  documentHasNext,
  maxVisibleChunks,
  maxVisibleResources,
  chunkSearch,
  documentLanguage,
  documentTitle,
  documentContent,
  selectedDocument,
  documentDetail,
  knowledgeFolders,
  selectedFolderLabel,
  selectedFolderDocumentCount,
  canWriteKnowledge,
  canRunAgent,
  canManageResources,
  loading,
  onDocumentSearchChange,
  onDocumentPageChange,
  onChunkSearchChange,
  knowledgeFolderName,
  onKnowledgeFolderNameChange,
  onDocumentFolderIdChange,
  onUploadDocument,
  onSaveDocumentEdit,
  onMoveDocumentFolder,
  onDeleteDocument,
  onDeleteSelectedDocument,
  onResetDocumentForm,
  onMoveSelectedDocumentFolder,
  onLoadDocumentDetail,
  onLoadDocuments,
  onChangeDocumentLanguage,
  onSetDocumentTitle,
  onSetDocumentContent,
  onSetDocumentLanguage,
  onGoToTab,
  matchesSearch,
  folderLabel,
  resourceItemCount,
  formatDate,
  formatCost,
  goToTab,
  resourceFolderPanel,
  folderPicker,
  onSelectKnowledgeFolder,
  canManageResourceFolders,
}: DocumentsPageProps) {
  const indexedDocumentCount = documents.filter((document) => document.status === "indexed").length;
  const selectedDocumentName = selectedDocument?.title ?? "";
  const displayedDocuments = documents;
  const documentPageStart = documentPage * maxVisibleResources + (documents.length ? 1 : 0);
  const documentPageEnd = documentPage * maxVisibleResources + documents.length;
  const canGoToPreviousDocumentPage = documentPage > 0;
  const canGoToNextDocumentPage = documentHasNext;
  const visibleChunks = documentDetail
    ? documentDetail.chunks.filter((chunk) =>
      matchesSearch(
        chunkSearch,
        chunk.id,
        `chunk ${chunk.chunk_index}`,
        chunk.language,
        String(chunk.token_count),
        chunk.content,
      ),
    )
    : [];
  const displayedChunks = visibleChunks.slice(0, maxVisibleChunks);
  const hiddenChunkCount = Math.max(visibleChunks.length - displayedChunks.length, 0);

  return (
    <div className="knowledge-console">
      <section className="panel knowledge-hero">
        <div>
          <p className="eyebrow">Knowledge base</p>
          <h2>Manage retrieval evidence</h2>
          <p className="muted">Upload, edit, reindex, and inspect the exact chunks the LangChain retrieval tool can cite during a LangGraph run.</p>
        </div>
        <div className="knowledge-health-grid">
          <Metric label="Documents" value={totalKnowledgeDocumentCount} />
          <Metric label="Page indexed" value={indexedDocumentCount} />
          <Metric label="Selected chunks" value={documentDetail?.chunks.length ?? 0} />
          <Metric label="Embeddings" value={documentDetail?.embedding_count ?? 0} />
        </div>
      </section>

      <section className="knowledge-workbench">
        {resourceFolderPanel({
          resourceType: "knowledge_document",
          title: "Knowledge folders",
          detail: "Organize uploaded policies, FAQs, release notes, and manuals before the library becomes large.",
          selectedFolderId: selectedKnowledgeFolderId,
          onSelectFolder: onSelectKnowledgeFolder,
          folderName: knowledgeFolderName,
          onFolderNameChange: onKnowledgeFolderNameChange,
        })}
        <aside className="panel stack document-library-panel">
          <div className="row-head">
            <div>
              <h3>Document library</h3>
              <p className="muted">Workspace-owned policies and FAQs available to retrieval.</p>
            </div>
            <button type="button" onClick={() => onResetDocumentForm()}>New</button>
          </div>
          <div className="library-toolbar">
            <div className="folder-scope-banner">
              <span>Current folder</span>
              <strong>{selectedFolderLabel}</strong>
              <small>{documents.length ? `${documentPageStart}-${documentPageEnd}` : "0"} shown from {documentTotal} matching this view.</small>
            </div>
            <div className="folder-scope-banner">
              <span>Upload target</span>
              <strong>{folderLabel("knowledge_document", documentFolderId || null)}</strong>
              <small>New knowledge files and edits stay attached to this folder unless you choose another target.</small>
            </div>
            <label>
              Search current folder
              <input
                value={documentSearch}
                onChange={(event) => { onDocumentPageChange(0); onDocumentSearchChange(event.target.value); }}
                placeholder="Document title, language, status, or id"
              />
            </label>
            <p className="permission-note">
              Role-aware controls: knowledge writers can upload and reindex, folder managers can organize, and deletion requires owner permission.
            </p>
          </div>
          <div className="document-list">
            {displayedDocuments.map((document) => (
              <article
                key={document.id}
                className={`document-card ${selectedDocumentId === document.id ? "selected" : ""}`}
              >
                <button type="button" className="document-select-button" onClick={() => void onLoadDocumentDetail(document.id)}>
                  <strong>{document.title}</strong>
                  <Badge tone={document.status === "indexed" ? "good" : document.status === "failed" ? "bad" : "warn"}>{document.status}</Badge>
                </button>
                <span className="document-metadata">{document.language.toUpperCase()} · {folderLabel("knowledge_document", document.folder_id)} · updated {formatDate(document.updated_at)}</span>
                {document.error_message && <small>{document.error_message}</small>}
                <div className="document-card-actions">
                  <label className="document-card-folder-control">
                    <span>Folder</span>
                    <select
                      value={document.folder_id ?? ""}
                      onChange={(event) => void onMoveDocumentFolder(document.id, event.target.value)}
                      disabled={!canManageResourceFolders || loading}
                    >
                      <option value="">Unfiled</option>
                      {knowledgeFolders.map((folder) => (
                        <option key={folder.id} value={folder.id}>{folder.name}</option>
                      ))}
                    </select>
                  </label>
                  <button type="button" className="danger-button" onClick={() => void onDeleteDocument(document.id)} disabled={!canManageResources || loading}>Delete</button>
                </div>
              </article>
            ))}
            {documents.length === 0 && (
              <EmptyState
                title="No documents match this view"
                detail={documentTotal === 0 && selectedFolderDocumentCount === 0 ? "Upload a policy or FAQ here, or switch folders." : "Clear search, move to the previous page, or try another folder."}
              />
            )}
          </div>
          <div className="pagination-bar">
            <button type="button" onClick={() => onDocumentPageChange((page) => Math.max(page - 1, 0))} disabled={!canGoToPreviousDocumentPage || loading}>Previous</button>
            <span>Page {documentPage + 1} · {documents.length ? `${documentPageStart}-${documentPageEnd}` : "0"} of {documentTotal}</span>
            <button type="button" onClick={() => onDocumentPageChange((page) => page + 1)} disabled={!canGoToNextDocumentPage || loading}>Next</button>
          </div>
          <p className="permission-note">This library is loaded from the backend by folder, search, offset, and limit so large knowledge bases stay navigable without loading every file into the browser.</p>
        </aside>

        <form className="panel stack knowledge-editor-panel" onSubmit={selectedDocumentId ? onSaveDocumentEdit : onUploadDocument}>
          <div className="row-head">
            <div>
              <h3>{selectedDocumentId ? "Edit and reindex" : "Create knowledge document"}</h3>
              <p className="muted">Saving creates an indexed document version. The agent only answers from retrieved chunks.</p>
            </div>
            <div className="review-actions">
              {selectedDocument && <Badge tone={selectedDocument.status === "indexed" ? "good" : "warn"}>{selectedDocument.status}</Badge>}
              {selectedDocumentId && (
                <button type="button" className="danger-button" onClick={() => void onDeleteSelectedDocument()} disabled={!canManageResources || loading}>Delete</button>
              )}
            </div>
          </div>
          <div className="knowledge-meta-grid">
            <label>Title<input value={documentTitle} onChange={(event) => onSetDocumentTitle(event.target.value)} placeholder="Example: Refund policy EN" /></label>
            <label>
              Language
              <select value={documentLanguage} onChange={(event) => onSetDocumentLanguage(event.target.value as Language)}>
                <option value="en">English</option>
                <option value="ja">Japanese</option>
                <option value="zh">Chinese</option>
              </select>
            </label>
            {folderPicker({
              label: "Knowledge target folder",
              value: documentFolderId,
              folders: knowledgeFolders,
              onChange: onDocumentFolderIdChange,
              disabled: loading,
              resourceLabel: "knowledge",
            })}
            <div className="version-card">
              <span>Version</span>
              <strong>{documentDetail?.latest_version ? `v${documentDetail.latest_version.version}` : "new"}</strong>
              <small>{documentDetail?.latest_version ? formatDate(documentDetail.latest_version.created_at) : "Not indexed yet"}</small>
            </div>
          </div>
          <label>
            Source content
            <textarea rows={16} value={documentContent} onChange={(event) => onSetDocumentContent(event.target.value)} placeholder="Paste the policy, FAQ, release note, or support manual text here." />
          </label>
          <div className="run-action-bar">
            <button type="submit" className="primary" disabled={!canWriteKnowledge || loading || !documentTitle.trim() || !documentContent.trim()}>
              {selectedDocumentId ? "Save edits and reindex" : "Upload and index"}
            </button>
            {selectedDocumentId && <button type="button" onClick={() => onMoveSelectedDocumentFolder()} disabled={!canManageResourceFolders || loading}>Move only</button>}
            {selectedDocumentId && <button type="button" onClick={() => onResetDocumentForm()}>Start new document</button>}
            <button type="button" onClick={() => goToTab("agent")} disabled={!canRunAgent && selectedDocumentId === ""} >
              {canRunAgent ? "Run agent" : "View agents"}
            </button>
          </div>
        </form>
      </section>

      <section className="panel stack full-width chunk-inspector-panel">
        <div className="row-head">
          <div>
            <p className="eyebrow">Retrieval inspector</p>
            <h3>{selectedDocumentName || "No document selected"}</h3>
            <p className="muted">These chunks are the evidence units stored for citation and token budgeting.</p>
          </div>
          {documentDetail && <Badge>{documentDetail.embedding_count} embeddings</Badge>}
        </div>
        {documentDetail ? (
          <>
            <div className="metric-grid compact">
              <Metric label="Chunks" value={documentDetail.chunks.length} />
              <Metric label="Total tokens" value={documentDetail.chunks.reduce((sum, chunk) => sum + chunk.token_count, 0)} />
              <Metric label="Language" value={documentDetail.document.language} />
              <Metric label="Version" value={documentDetail.latest_version ? `v${documentDetail.latest_version.version}` : "-"} />
            </div>
            <div className="library-toolbar inspector-toolbar">
              <div className="folder-scope-banner">
                <span>Selected document</span>
                <strong>{selectedDocument?.title ?? "None selected"}</strong>
                <small>{visibleChunks.length} chunks match the current search. Document folders control the larger knowledge library above.</small>
              </div>
              <label>
                Search chunks
                <input
                  value={chunkSearch}
                  onChange={(event) => onChunkSearchChange(event.target.value)}
                  placeholder="Chunk id, index, language, token count, or text"
                />
              </label>
              <p className="permission-note">
                The inspector is bounded to {maxVisibleChunks} matching chunks so long source files stay usable after indexing.
              </p>
            </div>
            <div className="chunk-list chunk-inspector-list bounded-inspector-list">
              {displayedChunks.map((chunk) => (
                <article className="chunk" key={chunk.id}>
                  <div className="row-head">
                    <strong>Chunk {chunk.chunk_index}</strong>
                    <div className="review-actions"><Badge>{chunk.language.toUpperCase()}</Badge><span>{chunk.token_count} tokens</span></div>
                  </div>
                  <p>{chunk.content}</p>
                </article>
              ))}
              {visibleChunks.length === 0 && <EmptyState title="No chunks match this search" detail="Clear search or select another document from a knowledge folder." />}
            </div>
            {hiddenChunkCount > 0 && <p className="permission-note">Showing first {maxVisibleChunks} of {visibleChunks.length} matching chunks. Use search to narrow large files before inspecting evidence.</p>}
          </>
        ) : <EmptyState title="No document selected" detail="Select a document to inspect indexed chunks and embeddings." />}
      </section>
    </div>
  );
}

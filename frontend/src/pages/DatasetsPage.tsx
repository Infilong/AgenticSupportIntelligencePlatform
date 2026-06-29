import { FormEvent, ReactNode, SetStateAction } from "react";
import { Badge, EmptyState } from "../app/shared/Primitives";

type Language = "en" | "ja" | "zh";

type ResourceType = "knowledge_document" | "dataset" | "evaluation_run" | "agent_config";

type Dataset = {
  id: string;
  name: string;
  description: string | null;
  folder_id: string | null;
  created_at: string;
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

type Message = {
  id: string;
  role: string;
  language: string;
  content: string;
  created_at: string;
};

type Label = {
  id: string;
  label_type: string;
  value: string;
  source: string;
  created_at: string;
};

type ConversationExample = {
  id: string;
  external_id: string | null;
  language: string;
  status: string;
  messages: Message[];
  labels: Label[];
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

type ActionGuideRenderer = (props: {
  title: string;
  detail: string;
  action: string;
  onAction: () => void;
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

type LabelDrafts = Record<string, { label_type: string; value: string }>;

type MatchesSearch = (query: string, ...values: Array<string | null | undefined>) => boolean;
type FolderLabel = (resourceType: ResourceType, folderId: string | null) => string;
type ResourceItemCount = (resourceType: ResourceType, folderId: string) => number;
type SetPage = (updater: number | ((current: number) => number)) => void;

type DatasetsPageProps = {
  datasetName: string;
  onDatasetNameChange: (value: string) => void;
  datasetFolders: ResourceFolder[];
  datasetFolderId: string;
  onDatasetFolderIdChange: (value: string) => void;
  selectedDataFolderId: string;
  selectedFolderLabel: string;
  selectedFolderDatasetCount: number;
  onSelectDataFolder: (folderId: string) => void;
  dataFolderName: string;
  onDataFolderNameChange: (value: string) => void;
  datasetSearch: string;
  onDatasetSearchChange: (value: string) => void;
  datasetContent: string;
  onDatasetContentChange: (value: string) => void;
  examples: ConversationExample[];
  exampleSearch: string;
  onExampleSearchChange: (value: string) => void;
  datasetPage: number;
  datasetTotal: number;
  datasetHasNext: boolean;
  onDatasetPageChange: SetPage;
  setDatasetSearch: (value: string) => void;
  setExampleSearch: (value: string) => void;
  datasets: Dataset[];
  selectedDatasetId: string;
  onSelectDataset: (datasetId: string) => Promise<void> | void;
  onLoadExamples: (datasetId: string) => Promise<void> | void;

  canWriteData: boolean;
  canManageResourceFolders: boolean;
  canManageResources: boolean;
  loading: boolean;
  onImportDataset: (event: FormEvent) => Promise<void>;
  onMoveDatasetFolder: (datasetId: string, folderId: string) => Promise<void>;
  onDeleteDataset: (datasetId: string) => Promise<void>;
  matchesSearch: MatchesSearch;
  resourceItemCount: ResourceItemCount;
  folderLabel: FolderLabel;
  onGoToTab: (tab: "documents") => void;
  labelDrafts: LabelDrafts;
  onSetLabelDrafts: React.Dispatch<SetStateAction<LabelDrafts>>;
  onSaveLabel: (exampleId: string) => Promise<void>;
  formatDate: (value: string) => string;
  goToTab: (tab: "documents") => void;
  maxVisibleResources: number;
  maxVisibleExamples: number;
  onResetDatasetState: () => void;
  onRefreshDatasets?: () => void;
  resourceFolderPanel: ResourceFolderPanelRenderer;
  actionGuide: ActionGuideRenderer;
  folderPicker: FolderPickerRenderer;
};

export function DatasetsPage({
  datasetName,
  onDatasetNameChange,
  datasetFolders,
  datasetFolderId,
  onDatasetFolderIdChange,
  selectedDataFolderId,
  selectedFolderLabel,
  selectedFolderDatasetCount,
  onSelectDataFolder,
  dataFolderName,
  onDataFolderNameChange,
  datasetSearch,
  onDatasetSearchChange,
  datasetContent,
  onDatasetContentChange,
  examples,
  exampleSearch,
  onExampleSearchChange,
  datasetPage,
  datasetTotal,
  datasetHasNext,
  onDatasetPageChange,
  datasets,
  selectedDatasetId,
  onSelectDataset,
  onLoadExamples,
  onImportDataset,
  canWriteData,
  canManageResources,
  canManageResourceFolders,
  loading,
  onMoveDatasetFolder,
  onDeleteDataset,
  matchesSearch,
  folderLabel,
  onGoToTab,
  labelDrafts,
  onSetLabelDrafts,
  onSaveLabel,
  formatDate,
  resourceFolderPanel,
  actionGuide,
  folderPicker,
  setDatasetSearch,
  setExampleSearch,
  maxVisibleResources,
  maxVisibleExamples,
}: DatasetsPageProps) {
  const selectedDataset = datasets.find((dataset) => dataset.id === selectedDatasetId) ?? null;
  const datasetPageStart = datasetPage * maxVisibleResources + (datasets.length ? 1 : 0);
  const datasetPageEnd = datasetPage * maxVisibleResources + datasets.length;
  const canGoToPreviousDatasetPage = datasetPage > 0;
  const canGoToNextDatasetPage = datasetHasNext;
  const visibleExamples = examples.filter((example) =>
    matchesSearch(
      exampleSearch,
      example.external_id,
      example.id,
      example.language,
      example.status,
      ...example.messages.map((message) => `${message.role} ${message.content}`),
      ...example.labels.map((label) => `${label.label_type} ${label.value}`),
    ),
  );
  const displayedExamples = visibleExamples.slice(0, maxVisibleExamples);
  const hiddenExampleCount = Math.max(visibleExamples.length - displayedExamples.length, 0);

  return (
    <div className="grid data-workbench-grid">
      {actionGuide({
        title: "Data powers evaluation and routing",
        detail: "Import real conversation examples in English, Japanese, and Chinese. Labels make the data useful for evaluation, routing, and safety checks.",
        action: "Next after import: upload knowledge documents",
        onAction: () => onGoToTab("documents"),
      })}
      {resourceFolderPanel({
        resourceType: "dataset",
        title: "Dataset folders",
        detail: "Keep imports grouped by product, client, language, or test purpose as the workspace grows.",
        selectedFolderId: selectedDataFolderId,
        onSelectFolder: onSelectDataFolder,
        folderName: dataFolderName,
        onFolderNameChange: onDataFolderNameChange,
      })}
      <form className="panel stack" onSubmit={onImportDataset}>
        <h3>Import multilingual data</h3>
        <label>Dataset name<input value={datasetName} onChange={(event) => onDatasetNameChange(event.target.value)} /></label>
        {folderPicker({
          label: "Import target folder",
          value: datasetFolderId,
          folders: datasetFolders,
          onChange: onDatasetFolderIdChange,
          disabled: loading,
          resourceLabel: "dataset",
        })}
        <label>JSONL content<textarea rows={14} value={datasetContent} onChange={(event) => onDatasetContentChange(event.target.value)} /></label>
        <button type="submit" className="primary" disabled={!canWriteData || loading}>Import JSONL</button>
      </form>
      <section className="panel stack dataset-library-panel">
        <div className="row-head">
          <div>
            <h3>Datasets</h3>
            <p className="muted">{selectedDataset ? `Selected: ${selectedDataset.name}` : "Select a dataset to inspect examples."}</p>
          </div>
          <Badge>{datasets.length} of {datasetTotal} shown</Badge>
        </div>
        <div className="library-toolbar">
          <div className="folder-scope-banner">
            <span>Current folder</span>
            <strong>{selectedFolderLabel}</strong>
            <small>{datasets.length ? `${datasetPageStart}-${datasetPageEnd}` : "0"} shown from {datasetTotal} matching this view.</small>
          </div>
          <div className="folder-scope-banner">
            <span>Import target</span>
            <strong>{folderLabel("dataset", datasetFolderId || null)}</strong>
            <small>New JSONL imports are saved into this folder so the dataset list stays organized as it grows.</small>
          </div>
          <label>
            Search current folder
            <input
              value={datasetSearch}
              onChange={(event) => {
                onDatasetPageChange(0);
                setDatasetSearch(event.target.value);
              }}
              placeholder="Dataset name, folder, or id"
            />
          </label>
          <p className="permission-note">
            Role-aware controls: data writers can import, folder managers can organize, and resource cleanup requires owner permission.
          </p>
        </div>
        <div className="resource-list">
          {datasets.map((dataset) => (
            <article key={dataset.id} className={`resource-row ${selectedDatasetId === dataset.id ? "selected-list-item" : ""}`}>
              <button type="button" className="resource-main-button" onClick={() => {
                onSelectDataset(dataset.id);
                void onLoadExamples(dataset.id);
              }}>
                <strong>{dataset.name}</strong>
                <span>{formatDate(dataset.created_at)}</span>
              </button>
              <div className="resource-meta">
                <Badge>{folderLabel("dataset", dataset.folder_id)}</Badge>
              </div>
              <div className="resource-actions">
                {folderPicker({
                  label: `Move ${dataset.name}`,
                  value: dataset.folder_id ?? "",
                  folders: datasetFolders,
                  onChange: (folderId) => void onMoveDatasetFolder(dataset.id, folderId),
                  disabled: !canManageResourceFolders || loading,
                  resourceLabel: "dataset",
                  compact: true,
                })}
                <button type="button" className="danger-button" onClick={() => void onDeleteDataset(dataset.id)} disabled={!canManageResources || loading}>Delete</button>
              </div>
            </article>
          ))}
        </div>
        {datasets.length === 0 && (
          <EmptyState
            title="No datasets match this view"
            detail={datasetTotal === 0 && selectedFolderDatasetCount === 0 ? "Import data here or switch folders." : "Clear search, move to the previous page, or try another folder."}
          />
        )}
        <div className="pagination-bar">
          <button type="button" onClick={() => onDatasetPageChange((page) => Math.max(page - 1, 0))} disabled={!canGoToPreviousDatasetPage || loading}>Previous</button>
          <span>Page {datasetPage + 1} · {datasets.length ? `${datasetPageStart}-${datasetPageEnd}` : "0"} of {datasetTotal}</span>
          <button type="button" onClick={() => onDatasetPageChange((page) => page + 1)} disabled={!canGoToNextDatasetPage || loading}>Next</button>
        </div>
        <p className="permission-note">Dataset history is loaded from the backend by folder, search, offset, and limit so large import libraries stay navigable without loading every dataset into the browser.</p>
      </section>
      <section className="panel stack full-width inspector-panel">
        <div className="row-head">
          <div>
            <h3>Examples</h3>
            <p className="muted">Inspect and label the selected dataset without letting large imports stretch the page.</p>
          </div>
          <Badge>{displayedExamples.length}/{examples.length} loaded</Badge>
        </div>
        <div className="library-toolbar inspector-toolbar">
          <div className="folder-scope-banner">
            <span>Selected dataset</span>
            <strong>{selectedDataset?.name ?? "None selected"}</strong>
            <small>{visibleExamples.length} examples match the current search. Use dataset folders to switch large import groups.</small>
          </div>
          <label>
            Search loaded examples
            <input
              value={exampleSearch}
              onChange={(event) => setExampleSearch(event.target.value)}
              placeholder="External id, language, message, or label"
            />
          </label>
          <p className="permission-note">
            Large datasets stay folder-scoped above; this inspector shows the first {maxVisibleExamples} matching examples to keep labeling usable.
          </p>
        </div>
        <div className="example-list bounded-inspector-list">
          {displayedExamples.map((example) => (
            <article key={example.id} className="example-row">
              <div className="row-head"><strong>{example.external_id ?? example.id}</strong><Badge>{example.language}</Badge></div>
              {example.messages.map((message) => <p key={message.id} className="message"><b>{message.role}</b>: {message.content}</p>)}
              <div className="label-list">{example.labels.map((label) => <Badge key={label.id} tone="good">{label.label_type}: {label.value}</Badge>)}</div>
              <div className="inline-form">
                <select
                  value={labelDrafts[example.id]?.label_type ?? "intent"}
                  onChange={(event) =>
                    onSetLabelDrafts((current) => ({
                      ...current,
                      [example.id]: { label_type: event.target.value, value: current[example.id]?.value ?? "" },
                    }))
                  }
                >
                  <option value="intent">intent</option><option value="sentiment">sentiment</option><option value="product_area">product_area</option><option value="safety_risk">safety_risk</option><option value="escalation_needed">escalation_needed</option>
                </select>
                <input
                  placeholder="label value"
                  value={labelDrafts[example.id]?.value ?? ""}
                  onChange={(event) =>
                    onSetLabelDrafts((current) => ({ ...current, [example.id]: { label_type: current[example.id]?.label_type ?? "intent", value: event.target.value } }))
                  }
                />
                <button type="button" onClick={() => void onSaveLabel(example.id)}>Save label</button>
              </div>
            </article>
          ))}
          {examples.length === 0 && <EmptyState title="No examples loaded" detail="Select a dataset to inspect messages and labels." />}
          {examples.length > 0 && visibleExamples.length === 0 && <EmptyState title="No examples match this search" detail="Clear search or select another dataset folder." />}
        </div>
        {hiddenExampleCount > 0 && <p className="permission-note">Showing first {maxVisibleExamples} of {visibleExamples.length} matching examples. Narrow the search before editing labels in very large imports.</p>}
      </section>
    </div>
  );
}

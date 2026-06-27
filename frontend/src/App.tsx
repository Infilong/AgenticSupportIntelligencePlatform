import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";

type Language = "en" | "ja" | "zh";
type Mode = "direct_llm" | "vector_rag" | "system_v1";
type Tab = "overview" | "datasets" | "documents" | "agent" | "trace" | "reviews" | "evaluations" | "costs";

type Workspace = {
  id: string;
  name: string;
  created_by_user_id: string;
  created_at: string;
};

type Dataset = {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
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

type KnowledgeDocument = {
  id: string;
  title: string;
  language: Language;
  status: string;
  error_message: string | null;
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

type DocumentDetail = {
  document: KnowledgeDocument;
  chunks: DocumentChunk[];
  embedding_count: number;
};

type Agent = {
  id: string;
  name: string;
  active: boolean;
  token_budget: number;
  created_at: string;
};

type GraphRun = {
  id: string;
  agent_config_id: string;
  input_message: string;
  language: string | null;
  status: string;
  route_decision: string | null;
  final_answer: string | null;
  created_at: string;
  completed_at: string | null;
};

type ToolCall = {
  id: string;
  tool_name: string;
  input_json: string;
  output_json: string;
  status: string;
  latency_ms: number;
  created_at: string;
};

type GraphStep = {
  id: string;
  step_name: string;
  input_json: string;
  output_json: string;
  status: string;
  latency_ms: number;
  ai_run_id: string | null;
  token_count: number | null;
  estimated_cost: number | null;
  error_message: string | null;
  retry_count: number;
  created_at: string;
  tool_calls: ToolCall[];
};

type GraphTrace = {
  run: GraphRun;
  steps: GraphStep[];
};

type HumanReview = {
  id: string;
  graph_run_id: string;
  reviewer_id: string | null;
  reason: string;
  proposed_answer: string | null;
  reviewer_decision: string;
  edited_answer: string | null;
  comments: string | null;
  created_at: string;
  resolved_at: string | null;
};

type EvaluationRun = {
  id: string;
  name: string;
  modes_json: string;
  status: string;
  total_cases: number;
  created_at: string;
  completed_at: string | null;
};

type EvaluationResult = {
  id: string;
  evaluation_case_id: string;
  mode: Mode;
  language: Language;
  actual_route: string;
  answer: string | null;
  citations_json: string;
  passed: boolean;
  scores_json: string;
  latency_ms: number;
  prompt_tokens: number;
  estimated_cost: number;
  error_message: string | null;
  created_at: string;
};

type EvaluationMetric = {
  id: string;
  mode: Mode;
  language: Language;
  metric_name: string;
  metric_value: number;
};

type EvaluationDetail = {
  run: EvaluationRun;
  results: EvaluationResult[];
  metrics: EvaluationMetric[];
};

type CostSummary = {
  workspace_id: string;
  total_runs: number;
  total_tokens: number;
  total_estimated_cost: number;
  average_latency_ms: number;
  cache_hit_rate: number;
  by_purpose: Array<{ purpose: string; runs: number; tokens: number; estimated_cost: number }>;
};

type ApiOptions = {
  method?: string;
  token?: string | null;
  body?: unknown;
};

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const tabs: Array<{ id: Tab; label: string }> = [
  { id: "overview", label: "Overview" },
  { id: "datasets", label: "Datasets" },
  { id: "documents", label: "Documents" },
  { id: "agent", label: "Agent" },
  { id: "trace", label: "Trace" },
  { id: "reviews", label: "Reviews" },
  { id: "evaluations", label: "Evaluations" },
  { id: "costs", label: "Costs" },
];

const demoDataset = `{"external_id":"en_refund_001","messages":[{"role":"user","content":"Can I get a refund within 30 days?"}],"labels":{"intent":"refund_request","product_area":"billing"}}
{"external_id":"ja_refund_001","messages":[{"role":"user","content":"30日以内なら返金できますか？"}],"labels":{"intent":"refund_request","product_area":"billing"}}
{"external_id":"zh_privacy_001","messages":[{"role":"user","content":"我要投诉，你们泄露了我的个人信息。"}],"labels":{"intent":"complaint","safety_risk":"high"}}`;

const demoDocument = `Refund Policy
Refunds are available within 30 days after purchase when the account is in good standing. Privacy or security complaints must be escalated to human review.`;

const demoEvaluation = `{"id":"en_refund_001","language":"en","input_message":"Can I get a refund within 30 days?","expected_route":"finalize","must_include":["30 days"]}
{"id":"ja_no_source_001","language":"ja","input_message":"アカウントを完全に削除する方法を教えてください。","expected_route":"human_review","must_not_include":["できます"]}
{"id":"zh_refund_001","language":"zh","input_message":"我可以在30天内申请退款吗？","expected_route":"finalize","must_include":["30天"]}`;

async function apiRequest<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: options.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      ...(options.token ? { Authorization: `Bearer ${options.token}` } : {}),
    },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const detail = payload?.detail;
    const message = typeof detail === "string" ? detail : detail?.message ?? response.statusText;
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

function safeJson(value: string): unknown {
  try {
    return JSON.parse(value);
  } catch {
    return value;
  }
}

function formatCost(value: number | null | undefined) {
  if (!value) return "$0.0000";
  return `$${value.toFixed(4)}`;
}

function formatNumber(value: number | null | undefined) {
  return (value ?? 0).toLocaleString();
}

function formatDate(value: string | null) {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}

function Badge({ tone = "neutral", children }: { tone?: "neutral" | "good" | "warn" | "bad"; children: ReactNode }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function JsonBlock({ value }: { value: unknown }) {
  const text = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  return <pre className="json-block">{text}</pre>;
}

export function App() {
  const [token, setToken] = useState(() => localStorage.getItem("asi_token") ?? "");
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("demo@example.com");
  const [password, setPassword] = useState("strong-password");
  const [displayName, setDisplayName] = useState("Demo User");
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [workspaceName, setWorkspaceName] = useState("Support Intelligence Demo");
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState("");
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [datasetName, setDatasetName] = useState("Demo Support Conversations");
  const [datasetContent, setDatasetContent] = useState(demoDataset);
  const [selectedDatasetId, setSelectedDatasetId] = useState("");
  const [examples, setExamples] = useState<ConversationExample[]>([]);
  const [labelDrafts, setLabelDrafts] = useState<Record<string, { label_type: string; value: string }>>({});

  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [documentTitle, setDocumentTitle] = useState("Refund Policy EN");
  const [documentLanguage, setDocumentLanguage] = useState<Language>("en");
  const [documentContent, setDocumentContent] = useState(demoDocument);
  const [documentDetail, setDocumentDetail] = useState<DocumentDetail | null>(null);

  const [agents, setAgents] = useState<Agent[]>([]);
  const [agentName, setAgentName] = useState("Support Agent");
  const [agentMessage, setAgentMessage] = useState("Can I get a refund within 30 days?");
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const [latestRun, setLatestRun] = useState<GraphRun | null>(null);
  const [trace, setTrace] = useState<GraphTrace | null>(null);
  const [traceRunId, setTraceRunId] = useState("");

  const [reviews, setReviews] = useState<HumanReview[]>([]);
  const [reviewDecision, setReviewDecision] = useState<"approved" | "edited" | "rejected">("approved");
  const [reviewEditedAnswer, setReviewEditedAnswer] = useState("");
  const [reviewComments, setReviewComments] = useState("");

  const [evaluationRuns, setEvaluationRuns] = useState<EvaluationRun[]>([]);
  const [evaluationDetail, setEvaluationDetail] = useState<EvaluationDetail | null>(null);
  const [evaluationName, setEvaluationName] = useState("Smoke Evaluation");
  const [evaluationCases, setEvaluationCases] = useState(demoEvaluation);
  const [evaluationModes, setEvaluationModes] = useState<Mode[]>(["direct_llm", "vector_rag", "system_v1"]);

  const [costSummary, setCostSummary] = useState<CostSummary | null>(null);

  const selectedWorkspace = useMemo(
    () => workspaces.find((workspace) => workspace.id === selectedWorkspaceId),
    [selectedWorkspaceId, workspaces],
  );

  useEffect(() => {
    if (!token) return;
    void loadWorkspaces();
  }, [token]);

  useEffect(() => {
    if (!token || !selectedWorkspaceId) return;
    void refreshWorkspaceData();
  }, [token, selectedWorkspaceId]);

  function setSessionToken(value: string) {
    setToken(value);
    localStorage.setItem("asi_token", value);
  }

  function resetMessages() {
    setNotice("");
    setError("");
  }

  async function runAction(label: string, action: () => Promise<void>) {
    resetMessages();
    setLoading(true);
    try {
      await action();
      setNotice(label);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Unexpected error");
    } finally {
      setLoading(false);
    }
  }

  async function handleAuth(event: FormEvent) {
    event.preventDefault();
    await runAction("Authentication succeeded", async () => {
      if (authMode === "register") {
        await apiRequest("/api/v1/auth/register", {
          method: "POST",
          body: { email, password, display_name: displayName },
        });
      }
      const response = await apiRequest<{ access_token: string }>("/api/v1/auth/login", {
        method: "POST",
        body: { email, password },
      });
      setSessionToken(response.access_token);
    });
  }

  async function loadWorkspaces() {
    const data = await apiRequest<Workspace[]>("/api/v1/workspaces", { token });
    setWorkspaces(data);
    setSelectedWorkspaceId((current) => current || data[0]?.id || "");
  }

  async function createWorkspace(event: FormEvent) {
    event.preventDefault();
    await runAction("Workspace created", async () => {
      const workspace = await apiRequest<Workspace>("/api/v1/workspaces", {
        method: "POST",
        token,
        body: { name: workspaceName },
      });
      await loadWorkspaces();
      setSelectedWorkspaceId(workspace.id);
    });
  }

  async function refreshWorkspaceData() {
    await Promise.all([
      loadDatasets(),
      loadDocuments(),
      loadAgents(),
      loadReviews(),
      loadEvaluations(),
      loadCosts(),
    ]);
  }

  function workspacePath(path: string) {
    return `/api/v1/workspaces/${selectedWorkspaceId}${path}`;
  }

  async function loadDatasets() {
    if (!selectedWorkspaceId) return;
    const data = await apiRequest<Dataset[]>(workspacePath("/datasets"), { token });
    setDatasets(data);
    setSelectedDatasetId((current) => current || data[0]?.id || "");
  }

  async function importDataset(event: FormEvent) {
    event.preventDefault();
    await runAction("Dataset imported", async () => {
      const response = await apiRequest<{ dataset: Dataset }>(workspacePath("/datasets/import"), {
        method: "POST",
        token,
        body: {
          dataset_name: datasetName,
          description: "Imported from the browser demo UI.",
          source_type: "jsonl",
          content: datasetContent,
        },
      });
      await loadDatasets();
      setSelectedDatasetId(response.dataset.id);
      await loadExamples(response.dataset.id);
    });
  }

  async function loadExamples(datasetId = selectedDatasetId) {
    if (!datasetId) return;
    const data = await apiRequest<ConversationExample[]>(workspacePath(`/datasets/${datasetId}/examples`), {
      token,
    });
    setExamples(data);
  }

  async function saveLabel(exampleId: string) {
    const draft = labelDrafts[exampleId] ?? { label_type: "intent", value: "refund_request" };
    await runAction("Label saved", async () => {
      await apiRequest(workspacePath(`/examples/${exampleId}/labels`), {
        method: "POST",
        token,
        body: draft,
      });
      await loadExamples();
    });
  }

  async function loadDocuments() {
    if (!selectedWorkspaceId) return;
    const data = await apiRequest<KnowledgeDocument[]>(workspacePath("/knowledge-documents"), { token });
    setDocuments(data);
  }

  async function uploadDocument(event: FormEvent) {
    event.preventDefault();
    await runAction("Document indexed", async () => {
      const response = await apiRequest<{ document: KnowledgeDocument }>(workspacePath("/knowledge-documents"), {
        method: "POST",
        token,
        body: {
          title: documentTitle,
          content_type: "text/plain",
          language: documentLanguage,
          content: documentContent,
        },
      });
      await loadDocuments();
      await loadDocumentDetail(response.document.id);
    });
  }

  async function loadDocumentDetail(documentId: string) {
    const detail = await apiRequest<DocumentDetail>(workspacePath(`/knowledge-documents/${documentId}`), {
      token,
    });
    setDocumentDetail(detail);
  }

  async function loadAgents() {
    if (!selectedWorkspaceId) return;
    const data = await apiRequest<Agent[]>(workspacePath("/agents"), { token });
    setAgents(data);
    setSelectedAgentId((current) => current || data[0]?.id || "");
  }

  async function createAgent(event: FormEvent) {
    event.preventDefault();
    await runAction("Agent created", async () => {
      const agent = await apiRequest<Agent>(workspacePath("/agents"), {
        method: "POST",
        token,
        body: { name: agentName, token_budget: 4000 },
      });
      await loadAgents();
      setSelectedAgentId(agent.id);
    });
  }

  async function runAgent(event: FormEvent) {
    event.preventDefault();
    if (!selectedAgentId) {
      setError("Create or select an agent first.");
      return;
    }
    await runAction("Agent run completed", async () => {
      const run = await apiRequest<GraphRun>(workspacePath(`/agents/${selectedAgentId}/runs`), {
        method: "POST",
        token,
        body: { input_message: agentMessage },
      });
      setLatestRun(run);
      setTraceRunId(run.id);
      await loadTrace(run.id);
      await loadReviews();
      await loadCosts();
      setActiveTab("trace");
    });
  }

  async function loadTrace(runId = traceRunId) {
    if (!runId) return;
    const data = await apiRequest<GraphTrace>(workspacePath(`/agent-runs/${runId}/trace`), { token });
    setTrace(data);
    setTraceRunId(runId);
  }

  async function loadReviews() {
    if (!selectedWorkspaceId) return;
    const data = await apiRequest<HumanReview[]>(workspacePath("/human-reviews"), { token });
    setReviews(data);
  }

  async function resolveReview(reviewId: string) {
    await runAction("Review resolved", async () => {
      await apiRequest(workspacePath(`/human-reviews/${reviewId}/resolve`), {
        method: "POST",
        token,
        body: {
          decision: reviewDecision,
          edited_answer: reviewDecision === "edited" ? reviewEditedAnswer : null,
          comments: reviewComments || null,
        },
      });
      setReviewEditedAnswer("");
      setReviewComments("");
      await loadReviews();
    });
  }

  async function loadEvaluations() {
    if (!selectedWorkspaceId) return;
    const data = await apiRequest<EvaluationRun[]>(workspacePath("/evaluations"), { token });
    setEvaluationRuns(data);
  }

  async function runEvaluation(event: FormEvent) {
    event.preventDefault();
    await runAction("Evaluation completed", async () => {
      const detail = await apiRequest<EvaluationDetail>(workspacePath("/evaluations"), {
        method: "POST",
        token,
        body: {
          name: evaluationName,
          jsonl_cases: evaluationCases,
          modes: evaluationModes,
          agent_id: selectedAgentId || null,
        },
      });
      setEvaluationDetail(detail);
      await loadEvaluations();
      await loadCosts();
    });
  }

  async function loadEvaluationDetail(runId: string) {
    const detail = await apiRequest<EvaluationDetail>(workspacePath(`/evaluations/${runId}`), { token });
    setEvaluationDetail(detail);
  }

  async function loadCosts() {
    if (!selectedWorkspaceId) return;
    const data = await apiRequest<CostSummary>(workspacePath("/costs/summary"), { token });
    setCostSummary(data);
  }

  function toggleMode(mode: Mode) {
    setEvaluationModes((current) =>
      current.includes(mode) ? current.filter((item) => item !== mode) : [...current, mode],
    );
  }

  if (!token) {
    return (
      <main className="auth-page">
        <section className="auth-copy">
          <p className="eyebrow">AI support intelligence</p>
          <h1>Multilingual Agentic Support Intelligence Platform</h1>
          <p>
            Local-first internal tool for multilingual datasets, RAG, LangGraph traces, human review,
            evaluation, and token-cost observability.
          </p>
        </section>
        <form className="auth-panel" onSubmit={handleAuth}>
          <div className="segmented">
            <button type="button" className={authMode === "login" ? "selected" : ""} onClick={() => setAuthMode("login")}>Login</button>
            <button type="button" className={authMode === "register" ? "selected" : ""} onClick={() => setAuthMode("register")}>Register</button>
          </div>
          {authMode === "register" && (
            <label>
              Display name
              <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} />
            </label>
          )}
          <label>
            Email
            <input value={email} onChange={(event) => setEmail(event.target.value)} />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
          </label>
          <button className="primary" disabled={loading}>{authMode === "login" ? "Login" : "Register and login"}</button>
          <Status notice={notice} error={error} />
        </form>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">Workspace</p>
          <h1>Support Intelligence</h1>
        </div>
        <label>
          Active workspace
          <select value={selectedWorkspaceId} onChange={(event) => setSelectedWorkspaceId(event.target.value)}>
            <option value="">Select workspace</option>
            {workspaces.map((workspace) => (
              <option key={workspace.id} value={workspace.id}>{workspace.name}</option>
            ))}
          </select>
        </label>
        <form className="stack" onSubmit={createWorkspace}>
          <input value={workspaceName} onChange={(event) => setWorkspaceName(event.target.value)} />
          <button>Create workspace</button>
        </form>
        <nav className="tab-nav">
          {tabs.map((tab) => (
            <button key={tab.id} className={activeTab === tab.id ? "active" : ""} onClick={() => setActiveTab(tab.id)}>{tab.label}</button>
          ))}
        </nav>
        <button className="secondary" onClick={() => { localStorage.removeItem("asi_token"); setToken(""); }}>Logout</button>
      </aside>

      <section className="workspace-main">
        <header className="topbar">
          <div>
            <p className="eyebrow">{selectedWorkspace ? selectedWorkspace.name : "No workspace selected"}</p>
            <h2>{tabs.find((tab) => tab.id === activeTab)?.label}</h2>
          </div>
          <button className="secondary" disabled={!selectedWorkspaceId || loading} onClick={() => void runAction("Workspace data refreshed", refreshWorkspaceData)}>Refresh</button>
        </header>
        <Status notice={notice} error={error} />
        {!selectedWorkspaceId ? <EmptyState title="Create or select a workspace" detail="Workspace isolation is enforced by every backend route." /> : renderActiveTab()}
      </section>
    </main>
  );

  function renderActiveTab() {
    switch (activeTab) {
      case "datasets":
        return <DatasetsPanel />;
      case "documents":
        return <DocumentsPanel />;
      case "agent":
        return <AgentPanel />;
      case "trace":
        return <TracePanel />;
      case "reviews":
        return <ReviewsPanel />;
      case "evaluations":
        return <EvaluationsPanel />;
      case "costs":
        return <CostsPanel />;
      default:
        return <OverviewPanel />;
    }
  }

  function OverviewPanel() {
    return (
      <div className="grid two">
        <section className="panel">
          <h3>Demo path</h3>
          <ol className="ordered">
            <li>Import multilingual conversations.</li>
            <li>Upload knowledge documents.</li>
            <li>Create an agent and run a support request.</li>
            <li>Inspect LangGraph trace, token fields, citations, and routing.</li>
            <li>Resolve human reviews and run per-language evaluations.</li>
          </ol>
        </section>
        <section className="panel metric-grid">
          <Metric label="Datasets" value={datasets.length} />
          <Metric label="Documents" value={documents.length} />
          <Metric label="Agents" value={agents.length} />
          <Metric label="Reviews" value={reviews.length} />
          <Metric label="AI runs" value={costSummary?.total_runs ?? 0} />
          <Metric label="Estimated cost" value={formatCost(costSummary?.total_estimated_cost)} />
        </section>
      </div>
    );
  }

  function DatasetsPanel() {
    return (
      <div className="grid two-wide-left">
        <form className="panel stack" onSubmit={importDataset}>
          <h3>Import conversations</h3>
          <label>Dataset name<input value={datasetName} onChange={(event) => setDatasetName(event.target.value)} /></label>
          <label>JSONL content<textarea rows={14} value={datasetContent} onChange={(event) => setDatasetContent(event.target.value)} /></label>
          <button className="primary" disabled={loading}>Import JSONL</button>
        </form>
        <section className="panel stack">
          <h3>Datasets</h3>
          {datasets.map((dataset) => (
            <button key={dataset.id} className="list-button" onClick={() => { setSelectedDatasetId(dataset.id); void loadExamples(dataset.id); }}>
              <strong>{dataset.name}</strong><span>{formatDate(dataset.created_at)}</span>
            </button>
          ))}
          {datasets.length === 0 && <EmptyState title="No datasets" detail="Import JSONL examples to begin curation." />}
        </section>
        <section className="panel full-width">
          <h3>Examples</h3>
          <div className="example-list">
            {examples.map((example) => (
              <article key={example.id} className="example-row">
                <div className="row-head"><strong>{example.external_id ?? example.id}</strong><Badge>{example.language}</Badge></div>
                {example.messages.map((message) => <p key={message.id} className="message"><b>{message.role}</b>: {message.content}</p>)}
                <div className="label-list">{example.labels.map((label) => <Badge key={label.id} tone="good">{label.label_type}: {label.value}</Badge>)}</div>
                <div className="inline-form">
                  <select value={labelDrafts[example.id]?.label_type ?? "intent"} onChange={(event) => setLabelDrafts((current) => ({ ...current, [example.id]: { label_type: event.target.value, value: current[example.id]?.value ?? "" } }))}>
                    <option value="intent">intent</option><option value="sentiment">sentiment</option><option value="product_area">product_area</option><option value="safety_risk">safety_risk</option><option value="escalation_needed">escalation_needed</option>
                  </select>
                  <input placeholder="label value" value={labelDrafts[example.id]?.value ?? ""} onChange={(event) => setLabelDrafts((current) => ({ ...current, [example.id]: { label_type: current[example.id]?.label_type ?? "intent", value: event.target.value } }))} />
                  <button onClick={() => void saveLabel(example.id)}>Save label</button>
                </div>
              </article>
            ))}
            {examples.length === 0 && <EmptyState title="No examples loaded" detail="Select a dataset to inspect messages and labels." />}
          </div>
        </section>
      </div>
    );
  }

  function DocumentsPanel() {
    return (
      <div className="grid two-wide-left">
        <form className="panel stack" onSubmit={uploadDocument}>
          <h3>Upload knowledge</h3>
          <label>Title<input value={documentTitle} onChange={(event) => setDocumentTitle(event.target.value)} /></label>
          <label>Language<select value={documentLanguage} onChange={(event) => setDocumentLanguage(event.target.value as Language)}><option value="en">English</option><option value="ja">Japanese</option><option value="zh">Chinese</option></select></label>
          <label>Content<textarea rows={14} value={documentContent} onChange={(event) => setDocumentContent(event.target.value)} /></label>
          <button className="primary" disabled={loading}>Upload and index</button>
        </form>
        <section className="panel stack">
          <h3>Documents</h3>
          {documents.map((document) => (
            <button key={document.id} className="list-button" onClick={() => void loadDocumentDetail(document.id)}>
              <strong>{document.title}</strong><span>{document.language} · {document.status}</span>
            </button>
          ))}
          {documents.length === 0 && <EmptyState title="No documents" detail="Upload policy or FAQ text to build retrieval evidence." />}
        </section>
        <section className="panel full-width">
          <h3>Document chunks</h3>
          {documentDetail ? <div className="chunk-list">{documentDetail.chunks.map((chunk) => <article className="chunk" key={chunk.id}><div className="row-head"><strong>Chunk {chunk.chunk_index}</strong><span>{chunk.token_count} tokens</span></div><p>{chunk.content}</p></article>)}</div> : <EmptyState title="No document selected" detail="Select a document to inspect indexed chunks." />}
        </section>
      </div>
    );
  }

  function AgentPanel() {
    return (
      <div className="grid two">
        <section className="panel stack">
          <h3>Agents</h3>
          <form className="inline-form" onSubmit={createAgent}>
            <input value={agentName} onChange={(event) => setAgentName(event.target.value)} />
            <button>Create</button>
          </form>
          <select value={selectedAgentId} onChange={(event) => setSelectedAgentId(event.target.value)}>
            <option value="">Select agent</option>
            {agents.map((agent) => <option key={agent.id} value={agent.id}>{agent.name} · budget {agent.token_budget}</option>)}
          </select>
        </section>
        <form className="panel stack" onSubmit={runAgent}>
          <h3>Run support workflow</h3>
          <textarea rows={8} value={agentMessage} onChange={(event) => setAgentMessage(event.target.value)} />
          <button className="primary" disabled={loading || !selectedAgentId}>Run LangGraph agent</button>
        </form>
        <section className="panel full-width">
          <h3>Latest run</h3>
          {latestRun ? <RunSummary run={latestRun} /> : <EmptyState title="No run yet" detail="Run the support workflow to inspect trace and routing." />}
        </section>
      </div>
    );
  }

  function TracePanel() {
    return (
      <div className="stack">
        <section className="panel inline-form">
          <input placeholder="Graph run id" value={traceRunId} onChange={(event) => setTraceRunId(event.target.value)} />
          <button onClick={() => void runAction("Trace loaded", () => loadTrace())}>Load trace</button>
        </section>
        {trace ? <TraceViewer trace={trace} /> : <EmptyState title="No trace loaded" detail="Run an agent or paste a graph run ID." />}
      </div>
    );
  }

  function ReviewsPanel() {
    return (
      <section className="panel stack">
        <div className="row-head"><h3>Human reviews</h3><button onClick={() => void runAction("Reviews refreshed", loadReviews)}>Refresh reviews</button></div>
        <div className="inline-form">
          <select value={reviewDecision} onChange={(event) => setReviewDecision(event.target.value as "approved" | "edited" | "rejected")}><option value="approved">approved</option><option value="edited">edited</option><option value="rejected">rejected</option></select>
          <input placeholder="edited answer" value={reviewEditedAnswer} onChange={(event) => setReviewEditedAnswer(event.target.value)} />
          <input placeholder="comments" value={reviewComments} onChange={(event) => setReviewComments(event.target.value)} />
        </div>
        {reviews.map((review) => <article className="review-row" key={review.id}><div className="row-head"><strong>{review.reason}</strong><Badge tone={review.reviewer_decision === "pending" ? "warn" : "good"}>{review.reviewer_decision}</Badge></div><p>{review.proposed_answer ?? "No proposed answer"}</p><small>Graph run {review.graph_run_id}</small>{review.reviewer_decision === "pending" && <button onClick={() => void resolveReview(review.id)}>Resolve selected way</button>}</article>)}
        {reviews.length === 0 && <EmptyState title="No reviews" detail="Low-confidence or risky agent runs will appear here." />}
      </section>
    );
  }

  function EvaluationsPanel() {
    return (
      <div className="grid two-wide-left">
        <form className="panel stack" onSubmit={runEvaluation}>
          <h3>Run evaluation</h3>
          <label>Name<input value={evaluationName} onChange={(event) => setEvaluationName(event.target.value)} /></label>
          <div className="check-row">{(["direct_llm", "vector_rag", "system_v1"] as Mode[]).map((mode) => <label key={mode}><input type="checkbox" checked={evaluationModes.includes(mode)} onChange={() => toggleMode(mode)} />{mode}</label>)}</div>
          <label>JSONL cases<textarea rows={14} value={evaluationCases} onChange={(event) => setEvaluationCases(event.target.value)} /></label>
          <button className="primary" disabled={loading || evaluationModes.length === 0}>Run evaluation</button>
        </form>
        <section className="panel stack">
          <h3>Runs</h3>
          {evaluationRuns.map((run) => <button key={run.id} className="list-button" onClick={() => void loadEvaluationDetail(run.id)}><strong>{run.name}</strong><span>{run.status} · {run.total_cases} cases</span></button>)}
          {evaluationRuns.length === 0 && <EmptyState title="No evaluations" detail="Run JSONL cases to compare baselines and system v1." />}
        </section>
        <section className="panel full-width">
          <h3>Metrics by mode and language</h3>
          {evaluationDetail ? <EvaluationDashboard detail={evaluationDetail} /> : <EmptyState title="No evaluation selected" detail="Metrics will show language-specific quality and cost signals." />}
        </section>
      </div>
    );
  }

  function CostsPanel() {
    return (
      <section className="panel stack">
        <div className="row-head"><h3>Token and cost summary</h3><button onClick={() => void runAction("Costs refreshed", loadCosts)}>Refresh costs</button></div>
        {costSummary ? <><div className="metric-grid"><Metric label="AI runs" value={costSummary.total_runs} /><Metric label="Tokens" value={formatNumber(costSummary.total_tokens)} /><Metric label="Estimated cost" value={formatCost(costSummary.total_estimated_cost)} /><Metric label="Avg latency" value={`${costSummary.average_latency_ms.toFixed(1)} ms`} /><Metric label="Cache hit rate" value={`${(costSummary.cache_hit_rate * 100).toFixed(1)}%`} /></div><table><thead><tr><th>Purpose</th><th>Runs</th><th>Tokens</th><th>Cost</th></tr></thead><tbody>{costSummary.by_purpose.map((item) => <tr key={item.purpose}><td>{item.purpose}</td><td>{item.runs}</td><td>{formatNumber(item.tokens)}</td><td>{formatCost(item.estimated_cost)}</td></tr>)}</tbody></table></> : <EmptyState title="No cost data" detail="Model calls create AI run ledger entries with token and latency estimates." />}
      </section>
    );
  }
}

function Status({ notice, error }: { notice: string; error: string }) {
  return <>{notice && <div className="status success">{notice}</div>}{error && <div className="status error">{error}</div>}</>;
}

function EmptyState({ title, detail }: { title: string; detail: string }) {
  return <div className="empty"><strong>{title}</strong><span>{detail}</span></div>;
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return <div className="metric"><span>{label}</span><strong>{value}</strong></div>;
}

function RunSummary({ run }: { run: GraphRun }) {
  return <div className="run-summary"><div className="metric-grid"><Metric label="Status" value={run.status} /><Metric label="Language" value={run.language ?? "-"} /><Metric label="Route" value={run.route_decision ?? "-"} /><Metric label="Completed" value={formatDate(run.completed_at)} /></div><p className="answer">{run.final_answer ?? "No final answer. The run may require human review."}</p><small>{run.id}</small></div>;
}

function TraceViewer({ trace }: { trace: GraphTrace }) {
  const totalTokens = trace.steps.reduce((sum, step) => sum + (step.token_count ?? 0), 0);
  const totalCost = trace.steps.reduce((sum, step) => sum + (step.estimated_cost ?? 0), 0);
  return <section className="panel stack"><RunSummary run={trace.run} /><div className="metric-grid"><Metric label="Steps" value={trace.steps.length} /><Metric label="Trace tokens" value={totalTokens} /><Metric label="Trace cost" value={formatCost(totalCost)} /></div><div className="timeline">{trace.steps.map((step, index) => <article className="trace-step" key={step.id}><div className="row-head"><div><small>Step {index + 1}</small><h3>{step.step_name}</h3></div><Badge tone={step.status === "completed" ? "good" : "bad"}>{step.status}</Badge></div><div className="metric-grid compact"><Metric label="Latency" value={`${step.latency_ms} ms`} /><Metric label="Tokens" value={step.token_count ?? 0} /><Metric label="Cost" value={formatCost(step.estimated_cost)} /><Metric label="Retries" value={step.retry_count} /></div>{step.error_message && <div className="status error">{step.error_message}</div>}<details><summary>Input</summary><JsonBlock value={safeJson(step.input_json)} /></details><details open><summary>Output</summary><JsonBlock value={safeJson(step.output_json)} /></details>{step.tool_calls.length > 0 && <details><summary>Tool calls</summary>{step.tool_calls.map((tool) => <div className="tool-call" key={tool.id}><strong>{tool.tool_name}</strong><span>{tool.status} · {tool.latency_ms} ms</span><JsonBlock value={safeJson(tool.output_json)} /></div>)}</details>}</article>)}</div></section>;
}

function EvaluationDashboard({ detail }: { detail: EvaluationDetail }) {
  const metricRows = detail.metrics;
  return <div className="stack"><div className="metric-grid"><Metric label="Run" value={detail.run.name} /><Metric label="Status" value={detail.run.status} /><Metric label="Cases" value={detail.run.total_cases} /><Metric label="Results" value={detail.results.length} /></div><table><thead><tr><th>Mode</th><th>Language</th><th>Metric</th><th>Value</th></tr></thead><tbody>{metricRows.map((metric) => <tr key={metric.id}><td>{metric.mode}</td><td>{metric.language}</td><td>{metric.metric_name}</td><td>{metric.metric_value.toFixed(4)}</td></tr>)}</tbody></table><h3>Case results</h3><div className="result-list">{detail.results.map((result) => <article className="result-row" key={result.id}><div className="row-head"><strong>{result.mode} · {result.language}</strong><Badge tone={result.passed ? "good" : "bad"}>{result.passed ? "passed" : "failed"}</Badge></div><div className="metric-grid compact"><Metric label="Route" value={result.actual_route} /><Metric label="Latency" value={`${result.latency_ms} ms`} /><Metric label="Prompt tokens" value={result.prompt_tokens} /><Metric label="Cost" value={formatCost(result.estimated_cost)} /></div><p>{result.answer ?? "No answer generated"}</p><details><summary>Scores and citations</summary><JsonBlock value={{ scores: safeJson(result.scores_json), citations: safeJson(result.citations_json), error: result.error_message }} /></details></article>)}</div></div>;
}

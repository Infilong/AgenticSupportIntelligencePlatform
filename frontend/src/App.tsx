const readinessItems = [
  "FastAPI backend skeleton",
  "PostgreSQL + pgvector service",
  "Redis service",
  "TypeScript frontend shell",
  "CI, tests, and linting foundation",
];

export function App() {
  return (
    <main className="app-shell">
      <section className="intro-panel" aria-labelledby="page-title">
        <p className="eyebrow">Milestone 1 skeleton</p>
        <h1 id="page-title">Multilingual Agentic Support Intelligence Platform</h1>
        <p className="summary">
          Local-first foundation for a multilingual AI support platform. Product workflows will be
          added milestone by milestone after the backend, data, and verification base is stable.
        </p>
      </section>

      <section className="status-panel" aria-labelledby="status-title">
        <h2 id="status-title">Current foundation</h2>
        <ul>
          {readinessItems.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}

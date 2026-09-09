import { useState } from 'react';
import type { components } from '../../api/schema';
import { RetrievalTrace } from '../knowledge/RetrievalTrace';

type Detail = components['schemas']['EvaluationDetail'];
type Strategy = components['schemas']['EvaluationStrategy'];
const labels: Record<Strategy['name'], string> = { vector: 'Vector', bm25: 'Keyword (BM25)', hybrid: 'Hybrid', vector_rerank: 'Vector + reranker', hybrid_rerank: 'Hybrid + reranker' };

export function EvaluationResults({ workspaceId, record }: { workspaceId: string; record: Detail }) {
  const [selected, setSelected] = useState<Strategy['name']>('vector_rerank');
  const [filter, setFilter] = useState('failed');
  const [language, setLanguage] = useState('all');
  const data = record.snapshot;
  const strategy = data.strategies.find(item => item.name === selected) ?? data.strategies[0];
  const cases = strategy.cases.filter(item => (language === 'all' || item.language === language) && (filter === 'all' || (filter === 'failed' ? item.passed === false : item.passed === null)));
  return <>
    <div className="evaluation-notice"><strong>Historical retrieval · Answer quality unverified</strong><p>Measured on a development corpus, not a held-out set. These results describe the saved experiment, not the current app.</p></div>
    <div className="inbox-panel evaluation-comparison" role="region" aria-label="Retrieval strategy comparison" tabIndex={0}><table><caption>Historical comparison · Top 5 retrieved passages</caption><thead><tr><th>Strategy</th><th>Evidence cases</th><th>Section groups</th><th>Warm p95</th><th>Recorded safety</th><th>Retrieval gate</th></tr></thead><tbody>{data.strategies.map(item => <tr key={item.name} className={strategy.name === item.name ? 'selected-strategy' : ''}><th><button aria-pressed={strategy.name === item.name} onClick={() => setSelected(item.name)}>{labels[item.name]}</button></th><td>{item.scores.all.passed} / {item.scores.all.total}</td><td>{item.scores.all.groups_found} / {item.scores.all.total_groups}</td><td>{item.warm_p95_seconds.toFixed(3)} s</td><td>{item.safety_passed ? 'Passed' : 'Failed'}</td><td>{item.retrieval_gate_passed ? 'Passed' : 'Failed'}</td></tr>)}</tbody></table></div>
    <p className="usage-note">Four routing-only cases are excluded from evidence scores. Warm p95 covers {strategy.measured_requests} recorded requests, one per case.</p>
    <section className="inbox-panel section-padding" aria-labelledby="strategy-detail-heading">
      <h3 id="strategy-detail-heading">{labels[strategy.name]} details</h3>
      <div className="evaluation-languages">{(['en', 'ja', 'zh'] as const).map(lang => <div key={lang}><strong>{({ en: 'English', ja: 'Japanese', zh: 'Chinese' })[lang]}</strong><p>{strategy.scores[lang].passed} / {strategy.scores[lang].total} evidence cases</p><p className="muted">{strategy.scores[lang].groups_found} / {strategy.scores[lang].total_groups} section groups</p></div>)}</div>
      <div className="evaluation-filters"><label>Case outcome <select value={filter} onChange={event => setFilter(event.target.value)}><option value="failed">Failed evidence cases</option><option value="all">All cases</option><option value="excluded">Excluded routing cases</option></select></label><label>Case language <select value={language} onChange={event => setLanguage(event.target.value)}><option value="all">All languages</option><option value="en">English</option><option value="ja">Japanese</option><option value="zh">Chinese</option></select></label></div>
      <p className="muted">{cases.length} matching cases. Open a case to inspect its saved request and current access to its stored trace.</p>
      {!cases.length && <p>No cases match these filters.</p>}
      <ul className="evaluation-cases">{cases.map(item => <li key={`${strategy.name}/${item.id}`}><details><summary>{item.id} · {item.language.toUpperCase()} · {item.passed == null ? 'Excluded from retrieval score' : item.passed ? 'Passed' : 'Failed'}</summary><p>{item.question}</p><p className="muted">{item.groups_found} / {item.total_groups} section groups · {item.elapsed_seconds.toFixed(3)} s</p><RetrievalTrace workspaceId={workspaceId} traceId={item.trace_id} /></details></li>)}</ul>
    </section>
    <details className="evaluation-provenance"><summary>Measurement provenance and limits</summary><p>Registered {new Date(record.registered_at).toLocaleString()}. The original report has no execution timestamp; registration time is not measurement time. Later source changes or document withdrawals do not rewrite this snapshot.</p><p>The retrieval gate requires ≥90% overall and ≥80% per language for both evidence metrics, no recorded leakage, and p95 ≤3 seconds. One warm sample per case is not a production service-level measurement. These five retrieval strategies do not establish the four generation-pipeline comparisons.</p><dl><dt>Report SHA-256</dt><dd>{record.report_sha256}</dd><dt>Measured source commit</dt><dd>{data.source_commit}</dd><dt>Measured source SHA-256 (includes working changes)</dt><dd>{data.source_sha256}</dd><dt>Canonical frozen corpus manifest SHA-256</dt><dd>{data.corpus_sha256}</dd><dt>Scorer</dt><dd>{data.scorer_version}</dd></dl><p>Hashes identify supplied evidence; they do not prove correctness. Case facts were checked by the historical scorer, not a semantic entailment judge. The app recomputes counts and p95 from reported case outcomes and verifies trace ownership during registration. Registration does not rerun or independently certify the measurements. No generation quality, token usage or API cost is inferred.</p></details>
  </>;
}

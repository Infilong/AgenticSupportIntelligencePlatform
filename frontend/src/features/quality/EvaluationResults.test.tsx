import { fireEvent, render, screen } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import type { components } from '../../api/schema';
import { EvaluationResults } from './EvaluationResults';
import { Evaluations } from './Evaluations';

const resource = vi.hoisted(() => vi.fn());
vi.mock('../workbench/useResource', () => ({ useResource: resource }));
const score = { passed: 8, total: 9, groups_found: 9, total_groups: 10 };
const record: components['schemas']['EvaluationDetail'] = {
  id: 'report', registered_at: '2026-09-09T12:00:00Z', report_sha256: 'b'.repeat(64), source_commit: 'a'.repeat(40),
  snapshot: { source_commit: 'a'.repeat(40), source_sha256: 'c'.repeat(64), corpus_sha256: 'd'.repeat(64), scorer_version: 'active-required-sections-v2', generation: 'not_verified', strategies: [{
    name: 'vector_rerank', scores: { en: score, ja: score, zh: score, all: { passed: 25, total: 26, groups_found: 26, total_groups: 27 } }, measured_requests: 30, warm_p95_seconds: 2.516, safety_passed: true, retrieval_gate_passed: true,
    cases: [{ id: 'ja02', language: 'ja', question: 'ポリシーの矛盾を確認', passed: false, trace_id: 'trace', groups_found: 1, total_groups: 2, elapsed_seconds: 1.2 },
      { id: 'en10', language: 'en', question: 'w', passed: null, trace_id: 'trace2', groups_found: 0, total_groups: 0, elapsed_seconds: 0.3 }],
  }] },
};

test('historical results preserve failed and excluded cases and measurement limits', () => {
  render(<EvaluationResults workspaceId="ws" record={record} />);
  expect(screen.getByText('25 / 26')).toBeVisible();
  expect(screen.getByText(/Answer quality unverified/)).toBeVisible();
  expect(screen.getByText('ja02 · JA · Failed')).toBeVisible();
  expect(screen.queryByText(/en10/)).not.toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Case outcome'), { target: { value: 'excluded' } });
  expect(screen.getByText(/en10 · EN · Excluded/)).toBeVisible();
  expect(screen.queryByText(/ja02 · JA/)).not.toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Case language'), { target: { value: 'ja' } });
  expect(screen.getByText('No cases match these filters.')).toBeVisible();
  fireEvent.click(screen.getByText('Measurement provenance and limits'));
  expect(screen.getByText(/registration time is not measurement time/)).toBeVisible();
});

test('empty workspace does not imply successful evaluation', () => {
  resource.mockReturnValue({ data: { items: [], more: false }, error: '', refresh: vi.fn() });
  render(<Evaluations workspaceId="empty" />);
  expect(screen.getByText('No registered results')).toBeVisible();
  expect(resource).toHaveBeenCalledWith('/workspaces/empty/evaluations?page=1');
  expect(screen.queryByRole('region', { name: 'Retrieval strategy comparison' })).not.toBeInTheDocument();
});

test('denied evaluation history suppresses stale protected results and offers retry', () => {
  const refresh = vi.fn();
  resource.mockReturnValue({ data: { items: [record], more: false }, error: 'Workspace not found', refresh });
  render(<Evaluations workspaceId="denied" />);
  expect(screen.getByRole('alert')).toHaveTextContent('Workspace not found');
  expect(screen.queryByLabelText('Saved report')).not.toBeInTheDocument();
  fireEvent.click(screen.getByText('Retry evaluations'));
  expect(refresh).toHaveBeenCalledOnce();
});

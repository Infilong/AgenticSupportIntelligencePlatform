import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, expect, test, vi } from 'vitest';
import { RunView } from './RunView';
import type { Run } from './types';

const fixture = vi.hoisted(() => ({ run: {} as Run }));
vi.mock('./useResource', () => ({ useResource: () => ({ data: fixture.run, error: '', refresh: vi.fn() }) }));
beforeEach(() => { fixture.run = {
  id: 'run', latest_run_id: 'run', original: 'Refund question', input_text: 'Refund question', state: 'awaiting_review', language: 'en',
  draft: 'Draft response', draft_hash: 'hash', review_version: 1, review_kind: 'standard', attempt_number: 1, attempts: [],
  citations: [{ chunk_id: 'chunk', title: 'Policy', section: 'Refund', quote: 'Exact evidence', document_id: 'doc', version_id: 'version', quote_start: 0 }],
  model_calls: [], steps: [], review: null, handoff: null,
} as unknown as Run; });
function show(role: 'admin' | 'viewer' = 'admin') {
  return render(<MemoryRouter><RunView workspace={{ id: 'ws', name: 'Test', default_language: 'en', role }} runId="run" /></MemoryRouter>);
}
test('review text survives keyboard tab navigation; cancellation stays available in workflow', () => {
  show(); fireEvent.change(screen.getByLabelText('Reason for your decision'), { target: { value: 'Checked policy evidence' } });
  const response = screen.getByRole('tab', { name: 'Response' }); response.focus(); fireEvent.keyDown(response, { key: 'ArrowRight' });
  expect(screen.getByRole('tab', { name: 'Workflow' })).toHaveFocus();
  expect(screen.getByRole('region', { name: 'Workflow execution' })).toBeVisible();
  expect(screen.getByRole('button', { name: 'Cancel processing' })).toBeVisible();
  fireEvent.keyDown(screen.getByRole('tab', { name: 'Workflow' }), { key: 'Home' });
  expect(screen.getByLabelText('Reason for your decision')).toHaveValue('Checked policy evidence');
});
test.each(['Response', 'Sources'])('closing a citation restores its %s opener and focus', async tab => {
  show(); fireEvent.click(screen.getByRole('tab', { name: tab }));
  const opener = screen.getByRole('button', { name: /1.*Refund/ }); fireEvent.click(opener);
  await waitFor(() => expect(screen.getByRole('complementary', { name: 'Source excerpt' })).toHaveFocus());
  fireEvent.click(screen.getByRole('button', { name: 'Close source' }));
  await waitFor(() => expect(opener).toHaveFocus());
  expect(screen.getByRole('tab', { name: tab })).toHaveAttribute('aria-selected', 'true');
});
test('viewer can inspect workflow but never receives review or cancellation controls', () => {
  show('viewer'); expect(screen.queryByLabelText('Reason for your decision')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('tab', { name: 'Workflow' }));
  expect(screen.getByRole('region', { name: 'Workflow execution' })).toBeVisible();
  expect(screen.queryByRole('button', { name: 'Cancel processing' })).not.toBeInTheDocument();
});

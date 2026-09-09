import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';
import { RunResult } from './RunResult';
import type { Run } from './types';

const approved = { id: 'one', state: 'completed', outcome: 'approved_response', language: 'ja',
  draft: 'Original unapproved wording', reviewed_response: '返金は14日以内です。\n条件をご確認ください。',
  citations: [], review: { action: 'edit' } } as unknown as Run;
afterEach(() => vi.unstubAllGlobals());

test('copies exact approved wording, reports denial, and supports retry', async () => {
  const writeText = vi.fn().mockRejectedValueOnce(new DOMException('Denied', 'NotAllowedError')).mockResolvedValue(undefined);
  vi.stubGlobal('navigator', { clipboard: { writeText } });
  render(<RunResult run={approved} />);
  fireEvent.click(screen.getByRole('button', { name: 'Copy approved response' }));
  expect(await screen.findByText(/Could not copy/)).toBeVisible();
  fireEvent.click(screen.getByRole('button', { name: 'Copy approved response' }));
  expect(await screen.findByText('Approved response copied.')).toBeVisible();
  expect(writeText.mock.calls).toEqual([[approved.reviewed_response], [approved.reviewed_response]]);
});

test.each([
  ['awaiting_review', 'grounded_draft'], ['failed', 'approved_response'],
  ['rejected', 'rejected_response'], ['completed', 'clarification_needed'],
])('does not offer approved copying for %s / %s', (state, outcome) => {
  render(<RunResult run={{ ...approved, state, outcome } as Run} />);
  expect(screen.queryByRole('button', { name: 'Copy approved response' })).not.toBeInTheDocument();
});

test('a different response clears previous copy feedback', async () => {
  vi.stubGlobal('navigator', { clipboard: { writeText: vi.fn().mockResolvedValue(undefined) } });
  const view = render(<RunResult run={approved} />);
  fireEvent.click(screen.getByRole('button', { name: 'Copy approved response' }));
  await screen.findByText('Approved response copied.');
  view.rerender(<RunResult run={{ ...approved, id: 'two', reviewed_response: 'Different final response' }} />);
  expect(screen.queryByText('Approved response copied.')).not.toBeInTheDocument();
});

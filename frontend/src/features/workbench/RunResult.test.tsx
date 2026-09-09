import { render, screen } from '@testing-library/react';
import { expect, test } from 'vitest';
import { RunResult } from './RunResult';
import type { Run } from './types';

test.each(['queued', 'failed', 'cancelled', 'completed'])('a recorded question is active only after publication: %s', state => {
  const run = { state, outcome: 'clarification_needed', draft: 'Preserved draft', language: 'en',
    citations: [], reviewed_response: null, review: { action: 'clarify', response: 'What was the purchase date?' } } as unknown as Run;
  render(<RunResult run={run} />);
  expect(screen.getByText('Preserved draft')).toBeInTheDocument();
  if (state === 'completed') {
    expect(screen.getByRole('heading', { name: 'Clarification requested' })).toBeVisible();
    expect(screen.getByText('What was the purchase date?')).toBeVisible();
    expect(screen.getByText('Original unapproved draft')).toBeVisible();
  } else {
    expect(screen.queryByText('What was the purchase date?')).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Clarification requested' })).not.toBeInTheDocument();
  }
});

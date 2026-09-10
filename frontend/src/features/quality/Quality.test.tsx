import { render, screen } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import { Quality } from './Quality';

vi.mock('../workbench/useResource', () => ({ useResource: () => ({ data: {
  until: '2026-09-09T00:00:00Z', more_models: false, models: [],
  totals: { calls: 3, succeeded: 1, failed: 1, uncertain: 1, started: 0, input_tokens: 10,
    missing_tokens: 2, recorded_cost_usd: 0, missing_cost: 2, recorded_duration_ms: 20, missing_duration: 2 },
}, error: '', refresh: () => {} }) }));

test('zero recorded charge retains unknown measurements and the development limitation', () => {
  render(<Quality workspace={{ id: 'ws', name: 'Test', default_language: 'en', role: 'viewer' }} />);
  expect(screen.getByText('$0.0000')).toBeVisible();
  expect(screen.getByText('2 calls without cost measurements')).toBeVisible();
  expect(screen.getByText(/not an answer-quality score/)).toBeVisible();
  expect(screen.getByText(/not automatic model calls/)).toBeVisible();
  expect(screen.queryByRole('button', { name: 'Generation comparisons' })).not.toBeInTheDocument();
});

import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { expect, test, vi } from 'vitest';
import { RetrievalTrace } from './RetrievalTrace';

const fixture = vi.hoisted(() => ({ status: 'started', phase: 'candidates' }));
vi.mock('../workbench/useResource', () => ({ useResource: () => ({ data: { ...fixture, candidates: [], parameters: {}, strategy: 'hybrid_rerank-v1' }, error: '', refresh: vi.fn() }) }));
test.each([
  ['started', 'candidates', 'Retrieval is in progress'],
  ['failed', 'candidates', 'Retrieval stopped'],
  ['uncertain', 'started', 'Retrieval stopped'],
  ['succeeded', 'unavailable', 'Candidate history was not recorded'],
])('trace %s/%s distinguishes live, incomplete and legacy evidence', async (status, phase, text) => {
  Object.assign(fixture, { status, phase });
  render(<MemoryRouter><RetrievalTrace workspaceId="ws" traceId="trace" /></MemoryRouter>);
  const summary = screen.getByText('Retrieval evidence');
  const details = summary.parentElement as HTMLDetailsElement;
  details.open = true; fireEvent(details, new Event('toggle'));
  expect(await screen.findByText(new RegExp(text))).toBeVisible();
  if (status === 'started') expect(screen.queryByText(/Retrieval stopped/)).not.toBeInTheDocument();
});

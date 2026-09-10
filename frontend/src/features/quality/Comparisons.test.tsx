import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, expect, test, vi } from 'vitest';
import { api } from '../../api/client';
import { ComparisonDetail } from './ComparisonDetail';
import { Comparisons } from './Comparisons';
import { NewComparison } from './NewComparison';

const resource = vi.hoisted(() => ({ data: null as unknown, error: '', refresh: vi.fn() }));
vi.mock('../workbench/useResource', () => ({ useResource: () => resource }));
vi.mock('../../api/client', () => ({ api: vi.fn() }));
const workspace = { id: 'ws', name: 'Test', default_language: 'en' as const, role: 'admin' as const };

beforeEach(() => { vi.clearAllMocks(); resource.data = null; resource.error = ''; });

test('submission failure preserves the question and retries with the same admission key', async () => {
  vi.mocked(api).mockRejectedValueOnce(new Error('Connection interrupted')).mockResolvedValueOnce({ id: 'created' });
  const created = vi.fn();
  render(<NewComparison workspace={workspace} onCreated={created} onBusy={vi.fn()} />);
  fireEvent.change(screen.getByLabelText('Question to compare'), { target: { value: '返金期限は？' } });
  fireEvent.click(screen.getByRole('button', { name: 'Start comparison' }));
  await screen.findByRole('alert');
  expect(screen.getByLabelText('Question to compare')).toHaveValue('返金期限は？');
  fireEvent.click(screen.getByRole('button', { name: 'Start comparison' }));
  await waitFor(() => expect(created).toHaveBeenCalledWith('created'));
  const calls = vi.mocked(api).mock.calls;
  expect(calls[0][1]?.headers).toEqual(calls[1][1]?.headers);
  expect(JSON.parse(calls[1][1]?.body as string)).toEqual({ original: '返金期限は？', language: 'en' });
});

test('all four outcomes remain visible and reviewed wording is separate from the original', () => {
  resource.data = { question: 'Refund?', language: 'en', cancelled: false, comparable: true,
    pipelines: ['direct_llm', 'vector_rag', 'hybrid_rag', 'system_v1'].map((name, index) => ({
      name, state: index === 1 ? 'failed' : 'completed', attempts: 1, configuration: { strategy: index ? 'hybrid' : null },
      initial_response: index === 3 ? { answer: 'Original wording' } : null,
      reviewed_response: index === 3 ? 'Reviewed wording' : null,
      error_code: index === 1 ? 'provider_failure' : null,
    })) };
  render(<MemoryRouter><ComparisonDetail workspaceId="ws" id="comparison" /></MemoryRouter>);
  expect(screen.getAllByRole('article')).toHaveLength(4);
  expect(screen.getByText('Original wording')).toBeVisible();
  expect(screen.getByText('Reviewed wording')).toBeVisible();
  expect(screen.getByText(/provider_failure/)).toBeVisible();
  expect(screen.getByText(/Answer quality unverified/)).toBeVisible();
  expect(screen.queryByRole('button', { name: 'Cancel pending comparison work' })).not.toBeInTheDocument();
});

test('permission error replaces protected comparison contents', () => {
  resource.error = 'Workspace access revoked';
  resource.data = { question: 'Protected question' };
  render(<MemoryRouter><ComparisonDetail workspaceId="ws" id="comparison" /></MemoryRouter>);
  expect(screen.getByRole('alert')).toHaveTextContent('Workspace access revoked');
  expect(screen.queryByText('Protected question')).not.toBeInTheDocument();
});

test('revoked history clears creation controls and the open question form', () => {
  resource.data = { items: [] };
  const view = render(<MemoryRouter><Comparisons workspace={workspace} /></MemoryRouter>);
  fireEvent.click(screen.getByRole('button', { name: 'New comparison' }));
  fireEvent.change(screen.getByLabelText('Question to compare'), { target: { value: 'Private draft' } });
  resource.data = null; resource.error = 'Workspace access revoked';
  view.rerender(<MemoryRouter><Comparisons workspace={workspace} /></MemoryRouter>);
  expect(screen.getByRole('alert')).toHaveTextContent('Workspace access revoked');
  expect(screen.queryByLabelText('Question to compare')).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'New comparison' })).not.toBeInTheDocument();
});

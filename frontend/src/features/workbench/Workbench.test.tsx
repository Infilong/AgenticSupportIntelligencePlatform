import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { Link, MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { beforeEach, expect, test, vi } from 'vitest';
import { Workbench } from './Workbench';

const fixture = vi.hoisted(() => ({ total: 51, paths: [] as string[] }));
vi.mock('./RunView', () => ({ RunView: () => {
  const { search } = useLocation();
  return <div>Selected detail<Link to={`/w/ws${search}`}>All messages</Link></div>;
} }));
vi.mock('./useResource', () => ({ useResource: (path: string) => {
  fixture.paths.push(path);
  const params = new URL(path, 'http://local').searchParams;
  const offset = Number(params.get('offset')); const limit = Number(params.get('limit'));
  return { error: '', refresh: () => {}, data: { total: fixture.total,
    items: Array.from({ length: Math.max(0, Math.min(limit, fixture.total - offset)) }, (_, i) => ({
      id: String(i + offset), run_id: String(i + offset), original: `Message ${i + offset}`,
      language: 'en', state: 'queued', outcome: null, created_at: '2026-09-09T00:00:00Z',
    })),
  } };
} }));
const workspace = { id: 'ws', name: 'Test', role: 'viewer' } as const;
function ui(path: string) { return <MemoryRouter initialEntries={[path]}><Routes>
  <Route path="/w/:workspaceId" element={<Workbench workspace={workspace} />} />
  <Route path="/w/:workspaceId/runs/:runId" element={<Workbench workspace={workspace} />} />
</Routes></MemoryRouter>; }
beforeEach(() => { fixture.total = 51; fixture.paths = []; });

test('detail unmounts the inbox and return restores submitted filter, page and page size', () => {
  render(ui('/w/ws?view=processing&search=Message&offset=50&limit=50'));
  expect(screen.getByText('Message 50')).toBeVisible();
  fireEvent.click(screen.getByRole('link', { name: 'Message 50' }));
  expect(screen.getByText('Selected detail')).toBeVisible();
  expect(screen.queryByRole('table')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('link', { name: 'All messages' }));
  expect(screen.getByLabelText('Message view')).toHaveValue('processing');
  expect(screen.getByRole('textbox', { name: 'Search messages' })).toHaveValue('Message');
  expect(screen.getByLabelText('Rows per page')).toHaveValue('50');
  expect(screen.getByText('Message 50')).toBeVisible();
});

test('a shrinking last page returns to a valid page and keeps filters', async () => {
  const { rerender } = render(ui('/w/ws?view=processing&offset=40'));
  expect(screen.getByText('Message 40')).toBeVisible(); fixture.total = 20;
  rerender(ui('/w/ws?view=processing&offset=40'));
  await waitFor(() => expect(screen.getByText('Message 0')).toBeVisible());
  expect(fixture.paths.at(-1)).toContain('view=processing&offset=0');
});

test('page jump and size changes request bounded pages; malformed URL values are normalized', () => {
  fixture.total = 50000;
  render(ui('/w/ws?view=invalid&offset=-90&limit=100000'));
  expect(fixture.paths.at(-1)).toContain('view=all&offset=0&limit=20');
  expect(screen.getAllByRole('row')).toHaveLength(21);
  fireEvent.change(screen.getByLabelText('Page'), { target: { value: '2500' } });
  fireEvent.click(screen.getByRole('button', { name: 'Go' }));
  expect(screen.getByText('Message 49999')).toBeVisible();
  expect(screen.getByRole('button', { name: 'Next' })).toBeDisabled();
  fireEvent.change(screen.getByLabelText('Rows per page'), { target: { value: '50' } });
  expect(fixture.paths.at(-1)).toContain('offset=0&limit=50');
  expect(screen.getAllByRole('row')).toHaveLength(51);
});

test('viewer compose deep links show the read-only inbox', () => {
  render(ui('/w/ws?compose=1'));
  expect(screen.getByRole('table')).toBeVisible();
  expect(screen.queryByRole('button', { name: 'Start processing' })).not.toBeInTheDocument();
});


test('a label-only empty result explains how to clear the filter', () => {
  fixture.total = 0;
  render(ui('/w/ws?label=missing'));
  expect(screen.getByRole('heading', { name: 'No matching messages' })).toBeVisible();
});

test('viewer import deep links remain read-only', () => {
  render(ui('/w/ws?import=1'));
  expect(screen.getByRole('table')).toBeVisible();
  expect(screen.queryByLabelText('JSONL file')).not.toBeInTheDocument();
});

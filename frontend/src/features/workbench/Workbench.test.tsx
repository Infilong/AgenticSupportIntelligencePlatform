import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { expect, test, vi } from 'vitest';
import { Workbench } from './Workbench';

const fixture = vi.hoisted(() => ({ total: 21, paths: [] as string[] }));
vi.mock('./RunView', () => ({ RunView: () => <div>Selected detail stays open</div> }));
vi.mock('./useResource', () => ({ useResource: (path: string) => {
  fixture.paths.push(path);
  const offset = Number(new URL(path, 'http://local').searchParams.get('offset'));
  return { error: '', refresh: () => {}, data: { total: fixture.total,
    items: Array.from({ length: Math.max(0, Math.min(20, fixture.total - offset)) }, (_, i) => ({
      id: String(i + offset), run_id: String(i + offset), original: `Message ${i + offset}`,
      language: 'en', state: 'queued', outcome: null,
    })),
  } };
} }));

test('a shrinking filtered last page returns to a valid page without losing the selected run', async () => {
  const ui = <MemoryRouter initialEntries={['/w/ws/runs/selected']}><Routes><Route path="/w/:workspaceId/runs/:runId"
    element={<Workbench workspace={{ id: 'ws', name: 'Test', role: 'viewer' }} />} /></Routes></MemoryRouter>;
  const { rerender } = render(ui);
  fireEvent.change(screen.getByLabelText('Message view'), { target: { value: 'processing' } });
  fireEvent.click(screen.getByRole('button', { name: 'Next' }));
  expect(screen.getByText('Message 20')).toBeVisible();
  fixture.total = 20;
  rerender(<MemoryRouter initialEntries={['/w/ws/runs/selected']}><Routes><Route path="/w/:workspaceId/runs/:runId"
    element={<Workbench workspace={{ id: 'ws', name: 'Test', role: 'viewer' }} />} /></Routes></MemoryRouter>);
  await waitFor(() => expect(screen.getByText('Message 0')).toBeVisible());
  expect(fixture.paths.at(-1)).toContain('view=processing&offset=0');
  expect(screen.getByText('Selected detail stays open')).toBeVisible();
});

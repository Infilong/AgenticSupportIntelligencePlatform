import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import { api } from '../../api/client';
import { ImportMessages } from './ImportMessages';

vi.mock('../../api/client', () => ({ api: vi.fn() }));
const workspace = { id: 'ws', name: 'Test', default_language: 'en', role: 'operator' } as const;

test('failed upload retains the file and idempotency key for a safe retry', async () => {
  vi.mocked(api).mockReset().mockRejectedValueOnce(new Error('Connection lost')).mockResolvedValueOnce({ id: 'batch', message_count: 1, filename: 'messages.jsonl' });
  render(<ImportMessages workspace={workspace} onClose={() => {}} onImported={() => {}} />);
  fireEvent.change(screen.getByLabelText('JSONL file'), { target: { files: [new File(['{}'], 'messages.jsonl')] } });
  fireEvent.submit(screen.getByRole('form', { name: 'Import customer messages' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Connection lost');
  fireEvent.submit(screen.getByRole('form', { name: 'Import customer messages' }));
  expect(await screen.findByRole('heading', { name: 'Messages imported' })).toBeVisible();
  const calls = vi.mocked(api).mock.calls;
  expect(calls[0][1]?.headers).toEqual(calls[1][1]?.headers);
});

test('leaving an in-flight import aborts its request and ignores its completion', async () => {
  let finish!: (value: unknown) => void;
  vi.mocked(api).mockReset().mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  const imported = vi.fn();
  const { unmount } = render(<ImportMessages workspace={workspace} onClose={() => {}} onImported={imported} />);
  fireEvent.change(screen.getByLabelText('JSONL file'), { target: { files: [new File(['{}'], 'messages.jsonl')] } });
  fireEvent.submit(screen.getByRole('form', { name: 'Import customer messages' }));
  await waitFor(() => expect(api).toHaveBeenCalledOnce());
  const signal = vi.mocked(api).mock.calls[0][1]?.signal;
  unmount(); expect(signal?.aborted).toBe(true);
  finish({ id: 'batch', message_count: 1, filename: 'messages.jsonl' });
  expect(imported).not.toHaveBeenCalled();
});

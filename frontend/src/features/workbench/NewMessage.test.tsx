import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';
import { api, type Workspace } from '../../api/client';
import { NewMessage } from './NewMessage';

vi.mock('../../api/client', () => ({ api: vi.fn() }));
const workspace: Workspace = { id: 'workspace-test', name: 'Test', default_language: 'en', role: 'operator' };
afterEach(() => vi.resetAllMocks());

test('Chinese input defaults to server-owned question language, not English workspace', async () => {
  vi.mocked(api).mockResolvedValue({ run_id: 'new-run' });
  render(<NewMessage workspace={workspace} onCreated={vi.fn()} onClose={vi.fn()} />);
  fireEvent.change(screen.getByLabelText('Customer message'), { target: { value: '删除账户确认' } });
  await act(async () => fireEvent.submit(screen.getByRole('form', { name: 'New customer message' })));
  expect(JSON.parse(vi.mocked(api).mock.calls[0][1]!.body as string)).toEqual({ original: '删除账户确认', language: 'auto' });
});

test('matches question by default but permits an explicit language choice', async () => {
  vi.mocked(api).mockResolvedValue({ run_id: 'new-run' });
  render(<NewMessage workspace={{ ...workspace, default_language: 'ja' }} onCreated={vi.fn()} onClose={vi.fn()} />);
  expect(screen.getByLabelText('Response language')).toHaveValue('auto');
  fireEvent.change(screen.getByLabelText('Response language'), { target: { value: 'zh' } });
  fireEvent.change(screen.getByLabelText('Customer message'), { target: { value: '退款期限是什么？' } });
  await act(async () => fireEvent.submit(screen.getByRole('form', { name: 'New customer message' })));
  expect(JSON.parse(vi.mocked(api).mock.calls[0][1]!.body as string).language).toBe('zh');
});

test('late successful submission does not invoke navigation after unmount', async () => {
  let resolve!: (value: unknown) => void;
  vi.mocked(api).mockImplementation(() => new Promise(r => { resolve = r; }));
  const onCreated = vi.fn();
  const view = render(<NewMessage workspace={workspace} onCreated={onCreated} onClose={vi.fn()} />);
  fireEvent.change(screen.getByLabelText('Customer message'), { target: { value: 'Refund question' } });
  fireEvent.submit(screen.getByRole('form', { name: 'New customer message' }));
  const options = vi.mocked(api).mock.calls[0][1]!;
  view.unmount();
  expect(options.signal?.aborted).toBe(true);
  await act(async () => resolve({ run_id: 'stored-run' }));
  expect(onCreated).not.toHaveBeenCalled();
});

test('retry preserves input and idempotency key after an uncertain network response', async () => {
  vi.mocked(api).mockRejectedValueOnce(new Error('Connection interrupted')).mockResolvedValueOnce({ run_id: 'same-run' });
  const onCreated = vi.fn();
  render(<NewMessage workspace={workspace} onCreated={onCreated} onClose={vi.fn()} />);
  fireEvent.change(screen.getByLabelText('Customer message'), { target: { value: 'Refund question' } });
  fireEvent.submit(screen.getByRole('form', { name: 'New customer message' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Connection interrupted');
  expect(screen.getByLabelText('Customer message')).toHaveValue('Refund question');
  await act(async () => fireEvent.submit(screen.getByRole('form', { name: 'New customer message' })));
  const calls = vi.mocked(api).mock.calls;
  expect(calls[0][1]?.headers).toEqual(calls[1][1]?.headers);
  expect(onCreated).toHaveBeenCalledWith('same-run');
});

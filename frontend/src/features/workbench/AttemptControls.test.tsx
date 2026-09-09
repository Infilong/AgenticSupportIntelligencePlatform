import { fireEvent, render, screen } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { api } from '../../api/client';
import { AttemptControls } from './AttemptControls';
import type { Run } from './types';

vi.mock('../../api/client', () => ({ api: vi.fn() }));

test('frozen comparison runs explain why retry and added-details actions are unavailable', () => {
  const run = { id: 'run', latest_run_id: 'run', state: 'failed', attempt_number: 1,
    input_text: 'Question', input_frozen: true, attempts: [] } as unknown as Run;
  render(<MemoryRouter><AttemptControls run={run} workspace={{ id: 'ws', name: 'Test', default_language: 'en', role: 'admin' }} onCreated={vi.fn()} /></MemoryRouter>);
  expect(screen.queryByText('Add customer details')).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Retry processing' })).not.toBeInTheDocument();
  expect(screen.getByText(/This comparison keeps its original question fixed/)).toBeVisible();
});

test('Unicode details use the server character limit and excess input cannot submit', () => {
  const separator = '\n\nCustomer clarification:\n';
  const run = { id: 'run', latest_run_id: 'run', state: 'completed', attempt_number: 1,
    input_text: 'x'.repeat(1000 - separator.length - 2), attempts: [] } as unknown as Run;
  render(<MemoryRouter><AttemptControls run={run} workspace={{ id: 'ws', name: 'Test', default_language: 'en', role: 'operator' }} onCreated={vi.fn()} /></MemoryRouter>);
  fireEvent.click(screen.getByText('Add customer details'));
  const input = screen.getByLabelText('Additional customer details');
  fireEvent.change(input, { target: { value: '😀𠮷' } });
  expect(input).toHaveValue('😀𠮷');
  expect(screen.getByRole('button', { name: 'Process with added details' })).toBeEnabled();
  expect(screen.getByText('0 characters available within the combined 1,000-character input limit.')).toBeVisible();
  fireEvent.change(input, { target: { value: '😀𠮷a' } });
  expect(input).toHaveAttribute('aria-invalid', 'true');
  expect(screen.getByRole('button', { name: 'Process with added details' })).toBeDisabled();
  fireEvent.submit(input.closest('form')!);
  expect(api).not.toHaveBeenCalled();
});

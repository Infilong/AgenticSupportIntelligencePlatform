import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, test, vi } from 'vitest';
import { Login } from './Login';

test('preserves entered information and explains a rejected sign-in', async () => {
  const login = vi.fn().mockRejectedValue(new Error('Email or password is incorrect'));
  render(<Login onLogin={login} />);
  const user = userEvent.setup();
  await user.type(screen.getByLabelText('Email address'), 'operator@example.test');
  await user.type(screen.getByLabelText('Password'), 'test-password');
  await user.click(screen.getByRole('button', { name: 'Sign in' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Email or password is incorrect');
  expect(screen.getByLabelText('Email address')).toHaveValue('operator@example.test');
  expect(screen.getByRole('button', { name: 'Sign in' })).toBeEnabled();
});

test('prevents repeat submissions while sign-in is pending', async () => {
  const login = vi.fn(() => new Promise<void>(() => {}));
  render(<Login onLogin={login} />);
  const user = userEvent.setup();
  await user.type(screen.getByLabelText('Email address'), 'operator@example.test');
  await user.type(screen.getByLabelText('Password'), 'test-password');
  await user.dblClick(screen.getByRole('button', { name: 'Sign in' }));
  expect(login).toHaveBeenCalledTimes(1);
  expect(screen.getByRole('button', { name: 'Signing in…' })).toBeDisabled();
});

import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';

const credentials = JSON.parse(readFileSync('../.artifacts/m1/demo-credentials.json', 'utf8'));
const base = 'http://127.0.0.1:5180';

async function login(page: Page, role: string) {
  await page.goto(base);
  await page.getByLabel('Email address').fill(credentials.accounts[role]);
  await page.getByLabel('Password', { exact: true }).fill(credentials.password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Workbench', exact: true })).toBeVisible();
}

test('admin signs in, inspects members, preserves last admin and signs out', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await login(page, 'admin');
  await page.getByRole('link', { name: 'Members', exact: true }).click();
  await expect(page.getByText('admin@asterworks.example', { exact: true })).toHaveCount(2);
  await page.getByLabel('Role for Demo Admin').selectOption('viewer');
  await expect(page.getByRole('alert')).toHaveText('Keep at least one administrator in this workspace');
  await expect(page.getByLabel('Role for Demo Admin')).toHaveValue('admin');
  await page.screenshot({ path: test.info().outputPath('members-desktop.png'), fullPage: true });
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
  expect(errors).toEqual([]);
});

test('viewer denied member management and foreign workspace, narrow layout remains usable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page, 'viewer');
  const home = page.url();
  await expect(page.getByRole('link', { name: 'Members', exact: true })).toHaveCount(0);
  await page.goto(`${home}/members`);
  await expect(page.getByRole('heading', { name: 'Administrator access required' })).toBeVisible();
  await page.goto(`${base}/w/00000000-0000-0000-0000-000000000001`);
  await expect(page.getByRole('heading', { name: 'Workspace unavailable' })).toBeVisible();
  await page.getByRole('button', { name: 'Back to my workspace' }).click();
  await expect(page.getByRole('heading', { name: 'Workbench', exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: test.info().outputPath('workbench-mobile.png'), fullPage: true });
});

test('failed login preserves entered email and a server outage offers recovery', async ({ page }) => {
  await page.goto(base);
  await page.getByLabel('Email address').fill(credentials.accounts.operator);
  await page.getByLabel('Password', { exact: true }).fill('deliberately-wrong');
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByRole('alert')).toBeVisible();
  await expect(page.getByLabel('Email address')).toHaveValue(credentials.accounts.operator);
  await page.route('**/api/session', route => route.abort());
  await page.reload();
  await expect(page.getByRole('alert')).toContainText('Cannot reach the server');
  await page.unroute('**/api/session');
  await page.getByRole('button', { name: 'Try again' }).click();
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
});

test('lost anonymous and authenticated sessions recover without replaying actions', async ({ page, context }) => {
  await page.goto(base);
  await page.getByLabel('Email address').fill(credentials.accounts.operator);
  await page.getByLabel('Password', { exact: true }).fill(credentials.password);
  await context.clearCookies();
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByRole('alert')).toHaveText('Your sign-in session changed. Please sign in again.');
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Workbench', exact: true })).toBeVisible();
  await context.clearCookies();
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
});

test('workspace denial refreshes the list instead of returning to a stale destination', async ({ page }) => {
  await login(page, 'viewer');
  const workspaceUrl = page.url();
  // Fault injection tests frontend recovery; real revocation is covered by PostgreSQL tests.
  await page.route('**/api/workspaces/*', route => route.fulfill({ status: 404, json: { detail: 'Workspace unavailable' } }));
  await page.goto(`${workspaceUrl}/members`);
  await expect(page.getByRole('heading', { name: 'Workspace unavailable' })).toBeVisible();
  await page.route('**/api/workspaces', route => route.fulfill({ json: [] }));
  await page.getByRole('button', { name: 'Back to my workspace' }).click();
  await expect(page.getByRole('heading', { name: 'No workspace access' })).toBeVisible();
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
});

test('operator message survives reload and asks for clarification without a model', async ({ page }) => {
  await login(page, 'operator');
  await page.getByRole('button', { name: 'New message', exact: true }).click();
  await page.getByLabel('Customer message', { exact: true }).fill('w');
  await page.getByRole('button', { name: 'Start processing', exact: true }).click();
  await expect(page.locator('.run-heading').getByRole('status')).toHaveText('Clarification needed', { timeout: 15000 });
  await page.reload();
  await expect(page.locator('.original-message')).toHaveText('w');
  await expect(page.locator('.response-text')).toContainText('describe your question');
  await expect(page.getByText('Development response controls', { exact: true })).toHaveCount(0);
});

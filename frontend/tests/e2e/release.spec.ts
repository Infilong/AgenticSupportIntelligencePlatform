import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';

const base = 'http://127.0.0.1:8011';
const credentials = JSON.parse(readFileSync('../.artifacts/m6/release-credentials.json', 'utf8'));
async function login(page: Page, role: string) {
  await page.goto(base);
  await page.getByLabel('Email address').fill(credentials.accounts[role]);
  await page.getByLabel('Password', { exact: true }).fill(credentials.password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Workbench', exact: true })).toBeVisible();
}

test('built assets are served by the API origin and errors never return the shell', async ({ request }) => {
  const html = await request.get(base);
  expect(html.status()).toBe(200);
  expect(html.headers()['cache-control']).toBe('no-store');
  const body = await html.text();
  expect(body).not.toContain('/@vite');
  const scripts = [...body.matchAll(/(?:src|href)="(\/assets\/[^" ]+)"/g)].map(match => match[1]);
  expect(scripts.length).toBeGreaterThanOrEqual(2);
  for (const path of scripts) {
    const asset = await request.get(base + path);
    expect(asset.status()).toBe(200);
    expect(asset.headers()['cache-control']).toContain('immutable');
    expect(asset.headers()['content-type']).toMatch(/javascript|text\/css/);
  }
  for (const path of ['/api/missing', '/assets/missing.js', '/.env', '/app/main.py', '/assets/%2e%2e%2findex.html']) {
    const response = await request.get(base + path);
    expect(response.status()).toBe(404);
    expect(response.headers()['content-type']).toContain('application/json');
  }
  expect((await request.get(base + '/api/workspaces')).status()).toBe(401);
});

test('same-origin login, worker clarification, nested refresh, CSRF denial and logout', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await login(page, 'operator');
  const workspaceId = page.url().split('/w/')[1];
  const csrf = (await (await page.request.get(base + '/api/session')).json()).csrf_token;
  const denied = await page.request.post(`${base}/api/workspaces/${workspaceId}/messages`, {
    headers: { Origin: 'https://untrusted.example', 'X-CSRF-Token': csrf, 'Idempotency-Key': 'release-denied' },
    data: { original: 'w', language: 'en' },
  });
  expect(denied.status()).toBe(403);
  await page.getByRole('button', { name: 'New message', exact: true }).click();
  await page.getByLabel('Customer message', { exact: true }).fill('w');
  await page.getByRole('button', { name: 'Start processing', exact: true }).click();
  await expect(page.locator('.run-heading').getByRole('status')).toHaveText('Completed', { timeout: 20000 });
  const runId = page.url().split('/runs/')[1];
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Clarification needed', exact: true })).toBeVisible();
  const run = await (await page.request.get(`${base}/api/workspaces/${workspaceId}/runs/${runId}`)).json();
  expect(run.outcome).toBe('clarification_needed');
  expect(run.model_calls).toEqual([]);
  for (const width of [360, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`release-${width}.png`), fullPage: true });
  }
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
  expect((await page.request.get(`${base}/api/workspaces/${workspaceId}/runs/${runId}`)).status()).toBe(401);
  expect(errors).toEqual([]);
});

test('viewer cannot mutate and a real foreign workspace remains unavailable', async ({ page, browser }) => {
  const privateContext = await browser.newContext();
  let privateWorkspaceId: string;
  try {
    const privatePage = await privateContext.newPage();
    await login(privatePage, 'private');
    privateWorkspaceId = privatePage.url().split('/w/')[1];
    expect((await privatePage.request.get(`${base}/api/workspaces/${privateWorkspaceId}`)).status()).toBe(200);
  } finally { await privateContext.close(); }
  await login(page, 'viewer');
  const workspaceId = page.url().split('/w/')[1];
  expect(privateWorkspaceId).not.toBe(workspaceId);
  const csrf = (await (await page.request.get(base + '/api/session')).json()).csrf_token;
  expect((await page.request.post(`${base}/api/workspaces/${workspaceId}/messages`, {
    headers: { Origin: base, 'X-CSRF-Token': csrf, 'Idempotency-Key': 'viewer-denied' },
    data: { original: 'w', language: 'en' },
  })).status()).toBe(403);
  expect((await page.request.get(`${base}/api/workspaces/${privateWorkspaceId}`)).status()).toBe(404);
  await page.goto(`${base}/w/${privateWorkspaceId}`);
  await expect(page.getByRole('heading', { name: 'Workspace unavailable' })).toBeVisible();
});

import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';

const credentials = JSON.parse(readFileSync(process.env.ASI_DEMO_CREDENTIALS ?? '../.artifacts/m1/demo-credentials.json', 'utf8'));
const base = process.env.ASI_APP_BASE_URL ?? 'http://127.0.0.1:5180';

test('administrator creates, inspects and cancels a comparison; denied history clears the view', async ({ page }) => {
  test.setTimeout(120000);
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(base);
  await page.getByLabel('Email address').fill(credentials.accounts.admin);
  await page.getByLabel('Password', { exact: true }).fill(credentials.password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByRole('link', { name: 'Quality', exact: true }).click();
  await page.getByRole('button', { name: 'Generation comparisons', exact: true }).click();
  await page.getByRole('button', { name: 'New comparison', exact: true }).click();
  const question = `Browser comparison ${Date.now()}: what is the refund deadline?`;
  await page.getByLabel('Question to compare').fill(question);
  await page.getByLabel('Answer language').selectOption('en');
  const admitted = page.waitForResponse(response => response.request().method() === 'POST' && response.url().endsWith('/comparisons'));
  await page.getByRole('button', { name: 'Start comparison', exact: true }).click();
  expect((await admitted).status()).toBe(202);
  await expect(page.getByRole('heading', { name: question, exact: true })).toBeVisible();
  await expect(page.locator('.comparison-grid h4')).toHaveText(['Direct answer', 'Vector retrieval', 'Hybrid retrieval', 'Governed support workflow']);
  await expect(page.getByText(/Answer quality unverified/)).toBeVisible();
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`comparison-${width}.png`), fullPage: true });
  }
  await page.getByRole('button', { name: 'Cancel pending comparison work', exact: true }).click();
  await expect(page.getByText('Comparison cancelled. Saved outcomes remain in history.')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Cancel pending comparison work', exact: true })).toHaveCount(0);
  // Browser denial behavior; PostgreSQL integration tests separately revoke actual membership.
  await page.route('**/api/workspaces/*/comparisons?offset=*', route => route.fulfill({ status: 403, json: { detail: 'Workspace access revoked' } }));
  await expect(page.getByRole('alert')).toHaveText('Workspace access revoked', { timeout: 10000 });
  await expect(page.getByRole('button', { name: 'New comparison', exact: true })).toHaveCount(0);
  await expect(page.getByLabel('Saved comparison')).toHaveCount(0);
  await expect(page.getByRole('heading', { name: question, exact: true })).toHaveCount(0);
  expect(errors).toEqual([]);
});

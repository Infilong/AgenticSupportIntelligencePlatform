import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';

const credentials = JSON.parse(readFileSync('../.artifacts/m1/demo-credentials.json', 'utf8'));
async function login(page: Page, role: string) {
  await page.goto('http://127.0.0.1:5180');
  await page.getByLabel('Email address').fill(credentials.accounts[role]);
  await page.getByLabel('Password', { exact: true }).fill(credentials.password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByRole('link', { name: 'Knowledge', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Knowledge', exact: true })).toBeVisible();
  await expect(page.getByText('Simulated responses · Development', { exact: true })).toBeVisible();
}

test('real upload, source preview, search, replacement failure and withdrawal', async ({ page }) => {
  test.setTimeout(150000);
  const errors: string[] = []; page.on('pageerror', error => errors.push(error.message));
  await login(page, 'admin');
  const title = `Travel-policy-QA-${Date.now()}.md`;
  const source = '# Company travel policy\n\n## LUNAR-TRAVEL\n\nLunar research travel requires approval from the science director at least 21 days before departure. Keep receipts for accommodation expenses.\n';
  await page.getByLabel('Knowledge document').setInputFiles({ name: title, mimeType: 'text/markdown', buffer: Buffer.from(source) });
  await page.getByRole('button', { name: 'Upload document', exact: true }).click();
  await expect(page.getByRole('heading', { name: title, exact: true })).toBeVisible();
  await expect(page.getByText('Ready', { exact: true })).toBeVisible({ timeout: 90000 });
  await expect(page.locator('.source-text')).toHaveText(source.trim());
  await page.getByText('Replace this document', { exact: true }).click();
  await page.getByLabel('Replacement document').setInputFiles({ name: 'invalid.txt', mimeType: 'text/plain', buffer: Buffer.from([255]) });
  await page.getByRole('button', { name: 'Upload replacement', exact: true }).click();
  await expect(page.getByRole('alert')).toBeVisible();
  await expect(page.getByText('Ready', { exact: true })).toBeVisible();
  await expect(page.locator('.source-text')).toHaveText(source.trim());
  const detailUrl = page.url();
  await page.screenshot({ path: test.info().outputPath('source-desktop.png'), fullPage: true });
  await page.getByRole('link', { name: '← Knowledge', exact: true }).click();
  await page.getByRole('link', { name: 'Search knowledge', exact: true }).click();
  await page.getByLabel('What would you like to find?').fill('Who approves lunar research travel and how many days before departure?');
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  await expect(page.getByRole('link', { name: title, exact: true }).first()).toBeVisible({ timeout: 90000 });
  await expect(page.getByRole('link', { name: title, exact: true }).first()).toHaveAttribute('href', /\?version=[a-f0-9-]+&offset=\d+$/);
  await expect(page.getByText(/science director at least 21 days/).first()).toBeVisible();
  await page.screenshot({ path: test.info().outputPath('retrieval-desktop.png'), fullPage: true });
  await page.getByRole('link', { name: title, exact: true }).first().click();
  await expect(page.locator('.source-text')).toContainText('science director at least 21 days');
  await page.goto(detailUrl);
  await page.getByRole('button', { name: 'Withdraw document', exact: true }).click();
  await expect(page.getByText('Withdrawn', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Restore document', exact: true }).click();
  await expect(page.getByText('Ready', { exact: true })).toBeVisible();
  expect(errors).toEqual([]);
});

test('viewer can inspect knowledge without management controls on mobile', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page, 'viewer');
  await expect(page.getByLabel('Knowledge document')).toHaveCount(0);
  await page.locator('.document-row').first().click();
  await expect(page.getByRole('heading', { name: 'Source preview', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Withdraw document', exact: true })).toHaveCount(0);
  await expect(page.getByText('Replace this document', { exact: true })).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: test.info().outputPath('source-mobile.png'), fullPage: true });
});

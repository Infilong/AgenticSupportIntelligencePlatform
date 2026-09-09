import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';

const credentials = JSON.parse(readFileSync('../.artifacts/m1/demo-credentials.json', 'utf8'));
test('keyword and hybrid traces show real ranks and exact source navigation at small widths', async ({ page }) => {
  test.setTimeout(150000);
  const errors: string[] = []; page.on('pageerror', error => errors.push(error.message));
  await page.goto('http://127.0.0.1:5180');
  await page.getByLabel('Email address').fill(credentials.accounts.admin);
  await page.getByLabel('Password', { exact: true }).fill(credentials.password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByRole('link', { name: 'Knowledge', exact: true }).click();
  const identifier = `TRACEQA-${Date.now()}`;
  const title = `${identifier}.txt`;
  await page.getByLabel('Knowledge document').setInputFiles({ name: title, mimeType: 'text/plain', buffer: Buffer.from(`# ${identifier}\n\n${identifier} requires a support ticket within 17 days.\n`) });
  await page.getByRole('button', { name: 'Upload document', exact: true }).click();
  await expect(page.getByRole('heading', { name: title, exact: true })).toBeVisible();
  await expect(page.getByText('Ready', { exact: true })).toBeVisible({ timeout: 90000 });
  await page.getByRole('link', { name: '← Knowledge', exact: true }).click();
  await page.getByRole('link', { name: 'Search knowledge', exact: true }).click();
  await page.getByText('Search method', { exact: true }).click();
  await page.getByLabel('Retrieval strategy').selectOption('bm25');
  await page.getByLabel('What would you like to find?').fill(identifier);
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Relevant passages', exact: true })).toBeVisible();
  await page.getByText('Retrieval evidence', { exact: true }).click();
  await expect(page.locator('.retrieval-trace')).toContainText('bm25-v1');
  await expect(page.locator('.trace-candidates > li').first()).toContainText('Final #1');
  const top = page.locator('.trace-candidates > li').first();
  await expect(top.locator('.trace-scores > div').first()).toContainText('—');
  await top.getByRole('link').click();
  await expect(page.locator('.source-text')).toContainText('17 days');
  await page.goBack();
  await page.getByText('Search method', { exact: true }).click();
  await page.getByLabel('Retrieval strategy').selectOption('hybrid_rerank');
  await page.getByLabel('What would you like to find?').fill(identifier);
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Relevant passages', exact: true })).toBeVisible({ timeout: 90000 });
  await page.getByText('Retrieval evidence', { exact: true }).click();
  await expect(page.locator('.retrieval-trace')).toContainText('hybrid_rerank-v1');
  await expect(page.locator('.retrieval-trace')).toContainText('Final #1');
  for (const width of [1440, 768, 360]) {
    await page.setViewportSize({ width, height: 900 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`trace-${width}.png`), fullPage: true });
  }
  expect(errors).toEqual([]);
});

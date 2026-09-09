import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';

const credentials = JSON.parse(readFileSync(process.env.ASI_DEMO_CREDENTIALS ?? '../.artifacts/m1/demo-credentials.json', 'utf8'));

test('import, inspect, label and explicitly process one customer message', async ({ page }) => {
  test.setTimeout(90000);
  await page.goto(process.env.ASI_APP_BASE_URL ?? 'http://127.0.0.1:5180');
  await page.getByLabel('Email address').fill(credentials.accounts.admin);
  await page.getByLabel('Password', { exact: true }).fill(credentials.password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Workbench', exact: true })).toBeVisible();
  const marker = `import-${Date.now()}`;
  const question = `What is the standard refund deadline? Reference ${marker}`;
  await page.getByRole('button', { name: 'Import', exact: true }).click();
  await page.getByLabel('JSONL file').setInputFiles({ name: 'invalid.jsonl', mimeType: 'application/jsonl', buffer: Buffer.from('{"original":"private","language":"fr"}') });
  await page.getByRole('button', { name: 'Import messages', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Line 1');
  const rows = [{ original: question, language: 'en', labels: [marker] },
    { original: `返金期限はいつですか？ ${marker}`, language: 'ja', labels: [marker] },
    { original: `退款期限是什么？ ${marker}`, language: 'zh', labels: [marker] }];
  await page.getByLabel('JSONL file').setInputFiles({ name: 'customer-demo.jsonl', mimeType: 'application/jsonl', buffer: Buffer.from(rows.map(row => JSON.stringify(row)).join('\n')) });
  await page.getByRole('button', { name: 'Import messages', exact: true }).click();
  await expect(page.getByRole('status')).toContainText('3 messages saved');
  await page.getByRole('button', { name: 'View unprocessed messages' }).click();
  await page.getByLabel('Filter by label').fill(marker);
  await page.getByRole('button', { name: 'Search messages', exact: true }).click();
  await expect(page.locator('.message-table tbody tr')).toHaveCount(3);
  for (const width of [1440, 768, 360]) {
    await page.setViewportSize({ width, height: 950 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`imports-${width}.png`), fullPage: true });
  }
  await page.getByRole('link', { name: question, exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Original message', exact: true })).toBeVisible();
  await expect(page.getByText('This message is saved and has not been processed.')).toBeVisible();
  await page.getByLabel('Labels', { exact: true }).fill(`${marker}, priority`);
  await page.getByRole('button', { name: 'Save labels' }).click();
  await expect(page.getByRole('status')).toHaveText('Labels saved.');
  await page.reload();
  await expect(page.getByLabel('Labels', { exact: true })).toHaveValue(`${marker}, priority`);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: test.info().outputPath('saved-message-360.png'), fullPage: true });
  await page.getByRole('button', { name: 'Start processing', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Selected message' })).toContainText('Waiting for development response', { timeout: 30000 });
  await page.getByRole('tab', { name: 'Workflow', exact: true }).click();
  await expect(page.getByText('Retrieve evidence', { exact: true }).first()).toBeVisible();
  await page.getByRole('link', { name: '← All messages' }).click();
  await expect(page.getByLabel('Message view')).toHaveValue('unprocessed');
  await expect(page.getByLabel('Filter by label')).toHaveValue(marker);
  await expect(page.locator('.message-table tbody tr')).toHaveCount(2);
});

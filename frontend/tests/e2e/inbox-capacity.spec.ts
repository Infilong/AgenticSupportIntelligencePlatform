import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';

const base = process.env.ASI_CAPACITY_WEB_URL;
test('50k real database inbox stays bounded through deep pages, filters and detail return', async ({ page }) => {
  test.skip(!base, 'Run manage.py verify-inbox-capacity to start the isolated real API and seed 50k rows.');
  test.setTimeout(90000);
  const credentials = JSON.parse(readFileSync(process.env.ASI_CAPACITY_CREDENTIALS!, 'utf8'));
  await page.goto(base!);
  await page.getByLabel('Email address').fill(credentials.email);
  await page.getByLabel('Password', { exact: true }).fill(credentials.password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.locator('.message-count')).toHaveText('50,000 messages');
  await expect(page.locator('.message-table tbody tr')).toHaveCount(20);
  await page.getByRole('button', { name: 'Last', exact: true }).click();
  await expect(page.getByLabel('Page', { exact: true })).toHaveValue('2500');
  await expect(page.locator('.message-table tbody tr')).toHaveCount(20);
  const selected = page.locator('.message-table tbody a').first();
  const original = await selected.innerText();
  await selected.click();
  await expect(page.getByRole('heading', { name: 'Original message', exact: true })).toBeVisible();
  await expect(page.locator('.original-message').first()).toHaveText(original);
  await expect(page.locator('.message-table')).toHaveCount(0);
  await page.getByRole('link', { name: '← All messages', exact: true }).click();
  await expect(page.getByLabel('Page', { exact: true })).toHaveValue('2500');
  await page.getByLabel('Rows per page').selectOption('50');
  await expect(page.getByLabel('Page', { exact: true })).toHaveValue('1');
  await expect(page.locator('.message-table tbody tr')).toHaveCount(50);
  await page.getByRole('textbox', { name: 'Search messages', exact: true }).fill('返金');
  await page.getByRole('button', { name: 'Search messages', exact: true }).click();
  await expect(page.locator('.message-count')).toContainText('16,667 messages');
  await page.getByLabel('Message view').selectOption('ready');
  await expect(page.locator('.message-table tbody tr').first()).toContainText('Approved response');
  for (const width of [1440, 768, 360]) {
    await page.setViewportSize({ width, height: 900 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await expect(page.locator('.message-table tbody tr')).toHaveCount(50);
    await page.screenshot({ path: test.info().outputPath(`capacity-${width}.png`), fullPage: true });
  }
  await page.getByRole('button', { name: 'Clear filters', exact: true }).click();
  await page.getByRole('textbox', { name: 'Search messages', exact: true }).fill('FOREIGN');
  await page.getByRole('button', { name: 'Search messages', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'No matching messages', exact: true })).toBeVisible();
  await page.goto(`${base}/w/${process.env.ASI_CAPACITY_WORKSPACE}?compose=1`);
  await expect(page.getByRole('button', { name: 'Start processing', exact: true })).toHaveCount(0);
  await expect(page.locator('.message-count')).toHaveText('50,000 messages');
  await page.goto(`${base}/w/${process.env.ASI_CAPACITY_FOREIGN}`);
  await expect(page.getByRole('heading', { name: 'Workspace unavailable', exact: true })).toBeVisible();
});

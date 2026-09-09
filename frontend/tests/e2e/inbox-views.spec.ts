import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';

const credentials = JSON.parse(readFileSync(process.env.ASI_DEMO_CREDENTIALS ?? '../.artifacts/m1/demo-credentials.json', 'utf8'));

test('inbox views preserve filters across full-width detail and responsive table navigation', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(process.env.ASI_APP_BASE_URL ?? 'http://127.0.0.1:5180');
  await page.getByLabel('Email address').fill(credentials.accounts.admin);
  await page.getByLabel('Password', { exact: true }).fill(credentials.password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Workbench', exact: true })).toBeVisible();
  const marker = `Inbox-view-${Date.now()}`;
  const original = `What is the standard refund deadline? Reference ${marker}`;
  await page.getByRole('button', { name: 'New message', exact: true }).click();
  await page.getByLabel('Customer message', { exact: true }).fill(original);
  await page.getByRole('button', { name: 'Start processing', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Selected message' })).toContainText('Waiting for development response', { timeout: 30000 });
  await page.getByRole('link', { name: '← All messages' }).click();
  await page.getByRole('textbox', { name: 'Search messages', exact: true }).fill(marker);
  await page.getByRole('button', { name: 'Search messages', exact: true }).click();
  await page.getByLabel('Message view').selectOption('attention');
  await expect(page.locator('.message-table tbody tr')).toHaveCount(1);
  await expect(page.locator('.message-table tbody tr')).toContainText(original);
  await expect(page.locator('.message-count')).toContainText('1 messages');
  await page.getByLabel('Message view').selectOption('ready');
  await expect(page.getByRole('heading', { name: 'No matching messages' })).toBeVisible();
  await expect(page.getByRole('region', { name: 'Selected message' })).toHaveCount(0);
  await page.getByRole('button', { name: 'Clear filters' }).click();
  await expect(page.getByLabel('Message view')).toHaveValue('all');
  await expect(page.getByRole('textbox', { name: 'Search messages', exact: true })).toHaveValue('');
  await expect(page.locator('.message-table tbody tr').first()).toBeVisible();
  const results = page.getByRole('region', { name: 'Message results', exact: true });
  await results.focus();
  await page.keyboard.press('End');
  await expect(results).toBeFocused();
  await expect(page.locator('.message-table tbody tr')).toHaveCount(20);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: test.info().outputPath('inbox-1440.png'), fullPage: true });
  for (const width of [768, 360]) {
    await page.setViewportSize({ width, height: 900 });

    await page.getByLabel('Message view').selectOption('attention');
    await page.getByRole('textbox', { name: 'Search messages', exact: true }).fill(marker);
    await page.getByRole('button', { name: 'Search messages', exact: true }).click();
    await expect(page.locator('.message-table tbody tr')).toHaveCount(1);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`inbox-${width}.png`), fullPage: true });
    await page.getByRole('link', { name: original, exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Original message', exact: true })).toBeVisible();
    await page.getByRole('link', { name: '← All messages' }).click();
    await expect(page.getByLabel('Message view')).toHaveValue('attention');
    await expect(page.getByRole('textbox', { name: 'Search messages', exact: true })).toHaveValue(marker);
  }
});

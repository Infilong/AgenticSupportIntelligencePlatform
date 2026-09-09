import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';

const credentials = JSON.parse(readFileSync('../.artifacts/m1/demo-credentials.json', 'utf8'));

test('admin settings persist and usage remains readable at three widths', async ({ page }) => {
  test.setTimeout(60000);
  await page.goto('http://127.0.0.1:5180');
  await page.getByLabel('Email address').fill(credentials.accounts.admin);
  await page.getByLabel('Password', { exact: true }).fill(credentials.password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByRole('link', { name: 'Settings', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'AI configuration' })).toBeVisible();
  await expect(page.getByText('Not configured', { exact: true })).toBeVisible();
  const original = await page.getByLabel('Default response language').inputValue();
  const next = original === 'ja' ? 'zh' : 'ja';
  await page.getByLabel('Default response language').selectOption(next);
  const saved = page.waitForResponse(response => response.url().endsWith('/settings') && response.request().method() === 'PUT');
  await page.getByRole('button', { name: 'Save defaults' }).click();
  expect((await saved).status()).toBe(200);
  await expect(page.getByLabel('Default response language')).toHaveValue(next);
  await page.reload();
  await expect(page.getByLabel('Default response language')).toHaveValue(next);
  await page.getByRole('link', { name: 'Workbench', exact: true }).click();
  await page.getByRole('button', { name: 'New message', exact: true }).click();
  await expect(page.getByLabel('Response language')).toHaveValue(next);
  await page.getByRole('button', { name: 'Cancel', exact: true }).click();
  await page.getByRole('link', { name: 'Settings', exact: true }).click();
  await page.getByLabel('Default response language').selectOption(original);
  const restored = page.waitForResponse(response => response.url().endsWith('/settings') && response.request().method() === 'PUT');
  await page.getByRole('button', { name: 'Save defaults' }).click();
  expect((await restored).status()).toBe(200);
  await page.reload();
  await expect(page.getByLabel('Default response language')).toHaveValue(original);
  for (const width of [1440, 768, 360]) {
    await page.setViewportSize({ width, height: 1000 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`settings-${width}.png`), fullPage: true });
    await page.getByRole('link', { name: 'Quality', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Recorded calls', exact: true })).toBeVisible();
    await expect(page.getByText('Development handoffs are not automatic model calls.', { exact: false })).toBeVisible();
    await page.getByLabel('Period').selectOption('30');
    await expect(page.getByRole('region', { name: 'Model usage results' })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`usage-${width}.png`), fullPage: true });
    await page.getByRole('link', { name: 'Settings', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'AI configuration' })).toBeVisible();
  }
});

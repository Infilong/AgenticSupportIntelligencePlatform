import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';

const credentials = JSON.parse(readFileSync('../.artifacts/m1/demo-credentials.json', 'utf8'));
test('workflow shows skipped, waiting and cancelled execution with real model records', async ({ page }) => {
  test.setTimeout(120000);
  await page.goto('http://127.0.0.1:5180');
  await page.getByLabel('Email address').fill(credentials.accounts.operator);
  await page.getByLabel('Password', { exact: true }).fill(credentials.password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Workbench', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'New message', exact: true }).click();
  await page.getByLabel('Customer message', { exact: true }).fill('w');
  await page.getByRole('button', { name: 'Start processing', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Clarification needed', exact: true })).toBeVisible({ timeout: 30000 });
  await page.getByRole('tab', { name: 'Workflow', exact: true }).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('button', { name: /2 Retrieve evidence Skipped by outcome/ })).toBeVisible();
  await page.getByRole('button', { name: 'New message', exact: true }).click();
  await page.getByLabel('Customer message', { exact: true }).fill('What is the standard refund request deadline?');
  await page.getByRole('button', { name: 'Start processing', exact: true }).click();
  await expect(page.locator('.run-heading').getByRole('status')).toHaveText('Waiting for development response', { timeout: 90000 });
  await page.getByRole('tab', { name: 'Workflow', exact: true }).click();
  await expect(page.getByRole('button', { name: /3 Prepare response Paused/ })).toBeVisible();
  await page.getByRole('button', { name: /2 Retrieve evidence Completed/ }).click();
  await expect(page.getByRole('region', { name: 'Retrieve evidence details' })).toContainText('intfloat/multilingual-e5-small');
  await expect(page.getByRole('region', { name: 'Retrieve evidence details' })).toContainText('cross-encoder/mmarco-mMiniLMv2-L12-H384-v1');
  await page.getByText('Retrieval evidence', { exact: true }).click();
  await expect(page.locator('.trace-candidates > li').first()).toBeVisible();
  await expect(page.locator('.retrieval-trace')).toContainText('cosine20-mmarco-rerank-v2');
  await expect(page.locator('.retrieval-trace')).toContainText('Final #1');
  await expect(page.locator('.trace-candidates > li')).toHaveCount(5);
  await page.getByRole('button', { name: /Show all \d+ candidates/ }).click();
  expect(await page.locator('.trace-candidates > li').count()).toBeGreaterThan(5);
  await page.getByRole('button', { name: 'Show fewer candidates', exact: true }).click();
  await expect(page.locator('.trace-candidates > li')).toHaveCount(5);
  for (const width of [1440, 768, 360]) {
    await page.setViewportSize({ width, height: 900 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`workflow-${width}.png`), fullPage: true });
  }
  await page.getByRole('button', { name: 'Cancel processing', exact: true }).click();
  await expect(page.locator('.run-heading').getByRole('status')).toHaveText('Cancelled');
  await expect(page.getByRole('button', { name: /3 Prepare response Paused before stop/ })).toBeVisible();
  await expect(page.getByRole('button', { name: /4 Human review Not reached/ })).toBeVisible();
  await expect(page.getByRole('button', { name: /Running/ })).toHaveCount(0);
});

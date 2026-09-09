import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';

const credentials = JSON.parse(readFileSync('../.artifacts/m1/demo-credentials.json', 'utf8'));
const report = JSON.parse(readFileSync(process.env.ASI_EVALUATION_REPORT ?? '../.artifacts/m2/strategy-comparison-20260909T083207Z/report.json', 'utf8'));
const workspace = report.workspaces.primary;

test('real historical comparison, failure trace, responsive layout and workspace switch', async ({ page }) => {
  test.setTimeout(60000);
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('http://127.0.0.1:5180');
  await page.getByLabel('Email address').fill(credentials.accounts.admin);
  await page.getByLabel('Password', { exact: true }).fill(credentials.password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByLabel('Workspace', { exact: true })).toBeVisible();
  await page.getByLabel('Workspace', { exact: true }).selectOption(workspace);
  await page.getByRole('link', { name: 'Quality', exact: true }).click();
  await page.getByRole('button', { name: 'Retrieval checks', exact: true }).click();
  const comparison = page.getByRole('region', { name: 'Retrieval strategy comparison' });
  await expect(comparison).toBeVisible();
  await expect(comparison.getByText('26 / 26', { exact: true })).toBeVisible();
  await expect(page.getByText('No cases match these filters.')).toBeVisible();
  await page.setViewportSize({ width: 1440, height: 1000 });
  await expect(page.locator('.quality-views')).toHaveCSS('flex-direction', 'row');
  await page.screenshot({ path: test.info().outputPath('evaluation-overview.png'), fullPage: true });
  await page.getByRole('button', { name: 'Hybrid + reranker', exact: true }).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('heading', { name: 'Hybrid + reranker details' })).toBeVisible();
  await page.getByText('ja02 · JA · Failed', { exact: true }).click();
  await page.getByText('Retrieval evidence', { exact: true }).click();
  await expect(page.getByText(/recorded candidates/)).toBeVisible();
  await expect(page.locator('.trace-candidates a').first()).toBeVisible();
  await page.getByText('Measurement provenance and limits', { exact: true }).click();
  await expect(page.getByText(report.source_state.source_sha256, { exact: true })).toBeVisible();
  for (const width of [1440, 768, 360]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.evaluate(() => window.scrollTo(0, 0));
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`evaluations-${width}.png`), fullPage: true });
  }
  await page.getByLabel('Case outcome').selectOption('excluded');
  await expect(page.getByText(/4 matching cases/)).toBeVisible();
  await page.getByLabel('Case language').selectOption('ja');
  await expect(page.getByText(/1 matching cases/)).toBeVisible();
  const options = await page.getByLabel('Workspace', { exact: true }).locator('option').evaluateAll(items => items.map(option => (option as HTMLOptionElement).value));
  let other: string | undefined;
  for (const candidate of options.filter(value => value !== workspace)) {
    const response = await page.request.get(`http://127.0.0.1:5180/api/workspaces/${candidate}/evaluations`);
    expect(response.status()).toBe(200);
    if (!(await response.json()).items.length) { other = candidate; break; }
  }
  expect(other, 'An authorized empty workspace is required for the switch check').toBeTruthy();
  await page.getByLabel('Workspace', { exact: true }).selectOption(other!);
  await page.getByRole('link', { name: 'Quality', exact: true }).click();
  await page.getByRole('button', { name: 'Retrieval checks', exact: true }).click();
  await expect(page.getByText('No registered results')).toBeVisible();
  await expect(comparison).toHaveCount(0);
  expect(errors).toEqual([]);
});

test('history outage can retry and foreign account cannot read the registered report', async ({ page }) => {
  await page.goto('http://127.0.0.1:5180');
  await page.getByLabel('Email address').fill(credentials.accounts.admin);
  await page.getByLabel('Password', { exact: true }).fill(credentials.password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByLabel('Workspace', { exact: true })).toBeVisible();
  await page.getByLabel('Workspace', { exact: true }).selectOption(workspace);
  await page.getByRole('link', { name: 'Quality', exact: true }).click();
  const route = `**/api/workspaces/${workspace}/evaluations?page=1`;
  await page.route(route, intercepted => intercepted.fulfill({ status: 503, json: { detail: 'Synthetic evaluation outage' } }));
  await page.getByRole('button', { name: 'Retrieval checks', exact: true }).click();
  await expect(page.getByRole('alert')).toHaveText('Synthetic evaluation outage');
  await page.unroute(route);
  await page.getByRole('button', { name: 'Retry evaluations' }).click();
  await expect(page.getByRole('region', { name: 'Retrieval strategy comparison' })).toBeVisible();
  const list = await page.request.get(`http://127.0.0.1:5180/api/workspaces/${workspace}/evaluations`);
  const recordId = (await list.json()).items[0].id;
  await page.getByRole('button', { name: 'Sign out' }).click();
  await page.getByLabel('Email address').fill(credentials.accounts.private);
  await page.getByLabel('Password', { exact: true }).fill(credentials.password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Workspace unavailable' })).toBeVisible();
  await page.getByRole('button', { name: 'Back to my workspace' }).click();
  await expect(page.getByLabel('Workspace', { exact: true })).toBeVisible();
  expect((await page.request.get(`http://127.0.0.1:5180/api/workspaces/${workspace}/evaluations/${recordId}`)).status()).toBe(404);
  await page.goto(`http://127.0.0.1:5180/w/${workspace}/quality`);
  await expect(page.getByRole('alert')).toBeVisible();
  await expect(page.getByRole('region', { name: 'Retrieval strategy comparison' })).toHaveCount(0);
});

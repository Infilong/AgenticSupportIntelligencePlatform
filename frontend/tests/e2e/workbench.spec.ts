import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';

const credentials = JSON.parse(readFileSync('../.artifacts/m1/demo-credentials.json', 'utf8'));
const base = 'http://127.0.0.1:5180';
async function login(page: Page, role = 'admin') {
  await page.goto(base);
  await page.getByLabel('Email address').fill(credentials.accounts[role]);
  await page.getByLabel('Password', { exact: true }).fill(credentials.password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Workbench', exact: true })).toBeVisible();
}
async function create(page: Page, original: string, language = 'en') {
  await page.getByRole('button', { name: 'New message', exact: true }).click();
  await page.getByLabel('Customer message', { exact: true }).fill(original);
  await page.getByLabel('Response language').selectOption(language);
  await page.getByRole('button', { name: 'Start processing', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Original message', exact: true })).toBeVisible();
}

for (const [language, question, answer] of [
  ['en', 'What is the standard refund request deadline?', 'The standard refund request window is 14 calendar days after the initial annual subscription purchase.'],
  ['ja', '通常の返金申請の期限はいつですか？', '年間サブスクリプションの初回購入から14暦日以内です。'],
  ['zh', '标准退款申请的期限是什么？', '标准退款申请期限是年度订阅首次购买后的14个日历日内。'],
]) {
  test(`${language}: real retrieval to development draft and exact source`, async ({ page }) => {
    test.setTimeout(120000);
    await login(page); await create(page, question, language);
    await expect(page.locator('.run-heading').getByRole('status')).toHaveText('Waiting for development response', { timeout: 90000 });
    await page.getByText('Development response controls', { exact: true }).click();
    const source = page.getByLabel('Supporting passage', { exact: true });
    await expect(source.locator('option').filter({ hasText: 'REFUND-STANDARD' }).first()).toBeAttached();
    const value = await source.locator('option').filter({ hasText: 'REFUND-STANDARD' }).first().getAttribute('value');
    await source.selectOption(value!);
    const quote = await page.locator('.development-form .source-excerpt').innerText();
    expect(quote).toContain('14 calendar days');
    await page.getByLabel('Exact supporting quote').fill(quote);
    // Explicit deterministic development contribution; the retrieval and application are real.
    await page.getByLabel('Development answer', { exact: true }).fill(answer);
    if (language === 'en') {
      await page.route('**/api/workspaces/*/runs/*', route => route.request().method() === 'GET' && !route.request().url().endsWith('development-handoff') ? route.fulfill({ status: 503, json: { detail: 'Injected poll outage' } }) : route.continue());
      await expect(page.getByRole('alert')).toContainText('Injected poll outage', { timeout: 10000 });
      await expect(page.getByLabel('Development answer', { exact: true })).toHaveValue(answer);
      await page.unroute('**/api/workspaces/*/runs/*');
    }
    await page.getByRole('button', { name: 'Submit development draft', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Response draft', exact: true })).toBeVisible({ timeout: 20000 });
    await expect(page.locator('.response-text')).toHaveText(answer);
    await expect(page.locator('.response-text')).toHaveAttribute('lang', language);
    await page.getByRole('button', { name: '1 REFUND-STANDARD', exact: true }).click();
    await expect(page.getByRole('complementary', { name: 'Source excerpt' })).toContainText(quote);
    await page.getByText('Processing details', { exact: true }).click();
    await expect(page.getByText('intfloat/multilingual-e5-small', { exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`draft-${language}.png`), fullPage: true });
    await page.getByRole('link', { name: 'Open exact document version' }).click();
    await expect(page.locator('.source-text')).toContainText('14 calendar days');
  });
}

test('short input requests clarification and waiting run can be cancelled', async ({ page }) => {
  test.setTimeout(120000); await login(page, 'operator');
  await create(page, 'w');
  await expect(page.locator('.run-heading').getByRole('status')).toHaveText('Clarification needed', { timeout: 15000 });
  await expect(page.getByText('Development response controls', { exact: true })).toHaveCount(0);
  await create(page, 'What is the standard refund request deadline?');
  await expect(page.locator('.run-heading').getByRole('status')).toHaveText('Waiting for development response', { timeout: 90000 });
  await expect(page.getByText('Development response controls', { exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Cancel processing', exact: true }).click();
  await expect(page.locator('.run-heading').getByRole('status')).toHaveText('Cancelled');
});

test('viewer inspection stays usable at 360, 768, 1440 and doubled content size', async ({ page }) => {
  await login(page, 'viewer');
  await expect(page.getByRole('button', { name: 'New message', exact: true })).toHaveCount(0);
  for (const width of [360, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await page.locator('.message-row').filter({ hasText: 'Draft ready' }).first().click();
    await expect(page.getByRole('heading', { name: 'Original message', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Cancel processing', exact: true })).toHaveCount(0);
    const citation = page.getByRole('button', { name: '1 REFUND-STANDARD', exact: true });
    await citation.focus(); await page.keyboard.press('Enter');
    await expect(page.getByRole('complementary', { name: 'Source excerpt' })).toBeFocused();
    await page.getByRole('button', { name: 'Close source' }).click();
    await expect(citation).toBeFocused();
    await citation.click();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`viewer-${width}.png`), fullPage: true });
    await page.getByRole('link', { name: '← All messages', exact: true }).click();
  }
  await page.evaluate(() => { document.documentElement.style.zoom = '2'; });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: test.info().outputPath('viewer-content-zoom.png'), fullPage: true });
});

test('leaving a pending submission does not navigate back on a late response', async ({ page }) => {
  await login(page);
  let release!: () => void;
  const gate = new Promise<void>(resolve => { release = resolve; });
  await page.route('**/api/workspaces/*/messages', async route => {
    if (route.request().method() !== 'POST') return route.continue();
    const response = await route.fetch(); await gate;
    await route.fulfill({ response }).catch(() => {}); // Navigation may abort the client, not the stored message.
  });
  await page.getByRole('button', { name: 'New message', exact: true }).click();
  await page.getByLabel('Customer message', { exact: true }).fill('w');
  const posted = page.waitForRequest(request => request.method() === 'POST' && request.url().endsWith('/messages'));
  await page.getByRole('button', { name: 'Start processing', exact: true }).click(); await posted;
  await page.getByRole('link', { name: 'Knowledge', exact: true }).click(); release();
  await expect(page.getByRole('heading', { name: 'Knowledge', exact: true })).toBeVisible();
  await expect(page).toHaveURL(/\/knowledge$/);
});

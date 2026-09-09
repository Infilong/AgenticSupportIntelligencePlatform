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
    if (language === 'ja') {
      await page.getByLabel('Decision', { exact: true }).selectOption('edit');
      await expect(page.getByLabel('Approved wording')).toHaveValue(answer);
      await page.getByLabel('Approved wording').fill(answer + ' 確認中。');
      await page.waitForResponse(response => response.request().method() === 'GET' && response.url().endsWith(page.url().split('/runs/')[1]) && response.ok());
      await expect(page.getByLabel('Approved wording')).toHaveValue(answer + ' 確認中。');
    }
    await page.getByRole('button', { name: '1 REFUND-STANDARD', exact: true }).click();
    await expect(page.getByRole('complementary', { name: 'Source excerpt' })).toContainText(quote);
    await page.getByText('Processing details', { exact: true }).click();
    await expect(page.getByText('intfloat/multilingual-e5-small', { exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: test.info().outputPath(`draft-${language}.png`), fullPage: true });
    const runUrl = page.url();
    await page.getByRole('link', { name: 'Open exact document version' }).click();
    await expect(page.locator('.source-text')).toContainText('14 calendar days');
    await page.goto(runUrl);
    if (language === 'en') {
      await page.getByRole('button', { name: 'Sign out', exact: true }).click();
      await login(page, 'operator'); await page.goto(runUrl);
    }
    const action = language === 'en' ? 'approve' : language === 'ja' ? 'edit' : 'reject';
    await page.getByLabel('Decision', { exact: true }).selectOption(action);
    const revised = answer + ' 対象となる条件もポリシーで確認してください。';
    if (action === 'edit') await page.getByLabel('Approved wording').fill(revised);
    await page.getByLabel('Reason for your decision').fill('Checked the policy source and preserved the original draft.');
    await page.getByRole('button', { name: action === 'reject' ? 'Reject response' : 'Approve response', exact: true }).click();
    await expect(page.locator('.run-heading').getByRole('status')).toHaveText(action === 'reject' ? 'Rejected' : 'Completed', { timeout: 20000 });
    if (action !== 'reject') {
      await expect(page.locator('.run-result > .response-text')).toHaveText(action === 'edit' ? revised : answer);
      await page.getByText('Original development draft', { exact: true }).click();
      await expect(page.locator('.run-result details .response-text')).toHaveText(answer);
    }
    await page.getByText(`Review decision · ${action}`, { exact: true }).click();
    await expect(page.locator('.review-history')).toContainText('Checked the policy source');
    await page.screenshot({ path: test.info().outputPath(`review-${language}.png`), fullPage: true });
  });
}

test('short input requests clarification and waiting run can be cancelled', async ({ page }) => {
  test.setTimeout(120000); await login(page, 'operator');
  await create(page, 'w');
  await expect(page.locator('.run-heading').getByRole('status')).toHaveText('Completed', { timeout: 15000 });
  await expect(page.getByRole('heading', { name: 'Clarification needed', exact: true })).toBeVisible();
  await expect(page.getByText('Development response controls', { exact: true })).toHaveCount(0);
  await create(page, 'What is the standard refund request deadline?');
  await expect(page.locator('.run-heading').getByRole('status')).toHaveText('Waiting for development response', { timeout: 90000 });
  await expect(page.getByText('Development response controls', { exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Cancel processing', exact: true }).click();
  await expect(page.locator('.run-heading').getByRole('status')).toHaveText('Cancelled');
});

test('viewer inspection stays usable at 360, 768, 1440 and doubled content size', async ({ page }) => {
  test.setTimeout(120000);
  await login(page); await create(page, 'What is the standard refund request deadline?');
  await expect(page.locator('.run-heading').getByRole('status')).toHaveText('Waiting for development response', { timeout: 90000 });
  await page.getByText('Development response controls', { exact: true }).click();
  const source = page.getByLabel('Supporting passage', { exact: true });
  const option = source.locator('option').filter({ hasText: 'REFUND-STANDARD' }).first();
  await expect(option).toBeAttached();
  await source.selectOption((await option.getAttribute('value'))!);
  await page.getByLabel('Exact supporting quote').fill(await page.locator('.development-form .source-excerpt').innerText());
  await page.getByLabel('Development answer', { exact: true }).fill('The standard refund request window is 14 calendar days.');
  await page.getByRole('button', { name: 'Submit development draft', exact: true }).click();
  await expect(page.locator('.run-heading').getByRole('status')).toHaveText('Needs review', { timeout: 20000 });
  const runUrl = page.url();
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await login(page, 'viewer');
  await expect(page.getByRole('button', { name: 'New message', exact: true })).toHaveCount(0);
  for (const width of [360, 768, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto(runUrl);
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

test('policy exception approval is restricted to administrators in the review UI', async ({ page }) => {
  test.setTimeout(120000);
  await login(page); await create(page, 'What is the standard refund request deadline?');
  await expect(page.locator('.run-heading').getByRole('status')).toHaveText('Waiting for development response', { timeout: 90000 });
  await page.getByText('Development response controls', { exact: true }).click();
  const source = page.getByLabel('Supporting passage', { exact: true });
  const option = source.locator('option').filter({ hasText: 'REFUND-STANDARD' }).first();
  await expect(option).toBeAttached();
  await source.selectOption((await option.getAttribute('value'))!);
  await page.getByLabel('Exact supporting quote').fill(await page.locator('.development-form .source-excerpt').innerText());
  await page.getByLabel('Development answer', { exact: true }).fill('The standard request window is 14 calendar days. This development routing test requires administrator review.');
  await page.getByLabel('Review category', { exact: true }).selectOption('policy_exception');
  await page.getByRole('button', { name: 'Submit development draft', exact: true }).click();
  await expect(page.locator('.run-heading').getByRole('status')).toHaveText('Needs review', { timeout: 20000 });
  const runUrl = page.url();
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await login(page, 'operator'); await page.goto(runUrl);
  await expect(page.getByLabel('Decision', { exact: true })).toHaveValue('reject');
  await expect(page.getByRole('button', { name: 'Approve response', exact: true })).toHaveCount(0);
  await expect(page.locator('.review-panel')).toContainText('Administrator approval is required');
  await page.setViewportSize({ width: 360, height: 900 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: test.info().outputPath('operator-exception-360.png'), fullPage: true });
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await login(page); await page.goto(runUrl);
  await page.getByLabel('Reason for your decision').fill('Administrator checked this explicit development routing test.');
  await page.getByRole('button', { name: 'Approve response', exact: true }).click();
  await expect(page.locator('.run-heading').getByRole('status')).toHaveText('Completed', { timeout: 20000 });
  await expect(page.getByRole('heading', { name: 'Approved response', exact: true })).toBeVisible();
});

test('clarification, cancellation and retry preserve the original and linked attempt history', async ({ page }) => {
  test.setTimeout(120000);
  await login(page, 'operator'); await create(page, 'w');
  await expect(page.getByRole('heading', { name: 'Clarification needed', exact: true })).toBeVisible({ timeout: 15000 });
  const originalUrl = page.url();
  await page.getByText('Add customer details', { exact: true }).click();
  await page.getByLabel('Additional customer details').fill('What is the standard refund request deadline?');
  await page.getByRole('button', { name: 'Process with added details', exact: true }).click();
  await expect(page).not.toHaveURL(originalUrl);
  await expect(page.locator('.run-heading').getByRole('status')).toHaveText('Waiting for development response', { timeout: 90000 });
  await expect(page.locator('.original-message').first()).toHaveText('w');
  await page.getByText('Processing input · attempt 2', { exact: true }).click();
  await expect(page.locator('.original-message').nth(1)).toContainText('What is the standard refund request deadline?');
  const secondUrl = page.url();
  await page.getByRole('button', { name: 'Cancel processing', exact: true }).click();
  await expect(page.locator('.run-heading').getByRole('status')).toHaveText('Cancelled');
  await page.getByRole('button', { name: 'Retry processing', exact: true }).click();
  await expect(page).not.toHaveURL(secondUrl);
  await expect(page.locator('.run-heading').getByRole('status')).toHaveText('Waiting for development response', { timeout: 90000 });
  const latestUrl = page.url();
  await page.getByText('Attempt history · 3', { exact: true }).click();
  await expect(page.getByRole('link', { name: 'Attempt 2 · Added details', exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Attempt 1 · Original', exact: true }).click();
  await expect(page).toHaveURL(originalUrl);
  await expect(page.getByRole('heading', { name: 'Clarification needed', exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Open latest attempt', exact: true }).click();
  await expect(page).toHaveURL(latestUrl);
  await page.setViewportSize({ width: 360, height: 900 });
  await page.getByText('Attempt history · 3', { exact: true }).click();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: test.info().outputPath('linked-attempt-history-360.png'), fullPage: true });
  await page.getByRole('button', { name: 'Sign out', exact: true }).click();
  await login(page, 'viewer'); await page.goto(latestUrl);
  await expect(page.getByText('Attempt history · 3', { exact: true })).toBeVisible();
  await expect(page.getByText('Add customer details', { exact: true })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Retry processing', exact: true })).toHaveCount(0);
});

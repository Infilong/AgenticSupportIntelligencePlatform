import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';

const credentials = JSON.parse(readFileSync(process.env.ASI_DEMO_CREDENTIALS ?? '../.artifacts/m1/demo-credentials.json', 'utf8'));

async function saveDefaults(page: Page) {
  const [response, click] = await Promise.allSettled([
    page.waitForResponse(result => result.url().endsWith('/settings') && result.request().method() === 'PUT', { timeout: 10000 }),
    page.getByRole('button', { name: 'Save defaults' }).click({ timeout: 10000 }),
  ]);
  const errors = [response, click].flatMap(result => result.status === 'rejected' ? [result.reason] : []);
  if (errors.length) throw new AggregateError(errors, 'Saving settings failed');
  if (response.status === 'fulfilled') expect(response.value.status()).toBe(200);
}

async function preserveLanguage(page: Page, original: string, flow: () => Promise<void>) {
  const location = new URL(page.url());
  const workspace = location.pathname.split('/')[2];
  const url = `${location.origin}/api/workspaces/${workspace}/settings`;
  let failed = false, failure: unknown;
  try { await flow(); } catch (error) { failed = true; failure = error; }
  try {
    const current = await page.request.get(url);
    expect(current.status()).toBe(200);
    if ((await current.json()).default_language !== original) {
      const session = await page.request.get(`${location.origin}/api/session`);
      expect(session.status()).toBe(200);
      const restored = await page.request.put(url, { data: { default_language: original },
        headers: { Origin: location.origin, 'X-CSRF-Token': (await session.json()).csrf_token } });
      expect(restored.status()).toBe(200);
      expect((await restored.json()).default_language).toBe(original);
    }
  } catch (cleanupError) {
    if (failed) throw new AggregateError([failure, cleanupError], 'Settings flow and cleanup failed');
    throw cleanupError;
  }
  if (failed) throw failure;
}

test('admin settings persist and usage remains readable at three widths', async ({ page }) => {
  test.setTimeout(60000);
  await page.goto(process.env.ASI_APP_BASE_URL ?? 'http://127.0.0.1:5180');
  await page.getByLabel('Email address').fill(credentials.accounts.admin);
  await page.getByLabel('Password', { exact: true }).fill(credentials.password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByRole('link', { name: 'Settings', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'AI configuration' })).toBeVisible();
  const settingsUrl = new URL(page.url());
  const settings = await page.request.get(`${settingsUrl.origin}/api/workspaces/${settingsUrl.pathname.split('/')[2]}/settings`);
  expect(settings.status()).toBe(200);
  const configuration = await settings.json();
  await expect(page.getByText(configuration.automatic_generation_available ? 'Available' : 'Not configured', { exact: true })).toBeVisible();
  const original = await page.getByLabel('Default response language').inputValue();
  await preserveLanguage(page, original, async () => {
    const next = original === 'ja' ? 'zh' : 'ja';
    await page.getByLabel('Default response language').selectOption(next);
    await saveDefaults(page);
    await expect(page.getByLabel('Default response language')).toHaveValue(next);
    await page.reload();
    await expect(page.getByLabel('Default response language')).toHaveValue(next);
    await page.getByRole('link', { name: 'Workbench', exact: true }).click();
    await page.getByRole('button', { name: 'New message', exact: true }).click();
    await expect(page.getByLabel('Response language')).toHaveValue('auto');
    await page.getByLabel('Customer message', { exact: true }).fill('。');
    await page.getByRole('button', { name: 'Start processing', exact: true }).click();
    await expect(page).toHaveURL(/\/runs\/[a-f0-9-]+$/);
    const runPath = new URL(page.url()).pathname.replace('/w/', '/api/workspaces/');
    const run = await page.request.get(`${settingsUrl.origin}${runPath}`);
    expect(run.status()).toBe(200);
    expect((await run.json()).language).toBe(next);
    await page.getByRole('link', { name: 'Settings', exact: true }).click();
    await page.getByLabel('Default response language').selectOption(original);
    await saveDefaults(page);
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
});

test('settings fixture restores the original language after a flow failure', async ({ page }) => {
  await page.goto(process.env.ASI_APP_BASE_URL ?? 'http://127.0.0.1:5180');
  await page.getByLabel('Email address').fill(credentials.accounts.admin);
  await page.getByLabel('Password', { exact: true }).fill(credentials.password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByRole('link', { name: 'Settings', exact: true }).click();
  const original = await page.getByLabel('Default response language').inputValue();
  await expect(preserveLanguage(page, original, async () => {
    await page.getByLabel('Default response language').selectOption(original === 'ja' ? 'zh' : 'ja');
    await saveDefaults(page);
    throw new Error('Injected post-save flow failure');
  })).rejects.toThrow('Injected post-save flow failure');
  await page.reload();
  await expect(page.getByLabel('Default response language')).toHaveValue(original);
});

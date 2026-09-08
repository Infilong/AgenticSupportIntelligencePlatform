import { expect, test } from '@playwright/test';

test('M0: Chromium launches and supports multilingual rendering and keyboard interaction', async ({ page }, testInfo) => {
  // Environment probe only. This cannot satisfy application UX, auth or RAG acceptance.
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.setContent(`<!doctype html><html lang="en"><meta charset="utf-8">
    <title>M0 browser readiness</title><main>
    <h1>Browser environment probe</h1><p>Environment verification only — no application is running.</p>
    <label for="message">Customer message / お問い合わせ / 客户消息</label>
    <textarea id="message"></textarea><button type="button">Inspect input</button>
    <output aria-label="Input preview"></output></main>
    <script>document.querySelector('button').onclick = () => {
      document.querySelector('output').textContent = document.querySelector('textarea').value;
    };</script></html>`);
  await page.getByRole('textbox').fill('Refund policy / 返金規定 / 退款政策');
  await page.getByRole('textbox').press('Tab');
  await expect(page.getByRole('button', { name: 'Inspect input' })).toBeFocused();
  await page.getByRole('button').press('Enter');
  await expect(page.getByLabel('Input preview')).toHaveText('Refund policy / 返金規定 / 退款政策');
  await page.screenshot({ path: testInfo.outputPath('environment.png') });
  expect(errors).toEqual([]);
});

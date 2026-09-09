import { test, expect, type Page, type BrowserContext } from '@playwright/test';
import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import type { components } from '../../src/api/schema';

type Run = components['schemas']['RunDetail'];
type Created = components['schemas']['MessageCreated'];
const base = 'http://127.0.0.1:8011';
const credentials = JSON.parse(readFileSync('../.artifacts/m6/release-credentials.json', 'utf8'));

async function login(page: Page, role: string) {
  await page.goto(base);
  await page.getByLabel('Email address').fill(credentials.accounts[role]);
  await page.getByLabel('Password', { exact: true }).fill(credentials.password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Workbench', exact: true })).toBeVisible();
  return page.url().split('/w/')[1];
}

async function upload(page: Page, file: string, name: string) {
  const bytes = readFileSync(file);
  await page.getByRole('link', { name: 'Knowledge', exact: true }).click();
  await page.getByLabel('Knowledge document').setInputFiles({ name, mimeType: 'text/markdown', buffer: bytes });
  const response = page.waitForResponse(value => value.request().method() === 'POST' && /\/documents$/.test(value.url()));
  const started = performance.now();
  const [received, clicked] = await Promise.allSettled([
    response, page.getByRole('button', { name: 'Upload document', exact: true }).click(),
  ]);
  if (clicked.status === 'rejected') throw clicked.reason;
  if (received.status === 'rejected') throw received.reason;
  const accepted = received.value;
  expect(accepted.status()).toBe(202);
  const acceptedAt = performance.now();
  const ids = await accepted.json();
  await expect(page.getByRole('heading', { name, exact: true })).toBeVisible();
  return { ids, started, accepted_at_ms: acceptedAt, bytes: bytes.length, sha256: createHash('sha256').update(bytes).digest('hex') };
}

test('five operator sessions retrieve, inspect and cancel alongside real ingestion', async ({ browser }, info) => {
  test.setTimeout(240000);
  const contexts: BrowserContext[] = [];
  const pending: Promise<unknown>[] = [];
  function track<T>(promise: Promise<T>): Promise<PromiseSettledResult<T>> {
    const safe = promise.then(value => ({ status: 'fulfilled', value } as const), reason => ({ status: 'rejected', reason } as const));
    pending.push(safe); return safe;
  }
  function unwrap<T>(result: PromiseSettledResult<T>): T {
    if (result.status === 'rejected') throw result.reason;
    return result.value;
  }
  const report: Record<string, unknown> = { status: 'started', generation: 'not_exercised', quality: 'not_measured',
    profile: 'Five separate sessions of one seeded operator; real retrieval and background ingestion, followed by cancellation.', runs: [], documents: [] };
  const save = () => writeFileSync(info.outputPath('profile.json'), JSON.stringify(report, null, 2));
  const errors: string[] = [];
  try {
    const adminContext = await browser.newContext(); contexts.push(adminContext);
    const admin = await adminContext.newPage();
    admin.on('pageerror', error => errors.push(error.message));
    const workspace = await login(admin, 'admin'); report.workspace_id = workspace;
    const stamp = Date.now();
    const initial = await upload(admin, '../evals/corpus/v1/customer-handbook-en.md', `Small-team-handbook-${stamp}.md`);
    await expect(admin.getByText('Ready', { exact: true })).toBeVisible({ timeout: 90000 });
    const initialReady = performance.now() - initial.started;
    report.documents = [{ ...initial, browser_ready_ms: initialReady }]; save();

    const sessions = await Promise.all(Array.from({ length: 5 }, () => track((async () => {
      const context = await browser.newContext(); contexts.push(context);
      const page = await context.newPage(); page.on('pageerror', error => errors.push(error.message));
      expect(await login(page, 'operator')).toBe(workspace);
      return page;
    })())));
    const pages = sessions.map(unwrap);
    const csrf = await Promise.all(pages.map(async page => (await (await page.request.get(base + '/api/session')).json()).csrf_token));
    expect(new Set(csrf).size).toBe(5); // Prove distinct sessions without saving their secrets.
    const messages = [
      ['en', 'What is the standard refund request deadline?'],
      ['ja', '通常の返金申請の期限はいつですか？'],
      ['zh', '标准退款申请的期限是什么？'],
      ['en', 'How many days do I have to request a refund for my first annual subscription purchase?'],
      ['ja', '年間サブスクリプションの初回購入後、何日以内に返金を申請できますか？'],
    ];
    await Promise.all(pages.map(async (page, index) => {
      await page.getByRole('button', { name: 'New message', exact: true }).click();
      await page.getByLabel('Customer message', { exact: true }).fill(messages[index][1]);
      await page.getByLabel('Response language').selectOption(messages[index][0]);
    }));
    const observations: Record<string, unknown>[] = Array.from({ length: 5 }, (_, index) => ({ session: index + 1, state: 'not_admitted' }));
    report.runs = observations;
    const background = track((async () => {
      const second = await upload(admin, '../evals/corpus/v1/service-operations-en.md', `Small-team-operations-${stamp}.md`);
      report.documents = [{ ...initial, browser_ready_ms: initialReady }, second]; save();
      await expect(admin.getByText('Ready', { exact: true })).toBeVisible({ timeout: 150000 });
      const completed = { ...second, browser_ready_at_ms: performance.now(), browser_ready_ms: performance.now() - second.started };
      report.documents = [{ ...initial, browser_ready_ms: initialReady }, completed]; save();
      return completed;
    })());
    const started = performance.now(); report.measurement_started_at = new Date().toISOString();
    const admissions = await Promise.all(pages.map((page, index) => track((async () => {
      const response = page.waitForResponse(value => value.request().method() === 'POST' && /\/messages$/.test(value.url()));
      const before = performance.now();
      const [received, clicked] = await Promise.allSettled([
        response, page.getByRole('button', { name: 'Start processing', exact: true }).click(),
      ]);
      if (clicked.status === 'rejected') throw clicked.reason;
      if (received.status === 'rejected') throw received.reason;
      const accepted = received.value; expect(accepted.status()).toBe(202);
      const result = { ids: await accepted.json() as Created, accepted_at_ms: performance.now(), admission_ms: performance.now() - before, offset_ms: before - started, request_id: accepted.headers()['x-request-id'] };
      Object.assign(observations[index], result, { state: 'admitted' }); save();
      return result;
    })())));
    const admitted = admissions.map(unwrap);
    expect(new Set(admitted.map(row => row.ids.run_id)).size).toBe(5);
    const runTasks = pages.map((page, index) => track((async () => {
      await expect(page.locator('.run-heading').getByRole('status')).toHaveText('Waiting for development response', { timeout: 150000 });
      const readyMs = performance.now() - started;
      const endpoint = `${base}/api/workspaces/${workspace}/runs/${admitted[index].ids.run_id}`;
      const response = await page.request.get(endpoint); expect(response.status()).toBe(200);
      const run: Run = await response.json();
      Object.assign(observations[index], { state: run.state, observed_ready_ms: readyMs, retrieval_id: run.retrieval_id, model_calls: run.model_calls, steps: run.steps }); save();
      expect(run.state).toBe('waiting_for_input'); expect(run.retrieval_id).toBeTruthy();
      expect(run.error_code).toBeNull(); expect(run.handoff?.provider).toBe('codex_assisted_development');
      expect(run.model_calls.some(call => call.operation === 'embed_query' && call.status === 'succeeded')).toBe(true);
      expect(run.model_calls.some(call => call.operation === 'rerank' && call.status === 'succeeded')).toBe(true);
      expect(run.model_calls.every(call => call.provider === 'local_cpu' && call.api_cost_usd === 0)).toBe(true);
      await expect(page.getByText('Development response controls', { exact: true })).toHaveCount(0);
      await page.getByRole('tab', { name: 'Workflow', exact: true }).click();
      await page.getByText('Processing details', { exact: true }).click();
      await expect(page.getByText('intfloat/multilingual-e5-small', { exact: true })).toBeVisible();
      const traceResponse = await page.request.get(`${base}/api/workspaces/${workspace}/retrieval/${run.retrieval_id}`);
      expect(traceResponse.status()).toBe(200);
      const trace = await traceResponse.json();
      expect(trace.status).toBe('succeeded'); expect(trace.phase).toBe('completed');
      expect(trace.candidates.length).toBeLessThanOrEqual(20);
      expect(trace.candidates.some((row: { final_rank: number | null }) => row.final_rank != null)).toBe(true);
      const cancelStart = performance.now();
      await page.getByRole('button', { name: 'Cancel processing', exact: true }).click();
      await expect(page.locator('.run-heading').getByRole('status')).toHaveText('Cancelled');
      const cancelMs = performance.now() - cancelStart;
      const terminal: Run = await (await page.request.get(endpoint)).json();
      expect(terminal.state).toBe('cancelled');
      await page.screenshot({ path: info.outputPath(`operator-${index + 1}.png`), fullPage: true });
      const result = { ...admitted[index], language: messages[index][0], observed_ready_ms: readyMs,
        cancel_ms: cancelMs, state: terminal.state, retrieval_id: run.retrieval_id,
        model_calls: run.model_calls, steps: run.steps, trace_duration_ms: trace.duration_ms,
        candidate_count: trace.candidates.length };
      Object.assign(observations[index], result); save(); return result;
    })()));
    const [backgroundResult, runResults] = await Promise.all([background, Promise.all(runTasks)]);
    const second = unwrap(backgroundResult);
    const results = runResults.map(unwrap);
    expect(second.accepted_at_ms).toBeLessThan(started + Math.max(...results.map(row => row.observed_ready_ms)));
    expect(second.browser_ready_at_ms).toBeGreaterThan(Math.min(...results.map(row => row.accepted_at_ms)));
    report.overlap_note = 'Browser observations overlap; verify actual stored intervals with app.profile_release. No simultaneous-inference claim.';
    report.runs = results; report.elapsed_ms = performance.now() - started;
    expect(errors).toEqual([]); report.page_errors = errors; report.status = 'passed'; save();
  } catch (error) {
    await Promise.all(pending); // Every tracked task settles safely before the final failed record.
    report.status = 'failed'; report.page_errors = errors; report.failure = String(error); save(); throw error;
  } finally {
    await Promise.allSettled(contexts.map(context => context.close()));
  }
});

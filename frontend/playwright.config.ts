import { defineConfig } from '@playwright/test';
import path from 'node:path';

const evidence = process.env.ASI_EVIDENCE_DIR ?? '../.artifacts/m0/browser-manual';

export default defineConfig({
  testDir: './tests/e2e',
  outputDir: path.join(evidence, 'results'),
  workers: 1,
  retries: 0,
  forbidOnly: true,
  reporter: [['list'], ['json', { outputFile: path.join(evidence, 'browser-report.json') }]],
  use: { browserName: 'chromium', headless: true, trace: 'on', screenshot: 'only-on-failure' },
});

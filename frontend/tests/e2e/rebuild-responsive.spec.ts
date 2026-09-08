import { expect, test } from "@playwright/test";

test("five areas and editing controls fit phone and tablet screens", async ({ page, request }, testInfo) => {
  const base = process.env.API_URL ?? "http://127.0.0.1:8000";
  const email = `responsive-${Date.now()}@example.test`;
  const credentials = { email, password: "Synthetic-responsive-2026!" };
  expect((await request.post(`${base}/api/v1/auth/register`, {
    data: { ...credentials, display_name: "Responsive QA" },
  })).status()).toBe(201);
  const login = await request.post(`${base}/api/v1/auth/login`, { data: credentials });
  expect(login.status()).toBe(200);
  const token = (await login.json()).access_token;
  const headers = { Authorization: `Bearer ${token}` };
  const created = await request.post(`${base}/api/v1/workspaces`, {
    headers, data: { name: "LongWorkspaceName".repeat(8) },
  });
  expect(created.status()).toBe(201);
  const workspace = (await created.json()).id;
  const agentName = "SupportAgent".repeat(10);
  expect((await request.post(`${base}/api/v1/workspaces/${workspace}/agents`, {
    headers, data: { name: agentName, token_budget: 4000 },
  })).status()).toBe(201);
  await page.addInitScript(value => localStorage.setItem("asi_token", value), token);
  await page.goto(`/?workspace=${workspace}`);
  async function fits() {
    expect(await page.evaluate(() => document.documentElement.scrollWidth
      - document.documentElement.clientWidth)).toBeLessThanOrEqual(1);
  }
  for (const width of [320, 768]) {
    await page.setViewportSize({ width, height: 900 });
    for (const area of ["Work", "Knowledge", "Agents", "Activity", "Settings"]) {
      await page.getByRole("link", { name: area, exact: true }).click();
      await expect(page.getByRole("heading", { name: area, exact: true })).toBeVisible();
      await expect(page.getByText(/^(Loading|Checking) /)).toHaveCount(0);
      await fits();
      if (area === "Knowledge") {
        await page.getByRole("button", { name: "Add knowledge", exact: true }).click();
        await expect(page.getByRole("textbox", { name: "Content", exact: true })).toBeVisible();
        await fits();
      }
      if (area === "Agents") {
        const search = page.getByRole("searchbox", { name: "Search agents", exact: true });
        await search.fill("does-not-match-any-agent");
        await page.getByRole("button", { name: "Search", exact: true }).click();
        await expect(page.getByRole("heading", { name: "No matching agents", exact: true })).toBeVisible();
        await search.fill("SupportAgent");
        await page.getByRole("button", { name: "Search", exact: true }).click();
        await page.getByRole("button", { name: `Edit ${agentName}`, exact: true }).click();
        await expect(page.getByRole("textbox", { name: "Instructions", exact: true })).toBeVisible();
        await fits();
      }
      const screenshot = testInfo.outputPath(`${area}-${width}.png`);
      await page.screenshot({ path: screenshot, fullPage: true });
      await testInfo.attach(`${area}-${width}`, { path: screenshot, contentType: "image/png" });
    }
  }
});

import { expect, test } from "@playwright/test";

test("new workspace knowledge supports file upload, versions, search and removal", async ({ page }) => {
  const stamp = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  await page.goto("/");
  await page.getByRole("button", { name: "New here? Create an account" }).click();
  await page.getByRole("textbox", { name: "Name", exact: true }).fill("Rebuild QA");
  await page.getByRole("textbox", { name: "Email", exact: true }).fill(`rebuild-${stamp}@example.test`);
  await page.getByRole("textbox", { name: "Password", exact: true }).fill("Synthetic-review-2026!");
  await page.getByRole("button", { name: "Create account", exact: true }).click();
  await page.getByRole("textbox", { name: "Workspace name", exact: true }).fill(`Rebuild ${stamp}`);
  await page.getByRole("button", { name: "Create workspace", exact: true }).click();
  await page.getByRole("link", { name: "Knowledge", exact: true }).click();
  await expect(page.getByRole("heading", { name: "No documents here yet" })).toBeVisible();
  await page.getByRole("button", { name: "Add knowledge", exact: true }).click();
  const file = page.getByLabel("Text or Markdown file", { exact: true });
  await file.setInputFiles({ name: "policy.exe", mimeType: "application/octet-stream", buffer: Buffer.from("bad") });
  await expect(page.getByRole("alert")).toHaveText("Choose a text or Markdown file.");
  await file.setInputFiles({ name: "policy.md", mimeType: "text/markdown",
    buffer: Buffer.from("返金は購入から7日以内に申請できます。領収書が必要です。", "utf8") });
  await expect(page.getByRole("textbox", { name: "Title", exact: true })).toHaveValue("policy");
  await page.getByRole("button", { name: "Add document", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "Document is ready to use." })).toBeVisible();
  await expect(page.getByRole("row", { name: /policy Ready JA/ })).toBeVisible();
  await page.getByRole("button", { name: "policy", exact: true }).click();
  await expect(page.getByText("Ready · Version 1", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Edit document", exact: true }).click();
  await page.getByRole("textbox", { name: "Content", exact: true }).fill("退款可以在购买后7天内申请。请提供收据。");
  await page.getByRole("combobox", { name: "Document language", exact: true }).selectOption("zh");
  await page.getByRole("button", { name: "Save new version", exact: true }).click();
  await expect(page.getByText("Ready · Version 2", { exact: true })).toBeVisible();
  await expect(page.getByRole("row", { name: /policy Ready ZH/ })).toBeVisible();
  await page.getByRole("button", { name: "Close", exact: true }).click();
  await page.getByRole("searchbox", { name: "Search documents" }).fill("no such policy");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await expect(page.getByRole("heading", { name: "No matching documents" })).toBeVisible();
  await page.getByRole("searchbox", { name: "Search documents" }).fill("policy");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await page.getByRole("button", { name: "policy", exact: true }).click();
  await page.getByRole("button", { name: "Remove document", exact: true }).click();
  await page.getByRole("button", { name: "Keep document", exact: true }).click();
  await expect(page.getByText("Ready · Version 2", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Remove document", exact: true }).click();
  await page.getByRole("button", { name: "Confirm removal", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "Document removed." })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("heading", { name: "No documents here yet" })).toBeVisible();
});

test("viewer can read knowledge but cannot upload through UI or API", async ({ page, request }) => {
  const base = process.env.API_URL ?? "http://127.0.0.1:8000";
  const stamp = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  async function user(label: string) {
    const credentials = { email: `${label}-${stamp}@example.test`, password: "Synthetic-review-2026!" };
    expect((await request.post(`${base}/api/v1/auth/register`, {
      data: { ...credentials, display_name: label },
    })).status()).toBe(201);
    const login = await request.post(`${base}/api/v1/auth/login`, { data: credentials });
    expect(login.status()).toBe(200);
    return { ...credentials, token: (await login.json()).access_token as string };
  }
  const owner = await user("owner"); const viewer = await user("viewer");
  const headers = { Authorization: `Bearer ${owner.token}` };
  const created = await request.post(`${base}/api/v1/workspaces`, { headers, data: { name: `Read-only ${stamp}` } });
  expect(created.status()).toBe(201);
  const workspace = (await created.json()).id as string;
  expect((await request.post(`${base}/api/v1/workspaces/${workspace}/members`, {
    headers, data: { email: viewer.email, role: "viewer" },
  })).status()).toBe(201);
  await page.goto("/");
  await page.getByRole("textbox", { name: "Email", exact: true }).fill(viewer.email);
  await page.getByRole("textbox", { name: "Password", exact: true }).fill(viewer.password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.getByRole("link", { name: "Knowledge", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Knowledge", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Add knowledge", exact: true })).toHaveCount(0);
  const denied = await request.post(`${base}/api/v1/workspaces/${workspace}/knowledge-documents`, {
    headers: { Authorization: `Bearer ${viewer.token}` },
    data: { title: "Forbidden", content: "Should not persist", content_type: "text/plain" },
  });
  expect(denied.status()).toBe(403);
  await page.getByRole("button", { name: "Refresh", exact: true }).click();
  await expect(page.getByRole("heading", { name: "No documents here yet" })).toBeVisible();
  await page.getByRole("link", { name: "Settings", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Settings", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Save workspace", exact: true })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Add model", exact: true })).toHaveCount(0);
  expect((await request.patch(`${base}/api/v1/workspaces/${workspace}`, {
    headers: { Authorization: `Bearer ${viewer.token}` }, data: { name: "Forbidden rename" },
  })).status()).toBe(403);
});

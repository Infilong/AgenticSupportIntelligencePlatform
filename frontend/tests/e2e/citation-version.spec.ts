import { expect, test } from "@playwright/test";

test("run source opens its saved version after edits and fails clearly after deletion", async ({ page, request }) => {
  const base = `${process.env.API_URL ?? "http://127.0.0.1:8000"}/api/v1`;
  const credentials = { email: `citation-${Date.now()}@example.test`, password: "Synthetic-review-2026!" };
  expect((await request.post(`${base}/auth/register`, { data: { ...credentials, display_name: "Citation QA" } })).status()).toBe(201);
  const login = await request.post(`${base}/auth/login`, { data: credentials });
  expect(login.status()).toBe(200);
  const token = (await login.json()).access_token;
  const headers = { Authorization: `Bearer ${token}` };
  const workspace = await request.post(`${base}/workspaces`, { headers, data: { name: "Citation QA" } });
  expect(workspace.status()).toBe(201);
  const id = (await workspace.json()).id;
  const api = `${base}/workspaces/${id}`;
  const upload = await request.post(`${api}/knowledge-documents`, { headers, data: {
    title: "Refund policy", content: "Refunds are available within 7 days.", content_type: "text/plain", language: "en",
  } });
  expect(upload.status()).toBe(201);
  const document = (await upload.json()).document.id;
  expect((await request.post(`${api}/agents`, { headers, data: { name: "Support" } })).status()).toBe(201);
  await page.addInitScript(value => localStorage.setItem("asi_token", value), token);
  await page.goto(`/?workspace=${id}#work`);
  await page.getByRole("textbox", { name: "Your request", exact: true }).fill("What is the refund policy?");
  await page.getByRole("button", { name: "Ask agent", exact: true }).click();
  const detail = page.getByRole("region", { name: "Run details", exact: true });
  await expect(detail.locator(".status").first()).toHaveText("Completed", { timeout: 30000 });
  const runUrl = page.url();
  const changed = await request.post(`${api}/knowledge-documents/${document}/reindex`, { headers,
    data: { title: "New refund policy", content: "Refunds now require approval within 3 days.", language: "en" } });
  expect(changed.status()).toBe(200);
  await detail.locator("summary").filter({ hasText: "Refund policy v1" }).click();
  await expect(detail).toContainText("Refunds are available within 7 days.");
  await detail.getByRole("link", { name: "Open document version 1", exact: true }).click();
  const saved = page.getByRole("region", { name: "Saved document version", exact: true });
  await expect(saved).toContainText("Refunds are available within 7 days.");
  await expect(saved).not.toContainText("3 days");
  await page.reload();
  await expect(saved).toContainText("Refunds are available within 7 days.");
  await page.goBack();
  await expect(page).toHaveURL(runUrl);
  await expect(detail).toContainText("Refunds are available within 7 days.");
  await detail.locator("summary").filter({ hasText: "Refund policy v1" }).click();
  await detail.getByRole("link", { name: "Open document version 1", exact: true }).click();
  expect((await request.delete(`${api}/knowledge-documents/${document}`, { headers })).status()).toBe(204);
  await page.reload();
  await expect(saved.getByRole("alert")).toContainText("Document version was not found.");
  await expect(saved).not.toContainText("Refunds are available within 7 days.");
});

import { expect, request, test } from "@playwright/test";

const apiUrl = process.env.API_URL ?? "http://127.0.0.1:8000";

test("temporary notifications fade and disappear consistently", async ({ page }) => {
  const api = await request.newContext({ baseURL: apiUrl });
  const runId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const email = `toast-${runId}@example.com`;
  const password = "strong-password";

  const register = await api.post("/api/v1/auth/register", {
    data: { email, password, display_name: "Toast Tester" },
  });
  expect(register.status()).toBe(201);

  const login = await api.post("/api/v1/auth/login", {
    data: { email, password },
  });
  expect(login.status()).toBe(200);
  const { access_token: token } = await login.json();

  const workspace = await api.post("/api/v1/workspaces", {
    headers: { Authorization: `Bearer ${token}` },
    data: { name: `Toast Workspace ${runId}` },
  });
  expect(workspace.status()).toBe(201);

  await page.addInitScript((sessionToken) => {
    window.localStorage.setItem("asi_token", sessionToken);
  }, token);

  await page.goto("/");
  await expect(page.getByRole("button", { name: "Refresh" })).toBeVisible();
  await page.getByRole("button", { name: "Refresh" }).click();

  const toast = page.locator(".status-slot");
  await expect(toast).toContainText("Workspace data refreshed");
  await expect(toast).toHaveClass(/visible/);
  await expect(toast).toHaveClass(/dismissing/, { timeout: 4200 });
  await expect(toast).not.toHaveClass(/visible/, { timeout: 1500 });

  await page.getByRole("button", { name: "Account", exact: true }).click();
  await page.getByRole("button", { name: "Create workspace" }).click();

  await expect(toast).toContainText("Workspace name is required.");
  await expect(toast).toHaveClass(/visible/);
  await expect(toast).toHaveClass(/dismissing/, { timeout: 4200 });
  await expect(toast).not.toHaveClass(/visible/, { timeout: 1500 });
});

import { expect, test } from "@playwright/test";

test("owner assigns Admin; Admin manages only lower roles through Settings", async ({ page, request }) => {
  const base = process.env.API_URL ?? "http://127.0.0.1:8000";
  const stamp = Date.now();
  async function account(name: string) {
    const credentials = { email: `${name.toLowerCase()}-${stamp}@members.test`, password: "Synthetic-review-2026!" };
    const registered = await request.post(`${base}/api/v1/auth/register`, { data: { ...credentials, display_name: name } });
    expect(registered.status()).toBe(201);
    const login = await request.post(`${base}/api/v1/auth/login`, { data: credentials });
    expect(login.status()).toBe(200);
    return { ...credentials, id: (await registered.json()).id as string, token: (await login.json()).access_token as string };
  }
  const owner = await account("Owner"); const admin = await account("Admin"); const operator = await account("Operator");
  const created = await request.post(`${base}/api/v1/workspaces`, {
    headers: { Authorization: `Bearer ${owner.token}` }, data: { name: `Members QA ${stamp}` },
  });
  expect(created.status()).toBe(201); const workspace = (await created.json()).id as string;
  async function signIn(user: typeof owner) {
    await page.goto(`/?workspace=${workspace}#settings`);
    await page.getByRole("textbox", { name: "Email", exact: true }).fill(user.email);
    await page.getByRole("textbox", { name: "Password", exact: true }).fill(user.password);
    await page.getByRole("button", { name: "Sign in", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Settings", exact: true })).toBeVisible();
  }
  async function add(email: string, role: string) {
    await page.getByRole("button", { name: "Add member", exact: true }).click();
    await page.getByRole("textbox", { name: "Email", exact: true }).fill(email);
    await page.getByRole("combobox", { name: "Role", exact: true }).selectOption(role);
    await page.getByRole("button", { name: "Save member", exact: true }).click();
    await expect(page.getByRole("status").filter({ hasText: "Membership saved" })).toBeVisible();
  }
  await signIn(owner); await add(admin.email, "admin");
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await signIn(admin);
  await expect(page.getByRole("button", { name: "Save workspace", exact: true })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Add model", exact: true })).toHaveCount(0);
  await expect(page.getByRole("button", { name: `Edit ${owner.email}`, exact: true })).toHaveCount(0);
  await add(operator.email, "viewer");
  await page.getByRole("button", { name: `Edit ${operator.email}`, exact: true }).click();
  await expect(page.getByRole("combobox", { name: "Role", exact: true }).locator("option")).toHaveText(["Viewer", "Operator"]);
  await page.getByRole("combobox", { name: "Role", exact: true }).selectOption("operator");
  await page.getByRole("button", { name: "Save member", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "Membership saved" })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("region", { name: "Members", exact: true })).toContainText(`${operator.email} · operator`);
  const denied = await request.patch(`${base}/api/v1/workspaces/${workspace}/members/${admin.id}`, {
    headers: { Authorization: `Bearer ${admin.token}` }, data: { role: "owner" },
  });
  expect(denied.status()).toBe(409);
  await page.getByRole("button", { name: `Remove ${operator.email}`, exact: true }).click();
  await page.getByRole("button", { name: "Keep member", exact: true }).click();
  await expect(page.getByRole("button", { name: `Edit ${operator.email}`, exact: true })).toBeVisible();
  await page.getByRole("button", { name: `Remove ${operator.email}`, exact: true }).click();
  await page.getByRole("button", { name: "Confirm removal", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "Member removed" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Members", exact: true })).not.toContainText(operator.email);
});

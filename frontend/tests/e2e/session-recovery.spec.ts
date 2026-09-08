import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

async function seed(request: APIRequestContext, page: Page) {
  const api = process.env.API_URL ?? "http://127.0.0.1:8000";
  const stamp = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const credentials = { email: `recovery-${stamp}@example.test`, password: "synthetic-password" };
  expect((await request.post(`${api}/api/v1/auth/register`, {
    data: { ...credentials, display_name: "Session recovery" },
  })).status()).toBe(201);
  const login = await request.post(`${api}/api/v1/auth/login`, { data: credentials });
  expect(login.status()).toBe(200);
  const token = (await login.json()).access_token;
  const workspace = await request.post(`${api}/api/v1/workspaces`, {
    headers: { Authorization: `Bearer ${token}` }, data: { name: `Recovery ${stamp}` },
  });
  expect(workspace.status()).toBe(201);
  await page.addInitScript((value) => localStorage.setItem("asi_token", value), token);
  return { token, credentials, workspace: await workspace.json() };
}

async function navigate(page: Page, name: string) {
  await page.getByRole("navigation", { name: "Main navigation" })
    .getByRole("link", { name, exact: true }).click();
}

async function signIn(page: Page, credentials: { email: string; password: string }) {
  await page.getByRole("textbox", { name: "Email", exact: true }).fill(credentials.email);
  await page.getByRole("textbox", { name: "Password", exact: true }).fill(credentials.password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("navigation", { name: "Main navigation" })).toBeVisible();
}

test("server error reference is visible while upload draft and session survive", async ({ page, request }) => {
  const { token } = await seed(request, page);
  await page.goto("/");
  await navigate(page, "Knowledge");
  await page.getByRole("button", { name: "Add knowledge", exact: true }).click();
  const title = page.getByLabel("Title", { exact: true });
  const content = page.getByRole("textbox", { name: "Content", exact: true });
  await title.fill("Recoverable policy");
  await content.fill("Refunds can be requested within seven days.");
  const reference = "af0a48c2-7461-40be-a3bd-9a5897329bf9";
  await page.route("**/knowledge-documents", (route) => route.request().method() === "POST"
    ? route.fulfill({ status: 500, headers: {
      "X-Request-ID": reference, "Access-Control-Expose-Headers": "X-Request-ID",
      "Access-Control-Allow-Origin": new URL(page.url()).origin,
    }, json: { detail: { code: "internal_error", message: "An internal error occurred." } } })
    : route.continue());
  await page.getByRole("button", { name: "Add document", exact: true }).click();
  await expect(page.getByText(`An internal error occurred. (Request ID: ${reference})`,
    { exact: true })).toBeVisible();
  await expect(title).toHaveValue("Recoverable policy");
  await expect(content).toHaveValue("Refunds can be requested within seven days.");
  expect(await page.evaluate(() => localStorage.getItem("asi_token"))).toBe(token);
  await page.unroute("**/knowledge-documents");
  const saved = page.waitForResponse((response) => response.request().method() === "POST" &&
    new URL(response.url()).pathname.endsWith("/knowledge-documents"));
  await page.getByRole("button", { name: "Add document", exact: true }).click();
  const response = await saved;
  expect(response.status()).toBe(201);
  expect((await response.json()).document.title).toBe("Recoverable policy");
});

test("an invalid saved session returns to login without browser exceptions", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.addInitScript(() => localStorage.setItem("asi_token", "invalid-synthetic-token"));
  await page.goto("/");
  await expect(page.getByRole("textbox", { name: "Email", exact: true })).toBeVisible();
  await expect(page.getByText("Your session expired. Sign in again.", { exact: true })).toBeVisible();
  await expect.poll(() => page.evaluate(() => localStorage.getItem("asi_token"))).toBeNull();
  expect(errors).toEqual([]);
});

for (const failure of ["service", "network"]) {
test(`${failure} account bootstrap failure is visible and Retry retries it`, async ({ page, request }) => {
  const { token, workspace } = await seed(request, page);
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  let unavailable = true;
  await page.route("**/api/v1/workspaces", (route) => {
    if (!unavailable) return route.continue();
    return failure === "network" ? route.abort("failed") : route.fulfill({
      status: 503, json: { detail: { message: "Workspace service unavailable." } },
    });
  });
  const message = failure === "network" ? "Failed to fetch" : "Workspace service unavailable.";
  await page.goto("/");
  await expect(page.getByRole("alert")).toHaveText(`${message} Retry`);
  expect(await page.evaluate(() => localStorage.getItem("asi_token"))).toBe(token);
  unavailable = false;
  await expect(page.getByRole("button", { name: "Retry", exact: true })).toBeEnabled();
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await expect(page.getByRole("combobox", { name: "Workspace", exact: true })).toHaveValue(workspace.id);
  await expect(page.getByRole("heading", { name: "Work", exact: true })).toBeVisible();
  await expect(page.getByText(message, { exact: true })).toHaveCount(0);
  expect(errors).toEqual([]);
});
}

for (const status of [401, 403]) {
  test(`protected HTTP ${status} has the correct session recovery behavior`, async ({ page, request }) => {
    const { token, credentials } = await seed(request, page);
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.goto("/");
    await navigate(page, "Knowledge");
    await page.getByRole("button", { name: "Add knowledge", exact: true }).click();
    await page.getByLabel("Title", { exact: true }).fill("Recoverable document draft");
    await page.getByRole("textbox", { name: "Content", exact: true }).fill("Recoverable policy content.");
    await page.route("**/knowledge-documents", (route) => route.request().method() === "POST"
      ? route.fulfill({ status, json: { detail: { message: "Protected request rejected." } } })
      : route.continue());
    await page.getByRole("button", { name: "Add document", exact: true }).click();
    if (status === 401) {
      await expect(page.getByRole("textbox", { name: "Email", exact: true })).toBeVisible();
      await expect(page.getByText("Your session expired. Sign in again.", { exact: true })).toBeVisible();
      await expect.poll(() => page.evaluate(() => localStorage.getItem("asi_token"))).toBeNull();
      await page.unroute("**/knowledge-documents");
      await signIn(page, credentials);
      await navigate(page, "Knowledge");
      await page.getByRole("button", { name: "Add knowledge", exact: true }).click();
      await expect(page.getByLabel("Title", { exact: true })).toHaveValue("");
    } else {
      await expect(page.getByText("Protected request rejected.", { exact: true })).toBeVisible();
      expect(await page.evaluate(() => localStorage.getItem("asi_token"))).toBe(token);
      await expect(page.getByLabel("Title", { exact: true })).toHaveValue("Recoverable document draft");
      await page.unroute("**/knowledge-documents");
      await page.getByRole("button", { name: "Add document", exact: true }).click();
      await expect(page.getByRole("status").filter({ hasText: "Document is ready to use." })).toBeVisible();
    }
    expect(errors).toEqual([]);
  });
}

test("a delayed 401 from an old scope cannot sign out a new login", async ({ page, request }) => {
  const { credentials } = await seed(request, page);
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await navigate(page, "Knowledge");
  await page.getByRole("button", { name: "Add knowledge", exact: true }).click();
  let release!: () => void;
  const gate = new Promise<void>((resolve) => { release = resolve; });
  let started!: () => void;
  const pending = new Promise<void>((resolve) => { started = resolve; });
  let delay = true;
  await page.route("**/knowledge-documents?*", async (route) => {
    if (!delay) return route.continue();
    started();
    await gate;
    await route.fulfill({ status: 401, json: { detail: { message: "Old session rejected." } } });
  });
  try {
    await page.getByRole("searchbox", { name: "Search documents", exact: true }).fill("old-session");
    await page.getByRole("searchbox", { name: "Search documents", exact: true }).press("Enter");
    await pending;
    await page.getByRole("button", { name: "Sign out", exact: true }).click();
    delay = false;
    await signIn(page, credentials);
    await navigate(page, "Knowledge");
    await page.getByRole("button", { name: "Add knowledge", exact: true }).click();
    const newToken = await page.evaluate(() => localStorage.getItem("asi_token"));
    const rejected = page.waitForResponse((response) => response.status() === 401);
    release();
    await (await rejected).finished();
    await page.waitForTimeout(500);
    await expect(page.getByLabel("Title", { exact: true })).toBeVisible();
    expect(await page.evaluate(() => localStorage.getItem("asi_token"))).toBe(newToken);
    expect(errors).toEqual([]);
  } finally {
    release();
    await page.unrouteAll({ behavior: "wait" });
  }
});

test("wrong password preserves login inputs and allows a corrected retry", async ({ page, request }) => {
  const { credentials } = await seed(request, page);
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await page.getByRole("textbox", { name: "Email", exact: true }).fill(credentials.email);
  await page.getByRole("textbox", { name: "Password", exact: true }).fill("wrong-synthetic-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByText("Invalid email or password.", { exact: true })).toBeVisible();
  await expect(page.getByRole("textbox", { name: "Email", exact: true })).toHaveValue(credentials.email);
  await expect(page.getByRole("textbox", { name: "Password", exact: true })).toHaveValue("wrong-synthetic-password");
  await expect(page.getByText("Your session expired. Sign in again.", { exact: true })).toHaveCount(0);
  await signIn(page, credentials);
  await navigate(page, "Knowledge");
  await page.getByRole("button", { name: "Add knowledge", exact: true }).click();
  expect(errors).toEqual([]);
});

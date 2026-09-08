import { expect, test, type Page } from "@playwright/test";

async function navigate(page: Page, name: string) {
  await page.getByRole("navigation", { name: "Main navigation" })
    .getByRole("link", { name, exact: true }).click();
}

for (const transition of ["workspace", "session", "return visit"] as const) {
test(`delayed knowledge responses cannot cross ${transition} selection`, async ({ page, request }) => {
  const browserErrors: string[] = [];
  page.on("pageerror", (error) => browserErrors.push(error.message));
  const api = process.env.API_URL ?? "http://127.0.0.1:8000";
  const stamp = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const credentials = { email: `scope-${stamp}@example.test`, password: "synthetic-password" };
  expect((await request.post(`${api}/api/v1/auth/register`, {
    data: { ...credentials, display_name: "Scope isolation" },
  })).status()).toBe(201);
  const login = await request.post(`${api}/api/v1/auth/login`, { data: credentials });
  expect(login.status()).toBe(200);
  const token = (await login.json()).access_token;
  let headers = { Authorization: `Bearer ${token}` };
  const otherCredentials = { ...credentials, email: `other-${stamp}@example.test` };
  const workspaces: { id: string; name: string; title: string }[] = [];
  for (const label of ["A", "B"]) {
    if (transition === "session" && label === "B") {
      expect((await request.post(`${api}/api/v1/auth/register`, {
        data: { ...otherCredentials, display_name: "Other session" },
      })).status()).toBe(201);
      const otherLogin = await request.post(`${api}/api/v1/auth/login`, { data: otherCredentials });
      expect(otherLogin.status()).toBe(200);
      headers = { Authorization: `Bearer ${(await otherLogin.json()).access_token}` };
    }
    const name = `Scope ${label} ${stamp}`;
    const created = await request.post(`${api}/api/v1/workspaces`, { headers, data: { name } });
    expect(created.status()).toBe(201);
    const { id } = await created.json();
    const title = `Private ${label} ${stamp}`;
    const document = await request.post(`${api}/api/v1/workspaces/${id}/knowledge-documents`, {
      headers, data: { title, language: "en", content_type: "text/plain", content: `${label} policy.` },
    });
    expect(document.status()).toBe(201);
    workspaces.push({ id, name, title });
  }
  const [a, b] = workspaces;
  await page.addInitScript((value) => localStorage.setItem("asi_token", value), token);
  await page.goto(`/?workspace=${a.id}#knowledge`);
  const documents = page.getByRole("region", { name: "Knowledge documents", exact: true });
  await expect(documents).toContainText(a.title);
  await page.getByRole("button", { name: "Add knowledge", exact: true }).click();
  await page.getByLabel("Title", { exact: true }).fill("Unsaved private A draft");

  let release!: () => void;
  const gate = new Promise<void>((resolve) => { release = resolve; });
  let started!: () => void;
  const pending = new Promise<void>((resolve) => { started = resolve; });
  const path = `/api/v1/workspaces/${a.id}/knowledge-documents`;
  let delayed = false;
  await page.route((url) => url.pathname === path, async (route) => {
    if (delayed) return route.continue();
    delayed = true;
    const response = await route.fetch();
    const payload = await response.json();
    // Make a stale same-workspace result distinguishable on an A -> B -> A visit.
    payload.items[0].title = "Stale private A response";
    started();
    await gate;
    await route.fulfill({ response, json: payload });
  });
  try {
    await page.getByRole("searchbox", { name: "Search documents", exact: true }).press("Enter");
    await pending;
    if (transition === "session") {
      await page.getByRole("button", { name: "Sign out", exact: true }).click();
      await page.getByRole("textbox", { name: "Email", exact: true }).fill(otherCredentials.email);
      await page.getByRole("textbox", { name: "Password", exact: true }).fill(otherCredentials.password);
      await page.getByRole("button", { name: "Sign in", exact: true }).click();
    } else {
      await page.getByRole("combobox", { name: "Workspace", exact: true }).selectOption(b.id);
    }
    await navigate(page, "Knowledge");
    await expect(documents).toContainText(b.title);
    if (transition === "return visit") {
      await page.getByRole("combobox", { name: "Workspace", exact: true }).selectOption(a.id);
    }
    const expectedWorkspace = transition === "return visit" ? a : b;
    await expect(documents).toContainText(expectedWorkspace.title);
    await page.getByRole("button", { name: "Add knowledge", exact: true }).click();
    await expect(page.getByLabel("Title", { exact: true })).toHaveValue("");
    await page.getByLabel("Title", { exact: true }).fill("Current workspace draft");
    const arrived = page.waitForResponse((response) => new URL(response.url()).pathname === path);
    release();
    await (await arrived).finished();
    await page.waitForTimeout(500);
    await expect(documents).toContainText(expectedWorkspace.title);
    await expect(documents).not.toContainText("Stale private A response");
    await expect(page.getByLabel("Title", { exact: true })).toHaveValue("Current workspace draft");
    if (transition !== "return visit") await expect(documents).not.toContainText(a.title);
    await expect(page.getByRole("combobox", { name: "Workspace", exact: true })).toHaveValue(expectedWorkspace.id);
    expect(browserErrors).toEqual([]);
  } finally {
    release();
    await page.unrouteAll({ behavior: "wait" });
  }
});
}

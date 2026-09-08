import { expect, test } from "@playwright/test";

test("Japanese language choice handles kanji-only input and Auto remains available", async ({ page, request }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const api = `${process.env.API_URL ?? "http://127.0.0.1:8000"}/api/v1`;
  const stamp = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const credentials = { email: `language-choice-${stamp}@example.test`, password: "synthetic-password" };
  expect((await request.post(`${api}/auth/register`, {
    data: { ...credentials, display_name: "Language choice" },
  })).status()).toBe(201);
  const login = await request.post(`${api}/auth/login`, { data: credentials });
  expect(login.status()).toBe(200);
  const token = (await login.json()).access_token;
  const headers = { Authorization: `Bearer ${token}` };
  const created = await request.post(`${api}/workspaces`, { headers, data: { name: `Language ${stamp}` } });
  expect(created.status()).toBe(201);
  const workspace = await created.json();
  const base = `${api}/workspaces/${workspace.id}`;
  expect((await request.post(`${base}/knowledge-documents`, { headers, data: {
    title: "返金規定", language: "ja", content_type: "text/plain",
    content: "返金申請：返金は購入から7日以内に申請できます。",
  } })).status()).toBe(201);
  await page.addInitScript((value) => localStorage.setItem("asi_token", value), token);
  await page.goto(`/?workspace=${workspace.id}#agents`);
  await page.getByRole("button", { name: "Create agent", exact: true }).click();
  await page.getByRole("textbox", { name: "Name", exact: true }).fill("Japanese support");
  await page.getByRole("button", { name: "Save agent", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "Agent created" })).toBeVisible();
  await page.getByRole("link", { name: "Work", exact: true }).click();
  const selector = page.getByRole("combobox", { name: "Response language", exact: true });
  await expect(selector).toHaveValue("");
  for (const language of ["ja", ""] as const) {
    await page.getByRole("textbox", { name: "Your request", exact: true }).fill("返金申請");
    await selector.selectOption(language);
    const pending = page.waitForResponse((response) =>
      response.request().method() === "POST" && new URL(response.url()).pathname === `/api/v1/workspaces/${workspace.id}/tasks`);
    await page.getByRole("button", { name: "Ask agent", exact: true }).click();
    const response = await pending;
    expect(response.status()).toBe(202);
    expect(response.request().postDataJSON().language).toBe(language || null);
    const admitted = (await response.json()).run;
    let trace: { run: { status: string; language: string; final_answer: string | null }; steps: { output_json: string }[] };
    await expect.poll(async () => {
      const result = await request.get(`${base}/agent-runs/${admitted.id}/trace`, { headers });
      expect(result.status()).toBe(200);
      trace = await result.json();
      return trace.run.status;
    }, { timeout: 30000 }).toMatch(/^(completed|needs_human_review)$/);
    expect(trace!.run.language).toBe(language || "zh");
    if (language) {
      expect(trace!.run.status).toBe("completed");
      expect(trace!.run.final_answer).toContain("7日");
      await expect(page.getByRole("region", { name: "Run details", exact: true }))
        .toContainText(trace!.run.final_answer!);
    }
    const selection = JSON.parse(trace!.steps[0].output_json);
    expect(selection.language_source).toBe(language ? "requested" : "detected");
    await expect(page.getByRole("button", { name: "Ask agent", exact: true })).toBeDisabled();
  }
  // A failed submission keeps its identity; changing language is a different request.
  const attempts: { request_key: string; language: string }[] = [];
  await page.route("**/tasks", async route => {
    attempts.push(route.request().postDataJSON());
    await route.fulfill({ status: 503, json: { detail: "Synthetic admission unavailable." } });
  });
  await page.getByRole("textbox", { name: "Your request", exact: true }).fill("返金申請");
  for (const language of ["ja", "ja", "zh"]) {
    await selector.selectOption(language);
    await page.getByRole("button", { name: "Ask agent", exact: true }).click();
    await expect(page.getByRole("alert")).toContainText("Synthetic admission unavailable.");
    await expect(page.getByRole("button", { name: "Ask agent", exact: true })).toBeEnabled();
    await expect(selector).toHaveValue(language);
  }
  expect(attempts).toHaveLength(3);
  expect(attempts[1].request_key).toBe(attempts[0].request_key);
  expect(attempts[2].request_key).not.toBe(attempts[1].request_key);
  expect(attempts.map(attempt => attempt.language)).toEqual(["ja", "ja", "zh"]);
  await page.reload();
  await expect(selector).toHaveValue("");
  expect(errors).toEqual([]);
});

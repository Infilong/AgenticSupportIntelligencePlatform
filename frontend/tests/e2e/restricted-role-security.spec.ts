import { expect, test, type Page } from "@playwright/test";
import { restrictedFixture } from "./restricted-role-fixture";

async function browserRequest(page: Page, api: string, path: string, method = "GET", body?: unknown) {
  return page.evaluate(async ({ api, path, method, body }) => {
    const response = await fetch(api + path, { method,
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("asi_token")}` },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    return { status: response.status, text: await response.text() };
  }, { api, path, method, body });
}

for (const role of ["viewer", "operator"] as const) {
  test(`${role} browser enforces real permissions and workspace boundaries`, async ({ page, request }) => {
    const f = await restrictedFixture(request, role);
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.addInitScript((token) => localStorage.setItem("asi_token", token), f.actor.token);
    await page.goto(`/?workspace=${f.shared.id}#knowledge`);
    const nav = page.getByRole("navigation", { name: "Main navigation" });
    await expect(page.getByRole("region", { name: "Knowledge documents" })).toContainText(f.shared.title);
    await expect(page.getByRole("button", { name: "Add knowledge", exact: true })).toHaveCount(0);
    await nav.getByRole("link", { name: "Agents", exact: true }).click();
    await expect(page.getByRole("button", { name: "Create agent", exact: true })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Edit Role-bound agent", exact: true })).toHaveCount(0);
    await nav.getByRole("link", { name: "Settings", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Settings", exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Add member", exact: true })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Add model", exact: true })).toHaveCount(0);
    const allowed = await browserRequest(page, f.api, `${f.base}/retrieval/search`, "POST", {
      query: "Refunds within 7 days", language: "en", min_score: 0,
    });
    expect(allowed.status).toBe(200);
    const retrieval = JSON.parse(allowed.text);
    expect(retrieval.results.length).toBeGreaterThan(0);
    for (const result of retrieval.results) {
      expect(result.document_id).toBe(f.shared.documentId);
      expect(result.citation).toContain("#chunk-");
    }
    expect(allowed.text).not.toContain(f.privateWorkspace.title);
    const filtered = await browserRequest(page, f.api, `${f.base}/retrieval/search`, "POST", {
      query: "Refunds", language: "en", document_id: f.privateWorkspace.documentId, min_score: 0,
    });
    expect(filtered.status).toBe(200);
    expect(JSON.parse(filtered.text).results).toEqual([]);

    const costBefore = await browserRequest(page, f.api, `${f.base}/costs/summary`);
    expect(costBefore.status).toBe(200);
    const denials: [string, string, unknown?][] = [
      ["POST", `${f.base}/knowledge-documents`, { title: "Forbidden", language: "en",
        content_type: "text/plain", content: "Must not be indexed" }],
      ["DELETE", `${f.base}/knowledge-documents/${f.shared.documentId}`],
      ["POST", `${f.base}/evaluations`, { name: "Forbidden", modes: ["direct_llm"],
        jsonl_cases: JSON.stringify({ id: "denied", language: "en", input_message: "Refunds?" }) }],
      ["POST", `${f.base}/members`, { email: f.actor.email, role: "owner" }],
    ];
    if (role === "viewer") denials.push(
      ["POST", `${f.base}/tasks`, { agent_id: f.agentId, input_message: "Refunds?", request_key: "denied" }],
      ["POST", `${f.base}/task-runs/${f.runId}/stop`],["POST", `${f.base}/human-reviews/${f.reviewId}/resolve`,
      { decision: "rejected", comments: "Unauthorized" }]);
    for (const [method, path, body] of denials) {
      const response = await browserRequest(page, f.api, path, method, body);
      expect(response.status, `${method} ${path}`).toBe(403);
    }
    const foreignBase = `/api/v1/workspaces/${f.privateWorkspace.id}`;
    for (const path of [`${foreignBase}/knowledge-documents`,
      `${foreignBase}/knowledge-documents/${f.privateWorkspace.documentId}`,
      `${foreignBase}/costs/summary`, `${f.base}/knowledge-documents/${f.privateWorkspace.documentId}`]) {
      const response = await browserRequest(page, f.api, path);
      expect(response.status, path).toBe(404);
      expect(response.text).not.toContain(f.privateWorkspace.title);
    }
    const foreignSearch = await browserRequest(page, f.api, `${foreignBase}/retrieval/search`,
      "POST", { query: "Refunds", language: "en" });
    expect(foreignSearch.status).toBe(404);
    expect(foreignSearch.text).not.toContain(f.privateWorkspace.title);
    const costAfter = await browserRequest(page, f.api, `${f.base}/costs/summary`);
    expect(costAfter.status).toBe(200);
    for (const key of ["ai_run_total", "graph_run_total", "total_tokens", "total_estimated_cost"]) {
      expect(JSON.parse(costAfter.text)[key], key).toBe(JSON.parse(costBefore.text)[key]);
    }
    const documents = await browserRequest(page, f.api, `${f.base}/knowledge-documents`);
    expect(documents.status).toBe(200);
    expect(JSON.parse(documents.text).items.map((item: { id: string }) => item.id)).toEqual([f.shared.documentId]);
    await nav.getByRole("link", { name: "Work", exact: true }).click();
    const attention = page.getByRole("region", { name: "Needs your attention", exact: true });
    await expect(attention).toContainText(f.unsafe);
    if (role === "operator") {
      await expect(page.getByRole("textbox", { name: "Your request", exact: true })).toBeVisible();
      await page.getByRole("button", { name: "Review answer", exact: true }).click();
      await page.getByRole("combobox", { name: "Decision", exact: true }).selectOption("rejected");
      await page.getByLabel("Review note", { exact: true }).fill("Unsafe instruction rejected by operator.");
      const resolved = page.waitForResponse(response => response.url().endsWith(`/human-reviews/${f.reviewId}/resolve`));
      await page.getByRole("button", { name: "Save decision", exact: true }).click();
      expect((await resolved).status()).toBe(200);
      await expect(attention).toHaveCount(0);
      const trace = await request.get(`${f.api}${f.base}/agent-runs/${f.runId}/trace`, { headers: f.ownerHeaders });
      expect(trace.status()).toBe(200);
      expect((await trace.json()).run.status).toBe("rejected");
      const task = await browserRequest(page, f.api, `${f.base}/tasks`, "POST", {
        agent_id: f.agentId, input_message: "Refunds?", request_key: "operator-allowed",
      });
      expect(task.status).toBe(202);
      const runId = JSON.parse(task.text).run.id;
      const stop = await browserRequest(page, f.api, `${f.base}/task-runs/${runId}/stop`, "POST");
      expect(stop.status).toBe(200);
      expect(["stopping", "stopped"]).toContain(JSON.parse(stop.text).status);
    } else {
      await expect(page.getByRole("textbox", { name: "Your request", exact: true })).toHaveCount(0);
      await expect(page.getByRole("button", { name: "Review answer", exact: true })).toHaveCount(0);
    }
    expect(await page.evaluate(() => localStorage.getItem("asi_token"))).toBe(f.actor.token);
    expect(errors).toEqual([]);
  });
}

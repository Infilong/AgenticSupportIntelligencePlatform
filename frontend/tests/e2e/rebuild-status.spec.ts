import { expect, test } from "@playwright/test";

test("run list follows active detail transitions without a manual refresh", async ({ page }) => {
  let status = "queued";
  const workspace = { id: "status-workspace", name: "Status QA", archived_at: null };
  const run = () => ({ id: "status-run", input_message: "Status transition test", status,
    final_answer: null, created_at: "2026-09-08T00:00:00Z", completed_at: null,
    language: "en", route_decision: null });
  const task = () => ({ task_id: "status-task", run: run(), parent_run_id: null,
    corrected_instructions: null });
  const empty = { items: [], total: 0, has_next: false };
  await page.addInitScript(() => localStorage.setItem("asi_token", "synthetic-status-token"));
  await page.route("**/api/v1/**", async route => {
    const path = new URL(route.request().url()).pathname;
    let body: unknown;
    if (path === "/api/v1/workspaces") body = [workspace];
    else if (path.endsWith("/membership")) body = { role: "viewer", permissions: ["traces:read"] };
    else if (path.endsWith("/agent-runs")) body = { items: [run()], total: 1, has_next: false };
    else if (path.endsWith("/trace")) body = { run: run(), steps: [], ai_runs: [], guardrails: [], checkpoints: [] };
    else if (path.endsWith("/task-runs/status-run")) body = task();
    else if (path.endsWith("/attempts")) body = { ...empty, items: [task()], total: 1 };
    else if (path.endsWith("/actions")) body = [];
    else throw new Error(`Unexpected status-test request: ${path}`);
    await route.fulfill({ json: body });
  });
  await page.goto("/?workspace=status-workspace#work?run=status-run");
  const detail = page.getByRole("region", { name: "Run details", exact: true });
  const list = page.getByRole("region", { name: "Runs", exact: true });
  for (const [next, label] of [["queued", "Queued"], ["running", "Running"],
    ["stopping", "Stopping"], ["stopped", "Stopped"]]) {
    status = next;
    await expect(detail.locator(".status")).toHaveText(label);
    await expect(list.locator("li p")).toContainText(label);
  }
  await page.reload();
  await expect(detail.locator(".status")).toHaveText("Stopped");
  await expect(list.locator("li p")).toContainText("Stopped");
});

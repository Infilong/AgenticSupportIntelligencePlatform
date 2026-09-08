import { expect, test } from "@playwright/test";

for (const width of [360, 1440]) test(`record detail and clarification at ${width}px`, async ({ page }) => {
  const errors: string[] = [];
  page.on("console", message => { if (message.type() === "error") errors.push(message.text()); });
  await page.setViewportSize({ width, height: 900 });
  let clarified = false;
  let resolved = false;
  let submissionKey = ""; let submissions = 0;
  const original = { id: "record", input_message: "w", received_at: "2026-09-08T10:00:00Z",
    latest_run_id: "run", status: "awaiting_clarification", result_summary: "Please clarify.",
    attempt_count: 1, input: { format: "text", content: "w", source: "admin", source_reference: null } };
  await page.route("**/api/v1/**", async route => {
    const path = new URL(route.request().url()).pathname;
    let body: unknown;
    if (path.endsWith("/auth/login")) body = { access_token: "fixture-token" };
    else if (path.endsWith("/workspaces")) body = [{ id: "workspace", name: "UI fixture" }];
    else if (path.endsWith("/membership")) body = { role: "operator", permissions: ["traces:read", "agents:run", "reviews:resolve"] };
    else if (path.endsWith("/agents")) body = { items: [{ id: "agent", name: "Support processor", active: true, archived_at: null }], total: 1, has_next: false };
    else if (path.endsWith("/records") && route.request().method() === "POST") {
      const data = route.request().postDataJSON();
      expect(data.input).toEqual({ format: "text", content: " w ", source: "admin", source_reference: null });
      submissions++;
      if (!submissionKey) {
        submissionKey = data.request_key;
        await route.fulfill({ status: 503, json: { detail: "Temporary service failure" } }); return;
      }
      expect(data.request_key).toBe(submissionKey); body = original;
    }
    else if (path.endsWith("/review")) body = { id: "review", graph_run_id: "run", reason: "Policy exception",
      proposed_answer: "Draft for review", reviewer_decision: "pending" };
    else if (path.endsWith("/actions")) body = [];
    else if (path.endsWith("/task-runs/run")) body = { task_id: "record", run: { id: "run" },
      parent_run_id: clarified ? "parent" : null, corrected_instructions: null,
      clarification_reply: clarified ? "What is the refund policy?" : null };
    else if (path.endsWith("/attempts")) body = { items: [], total: 1, has_next: false };
    else if (path.endsWith("/resolve")) {
      expect(route.request().postDataJSON().edited_answer).toBe("Checked human answer");
      resolved = true; body = {};
    }
    else if (path.endsWith("/clarifications")) {
      expect(route.request().postDataJSON().reply).toBe("What is the refund policy?");
      clarified = true; body = { ...original, status: "queued" };
    } else if (path.endsWith("/records")) body = { items: [original], total: 1, has_next: false };
    else if (path.endsWith("/records/record")) body = { ...original, status: resolved ? "completed" : clarified ? "needs_human_review" : original.status };
    else if (path.endsWith("/trace")) body = { run: { id: "run", final_answer: resolved ? "Checked human answer" : "Please clarify your request.",
      status: resolved ? "completed" : clarified ? "needs_human_review" : "awaiting_clarification" }, ai_runs: [], steps: [], guardrails: [], checkpoints: [] };
    else if (path.endsWith("/artifacts")) body = { items: [{ step_id: "step", kind: "request_clarification",
      status: "succeeded", data: { final_answer: "Please clarify your request." }, error: null }], total: 1, has_next: false };
    else throw new Error(`Unexpected fixture request: ${path}`);
    await route.fulfill({ json: body });
  });
  await page.goto("/");
  await page.getByRole("textbox", { name: "Email", exact: true }).fill("fixture@example.test");
  await page.getByRole("textbox", { name: "Password", exact: true }).fill("fixture-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Records", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "New record", exact: true }).click();
  await page.getByRole("combobox", { name: "Input format" }).selectOption("json");
  await page.getByRole("textbox", { name: "Input data" }).fill("invalid json");
  await page.getByRole("button", { name: "Save and process" }).click();
  await expect(page.getByRole("alert")).toContainText("Enter valid JSON");
  expect(submissions).toBe(0);
  await page.getByRole("combobox", { name: "Input format" }).selectOption("text");
  await page.getByRole("textbox", { name: "Input data" }).fill(" w ");
  await page.getByRole("button", { name: "Save and process" }).click();
  await expect(page.getByRole("alert")).toContainText("Temporary service failure");
  await page.getByRole("button", { name: "Save and process" }).click();
  await expect(page.getByRole("heading", { name: "Record details" })).toBeFocused();
  await expect(page.getByRole("heading", { name: "More information needed" })).toBeVisible();
  await page.getByRole("button", { name: "Processing", exact: true }).click();
  await expect(page.getByText("No model calls recorded.")).toBeVisible();
  await page.getByRole("button", { name: "Artifacts", exact: true }).click();
  await page.getByText("request clarification", { exact: true }).click();
  await expect(page.getByRole("region", { name: "Saved artifacts" })).toContainText("Please clarify your request.");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  await page.getByRole("button", { name: "Overview", exact: true }).click();
  await page.getByRole("textbox", { name: "Additional information" }).fill("What is the refund policy?");
  await page.getByRole("button", { name: "Continue processing" }).click();
  await expect(page.getByRole("heading", { name: "More information needed" })).toHaveCount(0);
  await expect(page.getByRole("region", { name: "Clarification reply" })).toContainText("What is the refund policy?");
  await page.getByRole("combobox", { name: "Decision", exact: true }).selectOption("edited");
  await page.getByRole("textbox", { name: "Human answer", exact: true }).fill("Checked human answer");
  await page.getByRole("button", { name: "Save decision", exact: true }).click();
  await expect(page.getByRole("region", { name: "Selected record" })).toContainText("Checked human answer");
  await page.getByRole("button", { name: "Back to records" }).click();
  await expect(page.getByRole("region", { name: "Input records" })).toBeVisible();
  expect(submissions).toBe(2);
  expect(errors.filter(error => !error.includes("503"))).toEqual([]);
});

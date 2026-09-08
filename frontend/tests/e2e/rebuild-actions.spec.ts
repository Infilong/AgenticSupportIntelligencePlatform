import { expect, test } from "@playwright/test";

test("agent actions require exact human review and preserve approval, rejection and stop", async ({ page }) => {
  const stamp = Date.now();
  await page.goto("/");
  await page.getByRole("button", { name: "New here? Create an account" }).click();
  await page.getByRole("textbox", { name: "Name", exact: true }).fill("Action QA");
  await page.getByRole("textbox", { name: "Email", exact: true }).fill(`actions-${stamp}@example.test`);
  await page.getByRole("textbox", { name: "Password", exact: true }).fill("Synthetic-review-2026!");
  await page.getByRole("button", { name: "Create account", exact: true }).click();
  await page.getByRole("textbox", { name: "Workspace name", exact: true }).fill(`Action QA ${stamp}`);
  await page.getByRole("button", { name: "Create workspace", exact: true }).click();
  await page.getByRole("link", { name: "Knowledge", exact: true }).click();
  await page.getByRole("button", { name: "Add knowledge", exact: true }).click();
  await page.getByRole("textbox", { name: "Title", exact: true }).fill("Refund policy");
  await page.getByRole("textbox", { name: "Content", exact: true }).fill("Refunds within 7 days require a receipt.");
  await page.getByRole("button", { name: "Add document", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "Document is ready to use." })).toBeVisible();
  await page.getByRole("link", { name: "Agents", exact: true }).click();
  await page.getByRole("button", { name: "Create agent", exact: true }).click();
  await page.getByRole("textbox", { name: "Name", exact: true }).fill("Action Support");
  await page.getByRole("button", { name: "Save agent", exact: true }).click();
  await page.getByRole("button", { name: "Edit Action Support", exact: true }).click();
  await page.getByRole("checkbox", { name: "Suggest a task category", exact: true }).check();
  await page.getByRole("checkbox", { name: "Suggest the answer as an internal note", exact: true }).check();
  await page.getByRole("button", { name: "Save settings", exact: true }).click();
  await page.reload();
  await page.getByRole("button", { name: "Edit Action Support", exact: true }).click();
  await expect(page.getByRole("checkbox", { name: "Suggest a task category", exact: true })).toBeChecked();
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  await page.getByRole("link", { name: "Work", exact: true }).click();
  const detail = page.getByRole("region", { name: "Run details", exact: true });
  const form = page.getByRole("form", { name: "Review decision", exact: true });
  for (const outcome of ["approve", "reject", "stop"]) {
    await page.getByRole("textbox", { name: "Your request", exact: true }).fill("What is the refund policy?");
    await page.getByRole("button", { name: "Ask agent", exact: true }).click();
    await expect(detail).toContainText("Needs review");
    await expect(detail.getByRole("region", { name: "Task action records" })).toContainText("Awaiting approval");
    if (outcome === "stop") {
      await detail.getByRole("button", { name: "Stop run", exact: true }).click();
      await expect(detail).toContainText("Stopped.");
      await expect(detail.getByRole("region", { name: "Task action records" })).toContainText("Rejected — no change applied");
      await page.reload();
      await expect(detail).toContainText("Stopped.");
      continue;
    }
    await page.getByRole("button", { name: "Review request", exact: true }).click();
    await expect(form.getByRole("button", { name: "Save decision", exact: true })).toBeDisabled();
    if (outcome === "approve") {
      await form.getByRole("button", { name: "Approve category", exact: true }).click();
      await expect(form.getByRole("article", { name: "Task category", exact: true })).toContainText("Applied");
      await form.getByRole("button", { name: "Approve note", exact: true }).click();
      await expect(form.getByRole("article", { name: "Task note", exact: true })).toContainText("Applied");
      await page.reload();
      await page.getByRole("button", { name: "Review request", exact: true }).click();
      await expect(form.getByRole("button", { name: "Approve note", exact: true })).toHaveCount(0);
      await form.getByRole("button", { name: "Save decision", exact: true }).click();
      await expect(detail).toContainText("Completed");
      await expect(detail).toContainText("7 days");
      await detail.getByText("Execution steps and model calls", { exact: true }).click();
      await expect(detail.getByText("Tool: add_note", { exact: false })).toHaveCount(1);
    } else {
      await form.getByRole("textbox", { name: "Reason to reject note", exact: true }).fill("Do not add this note");
      await form.getByRole("button", { name: "Reject note", exact: true }).click();
      await expect(form.getByRole("article", { name: "Task note", exact: true })).toContainText("Rejected — no change applied");
      await form.getByRole("combobox", { name: "Decision", exact: true }).selectOption("rejected");
      await form.getByRole("button", { name: "Save decision", exact: true }).click();
      await expect(detail).toContainText("Rejected");
      await expect(detail.getByRole("region", { name: "Task action records" }).getByText("Rejected — no change applied", { exact: true })).toHaveCount(2);
    }
  }
});

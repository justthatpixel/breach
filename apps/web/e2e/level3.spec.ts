import { expect, test } from "@playwright/test";

test.describe("Level 3 end to end", () => {
  test("select a component, play a card, write a note, run the attack, read the debrief", async ({
    page,
  }) => {
    await page.goto("/");
    await expect(page.getByText("Payments backend")).toBeVisible();

    await page.getByRole("link", { name: /Payments backend/ }).click();
    await expect(page).toHaveURL(/\/levels\/03-payments$/);

    // Select the queue component (nothing placed on it yet) and play a card.
    await page.getByTestId("component-queue").click();
    await expect(page.getByTestId("component-notes")).toBeEnabled();

    await page.getByTestId("card-least_privilege").click();
    await expect(page.getByTestId("card-least_privilege")).toBeDisabled();

    await page.getByTestId("component-notes").fill("Queue consumer uses a scoped role.");
    await expect(page.getByTestId("component-notes")).toHaveValue(
      "Queue consumer uses a scoped role."
    );

    // The "see debrief" link is inert until the attack finishes.
    await expect(page.getByTestId("see-debrief")).toHaveAttribute("aria-disabled", "true");

    await page.getByRole("button", { name: "Run attack" }).click();
    await expect(page.getByRole("button", { name: "Running…" })).toBeDisabled();

    // Four canned steps reveal one at a time (HANDOFF §9 / mocked backend).
    await expect(page.getByTestId("replay-step-1")).toBeVisible();
    await expect(page.getByTestId("replay-step-4")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId("see-debrief")).toHaveAttribute("aria-disabled", "false");

    await page.getByTestId("see-debrief").click();
    await expect(page).toHaveURL(/\/levels\/03-payments\/debrief$/);

    await expect(page.getByText("C+", { exact: true })).toBeVisible();
    await expect(page.getByText("The red team got in, in 3 steps.")).toBeVisible();
    await expect(page.getByText("T1190")).toBeVisible();
    await expect(page.getByText("T1078.004")).toBeVisible();
    await expect(page.getByText("What held")).toBeVisible();
  });

  test("a card cannot be played without selecting a component first", async ({ page }) => {
    await page.goto("/levels/03-payments");
    await expect(page.getByTestId("card-least_privilege")).toBeDisabled();
  });

  test("the attack cannot be re-run mid-replay and running disables the run button", async ({
    page,
  }) => {
    await page.goto("/levels/03-payments");
    await page.getByRole("button", { name: "Run attack" }).click();
    await expect(page.getByRole("button", { name: "Running…" })).toBeDisabled();
  });
});

test.describe("reduced motion", () => {
  test.use({ reducedMotion: "reduce" });

  test("the attack replay resolves immediately instead of staging reveals", async ({ page }) => {
    await page.goto("/levels/03-payments");
    await page.getByRole("button", { name: "Run attack" }).click();

    // With prefers-reduced-motion, GameScreen skips the staged reveal
    // entirely (see the effect in GameScreen.tsx) — all four steps and an
    // enabled debrief link should appear well under one staged-reveal
    // interval (900ms), not after ~3.6s of waiting for four of them.
    await expect(page.getByTestId("replay-step-4")).toBeVisible({ timeout: 500 });
    await expect(page.getByTestId("see-debrief")).toHaveAttribute("aria-disabled", "false");
  });
});

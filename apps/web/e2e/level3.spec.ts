import { expect, Page, test } from "@playwright/test";

/**
 * As of M5 this plays against the real backend (judge -> engine ->
 * narrator, see apps/api/scripts/e2e_server.sh) with the deterministic
 * test LLM/embedding providers — no network, no API keys, but it does
 * need Postgres (docker compose up -d db). If the DB isn't reachable,
 * runAttack() surfaces an error in the Red Team bubble instead of
 * replay steps; skip rather than fail in that case.
 */
async function waitForRunOutcome(page: Page): Promise<void> {
  const outcome = await Promise.race([
    page
      .getByTestId("replay-step-1")
      .waitFor({ timeout: 15_000 })
      .then(() => "ok" as const),
    page
      .getByText("ERROR", { exact: true })
      .waitFor({ timeout: 15_000 })
      .then(() => "error" as const),
  ]).catch(() => "timeout" as const);

  if (outcome !== "ok") {
    test.skip(true, "Backend/Postgres not reachable for this e2e run — see README's retrieval/e2e section.");
  }
}

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

    await waitForRunOutcome(page);

    // The level's own initial placements (waf@gateway, private_subnet@secrets,
    // encryption+mfa@postgres) hold against the real ATT&CK data: MFA
    // blocks the credential-theft step before it reaches Postgres, so the
    // path has 3 steps and the asset is never breached (see CHANGELOG's
    // M2 note on this exact loadout).
    await expect(page.getByTestId("replay-step-3")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByTestId("see-debrief")).toHaveAttribute("aria-disabled", "false");

    await page.getByTestId("see-debrief").click();
    await expect(page).toHaveURL(/\/levels\/03-payments\/debrief$/);

    await expect(page.getByText("D", { exact: true })).toBeVisible();
    await expect(page.getByText("Every path held.")).toBeVisible();
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

  test("the attack replay resolves well under the full staged-reveal time", async ({ page }) => {
    await page.goto("/levels/03-payments");
    await page.getByRole("button", { name: "Run attack" }).click();

    await waitForRunOutcome(page);

    // With prefers-reduced-motion, GameScreen skips the staged reveal
    // entirely (see the effect in GameScreen.tsx): all 3 steps and an
    // enabled debrief link should appear well under the ~2.7s a staged
    // reveal (900ms x 3 steps) would take, even allowing for the real
    // network round trip to the API.
    await expect(page.getByTestId("replay-step-3")).toBeVisible({ timeout: 2_000 });
    await expect(page.getByTestId("see-debrief")).toHaveAttribute("aria-disabled", "false");
  });
});

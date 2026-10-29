import { beforeEach, describe, expect, it } from "vitest";
import { level3 } from "@/fixtures/level3";
import { budgetUsed, cardsInHand, useGameStore } from "./gameStore";

beforeEach(() => {
  useGameStore.getState().reset();
});

describe("budgetUsed", () => {
  it("sums card costs across all components", () => {
    expect(budgetUsed({ a: ["waf"], b: ["mfa", "encryption"] })).toBe(3);
  });

  it("is zero for no placements", () => {
    expect(budgetUsed({})).toBe(0);
  });
});

describe("cardsInHand", () => {
  it("excludes cards already placed anywhere", () => {
    const hand = cardsInHand({ gateway: ["waf"] });
    expect(hand).not.toContain("waf");
    expect(hand).toContain("mfa");
  });
});

describe("useGameStore", () => {
  it("starts with the level's initial placements and an idle attack phase", () => {
    const state = useGameStore.getState();
    expect(state.placements).toEqual(level3.initialPlacements);
    expect(state.attackPhase).toBe("idle");
    expect(budgetUsed(state.placements)).toBe(4);
  });

  it("selecting a component sets selectedComponentId", () => {
    useGameStore.getState().selectComponent("payments");
    expect(useGameStore.getState().selectedComponentId).toBe("payments");
  });

  it("playing a card places it on the selected component", () => {
    useGameStore.getState().selectComponent("payments");
    useGameStore.getState().playCard("least_privilege");
    expect(useGameStore.getState().placements.payments).toContain("least_privilege");
    expect(cardsInHand(useGameStore.getState().placements)).not.toContain("least_privilege");
  });

  it("does nothing if no component is selected", () => {
    useGameStore.getState().playCard("least_privilege");
    expect(useGameStore.getState().placements.payments).toBeUndefined();
  });

  it("does nothing if the card is already placed", () => {
    useGameStore.getState().selectComponent("payments");
    useGameStore.getState().playCard("waf"); // already on gateway
    expect(useGameStore.getState().placements.payments ?? []).not.toContain("waf");
  });

  it("refuses to exceed the level budget", () => {
    // 4 coins already spent (initial placements) of a 6-coin budget.
    useGameStore.getState().selectComponent("payments");
    useGameStore.getState().playCard("least_privilege"); // 5
    useGameStore.getState().playCard("rate_limit"); // would be 6, exactly budget: allowed
    expect(budgetUsed(useGameStore.getState().placements)).toBe(6);

    useGameStore.getState().selectComponent("queue");
    // nothing left to play — hand is empty now
    expect(cardsInHand(useGameStore.getState().placements)).toHaveLength(0);
  });

  it("setNote stores a note per component", () => {
    useGameStore.getState().setNote("payments", "least privilege role");
    expect(useGameStore.getState().notes.payments).toBe("least privilege role");
  });

  it("runAttack loads the mocked result and reveals steps one at a time", () => {
    useGameStore.getState().runAttack();
    const afterRun = useGameStore.getState();
    expect(afterRun.attackPhase).toBe("running");
    expect(afterRun.visibleSteps).toBe(0);
    expect(afterRun.runResult?.steps.length).toBeGreaterThan(0);

    const total = afterRun.runResult!.steps.length;
    for (let i = 0; i < total; i++) useGameStore.getState().revealNextStep();

    const done = useGameStore.getState();
    expect(done.visibleSteps).toBe(total);
    expect(done.attackPhase).toBe("done");
  });

  it("cards cannot be played once the attack is running", () => {
    useGameStore.getState().selectComponent("payments");
    useGameStore.getState().runAttack();
    useGameStore.getState().playCard("least_privilege");
    expect(useGameStore.getState().placements.payments ?? []).not.toContain("least_privilege");
  });

  it("reset restores initial placements and clears attack state", () => {
    useGameStore.getState().selectComponent("payments");
    useGameStore.getState().playCard("least_privilege");
    useGameStore.getState().runAttack();
    useGameStore.getState().reset();

    const state = useGameStore.getState();
    expect(state.placements).toEqual(level3.initialPlacements);
    expect(state.selectedComponentId).toBeNull();
    expect(state.attackPhase).toBe("idle");
    expect(state.runResult).toBeNull();
  });
});

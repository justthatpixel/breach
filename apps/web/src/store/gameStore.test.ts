import { beforeEach, describe, expect, it, vi } from "vitest";
import { level3 } from "@/fixtures/level3";
import type { RunResponse } from "@/lib/runApi";
import { budgetUsed, cardsInHand, useGameStore } from "./gameStore";

const FAKE_RUN: RunResponse = {
  id: "fake-run-id",
  level_id: level3.id,
  engine_output: {
    paths: [
      {
        steps: [
          { step: 1, from: "internet", to: "gateway", technique_id: "T1190", blocked: false, blocked_by: null },
          { step: 2, from: "gateway", to: "payments", technique_id: "T1552.005", blocked: true, blocked_by: "M1026" },
        ],
      },
    ],
    paths_total: 1,
    paths_blocked: 0,
    techniques_attempted: 2,
    techniques_stopped: 1,
    budget_used: 4,
    budget_total: 6,
    score: 0.5,
    grade: "C",
  },
  narrator_output: {
    steps: [
      { step: 1, technique_id: "T1190", line: "Through at gateway." },
      { step: 2, technique_id: "T1552.005", line: "Blocked at payments." },
    ],
    debrief: { through: ["T1190"], held: ["T1552.005"], tips: ["Tighten the gateway."] },
  },
  judge_output: {},
  llm_calls: [],
  total_cost_usd_estimate: 0,
};

vi.mock("@/lib/runApi", () => ({
  createRun: vi.fn(() => Promise.resolve(FAKE_RUN)),
}));

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

  it("runAttack calls the API and reveals the returned steps one at a time", async () => {
    useGameStore.getState().runAttack();
    const midRun = useGameStore.getState();
    expect(midRun.attackPhase).toBe("running");
    expect(midRun.visibleSteps).toBe(0);

    await vi.waitFor(() => expect(useGameStore.getState().runResult).not.toBeNull());

    const afterRun = useGameStore.getState();
    expect(afterRun.runResult?.steps.length).toBe(2);
    expect(afterRun.debrief?.grade).toBe("C");

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

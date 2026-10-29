import { create } from "zustand";
import { cardCatalogue, level3, mockRunLevel3 } from "@/fixtures/level3";
import type { MockRunResult } from "@/lib/types";

type AttackPhase = "idle" | "running" | "done";

interface GameState {
  selectedComponentId: string | null;
  placements: Record<string, string[]>;
  notes: Record<string, string>;
  attackPhase: AttackPhase;
  visibleSteps: number;
  runResult: MockRunResult | null;

  selectComponent: (id: string) => void;
  playCard: (cardId: string) => void;
  setNote: (componentId: string, note: string) => void;
  reset: () => void;
  runAttack: () => void;
  revealNextStep: () => void;
}

function initialPlacements(): Record<string, string[]> {
  return Object.fromEntries(
    Object.entries(level3.initialPlacements).map(([componentId, cards]) => [
      componentId,
      [...cards],
    ])
  );
}

export function budgetUsed(placements: Record<string, string[]>): number {
  return Object.values(placements)
    .flat()
    .reduce((sum, cardId) => sum + (cardCatalogue[cardId]?.cost ?? 0), 0);
}

export function cardsInHand(placements: Record<string, string[]>): string[] {
  const placed = new Set(Object.values(placements).flat());
  return level3.cardsAvailable.filter((cardId) => !placed.has(cardId));
}

export const useGameStore = create<GameState>((set, get) => ({
  selectedComponentId: null,
  placements: initialPlacements(),
  notes: {},
  attackPhase: "idle",
  visibleSteps: 0,
  runResult: null,

  selectComponent: (id) => {
    if (get().attackPhase !== "idle") return;
    set({ selectedComponentId: id });
  },

  playCard: (cardId) => {
    const { selectedComponentId, placements, attackPhase } = get();
    if (attackPhase !== "idle" || !selectedComponentId) return;
    if (!cardsInHand(placements).includes(cardId)) return;
    const card = cardCatalogue[cardId];
    if (!card) return;
    if (budgetUsed(placements) + card.cost > level3.budget) return;

    const existing = placements[selectedComponentId] ?? [];
    set({
      placements: {
        ...placements,
        [selectedComponentId]: [...existing, cardId],
      },
    });
  },

  setNote: (componentId, note) => {
    set((state) => ({ notes: { ...state.notes, [componentId]: note } }));
  },

  reset: () => {
    set({
      selectedComponentId: null,
      placements: initialPlacements(),
      notes: {},
      attackPhase: "idle",
      visibleSteps: 0,
      runResult: null,
    });
  },

  runAttack: () => {
    set({
      attackPhase: "running",
      visibleSteps: 0,
      runResult: mockRunLevel3(),
    });
  },

  revealNextStep: () => {
    const { runResult, visibleSteps } = get();
    if (!runResult) return;
    const next = visibleSteps + 1;
    if (next >= runResult.steps.length) {
      set({ visibleSteps: runResult.steps.length, attackPhase: "done" });
    } else {
      set({ visibleSteps: next });
    }
  },
}));

import type {
  AttackReplayStep,
  DebriefData,
  DebriefHeldItem,
  DebriefThroughItem,
  MockRunResult,
} from "./types";
import type { RunResponse } from "./runApi";

/**
 * Display names for the curated ATT&CK subset (HANDOFF §4.1) — purely
 * cosmetic labels for the replay log and debrief, not game logic. The
 * real names/descriptions live in the backend's ATT&CK data; this is
 * just so the UI doesn't have to show bare technique IDs.
 */
const TECHNIQUE_NAMES: Record<string, string> = {
  T1190: "Exploit public-facing app",
  "T1078.004": "Valid cloud accounts",
  "T1552.005": "Cloud instance metadata",
  T1530: "Data from cloud storage",
  T1110: "Brute force",
  T1528: "Steal application access token",
  T1498: "Network denial of service",
};

function techniqueName(id: string): string {
  return TECHNIQUE_NAMES[id] ?? id;
}

function allEngineSteps(run: RunResponse): EngineStepWithPath[] {
  return run.engine_output.paths.flatMap((path) => path.steps);
}

type EngineStepWithPath = RunResponse["engine_output"]["paths"][number]["steps"][number];

export function mapRunToReplay(run: RunResponse): MockRunResult {
  const narratorLineByStep = new Map(run.narrator_output.steps.map((s) => [s.step, s.line]));
  const engineSteps = allEngineSteps(run);

  const steps: AttackReplayStep[] = engineSteps.map((step) => ({
    step: step.step,
    from: step.from,
    to: step.to,
    title: techniqueName(step.technique_id),
    techniqueId: step.technique_id,
    detail: narratorLineByStep.get(step.step) ?? (step.blocked ? "Blocked." : "Got through."),
    blocked: step.blocked,
  }));

  const breached = run.engine_output.paths.some((path) => path.steps.every((s) => !s.blocked));
  const last = steps[steps.length - 1] ?? null;

  return {
    steps,
    redTeamLine: last ? { techniqueId: last.techniqueId, text: last.detail } : { techniqueId: "", text: "" },
    breached,
  };
}

export function mapRunToDebrief(run: RunResponse): DebriefData {
  const engine = run.engine_output;
  const narrator = run.narrator_output;
  const engineSteps = allEngineSteps(run);
  const narratorLineByStep = new Map(narrator.steps.map((s) => [s.step, s.line]));
  const breached = engine.paths.some((path) => path.steps.every((s) => !s.blocked));

  const through: DebriefThroughItem[] = narrator.debrief.through.map((id) => {
    const step = engineSteps.find((s) => s.technique_id === id);
    return {
      id,
      name: techniqueName(id),
      why: (step && narratorLineByStep.get(step.step)) ?? "Got through.",
      fix: narrator.debrief.tips.find((tip) => tip.includes(id)) ?? "Review this component's defences.",
    };
  });

  const held: DebriefHeldItem[] = narrator.debrief.held.map((id) => {
    const step = engineSteps.find((s) => s.technique_id === id);
    return {
      what: techniqueName(id),
      why: (step && narratorLineByStep.get(step.step)) ?? "Blocked.",
    };
  });

  const throughCount = engineSteps.filter((s) => !s.blocked).length;

  return {
    grade: engine.grade,
    breached,
    headline: breached
      ? `The red team got in, in ${throughCount} step${throughCount === 1 ? "" : "s"}.`
      : "Every path held.",
    summary: narrator.debrief.tips[0] ?? (breached ? "Review what got through below." : "Nice work — nothing broke through."),
    stats: [
      { value: `${engine.paths_blocked}/${engine.paths_total}`, label: "attack paths blocked" },
      { value: `${engine.techniques_stopped}/${engine.techniques_attempted}`, label: "techniques stopped" },
      { value: `${engine.budget_used}/${engine.budget_total}`, label: "coins spent" },
    ],
    through,
    held,
    forA: narrator.debrief.tips,
    share: {
      headline: `I stopped ${engine.techniques_stopped} of ${engine.techniques_attempted} attacks on ${run.level_id}. Can you beat it?`,
      totalAttacks: engine.techniques_attempted,
      stopped: engine.techniques_stopped,
    },
  };
}

/**
 * The real backend (HANDOFF §10, wired up in M5). Shapes here mirror
 * apps/api/breach/app.py's response models exactly — snake_case, as
 * FastAPI returns them, not adapted to camelCase.
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface EngineStep {
  step: number;
  from: string;
  to: string;
  technique_id: string;
  blocked: boolean;
  blocked_by: string | null;
}

export interface EngineOutput {
  paths: { steps: EngineStep[] }[];
  paths_total: number;
  paths_blocked: number;
  techniques_attempted: number;
  techniques_stopped: number;
  budget_used: number;
  budget_total: number;
  score: number;
  grade: string;
}

export interface NarratorOutput {
  steps: { step: number; technique_id: string; line: string }[];
  debrief: { through: string[]; held: string[]; tips: string[] };
}

export interface RunResponse {
  id: string;
  level_id: string;
  engine_output: EngineOutput;
  narrator_output: NarratorOutput;
  judge_output: Record<string, { credited: unknown[]; rejected_claims: string[]; injection_suspected: boolean }>;
  llm_calls: { component: string; model: string; input_tokens: number; output_tokens: number; latency_seconds: number }[];
  total_cost_usd_estimate: number;
}

export interface RunDefenceInput {
  cards: string[];
  notes: string;
}

export async function createRun(
  levelId: string,
  defences: Record<string, RunDefenceInput>
): Promise<RunResponse> {
  const response = await fetch(`${API_BASE_URL}/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ level_id: levelId, defences }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Run failed (${response.status})`);
  }
  return response.json();
}

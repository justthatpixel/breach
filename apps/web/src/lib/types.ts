export type ComponentKind =
  | "internet"
  | "api_gateway"
  | "container"
  | "database"
  | "object_store"
  | "secrets"
  | "queue";

export interface GameComponent {
  id: string;
  type: ComponentKind;
  label: string;
  sublabel: string;
  position: { x: number; y: number };
  public?: boolean;
  asset?: boolean;
}

export type CardKind = "EDGE" | "NETWORK" | "DATA" | "IDENTITY";

export interface CardDef {
  id: string;
  kind: CardKind;
  name: string;
  effect: string;
  cost: number;
}

export interface Level {
  id: string;
  title: string;
  brief: string;
  threatLevel: "low" | "medium" | "high";
  budget: number;
  components: GameComponent[];
  edges: [string, string][];
  entryPoints: string[];
  cardsAvailable: string[];
  /** component id -> card ids already placed there when the level loads */
  initialPlacements: Record<string, string[]>;
}

export interface CampaignLevelSummary {
  id: string;
  label: string;
  title: string;
  state: "done" | "current" | "locked";
}

export interface AttackReplayStep {
  step: number;
  from: string;
  to: string;
  title: string;
  techniqueId: string;
  detail: string;
  blocked: boolean;
}

export interface MockRunResult {
  steps: AttackReplayStep[];
  redTeamLine: { techniqueId: string; text: string };
  breached: boolean;
}

export interface DebriefThroughItem {
  id: string;
  name: string;
  why: string;
  fix: string;
}

export interface DebriefHeldItem {
  what: string;
  why: string;
}

export interface DebriefStat {
  value: string;
  label: string;
}

export interface DebriefData {
  grade: string;
  breached: boolean;
  headline: string;
  summary: string;
  stats: DebriefStat[];
  through: DebriefThroughItem[];
  held: DebriefHeldItem[];
  forA: string[];
  share: {
    headline: string;
    totalAttacks: number;
    stopped: number;
  };
}

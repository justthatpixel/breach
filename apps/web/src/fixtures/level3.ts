import type { CampaignLevelSummary, CardDef, DebriefData, Level } from "@/lib/types";

/**
 * All sample content below is transcribed from design/game-screen.dc.html
 * and design/debrief.dc.html's renderVals() blocks (HANDOFF.md §9) — the
 * mockups' own "realistic sample data for fixtures in M3". Component
 * positions match the mockups' pixel layout exactly.
 *
 * Two small adaptations, since the mockup samples imagine a richer level
 * than the one actually authored in data/levels/03-payments.yaml:
 * - the MFA card's sample placement "ON ADMIN" became "ON POSTGRES" (no
 *   admin console component exists on this canvas)
 * - the debrief's "Admin console" held item became "Queue", for the same
 *   reason, keeping the same point (a private component with no direct
 *   route in).
 */

export const level3: Level = {
  id: "03-payments",
  title: "Payments backend",
  brief:
    "Build a backend for an app that lets friends send each other money. It stores card details and has to stay up 24/7.",
  threatLevel: "high",
  budget: 6,
  components: [
    {
      id: "internet",
      type: "internet",
      label: "Internet",
      sublabel: "Anyone",
      position: { x: 16, y: 240 },
    },
    {
      id: "gateway",
      type: "api_gateway",
      label: "API gateway",
      sublabel: "Public · HTTPS",
      position: { x: 224, y: 240 },
      public: true,
    },
    {
      id: "payments",
      type: "container",
      label: "Payments",
      sublabel: "Container",
      position: { x: 424, y: 240 },
    },
    {
      id: "postgres",
      type: "database",
      label: "Postgres",
      sublabel: "Card data",
      position: { x: 640, y: 100 },
      asset: true,
    },
    {
      id: "secrets",
      type: "secrets",
      label: "Secrets",
      sublabel: "Private · KMS",
      position: { x: 640, y: 380 },
    },
    {
      id: "queue",
      type: "queue",
      label: "Queue",
      sublabel: "Payouts",
      position: { x: 424, y: 430 },
    },
  ],
  edges: [
    ["internet", "gateway"],
    ["gateway", "payments"],
    ["payments", "postgres"],
    ["payments", "secrets"],
    ["payments", "queue"],
  ],
  entryPoints: ["internet"],
  cardsAvailable: [
    "waf",
    "private_subnet",
    "encryption",
    "mfa",
    "least_privilege",
    "rate_limit",
  ],
  initialPlacements: {
    gateway: ["waf"],
    secrets: ["private_subnet"],
    postgres: ["encryption", "mfa"],
  },
};

export const cardCatalogue: Record<string, CardDef> = {
  waf: {
    id: "waf",
    kind: "EDGE",
    name: "WAF",
    effect: "Blocks injection on public routes",
    cost: 1,
  },
  private_subnet: {
    id: "private_subnet",
    kind: "NETWORK",
    name: "Private subnet",
    effect: "No route in from the internet",
    cost: 1,
  },
  encryption: {
    id: "encryption",
    kind: "DATA",
    name: "Encryption",
    effect: "Protects data at rest",
    cost: 1,
  },
  mfa: {
    id: "mfa",
    kind: "IDENTITY",
    name: "MFA",
    effect: "Stops stolen passwords working",
    cost: 1,
  },
  least_privilege: {
    id: "least_privilege",
    kind: "IDENTITY",
    name: "Least privilege",
    effect: "Roles only get what they need",
    cost: 1,
  },
  rate_limit: {
    id: "rate_limit",
    kind: "EDGE",
    name: "Rate limit",
    effect: "Slows brute force and scraping",
    cost: 1,
  },
};

export const campaignLevels: CampaignLevelSummary[] = [
  { id: "01-static-site", label: "1", title: "Static site", state: "done" },
  { id: "02-internal-tool", label: "2", title: "Internal tool", state: "done" },
  { id: "03-payments", label: "3", title: "Payments backend", state: "current" },
  { id: "04-kubernetes", label: "4", title: "Kubernetes platform", state: "locked" },
  { id: "05-saas", label: "5", title: "Multi-tenant SaaS", state: "locked" },
];

/**
 * Sample debrief data, still used as a fallback if the debrief screen is
 * ever opened without a completed run (e.g. a direct link) — the real
 * run goes through the backend as of M5 (see src/lib/runApi.ts,
 * src/lib/runMapping.ts), not this fixture.
 */
export const debrief3: DebriefData = {
  grade: "C+",
  breached: true,
  headline: "The red team got in, in 3 steps.",
  summary:
    "Your perimeter held up well. One route without auth let them in, and an over-powered role did the rest. Fix those two and you're at a B.",
  stats: [
    { value: "2/5", label: "attack paths blocked" },
    { value: "6/11", label: "techniques stopped" },
    { value: "4/6", label: "coins spent" },
  ],
  through: [
    {
      id: "T1190",
      name: "Exploit public-facing app",
      why: "The WAF was a good call, but /refunds accepts requests without a token.",
      fix: "Require auth on every route at the gateway.",
    },
    {
      id: "T1552.005",
      name: "Cloud instance metadata",
      why: "Code in the container could read its own IAM credentials.",
      fix: "Use task roles with IMDSv2 and a hop limit of 1.",
    },
    {
      id: "T1078.004",
      name: "Valid cloud accounts",
      why: "The role can read every table, so stolen credentials read card data in plain text.",
      fix: "Scope the role to the tables it needs, and tokenise card numbers.",
    },
  ],
  held: [
    { what: "Secrets store.", why: "No public endpoint, so direct access was blocked." },
    { what: "Queue.", why: "Private subnet only, so no direct internet route." },
    {
      what: "Database network.",
      why: "The path in was stolen credentials, not a network hole — Postgres has no public endpoint of its own.",
    },
  ],
  forA: [
    "Auth on every route, not just the obvious ones",
    "Task roles with IMDSv2, so credentials can't be lifted",
    "Tokenised card numbers, so the database never holds raw values",
  ],
  share: {
    headline: "I stopped 6 of 11 attacks on a payments backend. Can you beat it?",
    totalAttacks: 11,
    stopped: 6,
  },
};

import { notFound } from "next/navigation";
import { GameScreen } from "./GameScreen";
import { level3 } from "@/fixtures/level3";

export default async function LevelPage({ params }: PageProps<"/levels/[id]">) {
  const { id } = await params;

  if (id !== level3.id) {
    // Only Level 3 is playable in this milestone — the rest of the
    // campaign is fixture-only lock/done state (HANDOFF §9, Level select).
    notFound();
  }

  return <GameScreen />;
}

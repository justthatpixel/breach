import { notFound } from "next/navigation";
import { DebriefScreen } from "./DebriefScreen";
import { level3 } from "@/fixtures/level3";

export default async function DebriefPage({ params }: PageProps<"/levels/[id]/debrief">) {
  const { id } = await params;

  if (id !== level3.id) {
    notFound();
  }

  return <DebriefScreen />;
}

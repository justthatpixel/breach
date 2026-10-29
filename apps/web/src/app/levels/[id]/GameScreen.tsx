"use client";

import { useEffect } from "react";
import { useReducedMotion } from "framer-motion";
import styles from "./GameScreen.module.css";
import { Header } from "@/components/Header";
import { MissionCard } from "@/components/MissionCard";
import { CampaignTrack } from "@/components/CampaignTrack";
import { GameCanvas } from "@/components/GameCanvas";
import { CardHand, type HandCard } from "@/components/CardHand";
import { ComponentPanel } from "@/components/ComponentPanel";
import { RedTeamBubble } from "@/components/RedTeamBubble";
import { AttackReplayLog } from "@/components/AttackReplayLog";
import { campaignLevels, cardCatalogue, level3 } from "@/fixtures/level3";
import { budgetUsed, cardsInHand, useGameStore } from "@/store/gameStore";

const STEP_REVEAL_MS = 900;

export function GameScreen() {
  const {
    selectedComponentId,
    placements,
    notes,
    attackPhase,
    visibleSteps,
    runResult,
    runError,
    selectComponent,
    playCard,
    setNote,
    reset,
    runAttack,
    revealNextStep,
  } = useGameStore();

  const reducedMotion = useReducedMotion();

  useEffect(() => {
    if (attackPhase !== "running" || !runResult) return;
    if (reducedMotion) {
      // Respect prefers-reduced-motion: skip the staged reveal and show
      // the final result immediately (HANDOFF §9).
      for (let i = visibleSteps; i < runResult.steps.length; i++) revealNextStep();
      return;
    }
    const timer = setTimeout(revealNextStep, STEP_REVEAL_MS);
    return () => clearTimeout(timer);
  }, [attackPhase, runResult, visibleSteps, reducedMotion, revealNextStep]);

  const used = budgetUsed(placements);
  const handCardIds = cardsInHand(placements);
  const placedCardIds = Object.values(placements).flat();

  const hand: HandCard[] = [...handCardIds, ...placedCardIds]
    .map((id) => cardCatalogue[id])
    .filter(Boolean)
    .map((card) => {
      const placedOn = Object.entries(placements).find(([, ids]) => ids.includes(card.id))?.[0];
      return { ...card, placedOn: placedOn ?? null };
    });

  const componentLabel = (id: string) =>
    level3.components.find((c) => c.id === id)?.label ?? id;

  const selectedComponent =
    level3.components.find((c) => c.id === selectedComponentId) ?? null;

  const revealedSteps = runResult ? runResult.steps.slice(0, visibleSteps) : [];
  const attackRunning = attackPhase === "running";
  const debriefReady = attackPhase === "done";

  const redTeamLine = runError
    ? { techniqueId: "ERROR", text: runError }
    : debriefReady && runResult
      ? runResult.redTeamLine
      : revealedSteps.length > 0
        ? { techniqueId: revealedSteps[revealedSteps.length - 1].techniqueId, text: revealedSteps[revealedSteps.length - 1].detail }
        : attackRunning
          ? { techniqueId: "…", text: "Running the attack…" }
          : null;

  return (
    <div className={styles.page}>
      <Header
        levelLabel="LVL 3"
        levelTitle={level3.title}
        budgetTotal={level3.budget}
        budgetUsed={used}
        defenceRating={used * 85}
        canRunAttack={attackPhase === "idle"}
        attackRunning={attackRunning}
        onReset={reset}
        onRunAttack={runAttack}
      />

      <div className={styles.body}>
        <aside className={styles.left}>
          <MissionCard level={level3} />
          <CampaignTrack levels={campaignLevels} />
        </aside>

        <main className={styles.main}>
          <GameCanvas
            level={level3}
            selectedComponentId={selectedComponentId}
            onSelect={selectComponent}
            attackRunning={attackRunning}
            revealedSteps={revealedSteps}
          />
          <CardHand
            cards={hand}
            componentLabel={componentLabel}
            canPlay={attackPhase === "idle" && selectedComponentId !== null}
            onPlay={playCard}
          />
        </main>

        <aside className={styles.right}>
          <RedTeamBubble line={redTeamLine} />
          <ComponentPanel
            component={selectedComponent}
            note={selectedComponentId ? notes[selectedComponentId] ?? "" : ""}
            onNoteChange={(note) => selectedComponentId && setNote(selectedComponentId, note)}
            disabled={attackPhase !== "idle" || !selectedComponentId}
          />
          <AttackReplayLog
            levelId={level3.id}
            steps={revealedSteps}
            debriefReady={debriefReady}
          />
        </aside>
      </div>
    </div>
  );
}

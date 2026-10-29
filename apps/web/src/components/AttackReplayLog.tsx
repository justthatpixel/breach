import Link from "next/link";
import styles from "./AttackReplayLog.module.css";
import { CheckIcon } from "./icons";
import type { AttackReplayStep } from "@/lib/types";

interface AttackReplayLogProps {
  levelId: string;
  steps: AttackReplayStep[];
  debriefReady: boolean;
}

export function AttackReplayLog({ levelId, steps, debriefReady }: AttackReplayLogProps) {
  return (
    <section className={styles.wrapper}>
      <span className={styles.heading}>ATTACK REPLAY</span>
      {steps.length === 0 && <p className={styles.empty}>Run the attack to see what happens.</p>}
      {steps.map((step) => (
        <div
          key={step.step}
          className={`${styles.row} ${!step.blocked ? styles.rowHit : ""}`}
          data-testid={`replay-step-${step.step}`}
        >
          <span className={`${styles.badge} ${step.blocked ? styles.badgeHeld : styles.badgeHit}`}>
            {step.blocked ? <CheckIcon /> : step.step}
          </span>
          <div className={styles.detailWrap}>
            <div className={styles.detailTop}>
              <span className={styles.title}>{step.title}</span>
              <span className={styles.techniqueId}>{step.techniqueId}</span>
            </div>
            <span className={styles.detail}>{step.detail}</span>
          </div>
        </div>
      ))}
      <Link
        href={`/levels/${levelId}/debrief`}
        className={styles.debriefLink}
        aria-disabled={!debriefReady}
        data-testid="see-debrief"
      >
        See debrief
      </Link>
    </section>
  );
}

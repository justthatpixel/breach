import Link from "next/link";
import styles from "./CampaignTrack.module.css";
import type { CampaignLevelSummary } from "@/lib/types";

export function CampaignTrack({ levels }: { levels: CampaignLevelSummary[] }) {
  return (
    <section className={styles.wrapper}>
      <span className={styles.heading}>CAMPAIGN</span>
      <div className={styles.track}>
        {levels.map((level) => {
          const stateClass =
            level.state === "done"
              ? styles.done
              : level.state === "current"
                ? styles.current
                : styles.locked;
          const content = (
            <span key={level.id} className={`${styles.node} ${stateClass}`}>
              {level.label}
            </span>
          );
          return level.state === "locked" ? (
            content
          ) : (
            <Link key={level.id} href={`/levels/${level.id}`} aria-label={level.title}>
              {content}
            </Link>
          );
        })}
      </div>
    </section>
  );
}

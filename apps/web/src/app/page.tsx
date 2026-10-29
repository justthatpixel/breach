import Link from "next/link";
import styles from "./page.module.css";
import { campaignLevels } from "@/fixtures/level3";

const STATUS_LABEL = { done: "Completed", current: "Play now", locked: "Locked" } as const;
const BADGE_CLASS = {
  done: styles.badgeDone,
  current: styles.badgeCurrent,
  locked: styles.badgeLocked,
} as const;

export default function LevelSelectPage() {
  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <span className={styles.logoMark} aria-hidden="true">
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#FFFFFF"
            strokeWidth="2.4"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12 3l8 3v6c0 4.5-3.4 8.3-8 9-4.6-.7-8-4.5-8-9V6l8-3z" />
            <path d="M9 12l6 0" />
          </svg>
        </span>
        <span className={styles.logoText}>Breach</span>
      </header>

      <div className={styles.content}>
        <div>
          <h1 className={styles.title}>Campaign</h1>
          <p className={styles.subtitle}>
            Secure a given system architecture. An AI red team attacks it with real MITRE
            ATT&amp;CK techniques, grounded and scored, never improvised.
          </p>
        </div>

        <div className={styles.grid}>
          {campaignLevels.map((level) => {
            const card = (
              <>
                <span className={`${styles.cardBadge} ${BADGE_CLASS[level.state]}`}>
                  {level.label}
                </span>
                <span className={styles.cardTitle}>{level.title}</span>
                <span className={styles.cardStatus}>{STATUS_LABEL[level.state]}</span>
              </>
            );
            return level.state === "locked" ? (
              <div key={level.id} className={`${styles.card} ${styles.cardLocked}`}>
                {card}
              </div>
            ) : (
              <Link key={level.id} href={`/levels/${level.id}`} className={styles.card}>
                {card}
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}

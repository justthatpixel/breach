import styles from "./MissionCard.module.css";
import type { Level } from "@/lib/types";

export function MissionCard({ level }: { level: Level }) {
  return (
    <section className={styles.card}>
      <span className={styles.badge}>MISSION</span>
      <h1 className={styles.title}>Keep the card data safe.</h1>
      <p className={styles.brief}>{level.brief}</p>
      <div className={styles.tags}>
        <span className={`${styles.tag} ${styles.threatHigh}`}>
          Threat: {level.threatLevel[0].toUpperCase() + level.threatLevel.slice(1)}
        </span>
        <span className={`${styles.tag} ${styles.budgetTag}`}>{level.budget} coins</span>
      </div>
    </section>
  );
}

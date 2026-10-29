import styles from "./GradeBadge.module.css";

export function GradeBadge({ grade, breached }: { grade: string; breached: boolean }) {
  return (
    <div className={styles.wrapper}>
      <span className={styles.circle} />
      <span className={styles.content}>
        <span className={styles.label}>GRADE</span>
        <span className={styles.grade}>{grade}</span>
      </span>
      {breached && <span className={styles.status}>Breached</span>}
    </div>
  );
}

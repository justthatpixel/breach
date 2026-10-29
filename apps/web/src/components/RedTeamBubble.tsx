import styles from "./RedTeamBubble.module.css";
import { AttackerIcon } from "./icons";

interface RedTeamBubbleProps {
  line: { techniqueId: string; text: string } | null;
}

export function RedTeamBubble({ line }: RedTeamBubbleProps) {
  return (
    <section className={styles.section}>
      <span className={styles.avatar} aria-hidden="true">
        <AttackerIcon />
      </span>
      <div className={styles.bubble}>
        <div className={styles.bubbleHeader}>
          <span className={styles.name}>Red Team</span>
          {line && <span className={styles.techniqueId}>{line.techniqueId}</span>}
        </div>
        {line ? (
          <p className={styles.line}>{line.text}</p>
        ) : (
          <p className={styles.idle}>Waiting for you to run the attack…</p>
        )}
      </div>
    </section>
  );
}

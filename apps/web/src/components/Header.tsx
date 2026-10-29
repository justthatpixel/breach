"use client";

import styles from "./Header.module.css";

interface HeaderProps {
  levelLabel: string;
  levelTitle: string;
  budgetTotal: number;
  budgetUsed: number;
  defenceRating: number;
  canRunAttack: boolean;
  attackRunning: boolean;
  onReset: () => void;
  onRunAttack: () => void;
}

export function Header({
  levelLabel,
  levelTitle,
  budgetTotal,
  budgetUsed,
  defenceRating,
  canRunAttack,
  attackRunning,
  onReset,
  onRunAttack,
}: HeaderProps) {
  const coinsLeft = budgetTotal - budgetUsed;

  return (
    <header className={styles.header}>
      <div className={styles.brand}>
        <div className={styles.logo}>
          <span className={styles.logoMark} aria-hidden="true">
            <ShieldIcon />
          </span>
          <span className={styles.logoText}>Breach</span>
        </div>
        <span className={styles.levelPill}>
          <span className={styles.levelPillId}>{levelLabel}</span>
          <span>{levelTitle}</span>
        </span>
      </div>

      <div className={styles.controls}>
        <div className={styles.defence}>
          <div className={styles.defenceLabels}>
            <span>Defence rating</span>
            <span>{defenceRating} / 600</span>
          </div>
          <div className={styles.defenceTrack}>
            <div
              className={styles.defenceFill}
              style={{ width: `${Math.min(100, (defenceRating / 600) * 100)}%` }}
            />
          </div>
        </div>

        <div
          className={styles.coins}
          aria-label={`Budget: ${coinsLeft} of ${budgetTotal} coins left`}
        >
          {Array.from({ length: budgetTotal }, (_, i) => (
            <span
              key={i}
              className={`${styles.coin} ${i < budgetUsed ? styles.coinSpent : styles.coinLeft}`}
            />
          ))}
          <span className={styles.coinsLabel}>{coinsLeft} left</span>
        </div>

        <button type="button" className={styles.resetButton} onClick={onReset}>
          Reset
        </button>
        <button
          type="button"
          className={styles.runButton}
          onClick={onRunAttack}
          disabled={!canRunAttack}
        >
          {attackRunning ? "Running…" : "Run attack"}
        </button>
      </div>
    </header>
  );
}

function ShieldIcon() {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="#FFFFFF"
      strokeWidth="2.4"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M12 3l8 3v6c0 4.5-3.4 8.3-8 9-4.6-.7-8-4.5-8-9V6l8-3z" />
      <path d="M9 12l6 0" />
    </svg>
  );
}

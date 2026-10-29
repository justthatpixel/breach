"use client";

import styles from "./ComponentPanel.module.css";
import { HintIcon } from "./icons";
import type { GameComponent } from "@/lib/types";

interface ComponentPanelProps {
  component: GameComponent | null;
  note: string;
  onNoteChange: (note: string) => void;
  disabled: boolean;
}

export function ComponentPanel({ component, note, onNoteChange, disabled }: ComponentPanelProps) {
  if (!component) {
    return (
      <section className={styles.section}>
        <p className={styles.empty}>Select a component on the canvas to secure it.</p>
      </section>
    );
  }

  return (
    <section className={styles.section}>
      <div className={styles.titleRow}>
        <span className={styles.title}>{component.label}</span>
      </div>
      <label className={styles.toggleRow}>
        Public endpoint
        <input type="checkbox" defaultChecked={component.public} disabled />
      </label>
      <label className={styles.toggleRow}>
        Encrypted at rest
        <input type="checkbox" defaultChecked={component.type === "database"} disabled />
      </label>
      <label className={styles.notesLabel}>
        How did you secure this?
        <textarea
          rows={4}
          className={styles.textarea}
          value={note}
          disabled={disabled}
          placeholder="Explain the cards you played here…"
          onChange={(e) => onNoteChange(e.target.value)}
          data-testid="component-notes"
        />
      </label>
      <div className={styles.hint}>
        <HintIcon />
        <span>Hint: which tables does this service actually need?</span>
      </div>
    </section>
  );
}

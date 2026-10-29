"use client";

import styles from "./CardHand.module.css";
import type { CardDef, CardKind } from "@/lib/types";

const BAND_COLOR: Record<CardKind, string> = {
  EDGE: "var(--edge-blue)",
  NETWORK: "var(--data-teal)",
  DATA: "var(--data-teal)",
  IDENTITY: "var(--security-violet)",
};

export interface HandCard extends CardDef {
  placedOn: string | null;
}

interface CardHandProps {
  cards: HandCard[];
  componentLabel: (id: string) => string;
  canPlay: boolean;
  onPlay: (cardId: string) => void;
}

export function CardHand({ cards, componentLabel, canPlay, onPlay }: CardHandProps) {
  return (
    <section className={styles.section}>
      <div className={styles.headerRow}>
        <span className={styles.heading}>Your hand</span>
        <span className={styles.hint}>Play a card, then explain it in your notes</span>
      </div>
      <div className={styles.row}>
        {cards.map((card) => {
          const placed = card.placedOn !== null;
          return (
            <button
              key={card.id}
              type="button"
              className={`${styles.card} ${placed ? styles.cardPlaced : ""}`}
              disabled={placed || !canPlay}
              onClick={() => onPlay(card.id)}
              data-testid={`card-${card.id}`}
            >
              <div className={styles.band} style={{ background: BAND_COLOR[card.kind] }}>
                <span className={styles.bandKind}>{card.kind}</span>
              </div>
              <div className={styles.body}>
                <span className={styles.name}>{card.name}</span>
                <span className={styles.effect}>{card.effect}</span>
              </div>
              <div className={styles.footer}>
                <span className={styles.status}>
                  {placed ? `ON ${componentLabel(card.placedOn!).toUpperCase()}` : "IN HAND"}
                </span>
                <span className={styles.cost}>{card.cost}</span>
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}

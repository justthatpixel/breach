"use client";

import Link from "next/link";
import styles from "./Debrief.module.css";
import { GradeBadge } from "@/components/GradeBadge";
import { CheckIcon, HintIcon, ShieldIcon } from "@/components/icons";
import { debrief3, level3 } from "@/fixtures/level3";
import { useGameStore } from "@/store/gameStore";

export function DebriefScreen() {
  const reset = useGameStore((s) => s.reset);
  const storedDebrief = useGameStore((s) => s.debrief);
  // Falls back to the M3 sample fixture only if the debrief is opened
  // without a completed run (e.g. a direct link) — the real run data is
  // in the store once "Run attack" has completed.
  const data = storedDebrief ?? debrief3;

  const bars = Array.from({ length: data.share.totalAttacks }, (_, i) => i < data.share.stopped);

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.brand}>
          <div className={styles.logo}>
            <span className={styles.logoMark} aria-hidden="true">
              <ShieldIcon />
            </span>
            <span className={styles.logoText}>Breach</span>
          </div>
          <span className={styles.levelPill}>
            <span className={styles.levelPillId}>LVL 3</span>
            <span>Debrief</span>
          </span>
        </div>
        <div className={styles.headerActions}>
          <Link href="/" className={styles.backLink}>
            Back to levels
          </Link>
          <Link
            href={`/levels/${level3.id}`}
            className={styles.tryAgain}
            onClick={() => reset()}
            data-testid="try-again"
          >
            Try again
          </Link>
        </div>
      </header>

      <div className={styles.content}>
        <section className={styles.heroSection}>
          <GradeBadge grade={data.grade} breached={data.breached} />
          <div className={styles.heroText}>
            <h1 className={styles.headline}>{data.headline}</h1>
            <p className={styles.summary}>{data.summary}</p>
            <div className={styles.statsRow}>
              {data.stats.map((stat) => (
                <span key={stat.label} className={styles.stat}>
                  <span className={styles.statValue}>{stat.value}</span>
                  <span className={styles.statLabel}>{stat.label}</span>
                </span>
              ))}
            </div>
          </div>
        </section>

        <section className={styles.grid}>
          <div className={`${styles.panel} ${styles.throughPanel}`}>
            <div className={styles.panelHeader}>
              <h2 className={styles.panelHeaderTitle}>What got through</h2>
              <span className={styles.panelHeaderCount}>
                {data.through.length} TECHNIQUES
              </span>
            </div>
            <div className={styles.throughBody}>
              {data.through.map((item) => (
                <div key={item.id} className={styles.throughItem}>
                  <div className={styles.throughTop}>
                    <span className={styles.techniqueId}>{item.id}</span>
                    <span className={styles.techniqueName}>{item.name}</span>
                  </div>
                  <span className={styles.why}>{item.why}</span>
                  <span className={styles.fix}>
                    <span className={styles.fixLabel}>Fix</span>
                    <span>{item.fix}</span>
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className={styles.sideColumn}>
            <div className={`${styles.panel} ${styles.heldPanel}`}>
              <div className={styles.panelHeader}>
                <h2 className={styles.panelHeaderTitle}>What held</h2>
              </div>
              <div className={styles.heldBody}>
                {data.held.map((item) => (
                  <div key={item.what} className={styles.heldItem}>
                    <span className={styles.heldBadge} aria-hidden="true">
                      <CheckIcon />
                    </span>
                    <span className={styles.heldText}>
                      <span className={styles.heldWhat}>{item.what}</span> {item.why}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className={styles.forAPanel}>
              <div className={styles.forAHeader}>
                <span className={styles.forAIcon} aria-hidden="true">
                  <HintIcon />
                </span>
                <h2 className={styles.forATitle}>For an A, also mention</h2>
              </div>
              <ul className={styles.forAList}>
                {data.forA.map((tip) => (
                  <li key={tip}>{tip}</li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        <section className={styles.shareSection}>
          <div className={styles.shareCard}>
            <div className={styles.shareCardHeader}>
              <span className={styles.shareBrand}>Breach</span>
              <span className={styles.shareLevelGrade}>LVL 3 · {data.grade}</span>
            </div>
            <span className={styles.shareHeadline}>{data.share.headline}</span>
            <div className={styles.shareBars}>
              {bars.map((stopped, i) => (
                <span
                  key={i}
                  className={styles.shareBar}
                  style={{ background: stopped ? "var(--gold)" : "var(--accent)" }}
                />
              ))}
            </div>
          </div>
          <div className={styles.shareText}>
            <h2 className={styles.shareTitle}>Show off your score</h2>
            <p className={styles.shareBody}>Shares your grade only, never your architecture.</p>
            <div className={styles.shareButtons}>
              <button type="button" className={styles.shareButtonPrimary}>
                Share to LinkedIn
              </button>
              <button type="button" className={styles.shareButtonSecondary}>
                Copy image
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

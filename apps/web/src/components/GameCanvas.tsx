"use client";

import { useMemo } from "react";
import ReactFlow, {
  Background,
  type Edge,
  type Node,
  ReactFlowProvider,
  useViewport,
} from "reactflow";
import "reactflow/dist/style.css";
import styles from "./GameCanvas.module.css";
import { ComponentNode, type ComponentNodeData } from "./ComponentNode";
import type { AttackReplayStep, Level } from "@/lib/types";

const NODE_TYPES = { component: ComponentNode };
const NODE_SIZE = { width: 160, height: 76 };

interface GameCanvasProps {
  level: Level;
  selectedComponentId: string | null;
  onSelect: (id: string) => void;
  attackRunning: boolean;
  revealedSteps: AttackReplayStep[];
}

export function GameCanvas({
  level,
  selectedComponentId,
  onSelect,
  attackRunning,
  revealedSteps,
}: GameCanvasProps) {
  const statusByComponent = useMemo(() => {
    const statuses: Record<string, "breached" | "held"> = {};
    for (const step of revealedSteps) {
      statuses[step.to] = step.blocked ? "held" : "breached";
    }
    return statuses;
  }, [revealedSteps]);

  const touchedEdges = useMemo(() => {
    const set = new Set<string>();
    for (const step of revealedSteps) set.add(`${step.from}->${step.to}`);
    return set;
  }, [revealedSteps]);

  const nodes: Node<ComponentNodeData>[] = useMemo(
    () =>
      level.components.map((component) => ({
        id: component.id,
        type: "component",
        position: component.position,
        draggable: false,
        selectable: true,
        data: {
          label: component.label,
          sublabel: component.sublabel,
          kind: component.type,
          selected: component.id === selectedComponentId,
          status: statusByComponent[component.id] ?? "default",
        },
      })),
    [level.components, selectedComponentId, statusByComponent]
  );

  const edges: Edge[] = useMemo(
    () =>
      level.edges.map(([from, to]) => {
        const hot = touchedEdges.has(`${from}->${to}`);
        return {
          id: `${from}-${to}`,
          source: from,
          target: to,
          animated: hot,
          style: {
            stroke: hot ? "var(--accent, #C8371E)" : "var(--grey-line, #A8A29E)",
            strokeWidth: hot ? 3 : 2,
            strokeDasharray: hot ? "6 4" : undefined,
          },
        };
      }),
    [level.edges, touchedEdges]
  );

  return (
    <div className={styles.wrapper}>
      <span className={styles.banner}>
        {attackRunning ? (
          <>
            <span className={styles.dot}>
              <span className={`${styles.dotCore} pulse`} />
            </span>
            Red team is attacking · step {revealedSteps.length} of{" "}
            {revealedSteps.length || "?"}
          </>
        ) : (
          "Select a component to secure it"
        )}
      </span>
      <span className={styles.legend}>
        <span className={styles.legendItem}>
          <span
            className={styles.legendSwatch}
            style={{
              background:
                "repeating-linear-gradient(90deg, var(--accent) 0 6px, transparent 6px 10px)",
            }}
          />
          Attack
        </span>
        <span className={styles.legendItem}>
          <span className={styles.legendSwatch} style={{ background: "var(--grey-line)" }} />
          Data flow
        </span>
      </span>
      <ReactFlowProvider>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={NODE_TYPES}
          onNodeClick={(_, node) => onSelect(node.id)}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable
          panOnDrag={false}
          zoomOnScroll={false}
          proOptions={{ hideAttribution: true }}
          fitView
        >
          <Background color="var(--paper-dot, #D9CFBC)" gap={22} size={1.2} />
        </ReactFlow>
        <StepBadges level={level} revealedSteps={revealedSteps} attackRunning={attackRunning} />
      </ReactFlowProvider>
    </div>
  );
}

interface StepBadgesProps {
  level: Level;
  revealedSteps: AttackReplayStep[];
  attackRunning: boolean;
}

/**
 * The attack step number markers live in the same coordinate space as
 * node.position (flow space), so they need React Flow's own pan/zoom
 * transform applied — otherwise they stay pinned to their initial screen
 * position while the canvas underneath zooms and pans past them.
 * useViewport() reads that transform; this renders as a sibling of
 * <ReactFlow> rather than a child so plain DOM positioning (not SVG)
 * works for the badges.
 */
function StepBadges({ level, revealedSteps, attackRunning }: StepBadgesProps) {
  const viewport = useViewport();

  return (
    <div
      className={styles.stepBadgeLayer}
      style={{ transform: `translate(${viewport.x}px, ${viewport.y}px) scale(${viewport.zoom})` }}
    >
      {revealedSteps.map((step) => {
        const from = level.components.find((c) => c.id === step.from);
        const to = level.components.find((c) => c.id === step.to);
        if (!from || !to) return null;
        const x = (from.position.x + to.position.x) / 2 + NODE_SIZE.width / 2;
        const y = (from.position.y + to.position.y) / 2 + NODE_SIZE.height / 2;
        const isLast = step === revealedSteps[revealedSteps.length - 1];
        return (
          <span
            key={step.step}
            className={`${styles.stepBadge} ${isLast && attackRunning ? styles.stepBadgeCurrent : ""}`}
            style={{ left: x, top: y }}
          >
            {step.step}
          </span>
        );
      })}
    </div>
  );
}

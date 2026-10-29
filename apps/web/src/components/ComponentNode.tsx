import { Handle, Position, type NodeProps } from "reactflow";
import styles from "./ComponentNode.module.css";
import {
  ContainerIcon,
  DatabaseIcon,
  GatewayIcon,
  GlobeIcon,
  LockIcon,
  QueueIcon,
} from "./icons";
import type { ComponentKind } from "@/lib/types";

const APPEARANCE: Record<ComponentKind, { bg: string; iconBg: string; Icon: () => React.JSX.Element }> = {
  internet: { bg: "#E9E1D0", iconBg: "#1C1917", Icon: GlobeIcon },
  api_gateway: { bg: "var(--edge-blue-tint)", iconBg: "var(--edge-blue)", Icon: GatewayIcon },
  container: { bg: "var(--compute-amber-tint)", iconBg: "var(--compute-amber)", Icon: ContainerIcon },
  database: { bg: "var(--data-teal-tint)", iconBg: "var(--data-teal)", Icon: DatabaseIcon },
  object_store: { bg: "var(--data-teal-tint)", iconBg: "var(--data-teal)", Icon: DatabaseIcon },
  secrets: { bg: "var(--security-violet-tint)", iconBg: "var(--security-violet)", Icon: LockIcon },
  queue: { bg: "var(--compute-amber-tint)", iconBg: "var(--compute-amber)", Icon: QueueIcon },
};

export interface ComponentNodeData {
  label: string;
  sublabel: string;
  kind: ComponentKind;
  selected: boolean;
  status: "default" | "breached" | "held" | "mitigated";
  mitigationLabel?: string;
}

export function ComponentNode({ data, id }: NodeProps<ComponentNodeData>) {
  const appearance = APPEARANCE[data.kind];
  const Icon = appearance.Icon;

  const statusClass =
    data.status === "breached" ? styles.hit : data.status === "held" ? styles.held : "";

  return (
    <button
      type="button"
      className={`${styles.node} ${data.selected ? styles.selected : ""} ${statusClass}`}
      style={{ background: appearance.bg }}
      aria-pressed={data.selected}
      data-testid={`component-${id}`}
    >
      <Handle type="target" position={Position.Left} style={{ visibility: "hidden" }} />
      <span className={styles.iconWrap} style={{ background: appearance.iconBg }}>
        <Icon />
      </span>
      <span className={styles.labels}>
        <span className={styles.label}>{data.label}</span>
        <span className={styles.sublabel}>{data.sublabel}</span>
      </span>
      {data.status === "breached" && (
        <span className={`${styles.tag} ${styles.tagBreached}`}>Breached</span>
      )}
      {data.status === "held" && <span className={`${styles.tag} ${styles.tagHeld}`}>Held</span>}
      {data.mitigationLabel && (
        <span className={`${styles.tag} ${styles.tagMitigation}`}>{data.mitigationLabel}</span>
      )}
      <Handle type="source" position={Position.Right} style={{ visibility: "hidden" }} />
    </button>
  );
}

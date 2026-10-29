type IconProps = { color?: string };

const base = {
  width: 22,
  height: 22,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "#FFFFFF",
  strokeWidth: 2,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true as const,
};

export function GlobeIcon() {
  return (
    <svg {...base}>
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18" />
      <path d="M12 3a14 14 0 0 1 0 18" />
      <path d="M12 3a14 14 0 0 0 0 18" />
    </svg>
  );
}

export function GatewayIcon() {
  return (
    <svg {...base}>
      <path d="M4 7h11" />
      <path d="M12 4l3 3-3 3" />
      <path d="M20 17H9" />
      <path d="M12 14l-3 3 3 3" />
    </svg>
  );
}

export function ContainerIcon() {
  return (
    <svg {...base}>
      <path d="M21 8l-9-5-9 5 9 5 9-5z" />
      <path d="M3 8v8l9 5 9-5V8" />
      <path d="M12 13v8" />
    </svg>
  );
}

export function DatabaseIcon() {
  return (
    <svg {...base}>
      <ellipse cx="12" cy="5" rx="8" ry="3" />
      <path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5" />
      <path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3" />
    </svg>
  );
}

export function LockIcon() {
  return (
    <svg {...base}>
      <circle cx="8" cy="15" r="4" />
      <path d="M11 12l9-9" />
      <path d="M17 6l3 3" />
    </svg>
  );
}

export function QueueIcon() {
  return (
    <svg {...base}>
      <path d="M4 7h16" />
      <path d="M4 12h16" />
      <path d="M4 17h10" />
    </svg>
  );
}

export function ShieldIcon(props: IconProps) {
  return (
    <svg {...base} stroke={props.color ?? "#FFFFFF"}>
      <path d="M12 3l8 3v6c0 4.5-3.4 8.3-8 9-4.6-.7-8-4.5-8-9V6l8-3z" />
    </svg>
  );
}

export function CheckIcon() {
  return (
    <svg {...base} strokeWidth={3.5}>
      <path d="M5 12l5 5L20 7" />
    </svg>
  );
}

export function AttackerIcon() {
  return (
    <svg {...base} role="img" aria-label="Attacker">
      <path d="M4 9c0-2 3.6-4 8-4s8 2 8 4v2c0 4-3.6 8-8 8s-8-4-8-8V9z" />
      <path d="M8 11l2.5 1" />
      <path d="M16 11l-2.5 1" />
    </svg>
  );
}

export function HintIcon() {
  return (
    <svg {...base} stroke="#1C1917">
      <path d="M9 18h6" />
      <path d="M10 22h4" />
      <path d="M12 2a7 7 0 0 0-4 12.7V17h8v-2.3A7 7 0 0 0 12 2z" />
    </svg>
  );
}

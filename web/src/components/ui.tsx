import { useState, type ButtonHTMLAttributes, type ReactNode } from "react";
import { LoaderCircle, type LucideIcon } from "lucide-react";

export const cx = (...c: (string | false | null | undefined)[]) => c.filter(Boolean).join(" ");

type Variant = "primary" | "secondary" | "quiet" | "light";

/** Chunky pill buttons. `primary` is the glossy violet game button. */
export function Button({
  variant = "primary",
  className,
  children,
  busy,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; busy?: boolean; ref?: React.Ref<HTMLButtonElement> }) {
  return (
    <button
      {...rest}
      disabled={rest.disabled || busy}
      className={cx(
        "inline-flex min-h-12 items-center justify-center gap-2 rounded-full px-6 font-extrabold",
        "transition-[transform,box-shadow,background-color,filter] duration-[var(--dur-fast)] ease-[var(--ease-bounce)]",
        "hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:translate-y-0",
        variant === "primary" && "tile shadow-pop [--tile:var(--violet)]",
        variant === "secondary" && "bg-surface-2 text-ink hover:bg-line",
        variant === "light" && "bg-white/90 text-[var(--night-2)] shadow-card hover:bg-white",
        variant === "quiet" && "text-ink-soft hover:bg-surface-2 hover:text-ink",
        className,
      )}
    >
      {busy && <LoaderCircle aria-hidden className="size-4 animate-spin" />}
      {children}
    </button>
  );
}

export function Panel({
  as: Tag = "section",
  pad = "md",
  look = "card",
  className,
  children,
  ...rest
}: {
  as?: "section" | "article" | "div";
  pad?: "none" | "sm" | "md";
  look?: "card" | "glass";
  className?: string;
  children: ReactNode;
} & Record<string, unknown>) {
  return (
    <Tag
      {...rest}
      className={cx(look, pad === "md" && "p-5 sm:p-6", pad === "sm" && "p-4 sm:p-5", className)}
    >
      {children}
    </Tag>
  );
}

/** Rounded gradient tile holding an icon (reference 2 category icons). */
export function IconTile({ icon: Icon, color, size = "md", className }: {
  icon: LucideIcon; color: string; size?: "sm" | "md" | "lg"; className?: string;
}) {
  return (
    <span
      aria-hidden
      className={cx(
        "tile inline-grid shrink-0 place-items-center",
        size === "sm" && "size-10 rounded-[14px]",
        size === "md" && "size-14 rounded-[18px]",
        size === "lg" && "size-16 rounded-[22px]",
        className,
      )}
      style={{ ["--tile" as string]: color }}
    >
      <Icon className={size === "sm" ? "size-5" : "size-7"} strokeWidth={2.2} />
    </span>
  );
}

/** Thin progress bar with an accessible name. */
export function Meter({ value, max, label, color = "var(--violet)" }: {
  value: number; max: number; label: string; color?: string;
}) {
  const pct = max > 0 ? Math.min(100, Math.round((value / max) * 100)) : 0;
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={max}
      aria-valuenow={Math.min(value, max)}
      className="h-2.5 w-full overflow-hidden rounded-full bg-surface-2"
    >
      <div
        className="h-full rounded-full transition-[width] duration-[var(--dur-slow)] ease-[var(--ease-out)]"
        style={{ width: `${pct}%`, background: `linear-gradient(90deg, color-mix(in srgb, ${color} 70%, white), ${color})` }}
      />
    </div>
  );
}

/** Circular progress ring (reference 3). */
export function Ring({ value, max, size = 64, stroke = 7, color = "var(--violet)", children, label }: {
  value: number; max: number; size?: number; stroke?: number; color?: string; children?: ReactNode; label: string;
}) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const pct = max > 0 ? Math.min(1, value / max) : 0;
  return (
    <div role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={max} aria-valuenow={Math.min(value, max)}
      className="relative inline-grid place-items-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90" aria-hidden>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--surface-2)" strokeWidth={stroke} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={c * (1 - pct)}
          style={{ transition: "stroke-dashoffset var(--dur-slow) var(--ease-out)" }} />
      </svg>
      <div className="absolute inset-0 grid place-items-center">{children}</div>
    </div>
  );
}

export function Badge({ children, tone = "neutral", className }: {
  children: ReactNode; tone?: "neutral" | "accent" | "success" | "warning" | "onDark"; className?: string;
}) {
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-extrabold",
        tone === "neutral" && "bg-surface-2 text-ink-soft",
        tone === "accent" && "bg-violet/12 text-violet",
        tone === "success" && "bg-success/12 text-success",
        tone === "warning" && "bg-warning/15 text-warning",
        tone === "onDark" && "bg-white/18 text-white backdrop-blur",
        className,
      )}
    >
      {children}
    </span>
  );
}

/** Honest marker for features that are planned but not built yet. */
export function Upcoming({ phase, onDark }: { phase: number; onDark?: boolean }) {
  return <Badge tone={onDark ? "onDark" : "neutral"}>Phase {phase}</Badge>;
}

export function Loading({ label = "Chargement…" }: { label?: string }) {
  return (
    <div role="status" className="flex items-center gap-3 py-16 font-bold text-ink-soft">
      <LoaderCircle aria-hidden className="size-5 animate-spin text-violet" />
      {label}
    </div>
  );
}

export function ErrorNote({ error, onRetry }: { error: Error; onRetry?: () => void }) {
  return (
    <Panel role="alert">
      <p className="font-extrabold text-danger">Something went wrong</p>
      <p className="mt-1 text-ink-soft">{error.message}</p>
      {error.message.includes("not running") && (
        <p className="mt-2 text-sm text-ink-faint">Start it with <code>scripts/dev.sh</code>.</p>
      )}
      {onRetry && (
        <Button variant="secondary" className="mt-4" onClick={onRetry}>Try again</Button>
      )}
    </Panel>
  );
}

/**
 * Generated artwork with a painted CSS fallback. If the file in /art is missing,
 * the fallback (a night gradient) shows instead, so screens never look broken.
 */
export function Art({ src, alt, className, fallback = "night", position = "center" }: {
  src: string; alt: string; className?: string; fallback?: "night" | "map"; position?: string;
}) {
  const [failed, setFailed] = useState(false);
  if (failed) {
    return <div role="img" aria-label={alt} className={cx(fallback === "map" ? "map-fallback" : "night", className)} />;
  }
  return (
    <img src={src} alt={alt} onError={() => setFailed(true)} draggable={false}
      className={cx("object-cover", className)} style={{ objectPosition: position }} />
  );
}

/** App mark: a glossy compass badge. */
export function CompassMark({ className = "size-9" }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" aria-hidden className={className}>
      <defs>
        <linearGradient id="cm-g" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#9b86ff" />
          <stop offset="1" stopColor="#5a3df0" />
        </linearGradient>
      </defs>
      <rect x="2" y="2" width="60" height="60" rx="18" fill="url(#cm-g)" />
      <path d="M8 14c8-8 40-8 48 0" stroke="#fff" strokeOpacity=".35" strokeWidth="3" fill="none" strokeLinecap="round" />
      <path d="M32 12 39 32 32 52 25 32Z" fill="#fff" />
      <path d="M32 12 39 32H25Z" fill="#ffbf2e" />
      <circle cx="32" cy="32" r="3.5" fill="#5a3df0" />
    </svg>
  );
}

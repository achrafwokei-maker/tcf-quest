import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion, useReducedMotion } from "motion/react";
import { BookOpen, Check, Crown, Feather, Headphones, Lock, Mic, PenLine, Repeat, Star, Swords } from "lucide-react";
import { openNode, type Chapter, type JourneyNode } from "../lib/journey";
import { cx } from "./ui";

/*
 * One reusable road for the whole journey: chapters are stages (CEFR-labelled), nodes are checkpoints.
 * Pure data → layout: nodes zigzag down a single curved SVG path; the travelled part glows gold.
 * Used full-size on Mon Aventure and as a small window around the current step on Home.
 */

const TYPE = {
  listening: { icon: Headphones, color: "var(--cyan)", label: "Listening" },
  reading: { icon: BookOpen, color: "var(--green)", label: "Reading" },
  speaking: { icon: Mic, color: "var(--pink)", label: "Speaking" },
  writing: { icon: PenLine, color: "var(--gold)", label: "Writing" },
  strategy: { icon: Feather, color: "var(--violet)", label: "Strategy" },
  revision: { icon: Repeat, color: "var(--orange)", label: "Revision" },
  boss: { icon: Swords, color: "var(--red)", label: "Trial" },
} as const;

const XS = [50, 66, 72, 60, 40, 28, 34, 46];          // zigzag columns (% of width), repeating
const ROW = 104, STAGE = 96, TOP = 24;

type Row = { kind: "stage"; chapter: Chapter } | { kind: "node"; node: JourneyNode; chapter: Chapter } | { kind: "more"; chapter: Chapter; count: number };

/** Road order: what's done (in the chapter's order), then what's next (personal order); locked chapters stay short. */
function rows(chapters: Chapter[]): Row[] {
  const out: Row[] = [];
  for (const c of chapters) {
    out.push({ kind: "stage", chapter: c });
    const done = c.nodes.filter((n) => n.state === "done");
    const next = c.nodes.filter((n) => n.state !== "done").sort((a, b) => (a.rank ?? 99) - (b.rank ?? 99));
    let list = [...done, ...next];
    if (!c.unlocked && list.length > 2) {
      out.push(...list.slice(0, 2).map((n) => ({ kind: "node" as const, node: n, chapter: c })));
      out.push({ kind: "more", chapter: c, count: list.length - 2 });
      list = [];
    }
    out.push(...list.map((n) => ({ kind: "node" as const, node: n, chapter: c })));
    if (c.boss) out.push({ kind: "node", node: c.boss, chapter: c });
  }
  return out;
}

export function currentRef(chapters: Chapter[], current: number): string | null {
  const open = chapters.filter((c) => c.unlocked);
  const all = open.flatMap((c) => [...c.nodes, ...(c.boss ? [c.boss] : [])]);
  const exam = all.find((n) => n.state === "in_progress" && n.type === "boss");
  if (exam) return exam.ref;
  const going = all.find((n) => n.state === "in_progress");
  if (going) return going.ref;
  const ch = chapters.find((c) => c.n === current);
  const first = ch?.nodes.filter((n) => n.state === "available").sort((a, b) => (a.rank ?? 99) - (b.rank ?? 99))[0];
  return first?.ref ?? (ch?.boss && ch.boss.state === "available" ? ch.boss.ref : null);
}

export function JourneyRoad({ chapters, current, sideMissions = [], window }: {
  chapters: Chapter[]; current: number; sideMissions?: JourneyNode[]; window?: { before: number; after: number };
}) {
  const reduce = useReducedMotion();
  const navigate = useNavigate();
  const [hint, setHint] = useState<string | null>(null);
  const cur = currentRef(chapters, current);

  const sideCount = sideMissions.length;
  const layout = useMemo(() => {
    let all = rows(chapters);
    if (window) {                                     // Home preview: a few checkpoints around "you are here"
      const nodes = all.filter((r) => r.kind === "node");
      const i = Math.max(0, nodes.findIndex((r) => r.kind === "node" && r.node.ref === cur));
      all = nodes.slice(Math.max(0, i - window.before), i + window.after + 1);
    }
    let y = TOP, k = 0;
    const placed = all.map((r) => {
      if (r.kind === "stage") { const p = { r, y, x: 50 }; y += STAGE; return p; }
      if (r.kind === "more") { const p = { r, y, x: XS[k % XS.length] }; y += ROW * 0.7; return p; }
      const p = { r, y: y + ROW / 2 - 10, x: XS[k++ % XS.length] };
      y += ROW + (r.node.ref === cur && sideCount > 0 ? 48 : 0);      // room for the detour under "you are here"
      return p;
    });
    return { placed, height: y + 20 };
  }, [chapters, window, cur, sideCount]);

  const points = layout.placed.filter((p) => p.r.kind === "node");
  const curIdx = points.findIndex((p) => p.r.kind === "node" && p.r.node.ref === cur);
  const lastDone = points.reduce((acc, p, i) => (p.r.kind === "node" && p.r.node.state === "done" ? i : acc), -1);
  const travelled = curIdx >= 0 ? curIdx : lastDone;            // gold road stops at "you are here"
  const path = (ps: typeof points) => ps.reduce((d, p, i) => {
    if (i === 0) return `M ${p.x} ${p.y}`;
    const a = ps[i - 1], my = (a.y + p.y) / 2;
    return `${d} C ${a.x} ${my}, ${p.x} ${my}, ${p.x} ${p.y}`;
  }, "");

  async function open(n: JourneyNode) {
    if (n.state === "locked" || n.state === "skipped") { setHint(n.hint ?? "Locked for now."); return; }
    setHint(null);
    try { await openNode(n, navigate); } catch (e) { setHint((e as Error).message); }
  }

  return (
    <div className="relative mx-auto w-full max-w-xl overflow-x-clip" style={{ height: layout.height }}>
      <svg aria-hidden className="absolute inset-0 h-full w-full" viewBox={`0 0 100 ${layout.height}`} preserveAspectRatio="none">
        <path d={path(points)} fill="none" stroke="var(--line)" strokeWidth="1.4" strokeDasharray="0.1 3.2" strokeLinecap="round"
          vectorEffect="non-scaling-stroke" style={{ strokeWidth: 10 }} />
        {travelled > 0 && (
          <motion.path d={path(points.slice(0, travelled + 1))} fill="none" stroke="var(--gold)" strokeLinecap="round"
            vectorEffect="non-scaling-stroke" style={{ strokeWidth: 10, opacity: 0.85 }}
            initial={reduce ? false : { pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1 }} />
        )}
      </svg>

      <ol aria-label="Journey checkpoints" className="relative">
        {layout.placed.map((p, i) => {
          if (p.r.kind === "stage") {
            const c = p.r.chapter;
            return (
              <li key={`s${c.n}`} className="absolute inset-x-0 flex justify-center" style={{ top: p.y }}>
                <div className={cx("glass flex items-center gap-3 rounded-full px-4 py-2", !c.unlocked && "opacity-70")}>
                  <span className="grid size-9 place-items-center rounded-full bg-[var(--gold)] text-sm font-extrabold text-[#2a1f00]">{c.cefr ?? c.n}</span>
                  <span>
                    <span className="block text-[0.65rem] font-extrabold uppercase tracking-wider text-ink-faint">Stage {c.n} · {c.place}</span>
                    <span className="block text-sm font-extrabold">{c.title}</span>
                  </span>
                  {c.complete ? <Check aria-hidden className="size-4 text-success" /> : !c.unlocked && <Lock aria-hidden className="size-4 text-ink-faint" />}
                </div>
              </li>
            );
          }
          if (p.r.kind === "more") {
            return (
              <li key={`m${p.r.chapter.n}`} className="absolute -translate-x-1/2 text-xs font-bold text-ink-faint" style={{ left: `${p.x}%`, top: p.y }}>
                + {p.r.count} more checkpoints
              </li>
            );
          }
          const n = p.r.node;
          const t = TYPE[n.type ?? "listening"];
          const isCur = n.ref === cur;
          const Icon = n.state === "done" ? Check : n.state === "locked" ? Lock : n.kind === "final" ? Crown : t.icon;
          const size = isCur ? 76 : n.type === "boss" ? 68 : 60;
          const labelRight = p.x <= 50;
          return (
            <li key={n.ref + i} className="absolute w-0" style={{ left: `${p.x}%`, top: p.y - size / 2 }}>
              <button type="button" onClick={() => open(n)} aria-label={`${n.title}, ${t.label}, ${n.state.replace("_", " ")}${isCur ? ", you are here" : ""}`}
                className={cx("relative -translate-x-1/2 rounded-full transition-transform hover:scale-105 focus-visible:scale-105",
                  n.state === "locked" && "cursor-not-allowed")}
                style={{ width: size, height: size }}>
                {isCur && !reduce && <span aria-hidden className="absolute inset-0 animate-ping rounded-full bg-[var(--gold)]/40" />}
                <span className={cx("relative grid h-full w-full place-items-center rounded-full border-4 shadow-card",
                  n.state === "locked" ? "border-line bg-surface-2 text-ink-faint" :
                    n.state === "done" ? "border-white/30 text-white" : isCur ? "border-white text-white" : "border-white/40 text-white")}
                  style={n.state === "locked" ? undefined : { background: n.state === "done" ? t.color : `linear-gradient(160deg, ${t.color}, color-mix(in oklab, ${t.color} 60%, black))`,
                    opacity: n.state === "available" && !isCur && !n.recommended ? 0.75 : 1 }}>
                  <Icon aria-hidden className={isCur ? "size-8" : "size-6"} />
                </span>
                {n.recommended && n.state !== "done" && !isCur && (
                  <span aria-hidden className="absolute -right-1 -top-1 grid size-6 place-items-center rounded-full bg-[var(--gold)] text-[#2a1f00]"><Star className="size-3.5 fill-current" /></span>
                )}
              </button>
              <div className={cx("pointer-events-none absolute top-1/2 w-[7.5rem] -translate-y-1/2 sm:w-48", labelRight ? "text-left" : "text-right")}
                style={labelRight ? { left: size / 2 + 12 } : { right: size / 2 + 12 }}>
                {isCur && <span className="mb-0.5 inline-block rounded-full bg-[var(--gold)] px-2 py-0.5 text-[0.65rem] font-extrabold uppercase text-[#2a1f00]">You are here</span>}
                <span className={cx("block text-xs font-extrabold leading-tight sm:text-sm", n.state === "locked" && "text-ink-faint", n.state === "done" && "text-ink-soft")}>{n.title}</span>
                <span className="block text-xs font-semibold text-ink-faint">{t.label} · {n.minutes} min</span>
              </div>
              {isCur && sideMissions.length > 0 && (
                <ul className="absolute left-0 top-full mt-3 flex -translate-x-1/2 gap-2 whitespace-nowrap" aria-label="Quick detours">
                  {sideMissions.slice(0, 2).map((s) => (
                    <li key={s.ref}>
                      <button type="button" onClick={() => open(s)} title={s.reason}
                        className="flex items-center gap-1.5 rounded-full border-2 border-dashed border-[var(--orange)] bg-surface px-3 py-1 text-xs font-extrabold hover:bg-surface-2">
                        <Repeat aria-hidden className="size-3.5 text-[var(--orange)]" /> Detour: {s.title}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </li>
          );
        })}
      </ol>
      {hint && (
        <p role="status" onClick={() => setHint(null)}
          className="glass fixed inset-x-4 bottom-28 z-50 mx-auto max-w-md rounded-full px-4 py-2 text-center text-sm font-semibold">{hint}</p>
      )}
      {window && (
        <Link to="/aventure" className="absolute bottom-0 right-0 text-sm font-extrabold text-violet hover:underline">See the whole journey →</Link>
      )}
    </div>
  );
}

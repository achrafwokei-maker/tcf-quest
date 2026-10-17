import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { BookOpen, Check, Compass, Lightbulb, Play, RotateCcw, Snail, Target, Volume2 } from "lucide-react";
import type { ArrangeItem, CardItem, ChoiceItem, MultiItem, Speech, TypeItem } from "../../lib/exercises";
import { speak, speechAvailable } from "../../lib/speak";
import { IconTile, cx } from "../ui";

/* ---------- character speech bubble (story lines, guided calls) ---------- */

const SPEAKER_COLOR: Record<string, string> = {
  "Madame Roux": "var(--orange)", "M. Delaunay": "var(--blue)", Narratrice: "var(--violet)",
};

export function SpeechBubble({ line, autoPlay = false, side = "left" }: { line: Speech; autoPlay?: boolean; side?: "left" | "right" }) {
  useEffect(() => {
    if (autoPlay) void speak(line.text, { speaker: line.speaker });
  }, [autoPlay, line.text, line.speaker]);
  const color = SPEAKER_COLOR[line.speaker] ?? "var(--pink)";
  return (
    <div className={cx("flex items-start gap-3", side === "right" && "flex-row-reverse")}>
      <span className="tile grid size-11 shrink-0 place-items-center rounded-full text-sm font-extrabold" style={{ ["--tile" as string]: color }} aria-hidden>
        {line.speaker.replace("M. ", "").replace("Madame ", "")[0]}
      </span>
      <div className="card relative max-w-xl rounded-tl-md p-4">
        <p className="text-xs font-extrabold uppercase tracking-wider" style={{ color }}>{line.speaker}</p>
        <p className="mt-0.5 text-lg font-bold">{line.text}</p>
        {line.en && <p className="mt-1 text-sm font-semibold text-ink-faint">{line.en}</p>}
        {speechAvailable() && (
          <button type="button" onClick={() => speak(line.text, { speaker: line.speaker })} aria-label={`Hear ${line.speaker}`}
            className="absolute -bottom-3 right-3 grid size-8 place-items-center rounded-full bg-surface-2 text-ink-soft shadow-card hover:text-ink">
            <Volume2 aria-hidden className="size-4" />
          </button>
        )}
      </div>
    </div>
  );
}

/* ---------- cards: story, objective, method, language, outro (not scored) ---------- */

const CARD_LOOK = {
  story: { icon: BookOpen, color: "var(--orange)" },
  objective: { icon: Target, color: "var(--green)" },
  method: { icon: Compass, color: "var(--violet)" },
  language: { icon: Lightbulb, color: "var(--gold)" },
  outro: { icon: Check, color: "var(--green)" },
} as const;

export function CardView({ item }: { item: CardItem }) {
  const look = CARD_LOOK[item.kind];
  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <IconTile icon={look.icon} color={look.color} size="sm" />
        <h2 className="title-poster text-3xl sm:text-4xl">{item.title}</h2>
      </div>
      {item.lines.length > 0 && (
        <div className="space-y-5">
          {item.lines.map((l, i) => <SpeechBubble key={i} line={l} />)}
        </div>
      )}
      {item.body && (
        <div className="card p-5">
          <p className="text-lg font-semibold">{item.body}</p>
          {item.body_en && <p className="mt-1 text-sm font-semibold text-ink-faint">{item.body_en}</p>}
        </div>
      )}
      {item.link && (
        <Link to={item.link.to} className="tile inline-flex min-h-12 items-center gap-2 rounded-full px-6 font-extrabold [--tile:var(--pink)]">
          <Play aria-hidden className="size-4 fill-current" /> {item.link.label}
        </Link>
      )}
      {item.points.length > 0 && (
        <ul className="grid gap-2">
          {item.points.map((p, i) => (
            <li key={p} className="card flex items-start gap-3 p-4">
              <span className="grid size-7 shrink-0 place-items-center rounded-full bg-surface-2 text-sm font-extrabold">{i + 1}</span>
              <span className="flex-1 text-lg font-bold">{p}</span>
              {item.kind === "language" && speechAvailable() && (
                <button type="button" onClick={() => speak(p, { speaker: "Céleste" })} aria-label="Hear it"
                  className="grid size-8 place-items-center rounded-full text-ink-faint hover:bg-surface-2 hover:text-ink">
                  <Volume2 aria-hidden className="size-4" />
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/* ---------- checklist (pick every correct option) ---------- */

export function MultiView({ item, value, onChange, locked, missed, extra }: {
  item: MultiItem; value: string[]; onChange: (v: string[]) => void; locked: boolean; missed?: string[]; extra?: string[];
}) {
  const toggle = (id: string) => onChange(value.includes(id) ? value.filter((x) => x !== id) : [...value, id]);
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-extrabold sm:text-2xl">{item.question}</h2>
      <p className="text-sm font-semibold text-ink-faint">Choose all that apply.</p>
      <div className="grid gap-2.5" role="group" aria-label={item.question}>
        {item.options.map((o) => {
          const on = value.includes(o.id);
          const isMissed = locked && missed?.includes(o.id);
          const isExtra = locked && extra?.includes(o.id);
          return (
            <button key={o.id} type="button" role="checkbox" aria-checked={on} disabled={locked} onClick={() => toggle(o.id)}
              className={cx("flex items-center gap-3 rounded-[18px] border-2 px-4 py-3.5 text-left text-lg font-semibold transition-colors",
                on ? "border-violet bg-violet/10" : "border-line bg-surface hover:border-ink-faint",
                isMissed && "border-warning", isExtra && "border-danger")}>
              <span className={cx("grid size-6 shrink-0 place-items-center rounded-md border-2", on ? "border-violet bg-violet text-white" : "border-line")}>
                {on && <Check aria-hidden className="size-4" strokeWidth={3} />}
              </span>
              <span className="flex-1">{o.text}</span>
              {isMissed && <span className="text-xs font-extrabold text-warning">missing</span>}
              {isExtra && <span className="text-xs font-extrabold text-danger">not needed</span>}
            </button>
          );
        })}
      </div>
    </div>
  );
}

/* ---------- shared bits ---------- */

/** True when the keystroke is inside a text field (so global shortcuts stay out of the way). */
const typing = (e: KeyboardEvent) =>
  e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement;

/* ---------- Types 1 and 2: select / listen and choose ---------- */

export const MAX_PLAYS = 3; // first play + 2 replays in training

export function ChoiceView({ item, value, onChange, locked, audioOff, plays, onPlay, playing }: {
  item: ChoiceItem;
  value: string | null;
  onChange: (v: string) => void;
  locked: boolean;
  audioOff: boolean;
  plays: number;
  playing: boolean;
  onPlay: (slow: boolean) => void;
}) {
  const isListen = item.type === "listen";
  // Listening: options appear after the first full play, so the learner listens before reading.
  const showOptions = !isListen || audioOff || plays > 0;

  useEffect(() => {
    if (locked || !showOptions) return;
    const onKey = (e: KeyboardEvent) => {
      if (typing(e)) return;
      const n = Number(e.key);
      if (n >= 1 && n <= item.options.length) onChange(item.options[n - 1].id);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [item, locked, onChange, showOptions]);

  return (
    <div className="space-y-5">
      {item.passage && (
        <div className="card whitespace-pre-line p-5 text-lg leading-relaxed">{item.passage}</div>
      )}

      {isListen && item.audio && (
        audioOff ? (
          <div className="card p-5">
            <p className="eyebrow mb-1">Transcript (listening off)</p>
            <p className="text-lg">{item.audio.text}</p>
          </div>
        ) : (
          <div className="flex flex-wrap items-center gap-3">
            <button type="button" onClick={() => onPlay(false)} disabled={playing || plays >= MAX_PLAYS || locked}
              aria-label={plays === 0 ? "Play the audio" : "Play again"}
              className="tile grid size-20 place-items-center rounded-full transition-transform hover:scale-105 disabled:opacity-50 [--tile:var(--blue)]">
              {plays === 0 ? <Play aria-hidden className="size-9 fill-current" /> : <Volume2 aria-hidden className={cx("size-9", playing && "animate-pulse")} />}
            </button>
            <button type="button" onClick={() => onPlay(true)} disabled={playing || plays === 0 || plays >= MAX_PLAYS || locked}
              className="flex items-center gap-1.5 rounded-full bg-surface-2 px-4 py-2 text-sm font-extrabold text-ink-soft hover:text-ink disabled:opacity-40">
              <Snail aria-hidden className="size-4" /> Slower
            </button>
            <span className="text-sm font-bold text-ink-faint" aria-live="polite">
              {playing ? "Listening…" : plays === 0 ? "Press play" : `${MAX_PLAYS - plays} replay${MAX_PLAYS - plays === 1 ? "" : "s"} left`}
            </span>
          </div>
        )
      )}

      {item.prompt_line && <SpeechBubble line={item.prompt_line} autoPlay={!locked && !audioOff} />}

      <h2 className="text-xl font-extrabold sm:text-2xl">{item.question}</h2>

      {showOptions ? (
        <div role="radiogroup" aria-label={item.question} className="grid gap-3">
          {item.options.map((o, i) => {
            const on = value === o.id;
            return (
              <button key={o.id} type="button" role="radio" aria-checked={on} disabled={locked}
                onClick={() => onChange(o.id)}
                className={cx(
                  "flex items-center gap-3 rounded-[18px] border-2 px-4 py-3.5 text-left text-lg font-semibold transition-all duration-[var(--dur-fast)]",
                  on ? "border-violet bg-violet/10" : "border-line bg-surface hover:border-ink-faint",
                  locked && "cursor-default",
                )}>
                <span className={cx("grid size-7 shrink-0 place-items-center rounded-lg text-sm font-extrabold", on ? "bg-violet text-white" : "bg-surface-2 text-ink-faint")}>
                  {i + 1}
                </span>
                {o.text}
              </button>
            );
          })}
        </div>
      ) : (
        <p className="font-semibold text-ink-faint">The answers appear after the first listening.</p>
      )}
    </div>
  );
}

/* ---------- Type 3: arrange the words ---------- */

export function ArrangeView({ item, onChange, locked, wrongPositions }: {
  item: ArrangeItem;
  onChange: (tiles: string[]) => void;
  locked: boolean;
  wrongPositions?: number[];
}) {
  const [placed, setPlaced] = useState<number[]>([]); // indices into item.tiles
  const bank = item.tiles.map((t, i) => ({ t, i })).filter(({ i }) => !placed.includes(i));

  useEffect(() => setPlaced([]), [item.id]);
  useEffect(() => onChange(placed.map((i) => item.tiles[i])), [placed, item.tiles, onChange]);

  useEffect(() => {
    if (locked) return;
    const onKey = (e: KeyboardEvent) => {
      if (typing(e)) return;
      if (e.key === "Backspace") setPlaced((p) => p.slice(0, -1));
      const n = Number(e.key);
      if (!Number.isInteger(n) || n < 1) return;
      // Compute the bank from the latest state so fast key presses never reuse a stale list.
      setPlaced((p) => {
        const free = item.tiles.map((_, i) => i).filter((i) => !p.includes(i));
        return n <= free.length ? [...p, free[n - 1]] : p;
      });
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [item.tiles, locked]);

  return (
    <div className="space-y-5">
      {item.translation && <p className="text-lg font-semibold text-ink-soft">« {item.translation} »</p>}

      <div aria-label="Your sentence" className="flex min-h-16 flex-wrap content-start gap-2 border-b-2 border-dashed border-line pb-3">
        {placed.length === 0 && <span className="py-2 text-ink-faint">Tap the words below in order.</span>}
        {placed.map((i, pos) => (
          <button key={`${i}-${pos}`} type="button" disabled={locked}
            onClick={() => setPlaced((p) => p.filter((x) => x !== i))}
            className={cx(
              "rounded-[14px] border-2 bg-surface px-3.5 py-2 text-lg font-bold shadow-card",
              locked && wrongPositions?.includes(pos) ? "border-danger text-danger" : "border-violet",
            )}>
            {item.tiles[i]}
          </button>
        ))}
      </div>

      <div className="flex flex-wrap gap-2" aria-label="Word bank">
        {bank.map(({ t, i }, n) => (
          <button key={i} type="button" disabled={locked} onClick={() => setPlaced((p) => (p.includes(i) ? p : [...p, i]))}
            title={`Key ${n + 1}`}
            className="rounded-[14px] border-2 border-line bg-surface-2 px-3.5 py-2 text-lg font-bold transition-transform hover:-translate-y-0.5 hover:border-ink-faint">
            {t}
          </button>
        ))}
      </div>

      {!locked && placed.length > 0 && (
        <button type="button" onClick={() => setPlaced([])} className="flex items-center gap-1.5 text-sm font-extrabold text-ink-faint hover:text-ink">
          <RotateCcw aria-hidden className="size-4" /> Clear
        </button>
      )}
    </div>
  );
}

/* ---------- Type 4: type the missing word ---------- */

const ACCENTS = ["é", "è", "ê", "à", "â", "ç", "ô", "û", "ù", "î", "ï", "ë", "œ"];

export function TypeView({ item, value, onChange, locked, hint, onHint }: {
  item: TypeItem;
  value: string;
  onChange: (v: string) => void;
  locked: boolean;
  hint: string | null;
  onHint: () => void;
}) {
  const input = useRef<HTMLInputElement>(null);
  const [before, after] = item.sentence.split("___");

  useEffect(() => {
    if (!locked) input.current?.focus();
  }, [item.id, locked]);

  function insert(ch: string) {
    const el = input.current;
    if (!el) return;
    const start = el.selectionStart ?? value.length;
    const end = el.selectionEnd ?? value.length;
    onChange(value.slice(0, start) + ch + value.slice(end));
    requestAnimationFrame(() => {
      el.focus();
      el.setSelectionRange(start + ch.length, start + ch.length);
    });
  }

  return (
    <div className="space-y-5">
      <p className="text-2xl font-bold leading-loose">
        {before}
        <input ref={input} value={value} disabled={locked} onChange={(e) => onChange(e.target.value)}
          aria-label="Missing word" autoComplete="off" autoCapitalize="off" spellCheck={false}
          className="mx-1 inline-block w-40 rounded-[12px] border-2 border-violet bg-surface px-3 py-1 text-center text-2xl font-extrabold outline-none focus:ring-4 focus:ring-violet/20 disabled:border-line"
          style={{ width: `${Math.max(6, value.length + 2)}ch` }} />
        {after}
      </p>
      {item.base_form && <p className="font-semibold text-ink-soft">({item.base_form})</p>}

      {!locked && (
        <div className="flex flex-wrap gap-1.5" aria-label="French accents">
          {ACCENTS.map((a) => (
            <button key={a} type="button" onMouseDown={(e) => e.preventDefault()} onClick={() => insert(a)}
              className="grid size-10 place-items-center rounded-[12px] bg-surface-2 text-lg font-bold hover:bg-line">
              {a}
            </button>
          ))}
        </div>
      )}

      {item.has_hint && !locked && (
        hint ? (
          <p role="status" className="flex items-start gap-2 rounded-[16px] bg-gold/15 px-4 py-3 font-semibold">
            <Lightbulb aria-hidden className="mt-0.5 size-5 shrink-0 text-warning" /> {hint}
          </p>
        ) : (
          <button type="button" onClick={onHint} className="flex items-center gap-1.5 text-sm font-extrabold text-ink-faint hover:text-ink">
            <Lightbulb aria-hidden className="size-4" /> Show a hint
          </button>
        )
      )}
    </div>
  );
}

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Check, Volume2 } from "lucide-react";
import { useAsync } from "../lib/useAsync";
import { speak } from "../lib/speak";
import { Badge, Button, ErrorNote, Loading, Meter, Panel } from "../components/ui";

interface Card {
  id: string; fr: string; en: string; example: string; level: string; function: string; function_label: string; new: boolean; box: number;
}
interface Overview {
  functions: { id: string; label: string; task: string; blurb: string; total: number; learned: number; mastered: number; due: number }[];
  total: number; learned: number; mastered: number; due: number; session_size: number; new_today: number;
}

const GRADES = [
  { g: "again", label: "Forgot", hint: "Back tomorrow", key: "1" },
  { g: "hard", label: "Hard", hint: "Soon", key: "2" },
  { g: "good", label: "Good", hint: "Later", key: "3" },
  { g: "easy", label: "Easy", hint: "Much later", key: "4" },
] as const;

const api = {
  overview: () => fetch("/api/vocab").then((r) => { if (!r.ok) throw new Error("The local server is not running."); return r.json() as Promise<Overview>; }),
  session: () => fetch("/api/vocab/session").then((r) => r.json() as Promise<{ cards: Card[] }>),
  grade: (id: string, grade: string) => fetch(`/api/vocab/${id}/grade`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ grade }) }),
};

/** Vocabulaire: useful expressions grouped by what you do with them in the TCF. A memory aid, not a test. */
export function VocabPage() {
  const [overview, reload] = useAsync(api.overview);
  const [queue, setQueue] = useState<Card[] | null>(null);
  const [done, setDone] = useState(0);

  async function start() {
    const s = await api.session();
    setQueue(s.cards); setDone(0);
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 px-5 pt-6 pb-10 sm:px-8">
      <Link to="/entrainement" className="inline-flex items-center gap-1 text-sm font-extrabold text-ink-soft hover:text-ink">
        <ArrowLeft aria-hidden className="size-4" /> Entraînement
      </Link>
      <header>
        <p className="eyebrow">Vocabulaire</p>
        <h1 className="title-poster mt-1 text-5xl">Words you'll use</h1>
        <p className="mt-2 font-semibold text-ink-soft">
          Expressions grouped by what they do in the TCF: ask politely, give an opinion, tell a story. A few each day, brought back just before you'd forget them.
        </p>
      </header>

      {queue === null ? (
        <>
          {overview.status === "loading" && <Loading />}
          {overview.status === "error" && <ErrorNote error={overview.error} onRetry={reload} />}
          {overview.status === "ready" && <Home o={overview.data} onStart={start} />}
        </>
      ) : done >= queue.length ? (
        <Panel className="text-center">
          <Check aria-hidden className="mx-auto size-10 text-success" />
          <h2 className="mt-2 text-2xl">Done for today</h2>
          <p className="text-ink-soft">{queue.length} card{queue.length === 1 ? "" : "s"} reviewed. They'll come back at the right moment.</p>
          <Button className="mt-4" onClick={() => { setQueue(null); reload(); }}>Back to my words</Button>
        </Panel>
      ) : (
        <Flash key={queue[done].id} card={queue[done]} position={done + 1} total={queue.length}
          onGrade={async (g) => { await api.grade(queue[done].id, g); setDone(done + 1); }} />
      )}
    </div>
  );
}

function Home({ o, onStart }: { o: Overview; onStart: () => void }) {
  return (
    <>
      <Panel>
        <div className="flex flex-wrap items-center gap-4">
          <div className="min-w-0 flex-1">
            <p className="text-lg font-extrabold">
              {o.session_size > 0 ? `${o.due} to review · ${o.new_today} new` : "Nothing to review right now"}
            </p>
            <p className="text-sm text-ink-soft">{o.learned} of {o.total} words met · {o.mastered} well known. About {Math.max(1, Math.round(o.session_size * 0.4))} min.</p>
          </div>
          <Button onClick={onStart} disabled={o.session_size === 0}>Start</Button>
        </div>
        <div className="mt-3"><Meter value={o.learned} max={o.total} label="Words met" /></div>
      </Panel>
      <ul className="grid gap-3 sm:grid-cols-2">
        {o.functions.map((f) => (
          <li key={f.id} className="card p-4">
            <div className="flex items-center justify-between gap-2">
              <p className="font-extrabold">{f.label}</p>
              <Badge>{f.task}</Badge>
            </div>
            <p className="text-sm text-ink-soft">{f.blurb}</p>
            <p className="mt-1 text-xs font-bold text-ink-faint">{f.learned}/{f.total} met · {f.mastered} well known{f.due ? ` · ${f.due} due` : ""}</p>
          </li>
        ))}
      </ul>
    </>
  );
}

function Flash({ card, position, total, onGrade }: { card: Card; position: number; total: number; onGrade: (g: string) => void }) {
  // A new card shows French + meaning + example (learn). A review asks for the French first (recall).
  const [shown, setShown] = useState(card.new);
  const [busy, setBusy] = useState(false);
  const say = useCallback(() => void speak(card.fr, { speaker: "Céleste" }), [card.fr]);
  const grade = useCallback(async (g: string) => { if (busy) return; setBusy(true); await onGrade(g); }, [busy, onGrade]);

  useEffect(() => { if (card.new) say(); }, [card.new, say]);
  useEffect(() => {
    const on = (e: KeyboardEvent) => {
      if (e.key === " " || e.key === "Enter") { e.preventDefault(); if (!shown) { setShown(true); say(); } }
      const g = GRADES.find((x) => x.key === e.key);
      if (g && shown) void grade(g.g);
    };
    window.addEventListener("keydown", on);
    return () => window.removeEventListener("keydown", on);
  }, [shown, say, grade]);

  return (
    <section aria-label="Vocabulary card" className="space-y-4">
      <div className="flex items-center justify-between text-sm font-extrabold text-ink-faint">
        <span>{card.function_label}</span><span>{position} / {total}</span>
      </div>
      <Panel className="min-h-56 text-center">
        <Badge tone={card.new ? "accent" : "neutral"}>{card.new ? "New" : "Review"} · {card.level}</Badge>
        {card.new || shown ? (
          <>
            <p className="title-poster mt-4 text-4xl sm:text-5xl">{card.fr}</p>
            <p className="mt-1 text-lg font-bold text-ink-soft">{card.en}</p>
            <p className="mx-auto mt-4 max-w-md rounded-[16px] bg-surface-2 p-3 font-semibold">{card.example}</p>
            <Button variant="secondary" className="mt-3 min-h-10" onClick={say} aria-label="Hear it"><Volume2 aria-hidden className="size-4" /> Hear it</Button>
          </>
        ) : (
          <>
            <p className="mt-6 text-sm font-extrabold uppercase tracking-wider text-ink-faint">How do you say…</p>
            <p className="mt-2 text-3xl font-extrabold">{card.en}</p>
            <Button className="mt-8" onClick={() => { setShown(true); say(); }}>Show the French</Button>
          </>
        )}
      </Panel>
      {shown && (
        <div>
          <p className="mb-2 text-center text-sm font-semibold text-ink-soft">{card.new ? "Got it? It comes back tomorrow." : "How well did you remember it?"}</p>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {GRADES.map(({ g, label, hint, key }) => (
              <button key={g} type="button" onClick={() => grade(g)} disabled={busy}
                className="rounded-[16px] border-2 border-line p-3 text-center hover:bg-surface-2 disabled:opacity-50">
                <span className="block font-extrabold">{label}</span>
                <span className="block text-xs text-ink-faint">{hint} · {key}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

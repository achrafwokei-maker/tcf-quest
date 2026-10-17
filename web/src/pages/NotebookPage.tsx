import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, CalendarClock, Check, MessageSquareText, Play, Repeat } from "lucide-react";
import { exercisesApi, type Mistake, type Notebook, type Weakness, type WeaknessState } from "../lib/exercises";
import { useAsync } from "../lib/useAsync";
import { skillName } from "../lib/labels";
import { Badge, Button, ErrorNote, Loading, Meter, Panel } from "../components/ui";

/** Carnet d'erreurs: recurring mistakes, what to review today, and what you've fixed. */
export function NotebookPage() {
  const [state, reload] = useAsync(exercisesApi.notebook);
  const [data, setData] = useState<Notebook | null>(null);
  const navigate = useNavigate();
  const nb = data ?? (state.status === "ready" ? state.data : null);

  async function startReviews() {
    await exercisesApi.startReviews();
    navigate("/set/revisions");
  }

  return (
    <div className="space-y-6 px-5 pt-6 sm:px-10 sm:pt-10">
      <Link to="/entrainement" className="inline-flex items-center gap-1 text-sm font-extrabold text-ink-soft hover:text-ink">
        <ArrowLeft aria-hidden className="size-4" /> Entraînement
      </Link>
      <header>
        <p className="eyebrow">Carnet d'erreurs</p>
        <h1 className="title-poster mt-1 text-5xl sm:text-6xl">Your mistakes, your map</h1>
        <p className="mt-2 max-w-2xl font-semibold text-ink-soft">
          Every mistake comes back at the right moment: tomorrow, then in 3, 7 and 14 days. Three good reviews in a row and it's mastered.
        </p>
      </header>

      {state.status === "loading" && <Loading />}
      {state.status === "error" && <ErrorNote error={state.error} onRetry={reload} />}
      {nb && (
        <>
          <Panel look="glass" className="flex flex-wrap items-center gap-4">
            <Repeat aria-hidden className="size-6 text-violet" />
            <div className="min-w-0 flex-1">
              <p className="text-lg font-extrabold">
                {nb.due_today > 0 ? `${nb.due_today} review${nb.due_today === 1 ? "" : "s"} for today` : "No reviews due today"}
              </p>
              <p className="text-sm font-semibold text-ink-soft">
                {nb.due_today > 0 ? "About 2–4 minutes. Maximum 10 a day, so it never piles up." : "Come back tomorrow, or keep training."}
              </p>
            </div>
            <Button onClick={startReviews} disabled={nb.due_today === 0}><Play aria-hidden className="size-4 fill-current" /> Review now</Button>
          </Panel>

          {nb.weaknesses.length > 0 && (
            <section aria-labelledby="weak-h">
              <h2 id="weak-h" className="text-xl">Weak points ({nb.weaknesses.filter((w) => w.state !== "mastered").length} active)</h2>
              <p className="text-sm font-semibold text-ink-soft">
                One per concept. A weak point is confirmed fixed only when you get a question you've never seen right, without hints.
              </p>
              <ul className="mt-3 grid gap-3 sm:grid-cols-2">
                {nb.weaknesses.map((w) => <WeaknessCard key={w.competency} w={w} />)}
              </ul>
            </section>
          )}

          {nb.open.length === 0 ? (
            <Panel className="flex items-center gap-3"><Check aria-hidden className="size-6 text-success" /><p className="font-bold">Nothing to fix yet. Mistakes will appear here as you practise.</p></Panel>
          ) : (
            <section aria-labelledby="open-h">
              <h2 id="open-h" className="text-xl">To work on ({nb.open.length})</h2>
              <ul className="mt-3 space-y-3">
                {nb.open.map((m) => <MistakeCard key={m.id} m={m} onUnderstood={async () => setData(await exercisesApi.understood(m.id))} />)}
              </ul>
            </section>
          )}

          {nb.mastered.length > 0 && (
            <section aria-labelledby="done-h">
              <h2 id="done-h" className="text-xl">Fixed ({nb.mastered.length})</h2>
              <ul className="mt-3 grid gap-2 sm:grid-cols-2">
                {nb.mastered.map((m) => (
                  <li key={m.id} className="card flex items-center gap-3 p-3">
                    <Check aria-hidden className="size-5 text-success" />
                    <span className="font-bold">{m.correction}</span>
                    <span className="ml-auto text-xs font-semibold text-ink-faint">{m.category}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </>
      )}
    </div>
  );
}

const STATE_LABEL: Record<WeaknessState, { label: string; tone: "neutral" | "accent" | "success" | "warning" }> = {
  detected: { label: "Detected", tone: "warning" },
  training: { label: "Training", tone: "accent" },
  improving: { label: "Improving", tone: "success" },
  retest_due: { label: "Retest due", tone: "accent" },
  mastered: { label: "Mastered", tone: "success" },
};
const CATEGORY_LABEL = { grammar: "Grammar", spelling: "Spelling", vocabulary: "Vocabulary", comprehension: "Comprehension", expression: "Expression", other: "Other" };

function WeaknessCard({ w }: { w: Weakness }) {
  const s = STATE_LABEL[w.state];
  const last = w.examples[w.examples.length - 1];
  return (
    <li className="card p-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone={s.tone}>{s.label}</Badge>
        <Badge>{CATEGORY_LABEL[w.category]}</Badge>
        {w.task && <Badge>{w.task}</Badge>}
        {w.reopen_count > 0 && <Badge tone="warning">Came back ×{w.reopen_count}</Badge>}
      </div>
      <p className="mt-2 font-extrabold">{w.competency}</p>
      {last && last.correction && (
        <p className="text-sm font-semibold text-ink-soft">
          Last time: <span className="text-danger">{last.answer || "—"}</span> → <span className="text-success">{last.correction}</span>
        </p>
      )}
      {w.state !== "mastered" && (
        <div className="mt-2">
          <Meter value={Math.round(w.severity * 100)} max={100} label={`Severity of ${w.competency}`} color="var(--orange)" />
          <p className="mt-1 text-xs font-bold text-ink-faint">
            Seen {w.frequency}× · diagnosis confidence {w.confidence}
            {w.state === "retest_due" && (w.retest_item ? " · a new question is waiting in your reviews" : " · no new question available yet")}
            {w.rethink ? " · trying a different approach next" : ""}
          </p>
        </div>
      )}
    </li>
  );
}

function MistakeCard({ m, onUnderstood }: { m: Mistake; onUnderstood: () => void }) {
  const skill = skillName[m.skill as keyof typeof skillName];
  return (
    <li className="card p-5">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone="accent">{skill?.fr ?? m.skill}</Badge>
        <Badge>{m.category}</Badge>
        {m.recurrence > 1 && <Badge tone="warning">×{m.recurrence}</Badge>}
        <Badge tone={m.status === "improving" ? "success" : "neutral"}>{m.status === "improving" ? "Improving" : "Open"}</Badge>
        <span className="ml-auto flex items-center gap-1 text-xs font-bold text-ink-faint">
          <CalendarClock aria-hidden className="size-3.5" /> {m.due ? "Review today" : `Next review ${m.next_review}`}
        </span>
      </div>
      <p className="mt-3 font-bold">{m.context}</p>
      <dl className="mt-2 grid gap-2 sm:grid-cols-2">
        <div><dt className="eyebrow">You answered</dt><dd className="font-extrabold text-danger">{m.learner_answer || "—"}</dd></div>
        <div><dt className="eyebrow">Correct</dt><dd className="font-extrabold text-success">{m.correction}</dd></div>
      </dl>
      <p className="mt-2 text-sm text-ink-soft">{m.explanation}</p>
      {m.review_note && (
        <p className="mt-2 flex items-start gap-2 rounded-[14px] bg-surface-2 px-3 py-2 text-sm">
          <MessageSquareText aria-hidden className="mt-0.5 size-4 shrink-0" /> Reviewed: {m.review_note}
        </p>
      )}
      <div className="mt-3 flex justify-end">
        <Button variant="quiet" onClick={onUnderstood}><Check aria-hidden className="size-4" /> I understand now</Button>
      </div>
    </li>
  );
}

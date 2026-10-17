import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Check, Scale, Wrench, X } from "lucide-react";
import { exercisesApi, type ReviewReport } from "../lib/exercises";
import { useAsync } from "../lib/useAsync";
import { Badge, Button, ErrorNote, Loading, Panel } from "../components/ui";

/** Review queue: disputed answers and technical reports (blueprint "Feedback system"). */
export function ReviewPage() {
  const [state, reload] = useAsync(exercisesApi.review);

  return (
    <div className="space-y-6 px-5 pt-6 sm:px-10 sm:pt-10">
      <Link to="/entrainement" className="inline-flex items-center gap-1 text-sm font-extrabold text-ink-soft hover:text-ink">
        <ArrowLeft aria-hidden className="size-4" /> Entraînement
      </Link>
      <header>
        <p className="eyebrow">Révision des réponses</p>
        <h1 className="title-poster mt-1 text-5xl sm:text-6xl">Answers to review</h1>
        <p className="mt-2 max-w-2xl font-semibold text-ink-soft">
          Disputed answers don't count until you decide. Accepting one adds it as a correct answer for everyone from now on.
        </p>
      </header>

      {state.status === "loading" && <Loading />}
      {state.status === "error" && <ErrorNote error={state.error} onRetry={reload} />}
      {state.status === "ready" && (
        <>
          {state.data.reports.length === 0 ? (
            <Panel look="glass" className="flex items-center gap-3">
              <Check aria-hidden className="size-6 text-success" /> <p className="font-bold">Nothing to review. All clear.</p>
            </Panel>
          ) : (
            <ul className="space-y-4">
              {state.data.reports.map((r) => <ReportCard key={r.id} r={r} onDone={reload} />)}
            </ul>
          )}

          {state.data.items_to_fix.length > 0 && (
            <Panel>
              <h2 className="text-xl">Exercises to rewrite</h2>
              <ul className="mt-3 space-y-2">
                {state.data.items_to_fix.map((f) => (
                  <li key={f.item_id}>
                    <p className="font-extrabold">{f.item_id}</p>
                    {f.reasons.map((x) => <p key={x} className="text-sm text-ink-soft">{x}</p>)}
                  </li>
                ))}
              </ul>
            </Panel>
          )}
        </>
      )}
    </div>
  );
}

function ReportCard({ r, onDone }: { r: ReviewReport; onDone: () => void }) {
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isDispute = r.kind === "dispute";

  async function act(action: "accept" | "reject" | "close") {
    if (action === "reject" && !note.trim()) {
      setError("Write a short reason first.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await exercisesApi.resolve(r.id, action, note);
      onDone();
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
    }
  }

  return (
    <li className="card p-5">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone={isDispute ? "accent" : "warning"}>
          {isDispute ? <><Scale aria-hidden className="size-3.5" /> Dispute</> : <><Wrench aria-hidden className="size-3.5" /> Technical problem</>}
        </Badge>
        <Badge>{r.set_id} · {r.item_id}</Badge>
        <span className="text-xs font-bold text-ink-faint">{r.created_at}</span>
      </div>
      {r.prompt && <p className="mt-3 text-lg font-bold">{r.prompt}</p>}
      <dl className="mt-2 grid gap-1 sm:grid-cols-2">
        <div><dt className="eyebrow">Learner's answer</dt><dd className="font-extrabold">{r.learner_answer || "—"}</dd></div>
        <div><dt className="eyebrow">Expected</dt><dd className="font-extrabold">{r.expected ?? "—"}</dd></div>
      </dl>
      {r.note && <p className="mt-2 rounded-[14px] bg-surface-2 px-3 py-2 text-sm">« {r.note} »</p>}

      <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-center">
        <input value={note} onChange={(e) => setNote(e.target.value)} maxLength={500}
          placeholder={isDispute ? "Reason (required to reject, optional to accept)" : "Note (optional)"}
          aria-label="Decision note"
          className="flex-1 rounded-[14px] border-2 border-line bg-surface-2 px-3 py-2 outline-none focus:border-violet" />
        {isDispute ? (
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => act("reject")} busy={busy}><X aria-hidden className="size-4" /> Keep the key</Button>
            <Button onClick={() => act("accept")} busy={busy}><Check aria-hidden className="size-4" /> Accept answer</Button>
          </div>
        ) : (
          <Button variant="secondary" onClick={() => act("close")} busy={busy}><Check aria-hidden className="size-4" /> Done</Button>
        )}
      </div>
      {error && <p role="alert" className="mt-2 text-sm font-bold text-danger">{error}</p>}
    </li>
  );
}

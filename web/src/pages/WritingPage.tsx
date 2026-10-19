import { AiFailedNote } from "../components/AiFailedNote";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { AlertTriangle, ArrowLeft, Check, Clock, FileText, PenLine, RotateCcw, Sparkles } from "lucide-react";
import { useAsync } from "../lib/useAsync";
import { countWords, writingApi, type EETask, type Feedback, type Submission, type Template, type WritingTask } from "../lib/writing";
import { Badge, Button, ErrorNote, Loading, Meter, Panel, cx } from "../components/ui";

const TASK_NAME: Record<EETask, string> = { "EE-T1": "Tâche 1 · Message", "EE-T2": "Tâche 2 · Récit", "EE-T3": "Tâche 3 · Points de vue" };

/** Écrit: list of writing tasks (EE T1–T3). */
export function WritingList() {
  const [state, reload] = useAsync(writingApi.list);
  return (
    <div className="space-y-6 px-5 pt-6 sm:px-10 sm:pt-10">
      <Link to="/entrainement" className="inline-flex items-center gap-1 text-sm font-extrabold text-ink-soft hover:text-ink">
        <ArrowLeft aria-hidden className="size-4" /> Entraînement
      </Link>
      <header>
        <p className="eyebrow">Expression écrite</p>
        <h1 className="title-poster mt-1 text-5xl sm:text-6xl">Writing studio</h1>
        <p className="mt-2 max-w-2xl font-semibold text-ink-soft">
          The three TCF Canada writing tasks with the real word ranges. Training mode shows a structure and useful phrases;
          exam mode is a countdown with nothing else on screen. Feedback comes from a local AI and is an unofficial estimate.
        </p>
      </header>
      {state.status === "loading" && <Loading />}
      {state.status === "error" && <ErrorNote error={state.error} onRetry={reload} />}
      {state.status === "ready" && (["EE-T1", "EE-T2", "EE-T3"] as EETask[]).map((t) => (
        <section key={t} aria-labelledby={`${t}-h`}>
          <h2 id={`${t}-h`} className="text-xl">{TASK_NAME[t]} <span className="text-sm font-semibold text-ink-faint">
            {state.data.tasks.find((x) => x.task === t)?.words.min}–{state.data.tasks.find((x) => x.task === t)?.words.max} mots</span></h2>
          <ul className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {state.data.tasks.filter((x) => x.task === t).map((x) => (
              <li key={x.id}>
                <Link to={`/ecrit/${x.id}`} className="card flex h-full flex-col gap-2 p-4 transition-transform hover:-translate-y-1">
                  <div className="flex flex-wrap gap-1.5"><Badge>{x.level}</Badge>
                    {x.last?.status === "submitted" && <Badge tone="success"><Check aria-hidden className="size-3" /> Done</Badge>}
                    {x.last?.status === "draft" && <Badge tone="accent">Draft saved</Badge>}</div>
                  <p className="text-lg font-extrabold">{x.title}</p>
                  <p className="line-clamp-3 text-sm text-ink-soft">{x.prompt}</p>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}

/** One writing task: choose mode → write (autosave, timer, live word count) → submit → feedback. */
export function WritingStudio() {
  const { taskId = "" } = useParams();
  const [state, reload] = useAsync(() => writingApi.task(taskId), [taskId]);
  const [sub, setSub] = useState<Submission | null>(null);
  if (state.status === "loading") return <div className="px-5"><Loading /></div>;
  if (state.status === "error") return <div className="p-5"><ErrorNote error={state.error} onRetry={reload} /></div>;
  const { task, template, history } = state.data;

  return (
    <div className="mx-auto max-w-4xl space-y-5 px-5 pt-6 pb-10 sm:px-10">
      <Link to="/ecrit" className="inline-flex items-center gap-1 text-sm font-extrabold text-ink-soft hover:text-ink">
        <ArrowLeft aria-hidden className="size-4" /> Writing studio
      </Link>
      {!sub ? (
        <TaskIntro task={task} history={history.length}
          onStart={async (mode) => setSub(await writingApi.start(task.id, mode))} />
      ) : sub.status === "draft" ? (
        <Editor task={task} template={sub.mode === "training" ? template : null} initial={sub} onSubmitted={setSub} />
      ) : (
        <Result task={task} sub={sub} onUpdate={setSub} onAgain={() => { setSub(null); reload(); }} />
      )}
    </div>
  );
}

function Prompt({ task }: { task: WritingTask }) {
  return (
    <Panel pad="sm">
      <div className="flex flex-wrap gap-1.5"><Badge tone="accent">{TASK_NAME[task.task]}</Badge><Badge>{task.level}</Badge>
        <Badge>{task.words.min}–{task.words.max} mots</Badge></div>
      <h1 className="mt-2 text-2xl">{task.title}</h1>
      <p className="mt-2 text-lg font-semibold">{task.prompt}</p>
      <p className="mt-1 text-sm text-ink-faint">Destinataire : {task.recipient}</p>
      {task.documents.map((d) => (
        <blockquote key={d.title} className="mt-3 rounded-[16px] bg-surface-2 p-3 text-sm">
          <p className="eyebrow">{d.title}</p><p className="mt-1">{d.text}</p>
        </blockquote>
      ))}
    </Panel>
  );
}

function TaskIntro({ task, history, onStart }: { task: WritingTask; history: number; onStart: (m: "training" | "exam") => void }) {
  return (
    <>
      <Prompt task={task} />
      <div className="grid gap-3 sm:grid-cols-2">
        <Panel pad="sm" className="flex flex-col gap-2">
          <p className="flex items-center gap-2 text-lg font-extrabold"><PenLine aria-hidden className="size-5" /> Training</p>
          <p className="text-sm text-ink-soft">Structure, useful phrases and a live word counter. No time limit.</p>
          <Button onClick={() => onStart("training")} className="mt-auto">Start training</Button>
        </Panel>
        <Panel pad="sm" className="flex flex-col gap-2">
          <p className="flex items-center gap-2 text-lg font-extrabold"><Clock aria-hidden className="size-5" /> Exam conditions</p>
          <p className="text-sm text-ink-soft">
            {Math.round(task.exam_seconds / 60)} min countdown (a suggested share of the 60-minute paper), no help on screen.
            The text is submitted automatically when time runs out.
          </p>
          <Button variant="secondary" onClick={() => onStart("exam")} className="mt-auto">Start in exam conditions</Button>
        </Panel>
      </div>
      {history > 0 && <p className="text-sm font-semibold text-ink-faint">You've submitted this task {history}×. Try it again to see if you've improved.</p>}
    </>
  );
}

export function Editor({ task, template, initial, onSubmitted }: {
  task: WritingTask; template: Template | null; initial: Submission; onSubmitted: (s: Submission) => void;
}) {
  const [text, setText] = useState(initial.text);
  const [saved, setSaved] = useState<"saved" | "saving" | "error">("saved");
  const [remaining, setRemaining] = useState<number | null>(initial.remaining_s);
  const [busy, setBusy] = useState(false);
  const lastSaved = useRef(initial.text);
  const words = countWords(text);
  const exam = initial.mode === "exam";

  const flush = useCallback(async (value: string) => {
    if (value === lastSaved.current) return;
    setSaved("saving");
    try {
      await writingApi.save(initial.id, value);
      lastSaved.current = value;
      setSaved("saved");
    } catch {
      setSaved("error");
    }
  }, [initial.id]);

  useEffect(() => {                                     // autosave 1.2 s after typing stops
    const t = setTimeout(() => void flush(text), 1200);
    return () => clearTimeout(t);
  }, [text, flush]);

  const submit = useCallback(async () => {
    setBusy(true);
    await flush(text).catch(() => undefined);
    onSubmitted(await writingApi.submit(initial.id));
  }, [flush, text, initial.id, onSubmitted]);

  useEffect(() => {                                     // exam countdown; auto-submit at zero
    if (remaining === null) return;
    if (remaining <= 0) { void submit(); return; }
    const t = setTimeout(() => setRemaining((r) => (r === null ? r : r - 1)), 1000);
    return () => clearTimeout(t);
  }, [remaining, submit]);

  const r = task.words;
  const state = words < r.min ? "short" : words > r.max ? "long" : "ok";
  return (
    <>
      <Prompt task={task} />
      <div className={cx("grid gap-4", template && "lg:grid-cols-[1fr_18rem]")}>
        <div>
          <div className="mb-2 flex flex-wrap items-center justify-between gap-2 text-sm font-extrabold">
            <span className={cx(state === "ok" ? "text-success" : "text-warning")}>
              {words} mots · {r.min}–{r.max} {state === "short" ? `(encore ${r.min - words})` : state === "long" ? `(${words - r.max} de trop)` : ""}
            </span>
            {exam && remaining !== null && (
              <span className={cx("flex items-center gap-1", remaining < 60 && "text-danger")} aria-live="polite">
                <Clock aria-hidden className="size-4" /> {Math.floor(remaining / 60)}:{String(remaining % 60).padStart(2, "0")}
              </span>
            )}
            <span className="text-ink-faint">{saved === "saving" ? "Saving…" : saved === "error" ? "Not saved (retrying)" : "Saved"}</span>
          </div>
          <textarea value={text} onChange={(e) => setText(e.target.value)} lang="fr" spellCheck={!exam} autoFocus
            aria-label="Your text" rows={14}
            className="w-full rounded-[20px] border-2 border-line bg-surface p-4 text-lg leading-relaxed focus:border-violet focus:outline-none" />
          <div className="mt-3 flex flex-wrap items-center justify-end gap-3">
            {state !== "ok" && words > 0 && (
              <p className="flex items-center gap-1 text-sm font-semibold text-warning">
                <AlertTriangle aria-hidden className="size-4" /> Outside the range: in the real test this can make the paper « A1 non atteint ».
              </p>
            )}
            <Button onClick={submit} busy={busy} disabled={words === 0}>Submit</Button>
          </div>
        </div>
        {template && (
          <Panel pad="sm" look="glass" className="h-fit text-sm">
            <p className="eyebrow">Structure</p>
            <ol className="mt-1 list-decimal space-y-1 pl-4">{template.steps.map((s) => <li key={s}>{s}</li>)}</ol>
            <p className="eyebrow mt-3">Useful phrases</p>
            <ul className="mt-1 space-y-1">{template.phrases.map((p) => <li key={p} className="font-semibold">{p}</li>)}</ul>
            <p className="mt-3 text-ink-faint">{template.avoid}</p>
          </Panel>
        )}
      </div>
    </>
  );
}

function Result({ task, sub, onUpdate, onAgain }: { task: WritingTask; sub: Submission; onUpdate: (s: Submission) => void; onAgain: () => void }) {
  const navigate = useNavigate();
  useEffect(() => {                                      // poll while the local AI is scoring
    if (sub.feedback_status !== "pending") return;
    const t = setInterval(async () => onUpdate(await writingApi.get(sub.id)), 3000);
    return () => clearInterval(t);
  }, [sub.feedback_status, sub.id, onUpdate]);

  return (
    <>
      <Panel pad="sm">
        <div className="flex flex-wrap gap-1.5">
          <Badge tone="accent">{TASK_NAME[task.task]}</Badge>
          <Badge tone={sub.range.ok ? "success" : "warning"}>{sub.word_count} mots · {sub.range.min}–{sub.range.max}</Badge>
          {sub.mode === "exam" && <Badge>{sub.timed_out ? "Time ran out" : "Exam conditions"}</Badge>}
        </div>
        {!sub.range.ok && (
          <p className="mt-2 flex items-start gap-2 text-sm font-semibold text-warning">
            <AlertTriangle aria-hidden className="mt-0.5 size-4 shrink-0" />
            {sub.range.state === "short" ? "Too short" : "Too long"} for {task.task}. In the real TCF, a task outside its word range can make the whole writing paper « A1 non atteint ».
          </p>
        )}
        <p className="mt-3 whitespace-pre-wrap rounded-[16px] bg-surface-2 p-3">{sub.text}</p>
      </Panel>

      {sub.feedback_status === "pending" && <Panel pad="sm"><Loading label="The AI is reading your text twice (about 30–60 s)…" /></Panel>}
      {sub.feedback_status === "failed" && <AiFailedNote what="text" onRetry={async () => onUpdate(await writingApi.retry(sub.id))} />}
      {sub.feedback && <FeedbackView fb={sub.feedback} />}

      <div className="flex flex-wrap justify-end gap-3">
        <Button variant="secondary" onClick={() => navigate("/carnet")}>Weak points</Button>
        <Button onClick={onAgain}><RotateCcw aria-hidden className="size-4" /> Rewrite this task</Button>
      </div>
    </>
  );
}

export function FeedbackView({ fb }: { fb: Feedback }) {
  const errors = fb.corrections.filter((c) => c.kind === "error");
  const style = fb.corrections.filter((c) => c.kind === "style");
  return (
    <>
      <Panel pad="sm">
        <div className="flex flex-wrap items-center gap-2">
          <Sparkles aria-hidden className="size-5 text-violet" />
          <p className="font-extrabold">Feedback · level of this text ≈ {fb.cefr_estimate}</p>
          {fb.agreement === "low" && <Badge tone="warning">The two readings disagreed: ranges shown</Badge>}
        </div>
        <p className="text-xs font-semibold text-ink-faint">{fb.label}</p>
        <ul className="mt-3 space-y-3">
          {Object.entries(fb.criteria).map(([k, c]) => (
            <li key={k}>
              <div className="mb-1 flex justify-between text-sm font-bold">
                <span>{c.label}</span><span className="text-ink-faint">{c.low === c.high ? c.low : `${c.low}–${c.high}`} / 5</span>
              </div>
              <Meter value={c.score} max={5} label={c.label} />
              <p className="mt-1 text-sm text-ink-soft">{c.comment}</p>
            </li>
          ))}
        </ul>
      </Panel>
      <div className="grid gap-3 sm:grid-cols-2">
        <Panel pad="sm"><p className="eyebrow">Strengths</p><ul className="mt-1 list-disc pl-4 text-sm">{fb.strengths.map((s) => <li key={s}>{s}</li>)}</ul></Panel>
        <Panel pad="sm"><p className="eyebrow">Work on next</p><ul className="mt-1 list-disc pl-4 text-sm">{fb.priorities.map((s) => <li key={s}>{s}</li>)}</ul></Panel>
      </div>
      <Panel pad="sm">
        <p className="eyebrow">Corrections ({errors.length})</p>
        {errors.length === 0 && <p className="text-sm text-ink-soft">No language errors found.</p>}
        <ul className="mt-2 space-y-2">
          {errors.map((c) => (
            <li key={c.original + c.corrected} className="text-sm">
              <span className="font-bold text-danger line-through">{c.original}</span> → <span className="font-bold text-success">{c.corrected}</span>
              <span className="ml-2 text-xs text-ink-faint">{c.category}{c.source === "rule" ? " · rule" : ""}</span>
              <p className="text-ink-soft">{c.explanation}</p>
            </li>
          ))}
        </ul>
        {style.length > 0 && (
          <>
            <p className="eyebrow mt-4">Style suggestions (not mistakes)</p>
            <ul className="mt-2 space-y-2">{style.map((c) => (
              <li key={c.original + c.corrected} className="text-sm"><span className="font-bold">{c.original}</span> → <span className="font-bold">{c.corrected}</span>
                <p className="text-ink-soft">{c.explanation}</p></li>))}</ul>
          </>
        )}
      </Panel>
      <Panel pad="sm">
        <p className="eyebrow flex items-center gap-1"><FileText aria-hidden className="size-3.5" /> A revised version</p>
        <p className="mt-1 whitespace-pre-wrap text-sm">{fb.revised_version}</p>
        <p className="mt-2 text-xs text-ink-faint">Read it, then close it and rewrite the task yourself. Copying it teaches nothing.</p>
      </Panel>
    </>
  );
}

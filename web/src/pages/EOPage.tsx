import { AiFailedNote } from "../components/AiFailedNote";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Check, Clock, Eye, RotateCcw, Sparkles, Square, Volume2, X } from "lucide-react";
import { MicRecorder } from "../components/MicRecorder";
import { useAsync } from "../lib/useAsync";
import { speak, stopSpeaking } from "../lib/speak";
import { EO_NAME, eoApi, type EOFeedback, type EOSession, type EOTask, type EOTaskInfo, type Guide } from "../lib/eo";
import { Badge, Button, ErrorNote, Loading, Meter, Panel, cx } from "../components/ui";

const fmt = (s: number) => `${Math.floor(s / 60)}:${String(Math.max(0, s) % 60).padStart(2, "0")}`;

/** List of examiner tasks, shown on the speaking page. */
export function EOTaskList() {
  const [state] = useAsync(eoApi.list);
  if (state.status !== "ready") return state.status === "loading" ? <Loading /> : null;
  return (
    <div className="space-y-4">
      {(["EO-T1", "EO-T2", "EO-T3"] as EOTask[]).map((t) => (
        <section key={t} aria-label={EO_NAME[t]}>
          <h3 className="font-extrabold">{EO_NAME[t]}</h3>
          <ul className="mt-2 grid gap-2 sm:grid-cols-2">
            {state.data.tasks.filter((x) => x.task === t).map((x) => (
              <li key={x.id}>
                <Link to={`/oral/${x.id}`} className="card flex items-center gap-3 p-3 transition-transform hover:-translate-y-0.5">
                  <Badge>{x.level}</Badge><span className="font-bold">{x.title}</span>
                  {x.last?.status === "ended" && <Check aria-hidden className="ml-auto size-4 text-success" />}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}

/** One speaking task with the AI examiner: intro → (T2 preparation) → timed conversation → feedback. */
export function EOSessionPage() {
  const { taskId = "" } = useParams();
  const [state, reload] = useAsync(() => eoApi.task(taskId), [taskId]);
  const [session, setSession] = useState<EOSession | null>(null);
  if (state.status === "loading") return <div className="px-5"><Loading /></div>;
  if (state.status === "error") return <div className="p-5"><ErrorNote error={state.error} onRetry={reload} /></div>;
  const { task, guide } = state.data;
  return (
    <div className="mx-auto max-w-3xl space-y-5 px-5 pt-6 pb-10 sm:px-10">
      <Link to="/oral" className="inline-flex items-center gap-1 text-sm font-extrabold text-ink-soft hover:text-ink">
        <ArrowLeft aria-hidden className="size-4" /> Expression orale
      </Link>
      {!session ? (
        <Intro task={task} guide={guide} onStart={async (mode) => setSession(await eoApi.start(task.id, mode))} />
      ) : session.status === "ended" ? (
        <Result task={task} session={session} onUpdate={setSession} onAgain={() => { setSession(null); reload(); }} />
      ) : (
        <Conversation task={task} guide={guide} session={session} onUpdate={setSession} />
      )}
    </div>
  );
}

function TaskCard({ task, showTargets }: { task: EOTaskInfo; showTargets: boolean }) {
  return (
    <Panel pad="sm">
      <div className="flex flex-wrap gap-1.5"><Badge tone="accent">{EO_NAME[task.task]}</Badge><Badge>{task.level}</Badge>
        <Badge>{task.prep_s ? `${task.prep_s / 60} min de préparation + ` : ""}{fmt(task.talk_s)}</Badge></div>
      <h1 className="mt-2 text-2xl">{task.title}</h1>
      <p className="mt-2 font-semibold">{task.instructions}</p>
      {showTargets && task.targets.length > 0 && (
        <ul className="mt-2 list-disc pl-5 text-sm text-ink-soft">{task.targets.map((t) => <li key={t}>{t}</li>)}</ul>
      )}
    </Panel>
  );
}

function GuidePanel({ guide }: { guide: Guide }) {
  return (
    <Panel pad="sm" look="glass" className="text-sm">
      <p className="eyebrow">{guide.title}</p>
      <ul className="mt-1 list-disc space-y-1 pl-4">{guide.tips.map((t) => <li key={t}>{t}</li>)}</ul>
      <p className="mt-2 font-semibold">{guide.phrases.join(" · ")}</p>
    </Panel>
  );
}

function Intro({ task, guide, onStart }: { task: EOTaskInfo; guide: Guide; onStart: (m: "training" | "exam") => void }) {
  return (
    <>
      <TaskCard task={task} showTargets />
      <GuidePanel guide={guide} />
      <div className="grid gap-3 sm:grid-cols-2">
        <Panel pad="sm" className="flex flex-col gap-2">
          <p className="text-lg font-extrabold">Training</p>
          <p className="text-sm text-ink-soft">The examiner's lines are shown as text, tips stay on screen.</p>
          <Button onClick={() => onStart("training")} className="mt-auto">Start</Button>
        </Panel>
        <Panel pad="sm" className="flex flex-col gap-2">
          <p className="text-lg font-extrabold">Exam conditions</p>
          <p className="text-sm text-ink-soft">Listen only (no examiner text), no tips, strict timer. Feedback at the end.</p>
          <Button variant="secondary" onClick={() => onStart("exam")} className="mt-auto">Start in exam conditions</Button>
        </Panel>
      </div>
      <p className="text-xs font-semibold text-ink-faint">
        The examiner is a local AI playing the role. Feedback covers content and language only: there's no pronunciation score,
        because the transcription itself can be wrong.
      </p>
    </>
  );
}

export function Conversation({ task, guide, session, onUpdate }: {
  task: EOTaskInfo; guide: Guide; session: EOSession; onUpdate: (s: EOSession) => void;
}) {
  const exam = session.mode === "exam";
  const [remaining, setRemaining] = useState(session.remaining_s);
  const [waiting, setWaiting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reveal, setReveal] = useState<number | null>(null);
  const spoken = useRef(0);
  const examinerTurns = session.turns.filter((t) => t.role === "examiner");

  useEffect(() => setRemaining(session.remaining_s), [session.remaining_s, session.status]);
  useEffect(() => {                                       // speak each new examiner line once
    if (examinerTurns.length > spoken.current) {
      spoken.current = examinerTurns.length;
      void speak(examinerTurns[examinerTurns.length - 1].text, { speaker: task.examiner });
    }
  }, [examinerTurns, task.examiner]);
  useEffect(() => () => stopSpeaking(), []);

  const finish = useCallback(async () => { stopSpeaking(); onUpdate(await eoApi.end(session.id)); }, [session.id, onUpdate]);
  useEffect(() => {
    if (remaining <= 0) {
      if (session.status === "prep") void eoApi.begin(session.id).then(onUpdate);
      else void finish();
      return;
    }
    const t = setTimeout(() => setRemaining((r) => r - 1), 1000);
    return () => clearTimeout(t);
  }, [remaining, session.status, session.id, onUpdate, finish]);

  async function send(r: { text: string; source: string; transcript: { confidence: number; status: string; recording_id: number } | null }) {
    setWaiting(true); setError(null); stopSpeaking();
    try {
      onUpdate(await eoApi.turn(session.id, {
        text: r.text, source: r.source, confidence: r.transcript?.confidence, asr_status: r.transcript?.status,
        recording_id: r.transcript?.recording_id }));
    } catch (e) {
      const err = e as Error & { status?: number };
      if (err.status === 409) onUpdate(await eoApi.get(session.id));
      else setError(err.message);
    } finally {
      setWaiting(false);
    }
  }

  if (session.status === "prep") {
    return (
      <>
        <TaskCard task={task} showTargets={!exam} />
        {!exam && <GuidePanel guide={guide} />}
        <Panel pad="sm" className="flex flex-wrap items-center gap-4">
          <Clock aria-hidden className="size-6 text-violet" />
          <div className="flex-1"><p className="text-lg font-extrabold">Preparation: {fmt(remaining)}</p>
            <p className="text-sm text-ink-soft">List the questions you'll ask. The conversation starts automatically.</p></div>
          <Button onClick={async () => onUpdate(await eoApi.begin(session.id))}>I'm ready</Button>
        </Panel>
      </>
    );
  }

  return (
    <>
      <div className="sticky top-2 z-10 flex items-center justify-between rounded-full bg-surface/90 px-4 py-2 shadow-card backdrop-blur">
        <span className="font-extrabold">{EO_NAME[task.task]}</span>
        <span className={cx("flex items-center gap-1 font-extrabold", remaining < 30 && "text-danger")} aria-live="off">
          <Clock aria-hidden className="size-4" /> {fmt(remaining)}
        </span>
      </div>
      {!exam && <TaskCard task={task} showTargets />}
      <ol className="space-y-3" aria-label="Conversation">
        {session.turns.map((t, i) => (
          <li key={i} className={cx("flex", t.role === "learner" && "justify-end")}>
            <div className={cx("card max-w-[85%] p-3", t.role === "learner" && "bg-violet/10")}>
              <p className="text-xs font-extrabold uppercase tracking-wider text-ink-faint">{t.role === "examiner" ? task.examiner : "Vous"}
                {t.role === "learner" && t.source !== "speech" && <span className="ml-1 normal-case">({t.source})</span>}</p>
              {t.role === "examiner" && exam && reveal !== i ? (
                <div className="mt-1 flex gap-2">
                  <Button variant="secondary" className="min-h-9" onClick={() => speak(t.text, { speaker: task.examiner })}><Volume2 aria-hidden className="size-4" /> Listen</Button>
                  <Button variant="quiet" className="min-h-9" onClick={() => setReveal(i)}><Eye aria-hidden className="size-4" /> Can't hear</Button>
                </div>
              ) : (
                <p className="mt-0.5 text-lg font-semibold">{t.text}
                  {t.role === "examiner" && <button type="button" onClick={() => speak(t.text, { speaker: task.examiner })} aria-label="Hear again"
                    className="ml-2 inline-grid size-7 place-items-center rounded-full bg-surface-2 align-middle"><Volume2 aria-hidden className="size-3.5" /></button>}
                </p>
              )}
            </div>
          </li>
        ))}
      </ol>
      {session.ai_fallbacks > 0 && <p className="text-xs font-semibold text-warning">The local AI didn't answer {session.ai_fallbacks}×: a standard examiner line was used.</p>}
      {error && <p className="text-sm font-semibold text-danger">{error}</p>}
      <Panel pad="sm">
        {waiting ? <Loading label={`${task.examiner} is answering…`} /> : (
          <MicRecorder onResult={send} maxSeconds={Math.max(10, remaining)} context="eo-task" refId={task.id}
            prompt="Press, answer in French, press to stop" />
        )}
      </Panel>
      <div className="flex justify-end"><Button variant="secondary" onClick={finish}><Square aria-hidden className="size-4" /> End the task</Button></div>
    </>
  );
}

function Result({ task, session, onUpdate, onAgain }: { task: EOTaskInfo; session: EOSession; onUpdate: (s: EOSession) => void; onAgain: () => void }) {
  const navigate = useNavigate();
  useEffect(() => {
    if (session.feedback_status !== "pending") return;
    const t = setInterval(async () => onUpdate(await eoApi.get(session.id)), 3000);
    return () => clearInterval(t);
  }, [session.feedback_status, session.id, onUpdate]);
  return (
    <>
      <Panel pad="sm">
        <div className="flex flex-wrap gap-1.5"><Badge tone="accent">{EO_NAME[task.task]}</Badge>
          <Badge>{session.end_reason === "time" ? "Time ran out" : "Ended"}</Badge><Badge>{session.mode === "exam" ? "Exam conditions" : "Training"}</Badge></div>
        <h1 className="mt-2 text-2xl">{task.title}</h1>
        <details className="mt-2"><summary className="cursor-pointer text-sm font-bold text-ink-soft">Transcript</summary>
          <ul className="mt-2 space-y-1 text-sm">{session.turns.map((t, i) => (
            <li key={i}><span className="font-extrabold">{t.role === "examiner" ? task.examiner : "Vous"} :</span> {t.text}</li>))}</ul>
        </details>
      </Panel>
      {session.feedback_status === "none" && <Panel pad="sm"><p className="font-semibold">You didn't answer, so there's nothing to give feedback on.</p></Panel>}
      {session.feedback_status === "pending" && <Panel pad="sm"><Loading label="The AI is reviewing the conversation (about 30 s)…" /></Panel>}
      {session.feedback_status === "failed" && <AiFailedNote what="conversation" onRetry={async () => onUpdate(await eoApi.retry(session.id))} />}
      {session.feedback && <EOFeedbackView fb={session.feedback} />}
      <div className="flex flex-wrap justify-end gap-3">
        <Button variant="secondary" onClick={() => navigate("/carnet")}>Weak points</Button>
        <Button onClick={onAgain}><RotateCcw aria-hidden className="size-4" /> Do it again</Button>
      </div>
    </>
  );
}

export function EOFeedbackView({ fb }: { fb: EOFeedback }) {
  const errors = fb.corrections.filter((c) => c.kind === "error");
  const style = fb.corrections.filter((c) => c.kind === "style");
  return (
    <>
      <Panel pad="sm">
        <div className="flex flex-wrap items-center gap-2">
          <Sparkles aria-hidden className="size-5 text-violet" />
          <p className="font-extrabold">Feedback · level of this performance ≈ {fb.cefr_estimate}</p>
          {fb.agreement === "low" && <Badge tone="warning">The two readings disagreed: ranges shown</Badge>}
        </div>
        <p className="text-xs font-semibold text-ink-faint">{fb.label}</p>
        <p className="mt-2 text-sm font-semibold">
          You spoke {fb.stats.words} words in {fb.stats.turns} turns (longest answer: {fb.stats.longest} words).
          {fb.stats.uncertain_turns > 0 && ` ${fb.stats.uncertain_turns} turn(s) had an uncertain transcription and weren't used for language corrections.`}
        </p>
        <ul className="mt-3 space-y-3">
          {Object.entries(fb.criteria).map(([k, c]) => (
            <li key={k}>
              <div className="mb-1 flex justify-between text-sm font-bold"><span>{c.label}</span>
                <span className="text-ink-faint">{c.low === c.high ? c.low : `${c.low}–${c.high}`} / 5</span></div>
              <Meter value={c.score} max={5} label={c.label} />
              <p className="mt-1 text-sm text-ink-soft">{c.comment}</p>
            </li>
          ))}
        </ul>
      </Panel>
      {fb.targets.length > 0 && (
        <Panel pad="sm"><p className="eyebrow">Information obtained</p>
          <ul className="mt-1 space-y-1 text-sm">{fb.targets.map((t) => (
            <li key={t.text} className="flex items-center gap-2">{t.obtained ? <Check aria-hidden className="size-4 text-success" /> : <X aria-hidden className="size-4 text-danger" />}{t.text}</li>))}</ul>
        </Panel>
      )}
      <div className="grid gap-3 sm:grid-cols-2">
        <Panel pad="sm"><p className="eyebrow">Strengths</p><ul className="mt-1 list-disc pl-4 text-sm">{fb.strengths.map((s) => <li key={s}>{s}</li>)}</ul></Panel>
        <Panel pad="sm"><p className="eyebrow">Work on next</p><ul className="mt-1 list-disc pl-4 text-sm">{fb.priorities.map((s) => <li key={s}>{s}</li>)}</ul></Panel>
      </div>
      <Panel pad="sm">
        <p className="eyebrow">Corrections ({errors.length})</p>
        {errors.length === 0 && <p className="text-sm text-ink-soft">No language errors found in the reliable turns.</p>}
        <ul className="mt-2 space-y-2">{errors.map((c) => (
          <li key={c.original + c.corrected} className="text-sm"><span className="font-bold text-danger line-through">{c.original}</span> → <span className="font-bold text-success">{c.corrected}</span>
            <p className="text-ink-soft">{c.explanation}</p></li>))}</ul>
        {style.length > 0 && (<><p className="eyebrow mt-4">Style suggestions (not mistakes)</p>
          <ul className="mt-2 space-y-2">{style.map((c) => (
            <li key={c.original + c.corrected} className="text-sm"><span className="font-bold">{c.original}</span> → <span className="font-bold">{c.corrected}</span>
              <p className="text-ink-soft">{c.explanation}</p></li>))}</ul></>)}
      </Panel>
      <Panel pad="sm">
        <p className="eyebrow">A better way to say one of your answers</p>
        <p className="mt-1 flex items-start gap-2 font-semibold">{fb.better_answer}
          <button type="button" onClick={() => speak(fb.better_answer, { speaker: "Céleste" })} aria-label="Hear it"
            className="grid size-7 shrink-0 place-items-center rounded-full bg-surface-2"><Volume2 aria-hidden className="size-3.5" /></button></p>
      </Panel>
    </>
  );
}

import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Check, Clock, Play, X } from "lucide-react";
import { useAsync } from "../lib/useAsync";
import { speak, stopSpeaking } from "../lib/speak";
import { examApi, SECTION_NAME, SECTION_RULES, type ExamAttempt, type ExamReport, type SectionResult } from "../lib/exam";
import { writingApi, type Submission } from "../lib/writing";
import { eoApi, type EOSession } from "../lib/eo";
import { Editor, FeedbackView } from "./WritingPage";
import { Conversation, EOFeedbackView } from "./EOPage";
import { Button, ErrorNote, Loading, Panel, cx } from "../components/ui";

const fmt = (s: number) => `${Math.floor(Math.max(0, s) / 60)}:${String(Math.max(0, s) % 60).padStart(2, "0")}`;

/** Examens: weekly trials (partial simulations). Plain, quiet layout: exam mode is separate from the game. */
export function ExamList() {
  const navigate = useNavigate();
  const [state, reload] = useAsync(examApi.list);
  const [error, setError] = useState<string | null>(null);
  async function start(id: string) {
    try {
      const a = await examApi.start(id);
      navigate(`/examen/${a.id}`);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  return (
    <div className="mx-auto max-w-3xl space-y-6 px-5 pt-6 pb-10 sm:px-10">
      <Link to="/entrainement" className="inline-flex items-center gap-1 text-sm font-semibold text-ink-soft hover:text-ink">
        <ArrowLeft aria-hidden className="size-4" /> Entraînement
      </Link>
      <header>
        <h1 className="text-3xl font-bold">Examens</h1>
        <p className="mt-2 text-ink-soft">
          A weekly four-skill trial, with unseen questions and exam rules: each recording plays once, there's no help and no feedback
          until the end, and every section is timed. It's a partial simulation, shorter than the real TCF Canada (2 h 47).
          Results are practice estimates, never an official score.
        </p>
      </header>
      {error && <p className="text-sm font-semibold text-danger">{error}</p>}
      {state.status === "loading" && <Loading />}
      {state.status === "error" && <ErrorNote error={state.error} onRetry={reload} />}
      {state.status === "ready" && (
        <ul className="space-y-3">
          {[...state.data.exams].sort((a, b) => ["diagnostic", "weekly", "section", "full"].indexOf(a.kind) - ["diagnostic", "weekly", "section", "full"].indexOf(b.kind)).map((e) => (
            <li key={e.id} className="rounded-[16px] border border-line bg-surface p-4">
              <div className="flex flex-wrap items-center gap-3">
                <div className="min-w-0 flex-1">
                  <p className="text-lg font-bold">{e.title} <span className="text-xs font-semibold uppercase text-ink-faint">{e.kind === "full" ? "full mock" : e.kind === "section" ? "section mock" : e.kind}</span></p>
                  <p className="text-sm text-ink-soft">
                    {e.sections.map((s) => `${SECTION_NAME[s.section]} ${Math.round(s.limit_s / 60)} min`).join(" · ")}
                  </p>
                </div>
                {e.blocked_by_seen && e.status === "available" ? (
                  <span className="max-w-48 text-right text-xs text-ink-faint">Already partly used ({e.blocked_by_seen}): no longer unseen.</span>
                ) : e.status === "completed" && e.attempt_id ? (
                  <Button variant="secondary" onClick={() => navigate(`/examen/${e.attempt_id}`)}>See results</Button>
                ) : (
                  <Button onClick={() => start(e.id)}>{e.status === "in_progress" ? "Continue" : "Start"}</Button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
      {state.status === "ready" && !state.data.weekly_due && state.data.next_weekly && (
        <p className="text-sm text-ink-faint">Your next weekly trial is recommended in {7 - (state.data.days_since_last_weekly ?? 0)} day(s).</p>
      )}
    </div>
  );
}

export function ExamRunner() {
  const { attemptId = "" } = useParams();
  const aid = Number(attemptId);
  const [state, reload] = useAsync(() => examApi.get(aid), [aid]);
  const [a, setA] = useState<ExamAttempt | null>(null);
  const attempt = a ?? (state.status === "ready" ? state.data : null);
  useEffect(() => () => stopSpeaking(), []);
  useEffect(() => {                                   // keep the report fresh until writing/speaking feedback is in
    if (!attempt?.report || attempt.report.complete) return;
    const t = setTimeout(async () => setA(await examApi.get(aid)), 4000);
    return () => clearTimeout(t);
  }, [attempt, aid]);
  if (state.status === "loading" && !a) return <div className="px-5"><Loading /></div>;
  if (state.status === "error" && !a) return <div className="p-5"><ErrorNote error={state.error} onRetry={reload} /></div>;
  if (!attempt) return null;
  return (
    <div className="mx-auto max-w-3xl space-y-5 px-5 pt-6 pb-10 sm:px-10">
      <div className="flex items-center justify-between gap-3">
        <p className="font-bold">{attempt.title}</p>
        <ol className="flex gap-1 text-xs" aria-label="Sections">
          {attempt.sections.map((s, i) => (
            <li key={i} className={cx("rounded-full px-2 py-1 font-semibold",
              s.ended ? "bg-surface-2 text-ink-faint" : i === attempt.section_index ? "bg-ink text-surface" : "bg-surface-2")}>{s.section}</li>
          ))}
        </ol>
      </div>
      {attempt.status === "completed" ? <Results attempt={attempt} /> : <Section attempt={attempt} onUpdate={setA} />}
    </div>
  );
}

function Countdown({ seconds, onZero }: { seconds: number; onZero: () => void }) {
  const [left, setLeft] = useState(seconds);
  useEffect(() => setLeft(seconds), [seconds]);
  useEffect(() => {
    if (left <= 0) { onZero(); return; }
    const t = setTimeout(() => setLeft((l) => l - 1), 1000);
    return () => clearTimeout(t);
  }, [left, onZero]);
  return <span className={cx("flex items-center gap-1 font-bold tabular-nums", left < 60 && "text-danger")}><Clock aria-hidden className="size-4" /> {fmt(left)}</span>;
}

function Section({ attempt, onUpdate }: { attempt: ExamAttempt; onUpdate: (a: ExamAttempt) => void }) {
  const cur = attempt.current!;
  const [error, setError] = useState<string | null>(null);
  const refresh = useCallback(async () => onUpdate(await examApi.get(attempt.id)), [attempt.id, onUpdate]);
  const guard = async (fn: () => Promise<ExamAttempt>) => {
    setError(null);
    try { onUpdate(await fn()); } catch (e) { setError((e as Error).message); await refresh(); }
  };

  if (!cur.started) {
    return (
      <Panel>
        <h2 className="text-2xl font-bold">{SECTION_NAME[cur.section]}</h2>
        <p className="mt-2">{SECTION_RULES[cur.section]}</p>
        <p className="mt-2 text-sm text-ink-soft">Time: {fmt(cur.remaining_s)}. The timer starts when you begin.</p>
        <Button className="mt-4" onClick={() => guard(() => examApi.begin(attempt.id))}>Begin</Button>
      </Panel>
    );
  }

  return (
    <>
      <div className="sticky top-2 z-10 flex items-center justify-between rounded-full border border-line bg-surface px-4 py-2">
        <span className="font-semibold">{SECTION_NAME[cur.section]}{cur.position ? ` · ${cur.position}/${cur.total}` : ""}</span>
        <Countdown seconds={cur.remaining_s} onZero={refresh} />
      </div>
      {error && <p className="text-sm font-semibold text-danger">{error}</p>}
      {(cur.section === "CO" || cur.section === "CE") && cur.item && (
        <McqItem key={cur.item.id} attempt={attempt} onAnswer={(resp) => guard(() => examApi.answer(attempt.id, cur.item!.id, resp))} />
      )}
      {cur.section === "EE" && cur.writing_task && cur.writing_submission_id && (
        <ExamWriting attempt={attempt} onDone={() => guard(() => examApi.finish(attempt.id))} />
      )}
      {cur.section === "EO" && cur.eo_task && cur.eo_session_id && (
        <ExamSpeaking attempt={attempt} onDone={() => guard(() => examApi.finish(attempt.id))} />
      )}
    </>
  );
}

function McqItem({ attempt, onAnswer }: { attempt: ExamAttempt; onAnswer: (r: string | null) => void }) {
  const cur = attempt.current!;
  const item = cur.item as unknown as { id: string; type: string; question: string; passage: string | null; options: { id: string; text: string }[] };
  const [played, setPlayed] = useState(!!cur.played);
  const [playing, setPlaying] = useState(false);
  const [choice, setChoice] = useState<string | null>(null);
  const listen = item.type === "listen";

  async function play() {
    setPlaying(true);
    try {
      const audio = await examApi.play(attempt.id, item.id);
      setPlayed(true);
      await speak(audio.text, { speaker: audio.speaker ?? undefined, rate: 1 });
    } finally {
      setPlaying(false);
    }
  }

  return (
    <Panel>
      {listen && (
        <div className="mb-4 flex items-center gap-3">
          <Button onClick={play} disabled={played || playing}><Play aria-hidden className="size-4 fill-current" /> {played ? (playing ? "Playing…" : "Played") : "Play the recording"}</Button>
          <span className="text-sm text-ink-soft">One play only.</span>
        </div>
      )}
      {item.passage && <p className="mb-4 whitespace-pre-wrap rounded-[12px] bg-surface-2 p-4 leading-relaxed">{item.passage}</p>}
      {(!listen || (played && !playing)) && (
        <>
          <p className="text-lg font-semibold">{item.question}</p>
          <div role="radiogroup" className="mt-3 space-y-2">
            {item.options.map((o) => (
              <button key={o.id} type="button" role="radio" aria-checked={choice === o.id} onClick={() => setChoice(o.id)}
                className={cx("block w-full rounded-[12px] border px-4 py-3 text-left", choice === o.id ? "border-ink bg-surface-2 font-semibold" : "border-line hover:bg-surface-2")}>
                <span className="mr-2 font-bold uppercase">{o.id}</span>{o.text}
              </button>
            ))}
          </div>
          <div className="mt-4 flex justify-end gap-2">
            <Button variant="quiet" onClick={() => onAnswer(null)}>Skip</Button>
            <Button onClick={() => onAnswer(choice)} disabled={!choice}>Confirm</Button>
          </div>
        </>
      )}
    </Panel>
  );
}

function ExamWriting({ attempt, onDone }: { attempt: ExamAttempt; onDone: () => void }) {
  const cur = attempt.current!;
  const ids = cur.writing_submission_ids?.length ? cur.writing_submission_ids : [cur.writing_submission_id!];
  const tasks = cur.writing_tasks?.length ? cur.writing_tasks : [cur.writing_task!];
  const [tab, setTab] = useState(0);
  const [subs, setSubs] = useState<(Submission | null)[]>(ids.map(() => null));
  useEffect(() => {
    void Promise.all(ids.map((i) => writingApi.get(i))).then(setSubs);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ids.join(",")]);
  const markDone = (i: number, s: Submission) => {
    const next = subs.map((x, k) => (k === i ? s : x));
    setSubs(next);
    if (next.every((x) => x?.status === "submitted")) onDone();
    else setTab(next.findIndex((x) => x?.status !== "submitted"));
  };
  if (subs.some((s) => !s)) return <Loading />;
  if (ids.length === 1) return <Editor task={tasks[0]} template={null} initial={subs[0]!} onSubmitted={() => onDone()} />;
  return (
    <>
      <div className="flex flex-wrap items-center gap-2" role="tablist" aria-label="Writing tasks">
        {tasks.map((t, i) => (
          <button key={t.id} type="button" role="tab" aria-selected={tab === i} onClick={() => setTab(i)}
            className={cx("rounded-full border px-3 py-1.5 text-sm font-semibold", tab === i ? "border-ink bg-ink text-surface" : "border-line")}>
            Tâche {t.task.slice(-1)}{subs[i]?.status === "submitted" ? " ✓" : ""}
          </button>
        ))}
        <span className="text-xs text-ink-faint">One 60-minute block for the three tasks, in any order.</span>
        <Button variant="secondary" className="ml-auto min-h-9" onClick={onDone}>Finish the writing section</Button>
      </div>
      {subs[tab]?.status === "submitted"
        ? <Panel><p className="font-semibold">Task submitted. Choose another task above.</p></Panel>
        : <Editor key={ids[tab]} task={tasks[tab]} template={null} initial={subs[tab]!} onSubmitted={(s) => markDone(tab, s)} />}
    </>
  );
}

function ExamSpeaking({ attempt, onDone }: { attempt: ExamAttempt; onDone: () => void }) {
  const cur = attempt.current!;
  const [session, setSession] = useState<EOSession | null>(null);
  useEffect(() => { void eoApi.get(cur.eo_session_id!).then(setSession); }, [cur.eo_session_id]);
  useEffect(() => { if (session?.status === "ended") onDone(); }, [session?.status, onDone]);
  if (!session || session.status === "ended") return <Loading />;
  return <Conversation task={cur.eo_task!} guide={{ title: "", tips: [], phrases: [] }} session={session} onUpdate={setSession} />;
}

function Results({ attempt }: { attempt: ExamAttempt }) {
  const r = attempt.results!;
  return (
    <>
      <Panel>
        <h1 className="text-2xl font-bold">Results</h1>
        <p className="mt-1 text-sm text-ink-soft">{r.label} These are practice results, not an official TCF score.</p>
        <ul className="mt-4 divide-y divide-line">
          {r.sections.map((s) => (
            <li key={s.section} className="flex flex-wrap items-center justify-between gap-2 py-2">
              <span className="font-semibold">{SECTION_NAME[s.section]}</span>
              <span className="text-sm">
                {s.total !== undefined ? `${s.correct}/${s.total} correct${s.unanswered ? ` · ${s.unanswered} unanswered` : ""}` : "AI feedback below"}
                {" · "}{fmt(s.time_used_s)} / {fmt(s.limit_s)}{s.timed_out ? " · time ran out" : ""}
              </span>
            </li>
          ))}
        </ul>
      </Panel>
      {attempt.report && <ReportView report={attempt.report} />}
      {r.sections.map((s) => <SectionReview key={s.section} s={s} />)}
    </>
  );
}

const SKILL_EN: Record<string, string> = { listening: "Listening", reading: "Reading", writing: "Writing", speaking: "Speaking" };

function ReportView({ report }: { report: ExamReport }) {
  return (
    <Panel>
      <h2 className="text-xl font-bold">{report.kind === "diagnostic" ? "Your level check" : "What this trial shows"}</h2>
      <p className="text-sm text-ink-soft">{report.label} Your goal: {report.goal.cefr}{report.goal.nclc ? ` · NCLC ${report.goal.nclc} target (shown separately, never converted)` : ""}.</p>
      {!report.complete && <p className="mt-2 text-sm font-semibold">Writing or speaking feedback is still being prepared; this report will update.</p>}
      <table className="mt-3 w-full text-sm">
        <thead><tr className="text-left text-ink-faint"><th className="py-1">Skill</th><th>This assessment</th><th>Estimate (CEFR)</th></tr></thead>
        <tbody>{report.skills.map((s) => (
          <tr key={s.skill} className="border-t border-line">
            <td className="py-1.5 font-semibold">{SKILL_EN[s.skill]}</td>
            <td>{s.total !== undefined ? `${s.correct}/${s.total}${s.adaptive_final_level ? ` · settled at ${s.adaptive_final_level}` : ""}`
              : s.ai?.status === "done" ? `≈ ${s.ai.cefr_estimate} (AI, ${s.ai.mean}/5)` : s.ai?.status === "pending" ? "being scored…" : "—"}</td>
            <td>{s.estimate?.cefr_low ? `${s.estimate.cefr_low}–${s.estimate.cefr_high} · ${s.estimate.confidence}` : "not measured"}</td>
          </tr>))}</tbody>
      </table>
      {report.strengths.length > 0 && (<><p className="mt-4 font-bold">Strengths</p><ul className="list-disc pl-5 text-sm">{report.strengths.map((s) => <li key={s}>{s}</li>)}</ul></>)}
      {Object.keys(report.error_categories).length > 0 && (<><p className="mt-4 font-bold">Error types found</p>
        <ul className="list-disc pl-5 text-sm">{Object.entries(report.error_categories).map(([k, v]) => <li key={k}><span className="font-semibold">{k}</span>: {v.join(", ")}</li>)}</ul></>)}
      {report.root_causes && report.root_causes.length > 0 && (<><p className="mt-4 font-bold">Possible causes</p>
        <ul className="list-disc pl-5 text-sm">{report.root_causes.map((c) => <li key={c.competency}><span className="font-semibold">{c.competency}</span>: {c.cause} ({c.evidence})</li>)}</ul></>)}
      {report.timing && report.timing.length > 0 && (<><p className="mt-4 font-bold">Timing</p>
        <ul className="list-disc pl-5 text-sm">{report.timing.map((t) => <li key={t.section}>{t.note}</li>)}</ul></>)}
      <p className="mt-4 font-bold">Priorities</p>
      <ul className="list-disc pl-5 text-sm">{report.priorities.map((p) => <li key={p.reason}>{p.reason}</li>)}</ul>
      {report.focus && report.focus.length > 0 && (<><p className="mt-4 font-bold">Next week's plan will focus on</p>
        <ul className="list-disc pl-5 text-sm">{report.focus.map((f) => <li key={f.skill}>{SKILL_EN[f.skill] ?? f.skill}: {f.reason}</li>)}</ul></>)}
      {report.retests && report.retests.length > 0 && <p className="mt-2 text-sm">Retests scheduled on new questions: {report.retests.join(", ")}.</p>}
      <p className="mt-4 font-bold">Next</p>
      <ol className="list-decimal pl-5 text-sm">{report.next.steps.map((s) => <li key={s.title}>{s.title} (≈ {s.minutes} min): {s.reason}</li>)}</ol>
      <details className="mt-4 text-sm"><summary className="cursor-pointer font-semibold text-ink-soft">What this can't tell you</summary>
        <ul className="mt-1 list-disc pl-5">{report.limits.map((l) => <li key={l}>{l}</li>)}</ul></details>
    </Panel>
  );
}

function SectionReview({ s }: { s: SectionResult }) {
  if (s.review) {
    return (
      <details className="rounded-[16px] border border-line bg-surface p-4">
        <summary className="cursor-pointer font-bold">{SECTION_NAME[s.section]}: review each question</summary>
        <ol className="mt-3 space-y-4">
          {s.review.map((q, i) => (
            <li key={q.item_id} className="text-sm">
              <p className="flex items-start gap-2 font-semibold">
                {q.correct ? <Check aria-hidden className="mt-0.5 size-4 shrink-0 text-success" /> : <X aria-hidden className="mt-0.5 size-4 shrink-0 text-danger" />}
                {i + 1}. {q.question} <span className="font-normal text-ink-faint">({q.level})</span>
              </p>
              {q.transcript && <p className="mt-1 rounded-[10px] bg-surface-2 p-2 text-ink-soft">Transcript: {q.transcript}</p>}
              <ul className="mt-1 space-y-0.5">
                {q.options.map((o) => (
                  <li key={o.id} className={cx(o.id === q.answer && "font-semibold text-success", o.id === q.response && o.id !== q.answer && "text-danger")}>
                    {o.id.toUpperCase()}. {o.text} <span className="font-normal text-ink-faint">— {o.explanation}</span>
                  </li>
                ))}
              </ul>
              {!q.answered && <p className="text-ink-faint">Not answered.</p>}
            </li>
          ))}
        </ol>
      </details>
    );
  }
  if (s.writing_submission_ids && s.writing_submission_ids.length > 1)
    return <>{s.writing_submission_ids.map((id) => <AIResult key={id} kind="writing" id={id} />)}</>;
  if (s.writing_submission_id) return <AIResult kind="writing" id={s.writing_submission_id} />;
  if (s.eo_session_id) return <AIResult kind="speaking" id={s.eo_session_id} />;
  return null;
}

function AIResult({ kind, id }: { kind: "writing" | "speaking"; id: number }) {
  const [data, setData] = useState<Submission | EOSession | null>(null);
  useEffect(() => {
    let alive = true;
    const load = async () => {
      const d = kind === "writing" ? await writingApi.get(id) : await eoApi.get(id);
      if (alive) setData(d);
      if (alive && d.feedback_status === "pending") setTimeout(load, 3000);
    };
    void load();
    return () => { alive = false; };
  }, [kind, id]);
  if (!data) return <Loading />;
  const title = kind === "writing" ? "Expression écrite" : "Expression orale";
  return (
    <section aria-label={title} className="space-y-3">
      <h2 className="text-xl font-bold">{title}</h2>
      {data.feedback_status === "pending" && <Loading label="The local AI is reviewing it…" />}
      {data.feedback_status === "none" && <p className="text-sm text-ink-soft">Nothing was produced in this section.</p>}
      {data.feedback_status === "failed" && <p className="text-sm text-ink-soft">Feedback couldn't be produced (is Ollama running?). Open the task again from the writing or speaking pages to retry.</p>}
      {data.feedback && (kind === "writing"
        ? <FeedbackView fb={(data as Submission).feedback!} />
        : <EOFeedbackView fb={(data as EOSession).feedback!} />)}
    </section>
  );
}

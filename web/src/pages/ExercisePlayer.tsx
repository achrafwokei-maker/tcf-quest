import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { Headphones, HeadphoneOff, RotateCcw, Sparkles, X } from "lucide-react";
import {
  exercisesApi, OutOfSyncError, tcfLabel,
  type Feedback, type Item, type SessionState, type SetPayload,
} from "../lib/exercises";
import { playAudio, speechAvailable, stopSpeaking } from "../lib/speak";
import { ArrangeView, CardView, ChoiceView, MAX_PLAYS, MultiView, TypeView } from "../components/exercise/ItemViews";
import { MissionReportView } from "../components/exercise/MissionReport";
import { FeedbackSheet } from "../components/exercise/FeedbackSheet";
import { Badge, Button, ErrorNote, Loading, Meter } from "../components/ui";

type Answer = string | string[] | null;
const AUDIO_OFF_KEY = "tcfq.audioOffUntil";

/** "Can't listen now": replaces audio with transcripts for 15 minutes (blueprint E.1). */
function useAudioOff(): [boolean, (on: boolean) => void] {
  const read = () => {
    try { return Number(localStorage.getItem(AUDIO_OFF_KEY) ?? 0) > Date.now(); } catch { return false; }
  };
  const [on, setOn] = useState(read);
  const set = (v: boolean) => {
    try { localStorage.setItem(AUDIO_OFF_KEY, v ? String(Date.now() + 15 * 60_000) : "0"); } catch { /* private mode */ }
    setOn(v);
  };
  return [on, set];
}

/** Full-screen exercise player: one item at a time, Vérifier → feedback → Continuer. */
export function ExercisePlayer() {
  const { setId = "" } = useParams();
  const [data, setData] = useState<SetPayload | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const load = useCallback(() => {
    setError(null);
    exercisesApi.load(setId).then(setData, setError);
  }, [setId]);
  useEffect(load, [load]);

  if (error) return <div className="mx-auto max-w-xl p-6"><ErrorNote error={error} onRetry={load} /></div>;
  if (!data) return <div className="mx-auto max-w-xl px-6"><Loading /></div>;
  return <Player key={setId} payload={data} />;
}

/**
 * The player. Standalone it lives at /set/:id; embedded (onboarding challenge) it reports
 * completion through `onDone` and replaces "close" with "skip the rest".
 */
export function Player({ payload, onDone }: { payload: SetPayload; onDone?: (state: SessionState) => void }) {
  const reduce = useReducedMotion();
  const navigate = useNavigate();
  const { set } = payload;
  const [state, setState] = useState<SessionState>(payload.state);
  const [answer, setAnswer] = useState<Answer>(null);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [plays, setPlays] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [hintsUsed, setHintsUsed] = useState(0);
  const [hint, setHint] = useState<string | null>(null);
  const [audioOff, setAudioOff] = useAudioOff();
  const shownAt = useRef(Date.now());

  const item: Item | null = state.current_item_id ? set.items[state.current_item_id] : null;
  const shown: Item | null = feedback ? set.items[feedback.state.results.at(-1)!.item_id] : item;
  const noSpeech = !speechAvailable();
  const listeningOff = audioOff || noSpeech;

  // Reset per-item state whenever a new item is presented.
  useEffect(() => {
    setAnswer(null); setPlays(0); setHintsUsed(0); setHint(null); setError(null);
    shownAt.current = Date.now();
    return () => stopSpeaking();
  }, [item?.id, state.index]);

  const hasAnswer = Array.isArray(answer) ? answer.length > 0 : typeof answer === "string" && answer.trim() !== "";

  const submit = useCallback(async (skipped = false) => {
    if (!item || feedback || checking || (!skipped && !hasAnswer)) return;
    stopSpeaking();
    setChecking(true);
    setError(null);
    try {
      const fb = await exercisesApi.answer(set.id, {
        item_id: item.id, response: skipped ? null : answer,
        duration_ms: Date.now() - shownAt.current, hints_used: hintsUsed,
        plays: Math.max(plays, 1), audio_off: item.type === "listen" && listeningOff, skipped,
      });
      setFeedback(fb);
    } catch (e) {
      if (e instanceof OutOfSyncError) { setState(e.state); return; } // another tab moved on: resync
      setError((e as Error).message);
    } finally {
      setChecking(false);
    }
  }, [item, feedback, checking, hasAnswer, set.id, answer, hintsUsed, plays, listeningOff]);

  const next = useCallback(() => {
    if (!feedback) return;
    setState(feedback.state);
    setFeedback(null);
  }, [feedback]);

  /** Cards are read, not answered: mark seen and move on. */
  const readCard = useCallback(async () => {
    if (!item || item.type !== "card" || checking) return;
    stopSpeaking();
    setChecking(true);
    try {
      const r = await exercisesApi.seen(set.id, item.id);
      setState(r.state);
    } catch (e) {
      if (e instanceof OutOfSyncError) setState(e.state);
      else setError((e as Error).message);
    } finally {
      setChecking(false);
    }
  }, [item, checking, set.id]);

  // Enter = check (or read a card), then continue.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Enter" || e.target instanceof HTMLTextAreaElement) return;
      e.preventDefault();
      if (feedback) next();
      else if (item?.type === "card") void readCard();
      else void submit();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [feedback, next, submit, readCard, item]);

  async function play(slow: boolean) {
    if (!item || item.type !== "listen" || !item.audio || plays >= MAX_PLAYS) return;
    if (slow) setHintsUsed((h) => Math.max(h, 1)); // slower audio counts as a hint
    setPlaying(true);
    const r = await playAudio(item.audio, slow ? 0.8 : undefined);
    setPlaying(false);
    setPlays((p) => p + 1);
    if (r === "failed") setAudioOff(true); // fall back to the transcript, tagged as audio-off
  }

  async function askHint() {
    if (!item) return;
    const r = await exercisesApi.hint(set.id, item.id).catch(() => null);
    setHint(r?.hint ?? null);
    setHintsUsed(1);
  }

  async function restart() {
    const r = await exercisesApi.restart(set.id);
    setFeedback(null);
    setState(r.state);
  }

  /* ---------- completed ---------- */
  if (state.status === "completed" && !feedback && (set.context === "mission" || set.context === "review")) {
    return <MissionReportView setId={set.id} isReview={set.context === "review"} summary={state.summary}
      onContinue={() => navigate("/")} onAgain={set.context === "mission" ? restart : undefined} />;
  }

  if (state.status === "completed" && !feedback) {
    const { items, correct_first_try } = state.summary;
    return (
      <div className="mx-auto flex min-h-dvh max-w-xl flex-col items-center justify-center gap-6 px-6 text-center">
        <motion.div initial={reduce ? false : { scale: 0.6, rotate: -10, opacity: 0 }} animate={{ scale: 1, rotate: 0, opacity: 1 }}
          transition={{ type: "spring", stiffness: 260, damping: 16 }}
          className="tile grid size-28 place-items-center rounded-[34px] [--tile:var(--gold)]">
          <Sparkles aria-hidden className="size-14" />
        </motion.div>
        <h1 className="title-poster text-6xl">Terminé !</h1>
        <p className="text-xl font-bold text-ink-soft">{correct_first_try} sur {items} du premier coup.</p>
        <p className="text-ink-faint">Your answers are saved.</p>
        <div className="flex flex-wrap justify-center gap-3">
          {!onDone && <Button variant="secondary" onClick={restart}><RotateCcw aria-hidden className="size-4" /> Practise again</Button>}
          <Button onClick={() => (onDone ? onDone(state) : navigate("/entrainement"))}>Continuer</Button>
        </div>
      </div>
    );
  }

  if (!shown) return <div className="mx-auto max-w-xl px-6"><Loading /></div>;
  const locked = !!feedback;

  return (
    <div className={onDone ? "flex min-h-[80dvh] flex-col" : "flex min-h-dvh flex-col"}>
      {/* Header: close, progress, listening toggle */}
      <header className="mx-auto flex w-full max-w-3xl items-center gap-3 px-5 pt-5 sm:px-8">
        {onDone ? (
          <button type="button" onClick={() => onDone(state)} aria-label="Skip the rest of the challenge"
            className="rounded-full px-3 py-2 text-sm font-extrabold text-ink-faint hover:bg-surface-2 hover:text-ink">
            Skip
          </button>
        ) : (
          <Link to={set.context === "practice" ? "/entrainement" : "/"} aria-label="Close" className="grid size-10 place-items-center rounded-full text-ink-faint hover:bg-surface-2 hover:text-ink">
            <X aria-hidden className="size-6" />
          </Link>
        )}
        <div className="flex-1">
          <Meter value={state.index + (feedback ? 1 : 0)} max={state.total} label="Progress" />
        </div>
        <button type="button" onClick={() => setAudioOff(!audioOff)} disabled={noSpeech}
          aria-pressed={listeningOff}
          title={listeningOff ? "Listening off for 15 min (transcripts shown)" : "Can't listen now? Show transcripts instead"}
          className="grid size-10 place-items-center rounded-full text-ink-faint hover:bg-surface-2 hover:text-ink aria-pressed:text-warning">
          {listeningOff ? <HeadphoneOff aria-hidden className="size-5" /> : <Headphones aria-hidden className="size-5" />}
        </button>
      </header>

      <main className="mx-auto w-full max-w-3xl flex-1 px-5 py-6 sm:px-8">
        <AnimatePresence mode="wait" initial={false}>
          <motion.div key={`${shown.id}-${state.index}`}
            initial={reduce ? false : { opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }}
            exit={reduce ? undefined : { opacity: 0, x: -24 }} transition={{ duration: 0.22 }}>
            <div className="mb-4 flex flex-wrap items-center gap-2">
              {set.mission && shown.stage && (
                <Badge tone="success">{shown.stage} · {set.mission.stage_titles[shown.stage] ?? ""}</Badge>
              )}
              <Badge tone="accent">Prépare : {tcfLabel(shown.tcf_target)}</Badge>
              <Badge>{shown.level}</Badge>
            </div>
            {shown.type !== "card" && <p className="eyebrow mb-1">{shown.instructions}</p>}
            {shown.type !== "card" && shown.instructions_en && <p className="mb-5 text-sm font-semibold text-ink-faint">{shown.instructions_en}</p>}

            {shown.type === "card" && <CardView item={shown} />}
            {shown.type === "multi" && (
              <MultiView item={shown} value={Array.isArray(answer) ? answer : []} onChange={setAnswer} locked={locked}
                missed={(feedback?.details as { missed?: string[] } | undefined)?.missed}
                extra={(feedback?.details as { extra?: string[] } | undefined)?.extra} />
            )}
            {(shown.type === "select" || shown.type === "listen") && (
              <ChoiceView item={shown} value={typeof answer === "string" ? answer : null} onChange={setAnswer}
                locked={locked} audioOff={listeningOff} plays={plays} playing={playing} onPlay={play} />
            )}
            {shown.type === "arrange" && (
              <ArrangeView item={shown} onChange={setAnswer} locked={locked} wrongPositions={feedback?.details.wrong_positions} />
            )}
            {shown.type === "type" && (
              <TypeView item={shown} value={typeof answer === "string" ? answer : ""} onChange={setAnswer}
                locked={locked} hint={hint} onHint={askHint} />
            )}
          </motion.div>
        </AnimatePresence>
        {shown.type !== "card" && shown.type !== "type" && shown.has_hint && !locked && (
          hint ? (
            <p role="status" className="mt-4 rounded-[16px] bg-gold/15 px-4 py-3 font-semibold">{hint}</p>
          ) : (
            <button type="button" onClick={askHint} className="mt-4 text-sm font-extrabold text-ink-faint hover:text-ink">Show a hint</button>
          )
        )}
        {shown.type !== "card" && shown.time_limit_s && !locked && (
          <ItemCountdown key={shown.id} seconds={shown.time_limit_s} onZero={() => void submit(true)} />
        )}
        {error && <p role="alert" className="mt-4 font-bold text-danger">{error}</p>}
      </main>

      {/* Footer: check / feedback */}
      <footer className="sticky bottom-0">
        {feedback ? (
          <FeedbackSheet fb={feedback} setId={set.id} itemId={shown.id} onContinue={next} />
        ) : shown.type === "card" ? (
          <div className="border-t border-line bg-bg/90 px-5 py-4 backdrop-blur sm:px-8">
            <div className="mx-auto flex max-w-3xl justify-end">
              <Button onClick={readCard} busy={checking} className="min-w-40">Continuer</Button>
            </div>
          </div>
        ) : (
          <div className="border-t border-line bg-bg/90 px-5 py-4 backdrop-blur sm:px-8">
            <div className="mx-auto flex max-w-3xl items-center justify-between gap-3">
              <Button variant="quiet" onClick={() => submit(true)} disabled={checking}>Skip</Button>
              <Button onClick={() => submit()} disabled={!hasAnswer} busy={checking} className="min-w-40">Vérifier</Button>
            </div>
          </div>
        )}
      </footer>
    </div>
  );
}


/** Timed challenge (training): a visible countdown; at zero the question is skipped. */
function ItemCountdown({ seconds, onZero }: { seconds: number; onZero: () => void }) {
  const [left, setLeft] = useState(seconds);
  useEffect(() => {
    if (left <= 0) { onZero(); return; }
    const t = setTimeout(() => setLeft((l) => l - 1), 1000);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [left]);
  return (
    <p className={`mt-4 text-sm font-extrabold ${left <= 10 ? "text-danger" : "text-ink-soft"}`} aria-live="off">
      Timed challenge: {left}s
    </p>
  );
}

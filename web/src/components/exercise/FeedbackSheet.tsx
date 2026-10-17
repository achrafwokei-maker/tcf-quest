import { useEffect, useRef, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { BookOpenCheck, Check, CircleQuestionMark, Ellipsis, RotateCcw, Scale, ThumbsDown, ThumbsUp, Wrench } from "lucide-react";
import { exercisesApi, type Feedback, type FlagKind } from "../../lib/exercises";
import { VERDICTS } from "../../lib/verdicts";
import { Button, cx } from "../ui";
import { WhyPanel } from "./WhyPanel";
import { SpeechBubble } from "./ItemViews";

const NOTEBOOK_NOTE = {
  opened: "Added to your notebook: it comes back as a review tomorrow.",
  reopened: "Back in your notebook for another review tomorrow.",
  progress: "Review done: next one in a few days.",
  mastered: "Mastered: it leaves your review list.",
} as const;

const REPORTS: { kind: FlagKind; label: string; icon: typeof ThumbsUp; done: string; needsNote?: boolean; onlyWrong?: boolean }[] = [
  { kind: "too_easy", label: "Too easy", icon: ThumbsUp, done: "Noted for your plan." },
  { kind: "too_hard", label: "Too hard", icon: ThumbsDown, done: "Noted for your plan." },
  { kind: "unclear", label: "I didn't understand the explanation", icon: BookOpenCheck, done: "Thanks. Explanations reported twice get rewritten." },
  { kind: "dispute", label: "My answer should be accepted", icon: Scale, needsNote: true, onlyWrong: true,
    done: "Sent for review. This answer won't count until it's checked." },
  { kind: "technical", label: "There was a technical problem", icon: Wrench, needsNote: true,
    done: "Thanks. This answer won't count against you." },
];

/** The verdict sheet (blueprint E.1 + feedback system). Colour + icon + words, never colour alone. */
export function FeedbackSheet({ fb, setId, itemId, onContinue }: {
  fb: Feedback; setId: string; itemId: string; onContinue: () => void;
}) {
  const reduce = useReducedMotion();
  const look = VERDICTS[fb.verdict];
  const Icon = look.icon;
  const button = useRef<HTMLButtonElement>(null);
  const [menu, setMenu] = useState(false);
  const [why, setWhy] = useState(false);
  const [sent, setSent] = useState<Partial<Record<FlagKind, string>>>({});
  const [pending, setPending] = useState<FlagKind | null>(null);
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const wrong = fb.verdict === "incorrect" || fb.verdict === "partial";
  const rightWhy = fb.correct_explanation ?? fb.explanation;

  useEffect(() => button.current?.focus(), []);

  async function send(kind: FlagKind, withNote = "") {
    setError(null);
    try {
      await exercisesApi.flag(fb.attempt_id, kind, withNote);
      setSent((s) => ({ ...s, [kind]: REPORTS.find((r) => r.kind === kind)!.done }));
      setPending(null);
      setNote("");
    } catch (e) {
      setError((e as Error).message);
    }
  }

  const lastSent = Object.values(sent).at(-1);

  return (
    <>
      <motion.section
        role="status"
        aria-live="polite"
        initial={reduce ? false : { y: 40, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ type: "spring", stiffness: 380, damping: 30 }}
        className="rounded-t-[30px] border-t border-line px-5 pb-[max(1.25rem,env(safe-area-inset-bottom))] pt-5 shadow-[0_-12px_30px_-12px_rgb(0_0_0/0.35)] sm:px-8"
        style={{ background: `color-mix(in srgb, ${look.tone} 14%, var(--surface))` }}
      >
        <div className="mx-auto max-w-3xl">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
            <div className="min-w-0 flex-1 space-y-2">
              <p className="flex items-center gap-2 text-2xl font-extrabold" style={{ color: look.tone }}>
                <span className="grid size-9 place-items-center rounded-full text-white" style={{ background: look.tone }}>
                  <Icon aria-hidden className="size-5" strokeWidth={3} />
                </span>
                {look.title}
              </p>
              {look.lead && <p className="font-semibold">{look.lead}</p>}
              {fb.note && <p className="font-semibold">{fb.note}</p>}
              {fb.verdict !== "correct" && (
                <p className="font-semibold">
                  <span className="text-ink-soft">Correct answer: </span>
                  <span className="font-extrabold">{fb.correct_answer}</span>
                </p>
              )}
              {wrong && fb.chosen_explanation && <p className="text-ink-soft">Your choice: {fb.chosen_explanation}</p>}
              {rightWhy && <p className="text-ink-soft">{rightWhy}</p>}
              {fb.notebook && (
                <p className="text-sm font-bold text-ink-soft">{NOTEBOOK_NOTE[fb.notebook]}</p>
              )}
              {fb.will_retry && (
                <p className="flex items-center gap-1.5 text-sm font-bold text-ink-soft">
                  <RotateCcw aria-hidden className="size-4" /> This one comes back at the end.
                </p>
              )}
              {lastSent && (
                <p role="status" className="flex items-center gap-1.5 text-sm font-bold text-success">
                  <Check aria-hidden className="size-4" /> {lastSent}
                </p>
              )}
            </div>

            <div className="flex items-center gap-2">
              <button type="button" onClick={() => setWhy(true)}
                className="flex min-h-12 items-center gap-1.5 rounded-full px-4 font-extrabold text-ink-soft hover:bg-black/5 hover:text-ink">
                <CircleQuestionMark aria-hidden className="size-5" /> Why?
              </button>
              <button type="button" onClick={() => setMenu((m) => !m)} aria-expanded={menu} aria-label="Give feedback on this exercise"
                className="grid size-12 place-items-center rounded-full text-ink-soft hover:bg-black/5 hover:text-ink">
                <Ellipsis aria-hidden className="size-5" />
              </button>
              <Button ref={button} onClick={onContinue} className="flex-1 sm:flex-none" style={{ ["--tile" as string]: look.button }}>
                Continuer
              </Button>
            </div>
          </div>

          {fb.reply && <div className="mt-4"><SpeechBubble line={fb.reply} autoPlay /></div>}

          {menu && (
            <div className="card mt-4 p-2" role="menu" aria-label="Feedback on this exercise">
              {REPORTS.filter((r) => !r.onlyWrong || wrong).map((r) => {
                const done = r.kind in sent;
                const RIcon = r.icon;
                return (
                  <div key={r.kind}>
                    <button type="button" role="menuitem" disabled={done}
                      onClick={() => (r.needsNote ? setPending(pending === r.kind ? null : r.kind) : send(r.kind))}
                      className={cx("flex w-full items-center gap-3 rounded-[14px] px-3 py-2.5 text-left font-bold hover:bg-surface-2",
                        done && "text-success")}>
                      {done ? <Check aria-hidden className="size-5" /> : <RIcon aria-hidden className="size-5 text-ink-faint" />}
                      {r.label}
                    </button>
                    {pending === r.kind && (
                      <form className="flex flex-col gap-2 px-3 pb-3 sm:flex-row"
                        onSubmit={(e) => { e.preventDefault(); e.stopPropagation(); void send(r.kind, note); }}>
                        <input autoFocus value={note} onChange={(e) => setNote(e.target.value)} maxLength={500}
                          onKeyDown={(e) => e.stopPropagation()}
                          placeholder={r.kind === "dispute" ? "Why should it be accepted? (optional)" : "What happened? (optional)"}
                          aria-label={r.kind === "dispute" ? "Why your answer should be accepted" : "What happened"}
                          className="flex-1 rounded-[14px] border-2 border-line bg-surface-2 px-3 py-2 outline-none focus:border-violet" />
                        <Button type="submit" variant="secondary">Send</Button>
                      </form>
                    )}
                  </div>
                );
              })}
              {error && <p role="alert" className="px-3 pb-2 text-sm font-bold text-danger">{error}</p>}
            </div>
          )}
        </div>
      </motion.section>

      {why && <WhyPanel setId={setId} itemId={itemId} onClose={() => setWhy(false)} />}
    </>
  );
}

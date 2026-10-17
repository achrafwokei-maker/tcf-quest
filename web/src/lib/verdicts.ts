import { Check, CircleAlert, CircleQuestionMark, Lightbulb, MessageCircleQuestionMark, SkipForward, Target, X, type LucideIcon } from "lucide-react";
import type { Verdict } from "./exercises";

/**
 * How each verdict looks and reads (blueprint "Feedback system").
 * Tone rules: no shaming, no "wrong!", start with what worked when something did,
 * and always pair colour with an icon and words.
 */
export const VERDICTS: Record<Verdict, { title: string; lead?: string; icon: LucideIcon; tone: string; button: string }> = {
  correct: { title: "Bien joué !", icon: Check, tone: "var(--success)", button: "var(--green)" },
  unnatural: { title: "Correct !", lead: "It works. A native speaker might say it differently:", icon: Lightbulb, tone: "var(--success)", button: "var(--green)" },
  understood: { title: "Compris !", lead: "Your meaning gets through. Let's fix the form:", icon: CircleAlert, tone: "var(--warning)", button: "var(--orange)" },
  partial: { title: "Presque !", icon: CircleAlert, tone: "var(--warning)", button: "var(--orange)" },
  incomplete: { title: "Bon début !", lead: "Something the task asks for is still missing:", icon: Target, tone: "var(--warning)", button: "var(--orange)" },
  off_task: { title: "Belle phrase…", lead: "…but it doesn't answer the question that was asked:", icon: MessageCircleQuestionMark, tone: "var(--warning)", button: "var(--orange)" },
  incorrect: { title: "Pas tout à fait.", icon: X, tone: "var(--danger)", button: "var(--violet)" },
  uncertain: { title: "Je n'ai pas bien entendu.", lead: "Nothing is counted against you. Want to try again?", icon: CircleQuestionMark, tone: "var(--ink-faint)", button: "var(--violet)" },
  skipped: { title: "Passé.", icon: SkipForward, tone: "var(--ink-faint)", button: "var(--violet)" },
  seen: { title: "Lu.", icon: Check, tone: "var(--ink-faint)", button: "var(--violet)" },
};

/** Words that must never appear in verdict copy (checked by a test). */
export const BANNED_WORDS = ["wrong", "faux", "nul", "bad", "fail", "stupid", "erreur !"];

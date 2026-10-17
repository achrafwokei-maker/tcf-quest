import { useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { BookOpen, Check, Headphones, Mic, PenLine, X } from "lucide-react";
import { Button, IconTile, cx } from "../ui";

/**
 * The interactive exam briefing (Part II R2). Facts verified against FEI on 2026-10-16
 * (docs/TCF_SPECIFICATION.md). The quiz checks format knowledge only, never French level.
 */
export function Briefing({ lang, onDone, onSkip }: {
  lang: "en" | "fr"; onDone: (quiz: Record<string, string>) => void; onSkip: () => void;
}) {
  const reduce = useReducedMotion();
  const [card, setCard] = useState(0);
  const [quiz, setQuiz] = useState<Record<string, string>>({});
  const en = lang === "en";
  const quizDone = !!quiz.q1 && !!quiz.q2;
  const last = 4;

  return (
    <div className="mt-6">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex gap-1.5" aria-label={`Card ${card + 1} of ${last + 1}`}>
          {Array.from({ length: last + 1 }).map((_, i) => (
            <span key={i} className={cx("h-2 rounded-full transition-all", i === card ? "w-6 bg-violet" : i < card ? "w-2 bg-violet/60" : "w-2 bg-line")} />
          ))}
        </div>
        <button type="button" onClick={onSkip} className="text-sm font-extrabold text-ink-faint hover:text-ink">
          {en ? "Skip the briefing" : "Passer la présentation"}
        </button>
      </div>

      <AnimatePresence mode="wait" initial={false}>
        <motion.div key={card} className="card p-5 sm:p-6"
          initial={reduce ? false : { opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }}
          exit={reduce ? undefined : { opacity: 0, x: -24 }} transition={{ duration: 0.2 }}>
          {card === 0 && <WhatIs en={en} />}
          {card === 1 && <FiveThings en={en} />}
          {card === 2 && <Sections en={en} />}
          {card === 3 && <Quiz en={en} quiz={quiz} setQuiz={setQuiz} />}
          {card === 4 && <Route en={en} />}
        </motion.div>
      </AnimatePresence>

      <div className="mt-4 flex justify-between gap-3">
        <Button variant="quiet" onClick={() => setCard((c) => Math.max(0, c - 1))} disabled={card === 0}>
          {en ? "Back" : "Retour"}
        </Button>
        {card < last ? (
          <Button onClick={() => setCard((c) => c + 1)} disabled={card === 3 && !quizDone}>{en ? "Next" : "Suivant"}</Button>
        ) : (
          <Button onClick={() => onDone(quiz)}>{en ? "Let's go" : "C'est parti"}</Button>
        )}
      </div>
    </div>
  );
}

function WhatIs({ en }: { en: boolean }) {
  return (
    <>
      <h2 className="title-poster text-3xl">Le TCF Canada</h2>
      <p className="mt-3 text-lg font-semibold">
        {en
          ? "A French test from France Éducation international, used for Canadian economic immigration and citizenship applications with IRCC. You get a separate result for each of four skills."
          : "Un test de français de France Éducation international, utilisé pour l'immigration économique et la citoyenneté canadienne auprès d'IRCC. Tu obtiens un résultat séparé pour chacune des quatre compétences."}
      </p>
      <p className="mt-4 rounded-[16px] bg-surface-2 p-3 text-sm font-bold text-ink-soft">
        {en
          ? "TCF Quest is not an official test centre. Its results are practice estimates, never official scores."
          : "TCF Quest n'est pas un centre d'examen officiel. Ses résultats sont des estimations d'entraînement, jamais des scores officiels."}
      </p>
    </>
  );
}

const FIVE = [
  { fr: "Le TCF Canada officiel", en: "The official TCF Canada", dfr: "Seul un centre agréé peut te le faire passer.", den: "Only an approved test centre can give it." },
  { fr: "Les niveaux CECR (A1–C2)", en: "CEFR levels (A1–C2)", dfr: "Une échelle générale du niveau de français.", den: "A general scale of French ability." },
  { fr: "Les niveaux NCLC", en: "NCLC levels", dfr: "L'échelle du Canada ; les résultats du TCF y sont convertis.", den: "Canada's scale; TCF results convert to it." },
  { fr: "Ton objectif personnel", en: "Your personal target", dfr: "Ce que tu vises, compétence par compétence.", den: "What you aim for, skill by skill." },
  { fr: "Les résultats de TCF Quest", en: "TCF Quest results", dfr: "Des estimations non officielles pour guider l'entraînement.", den: "Unofficial estimates that guide your training." },
];

function FiveThings({ en }: { en: boolean }) {
  const [open, setOpen] = useState<number[]>([]);
  return (
    <>
      <h2 className="title-poster text-3xl">{en ? "Five things not to mix up" : "Cinq choses à ne pas confondre"}</h2>
      <p className="mt-1 text-sm font-semibold text-ink-faint">{en ? "Tap each one." : "Touche chacune."}</p>
      <ul className="mt-4 grid gap-2">
        {FIVE.map((f, i) => {
          const on = open.includes(i);
          return (
            <li key={f.fr}>
              <button type="button" aria-expanded={on} onClick={() => setOpen((o) => (on ? o.filter((x) => x !== i) : [...o, i]))}
                className={cx("w-full rounded-[16px] border-2 px-4 py-3 text-left transition-colors", on ? "border-violet bg-violet/8" : "border-line hover:border-ink-faint")}>
                <span className="font-extrabold">{i + 1}. {f.fr}</span>
                {en && <span className="ml-2 text-sm font-semibold text-ink-faint">{f.en}</span>}
                {on && <span className="mt-1 block font-semibold text-ink-soft">{en ? f.den : f.dfr}</span>}
              </button>
            </li>
          );
        })}
      </ul>
    </>
  );
}

const SECTIONS = [
  { icon: Headphones, color: "var(--cyan)", fr: "Compréhension orale", fmt: "39 QCM · 35 min",
    en: "Listen to recordings, each played only once, and answer questions.", frd: "Tu écoutes des enregistrements, diffusés une seule fois, et tu réponds aux questions." },
  { icon: BookOpen, color: "var(--green)", fr: "Compréhension écrite", fmt: "39 QCM · 60 min",
    en: "Read texts: meaning, details, intentions, implied information.", frd: "Tu lis des textes : sens, détails, intentions, implicite." },
  { icon: PenLine, color: "var(--gold)", fr: "Expression écrite", fmt: "3 tâches · 60 min",
    en: "A message (60–120 words), an account with comments (120–150), a comparison of two viewpoints (120–180). Missing a word range can sink the whole paper.",
    frd: "Un message (60–120 mots), un compte rendu commenté (120–150), une comparaison de deux points de vue (120–180). Ne pas respecter le nombre de mots peut tout faire échouer." },
  { icon: Mic, color: "var(--pink)", fr: "Expression orale", fmt: "3 tâches · 12 min",
    en: "Face to face with an examiner: an interview (2 min), asking questions to get information (5 min 30, incl. 2 min to prepare), defending a viewpoint (4 min 30).",
    frd: "Face à un examinateur : un entretien (2 min), une interaction où tu poses des questions (5 min 30, dont 2 min de préparation), un point de vue à défendre (4 min 30)." },
];

function Sections({ en }: { en: boolean }) {
  return (
    <>
      <h2 className="title-poster text-3xl">{en ? "Four compulsory sections" : "Quatre épreuves obligatoires"}</h2>
      <ul className="mt-4 grid gap-3">
        {SECTIONS.map((s) => (
          <li key={s.fr} className="flex gap-3">
            <IconTile icon={s.icon} color={s.color} size="sm" />
            <div>
              <p className="font-extrabold">{s.fr} <span className="font-bold text-ink-faint">· {s.fmt}</span></p>
              <p className="text-sm font-semibold text-ink-soft">{en ? s.en : s.frd}</p>
            </div>
          </li>
        ))}
      </ul>
      <p className="mt-4 text-lg font-extrabold">{en ? "Total: 2 h 47." : "Total : 2 h 47."}</p>
    </>
  );
}

const QUESTIONS = [
  { id: "q1", fr: "Quelle épreuve te demande de défendre une opinion à l'oral ?", en: "Which section asks you to defend an opinion aloud?",
    options: ["Compréhension orale", "Compréhension écrite", "Expression écrite", "Expression orale"], answer: "Expression orale",
    right: { fr: "Exactement : c'est la tâche 3 de l'expression orale.", en: "Exactly: it's task 3 of the speaking section." } },
  { id: "q2", fr: "Combien de temps dure l'examen complet ?", en: "How long is the full exam?",
    options: ["1 h 30", "2 h 47", "4 h"], answer: "2 h 47",
    right: { fr: "Oui : 2 h 47, avec quatre épreuves obligatoires.", en: "Yes: 2 h 47, with four compulsory sections." } },
];

function Quiz({ en, quiz, setQuiz }: { en: boolean; quiz: Record<string, string>; setQuiz: (q: Record<string, string>) => void }) {
  return (
    <>
      <h2 className="title-poster text-3xl">{en ? "Quick check" : "Petit quiz"}</h2>
      <p className="text-sm font-semibold text-ink-faint">{en ? "About the exam format, not your French." : "Sur le format de l'examen, pas sur ton français."}</p>
      <div className="mt-4 space-y-5">
        {QUESTIONS.map((q) => {
          const picked = quiz[q.id];
          return (
            <fieldset key={q.id}>
              <legend className="font-extrabold">{q.fr}</legend>
              {en && <p className="text-sm font-semibold text-ink-faint">{q.en}</p>}
              <div className="mt-2 flex flex-wrap gap-2">
                {q.options.map((o) => {
                  const chosen = picked === o;
                  const correct = o === q.answer;
                  return (
                    <button key={o} type="button" disabled={!!picked && picked === q.answer}
                      onClick={() => setQuiz({ ...quiz, [q.id]: o })}
                      className={cx("flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-extrabold transition-colors",
                        chosen && correct && "bg-success text-white",
                        chosen && !correct && "bg-danger/15 text-danger",
                        !chosen && "bg-surface-2 text-ink-soft hover:text-ink")}>
                      {chosen && (correct ? <Check aria-hidden className="size-4" /> : <X aria-hidden className="size-4" />)}{o}
                    </button>
                  );
                })}
              </div>
              {picked && (
                <p role="status" className={cx("mt-2 text-sm font-bold", picked === q.answer ? "text-success" : "text-ink-soft")}>
                  {picked === q.answer ? (en ? q.right.en : q.right.fr) : (en ? "Not quite, try another." : "Pas tout à fait, essaie encore.")}
                </p>
              )}
            </fieldset>
          );
        })}
      </div>
    </>
  );
}

const ROUTE = [
  { fr: "Comprendre l'examen", en: "Understand the exam" },
  { fr: "Découvrir ton niveau", en: "Discover your level" },
  { fr: "Apprendre les méthodes", en: "Learn the methods" },
  { fr: "Entraîner les quatre compétences", en: "Train the four skills" },
  { fr: "Passer des tests réguliers", en: "Take regular practice tests" },
  { fr: "Préparer l'examen complet", en: "Prepare for the full exam" },
];

function Route({ en }: { en: boolean }) {
  return (
    <>
      <p className="text-lg font-extrabold">
        « Notre objectif est simple : comprendre l'examen, apprendre les bonnes méthodes, nous entraîner régulièrement et mesurer tes progrès jusqu'au jour du TCF Canada. »
      </p>
      {en && <p className="mt-1 text-sm font-semibold text-ink-soft">Our goal is simple: understand the exam, learn the right methods, practise regularly and measure your progress until TCF day.</p>}
      <ol className="mt-5 space-y-2">
        {ROUTE.map((r, i) => (
          <li key={r.fr} className="flex items-center gap-3">
            <span className={cx("grid size-8 shrink-0 place-items-center rounded-full text-sm font-extrabold",
              i === 0 ? "bg-success text-white" : "bg-surface-2 text-ink-soft")}>
              {i === 0 ? <Check aria-hidden className="size-4" strokeWidth={3} /> : i + 1}
            </span>
            <span className="font-extrabold">{r.fr}</span>
            {en && <span className="text-sm font-semibold text-ink-faint">{r.en}</span>}
          </li>
        ))}
      </ol>
    </>
  );
}

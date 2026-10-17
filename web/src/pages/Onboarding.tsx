import { useEffect, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { ArrowLeft, Check, Compass, Pause, Sparkles, Star, Volume2 } from "lucide-react";
import {
  L, nextStep, onboardingApi, path, prevStep, reaction,
  type Answers, type Campaign, type Line, type OnboardingState, type Step,
} from "../lib/onboarding";
import { exercisesApi, type SetPayload } from "../lib/exercises";
import { speak, speechAvailable } from "../lib/speak";
import { Player } from "./ExercisePlayer";
import { Briefing } from "../components/onboarding/Briefing";
import { CampaignView } from "../components/onboarding/CampaignView";
import { Badge, Button, CompassMark, ErrorNote, Loading, cx } from "../components/ui";

/** Conversational onboarding: one decision per screen, autosaved, resumable (blueprint B, Part II). */
export function Onboarding({ onDone }: { onDone: (avatarNow: boolean) => void }) {
  const [state, setState] = useState<OnboardingState | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [said, setSaid] = useState<Line | null>(null);
  const [paused, setPaused] = useState(false);
  const [campaign, setCampaign] = useState<Campaign | null>(null);

  useEffect(() => {
    onboardingApi.load().then(async (s) => {
      setState(s);
      if (s.completed) setCampaign(await onboardingApi.campaign().catch(() => null));
    }, setError);
  }, []);

  if (error) return <div className="mx-auto max-w-xl p-6"><ErrorNote error={error} /></div>;
  if (!state) return <div className="mx-auto max-w-xl px-6"><Loading /></div>;

  const a = state.answers;
  const lang = a.ui_language ?? "en";
  const steps = path(a);
  const index = steps.indexOf(state.step);

  async function answer(patch: Answers, from: Step = state!.step) {
    const merged = { ...a, ...patch };
    const to = nextStep(from, merged);
    try {
      const saved = await onboardingApi.save(to, patch);
      setSaid(reaction(from, merged));
      setState(saved);
    } catch (e) {
      setError(e as Error);
    }
  }

  async function back() {
    const p = prevStep(state!.step, a);
    if (!p) return;
    setSaid(null);
    setState(await onboardingApi.save(p, {}));
  }

  async function finish(patch: Answers) {
    try {
      await onboardingApi.save("campaign", patch);
      const c = await onboardingApi.complete();
      setCampaign(c);
      setSaid(null);
      setState((s) => (s ? { ...s, step: "campaign", completed: true, answers: { ...s.answers, ...patch } } : s));
    } catch (e) {
      setError(e as Error);
    }
  }

  if (paused) {
    return (
      <Shell>
        <Celeste line={{ fr: "À bientôt ! Tout est enregistré. On reprendra exactement ici.", en: "See you soon! Everything is saved. We'll pick up exactly here." }} lang={lang} />
        <Button className="mt-8 self-start" onClick={() => setPaused(false)}>Reprendre</Button>
      </Shell>
    );
  }

  // The challenge runs full width with the exercise player.
  if (state.step === "challenge") {
    return <ChallengeStep setId={state.challenge_set ?? "defi-a"} lang={lang} said={said}
      onDone={() => answer({}, "challenge")} onBack={back} />;
  }

  return (
    <Shell>
      {state.step !== "language" && state.step !== "campaign" && (
        <div className="mb-8 flex items-center gap-3">
          <button type="button" onClick={back} aria-label="Back" disabled={!prevStep(state.step, a)}
            className="grid size-10 place-items-center rounded-full text-ink-faint hover:bg-surface-2 hover:text-ink disabled:opacity-30">
            <ArrowLeft aria-hidden className="size-5" />
          </button>
          <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-surface-2" role="progressbar"
            aria-label="Onboarding progress" aria-valuemin={0} aria-valuemax={steps.length - 1} aria-valuenow={index}>
            <div className="h-full rounded-full bg-gradient-to-r from-violet to-pink transition-[width] duration-[var(--dur-slow)]"
              style={{ width: `${(index / (steps.length - 1)) * 100}%` }} />
          </div>
          <button type="button" onClick={() => setPaused(true)}
            className="flex items-center gap-1 rounded-full px-3 py-2 text-sm font-extrabold text-ink-faint hover:bg-surface-2 hover:text-ink">
            <Pause aria-hidden className="size-4" /> {lang === "en" ? "Later" : "Plus tard"}
          </button>
        </div>
      )}

      <AnimatePresence mode="wait" initial={false}>
        <StepFrame key={state.step}>
          {state.step === "language" && (
            <>
              <div className="flex items-center gap-3">
                <CompassMark className="size-12" />
                <p className="title-poster text-4xl">TCF Quest</p>
              </div>
              <p className="mt-8 text-xl font-bold">Choose the language for explanations.</p>
              <p className="font-semibold text-ink-soft">Choisis la langue des explications. Tu apprendras en français dans tous les cas.</p>
              <div className="mt-6 grid gap-3 sm:grid-cols-2">
                <BigChoice title="English" sub="Explanations in English" onClick={() => answer({ ui_language: "en" })} selected={a.ui_language === "en"} />
                <BigChoice title="Français" sub="Explications en français" onClick={() => answer({ ui_language: "fr" })} selected={a.ui_language === "fr"} />
              </div>
            </>
          )}

          {state.step === "welcome" && (
            <>
              <Celeste line={L.welcome} lang={lang} big />
              <div className="mt-8 grid gap-3">
                <BigChoice title="Découvrir le TCF Canada" sub={lang === "en" ? "A 2-minute interactive briefing" : "Une présentation interactive de 2 minutes"}
                  onClick={() => answer({ knows_exam: false })} />
                <BigChoice title="Je connais déjà l'examen" sub={lang === "en" ? "Skip the briefing (you can reopen it later)" : "Passer la présentation (tu pourras la revoir)"}
                  onClick={() => answer({ knows_exam: true })} />
              </div>
            </>
          )}

          {state.step === "briefing" && (
            <>
              <Celeste said={said} line={L.briefing} lang={lang} />
              <Briefing lang={lang} onDone={(quiz) => answer({ briefing_done: true, quiz })} onSkip={() => answer({ briefing_done: false })} />
            </>
          )}

          {state.step === "target" && <TargetStep a={a} lang={lang} said={said} onAnswer={answer} />}

          {state.step === "timing" && (
            <>
              <Celeste said={said} line={L.timing} lang={lang} />
              <Choices lang={lang} selected={a.exam_window} onPick={(v) => answer({ exam_window: v as Answers["exam_window"] })} options={[
                { value: "lt1m", fr: "Dans moins d'un mois", en: "Within a month" },
                { value: "3m", fr: "Dans 3 mois", en: "Within 3 months" },
                { value: "6m", fr: "Dans 6 mois", en: "Within 6 months" },
                { value: "later", fr: "Plus tard", en: "Later" },
                { value: "undecided", fr: "Je n'ai pas encore décidé", en: "I haven't decided" },
              ]} />
            </>
          )}

          {state.step === "comfort" && (
            <>
              <Celeste said={said} line={L.comfort} lang={lang} />
              <Choices lang={lang} selected={a.self_rating !== undefined ? String(a.self_rating) : undefined}
                onPick={(v) => answer({ self_rating: Number(v) })} options={[
                  { value: "1", fr: "Je débute.", en: "I'm just beginning.", example: "« Bonjour, merci »" },
                  { value: "2", fr: "Je comprends le français de base.", en: "I understand basic French.", example: "« Je voudrais un café »" },
                  { value: "3", fr: "Je me débrouille dans les conversations courantes.", en: "I can handle everyday conversations.", example: "« Mon train a du retard, je vais arriver vers midi. »" },
                  { value: "4", fr: "Je discute de sujets familiers avec aisance.", en: "I discuss familiar topics confidently.", example: "« À mon avis, le télétravail a plus d'avantages que d'inconvénients. »" },
                  { value: "5", fr: "Je communique sur des sujets complexes.", en: "I communicate about complex subjects.", example: "« Bien que cette réforme soit contestée, elle répond à un besoin réel. »" },
                ]} />
              <p className="mt-4 text-sm font-semibold text-ink-faint">
                {lang === "en" ? "This only picks your first exercises. It's not a level." : "Cela choisit seulement tes premiers exercices. Ce n'est pas un niveau."}
              </p>
            </>
          )}

          {state.step === "concern" && (
            <>
              <Celeste said={said} line={L.concern} lang={lang} />
              <Choices lang={lang} selected={a.concern} onPick={(v) => answer({ concern: v as Answers["concern"] })} options={[
                { value: "listening", fr: "Compréhension orale", en: "Listening" },
                { value: "reading", fr: "Compréhension écrite", en: "Reading" },
                { value: "speaking", fr: "Expression orale", en: "Speaking" },
                { value: "writing", fr: "Expression écrite", en: "Writing" },
                { value: "unsure", fr: "Je ne sais pas", en: "I'm not sure" },
              ]} />
              <p className="mt-4 text-sm font-semibold text-ink-faint">
                {lang === "en" ? "All four sections are still measured." : "Les quatre épreuves seront mesurées quand même."}
              </p>
            </>
          )}

          {state.step === "daily_time" && (
            <>
              <Celeste said={said} line={L.daily_time} lang={lang} />
              <div className="mt-6 grid grid-cols-3 gap-3 sm:grid-cols-5">
                {([10, 20, 30, 45, 60] as const).map((m) => (
                  <button key={m} type="button" onClick={() => answer({ daily_minutes: m })}
                    className={cx("card flex flex-col items-center py-4 transition-transform hover:-translate-y-1",
                      a.daily_minutes === m && "ring-3 ring-violet")}>
                    <span className="title-poster text-4xl">{m}{m === 60 ? "+" : ""}</span>
                    <span className="text-xs font-extrabold text-ink-faint">min</span>
                  </button>
                ))}
              </div>
            </>
          )}

          {state.step === "preference" && (
            <>
              <Celeste said={said} line={L.preference} lang={lang} />
              <Choices lang={lang} selected={a.preference} onPick={(v) => answer({ preference: v as Answers["preference"] })} options={[
                { value: "short", fr: "Beaucoup d'exercices courts", en: "Lots of short exercises" },
                { value: "conversation", fr: "Plus de conversations orales avec l'IA", en: "More spoken conversations with the AI" },
                { value: "explanations", fr: "Plus d'explications guidées", en: "More guided explanations" },
                { value: "timed", fr: "Plus d'entraînement chronométré", en: "More timed practice" },
                { value: "balanced", fr: "Un bon équilibre", en: "A good balance" },
              ]} />
              <p className="mt-4 text-sm font-semibold text-ink-faint">
                {lang === "en" ? "This changes the mix a little. Every TCF skill stays in your plan." : "Cela ajuste un peu le dosage. Toutes les compétences du TCF restent au programme."}
              </p>
            </>
          )}

          {state.step === "route" && (
            <>
              <Celeste said={said} line={L.route} lang={lang} />
              <div className="mt-6 grid gap-3">
                <BigChoice title="Évaluer mon niveau" badge={(a.self_rating ?? 3) > 1 ? (lang === "en" ? "Recommended" : "Recommandé") : undefined}
                  sub={lang === "en"
                    ? "About 25 minutes in four short parts you can spread over the week. Gives a real starting estimate per skill and lets you skip what you already know."
                    : "Environ 25 minutes en quatre petites parties, à étaler sur la semaine. Donne une vraie estimation par compétence."}
                  onClick={() => answer({ start_route: "evaluate" })} selected={a.start_route === "evaluate"} />
                <BigChoice title="Commencer mon entraînement" badge={(a.self_rating ?? 3) === 1 ? (lang === "en" ? "Recommended" : "Recommandé") : undefined}
                  sub={lang === "en"
                    ? "Start right away. Your level is measured little by little as you train; your starting point stays provisional for now."
                    : "On commence tout de suite. Ton niveau se mesure petit à petit ; ton point de départ reste provisoire."}
                  onClick={() => answer({ start_route: "train" })} selected={a.start_route === "train"} />
              </div>
            </>
          )}

          {state.step === "explorer" && <ExplorerStep a={a} lang={lang} said={said} onFinish={finish} />}

          {state.step === "campaign" && (
            campaign
              ? <CampaignView c={campaign} lang={lang} onStart={() => onDone(!!a.avatar_now)} />
              : <Loading />
          )}
        </StepFrame>
      </AnimatePresence>
    </Shell>
  );
}

/* ---------- building blocks ---------- */

function Shell({ children }: { children: React.ReactNode }) {
  return <div className="mx-auto flex min-h-dvh max-w-2xl flex-col px-5 py-8 sm:py-12">{children}</div>;
}

function StepFrame({ children }: { children: React.ReactNode }) {
  const reduce = useReducedMotion();
  return (
    <motion.div initial={reduce ? false : { opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
      exit={reduce ? undefined : { opacity: 0, y: -8 }} transition={{ duration: 0.22 }}>
      {children}
    </motion.div>
  );
}

/** Céleste: avatar, optional reaction to the last answer, then her line (French + translation). */
export function Celeste({ line, said, lang, big }: { line: Line; said?: Line | null; lang: "en" | "fr"; big?: boolean }) {
  return (
    <div className="flex items-start gap-4">
      <div className="relative shrink-0" aria-hidden>
        <div className={cx("tile grid place-items-center rounded-full [--tile:var(--violet)]", big ? "size-20" : "size-14")}>
          <Compass className={big ? "size-10" : "size-7"} strokeWidth={2.2} />
        </div>
        <Star className="absolute -right-1 -top-1 size-5 fill-[var(--gold)] text-[var(--gold)]" />
      </div>
      <div className="min-w-0 flex-1 space-y-2">
        <p className="text-xs font-extrabold uppercase tracking-[0.14em] text-violet">Céleste</p>
        {said && <Bubble line={said} lang={lang} muted />}
        <Bubble line={line} lang={lang} big={big} />
      </div>
    </div>
  );
}

function Bubble({ line, lang, big, muted }: { line: Line; lang: "en" | "fr"; big?: boolean; muted?: boolean }) {
  return (
    <div className={cx("card relative rounded-tl-md p-4", muted && "opacity-80")}>
      <p className={cx("font-extrabold", big ? "text-2xl leading-snug" : "text-xl")}>{line.fr}</p>
      {lang === "en" && <p className="mt-1 font-semibold text-ink-soft">{line.en}</p>}
      {speechAvailable() && !muted && (
        <button type="button" onClick={() => speak(line.fr, { speaker: "Céleste" })} aria-label="Hear it in French"
          className="absolute -bottom-3 right-3 grid size-8 place-items-center rounded-full bg-surface-2 text-ink-soft shadow-card hover:text-ink">
          <Volume2 aria-hidden className="size-4" />
        </button>
      )}
    </div>
  );
}

function BigChoice({ title, sub, onClick, selected, badge }: {
  title: string; sub?: string; onClick: () => void; selected?: boolean; badge?: string;
}) {
  return (
    <button type="button" onClick={onClick}
      className={cx("card flex w-full flex-col items-start gap-1 p-5 text-left transition-transform duration-[var(--dur-base)] ease-[var(--ease-bounce)] hover:-translate-y-1",
        selected && "ring-3 ring-violet")}>
      <span className="flex flex-wrap items-center gap-2 text-xl font-extrabold">{title}{badge && <Badge tone="accent">{badge}</Badge>}</span>
      {sub && <span className="font-semibold text-ink-soft">{sub}</span>}
    </button>
  );
}

function Choices({ options, onPick, lang, selected }: {
  options: { value: string; fr: string; en: string; example?: string }[];
  onPick: (v: string) => void; lang: "en" | "fr"; selected?: string;
}) {
  return (
    <div className="mt-6 grid gap-2.5">
      {options.map((o) => (
        <button key={o.value} type="button" onClick={() => onPick(o.value)}
          className={cx("card flex w-full items-center gap-3 px-5 py-4 text-left transition-transform duration-[var(--dur-fast)] hover:-translate-y-0.5",
            selected === o.value && "ring-3 ring-violet")}>
          <span className="min-w-0 flex-1">
            <span className="block text-lg font-extrabold">{o.fr}</span>
            {lang === "en" && <span className="block text-sm font-semibold text-ink-soft">{o.en}</span>}
            {o.example && <span className="mt-1 block text-sm italic text-ink-faint">{o.example}</span>}
          </span>
          {selected === o.value && <Check aria-hidden className="size-5 text-violet" strokeWidth={3} />}
        </button>
      ))}
    </div>
  );
}

/* ---------- steps with their own logic ---------- */

const SKILL_ROWS = [
  { key: "listening", fr: "Compréhension orale" },
  { key: "reading", fr: "Compréhension écrite" },
  { key: "speaking", fr: "Expression orale" },
  { key: "writing", fr: "Expression écrite" },
] as const;

function TargetStep({ a, lang, said, onAnswer }: { a: Answers; lang: "en" | "fr"; said: Line | null; onAnswer: (p: Answers) => void }) {
  const [perSkill, setPerSkill] = useState(a.target_choice === "nclc_specific");
  const [explain, setExplain] = useState(false);
  const [targets, setTargets] = useState(a.target_by_skill ?? { listening: 9, reading: 9, speaking: 9, writing: 9 });

  return (
    <>
      <Celeste said={said} line={L.target} lang={lang} />
      {!perSkill ? (
        <Choices lang={lang} selected={a.target_choice} onPick={(v) => (v === "nclc_specific" ? setPerSkill(true) : onAnswer({ target_choice: v as Answers["target_choice"] }))} options={[
          { value: "nclc_specific", fr: "Un niveau NCLC précis pour mon projet", en: "A specific NCLC level for my plans (per skill)" },
          { value: "nclc7", fr: "NCLC 7 dans les quatre compétences", en: "NCLC 7 in all four skills" },
          { value: "nclc9", fr: "NCLC 9 ou plus", en: "NCLC 9 or higher" },
          { value: "c1", fr: "Une solide performance de niveau C1", en: "A strong C1-level performance" },
          { value: "best", fr: "Le meilleur niveau possible", en: "The best level I can reach" },
          { value: "unsure", fr: "Je ne sais pas encore", en: "I'm not sure yet" },
        ]} />
      ) : (
        <div className="card mt-6 space-y-4 p-5">
          {SKILL_ROWS.map((s) => (
            <div key={s.key} className="flex flex-wrap items-center justify-between gap-2">
              <span className="font-extrabold">{s.fr}</span>
              <div className="flex gap-1.5" role="radiogroup" aria-label={`Target for ${s.fr}`}>
                {[5, 6, 7, 8, 9, 10].map((n) => (
                  <button key={n} type="button" role="radio" aria-checked={targets[s.key] === n}
                    onClick={() => setTargets((t) => ({ ...t, [s.key]: n }))}
                    className={cx("size-10 rounded-[12px] font-extrabold", targets[s.key] === n ? "tile [--tile:var(--violet)]" : "bg-surface-2 text-ink-soft")}>
                    {n}
                  </button>
                ))}
              </div>
            </div>
          ))}
          <div className="flex justify-between gap-2 pt-2">
            <Button variant="quiet" onClick={() => setPerSkill(false)}>Back</Button>
            <Button onClick={() => onAnswer({ target_choice: "nclc_specific", target_by_skill: targets })}>Continuer</Button>
          </div>
        </div>
      )}
      <button type="button" onClick={() => setExplain((e) => !e)} className="mt-4 text-sm font-extrabold text-violet hover:underline">
        {lang === "en" ? "What's the difference between CEFR, TCF and NCLC?" : "Quelle différence entre CECR, TCF et NCLC ?"}
      </button>
      {explain && (
        <p className="mt-2 rounded-[16px] bg-surface-2 p-4 text-sm font-semibold text-ink-soft">
          {lang === "en"
            ? "CEFR (A1–C2) describes your French in general. The TCF Canada gives a score for each skill. Canada converts those scores into NCLC levels. We track all three separately and always say which one we mean."
            : "Le CECR (A1–C2) décrit ton niveau général. Le TCF Canada donne un score par compétence. Le Canada convertit ces scores en niveaux NCLC. Nous suivons les trois séparément et précisons toujours lequel."}
        </p>
      )}
      <p className="mt-4 text-xs font-semibold text-ink-faint">
        {lang === "en"
          ? "I can't tell you which result your application needs; check IRCC's official requirements. I'll help you reach the target you set."
          : "Je ne peux pas te dire quel résultat ton dossier exige ; vérifie les exigences officielles d'IRCC. Je t'aide à atteindre l'objectif que tu fixes."}
      </p>
    </>
  );
}

function ChallengeStep({ setId, lang, said, onDone, onBack }: {
  setId: string; lang: "en" | "fr"; said: Line | null; onDone: () => void; onBack: () => void;
}) {
  const [started, setStarted] = useState(false);
  const [payload, setPayload] = useState<SetPayload | null>(null);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    exercisesApi.load(setId).then((p) => {
      setPayload(p);
      if (p.state.index > 0) setStarted(true); // resuming mid-challenge
    }, setError);
  }, [setId]);

  if (error) return <Shell><ErrorNote error={error} /></Shell>;
  if (!payload) return <Shell><Loading /></Shell>;
  if (started) return <Player payload={payload} onDone={onDone} />;

  return (
    <Shell>
      <button type="button" onClick={onBack} aria-label="Back" className="mb-8 grid size-10 place-items-center rounded-full text-ink-faint hover:bg-surface-2 hover:text-ink">
        <ArrowLeft aria-hidden className="size-5" />
      </button>
      <Celeste said={said} line={L.challenge} lang={lang} />
      <p className="mt-6 font-semibold text-ink-soft">
        {lang === "en"
          ? "4 short tasks, one per TCF section. You try, I react, we go on. No pressure: this isn't a test."
          : "4 petites tâches, une par épreuve du TCF. Tu essaies, je réagis, on avance. Pas de pression : ce n'est pas un test."}
      </p>
      <Button className="mt-6 self-start" onClick={() => setStarted(true)}><Sparkles aria-hidden className="size-4" /> C'est parti !</Button>
    </Shell>
  );
}

function ExplorerStep({ a, lang, said, onFinish }: { a: Answers; lang: "en" | "fr"; said: Line | null; onFinish: (p: Answers) => void }) {
  const [name, setName] = useState(a.display_name ?? "");
  return (
    <>
      <Celeste said={said} line={L.explorer} lang={lang} />
      <form className="mt-6 space-y-5" onSubmit={(e) => { e.preventDefault(); onFinish({ display_name: name.trim(), avatar_now: false }); }}>
        <input autoFocus value={name} onChange={(e) => setName(e.target.value)} maxLength={40}
          placeholder={lang === "en" ? "Your first name (optional)" : "Ton prénom (facultatif)"} aria-label="Your first name"
          className="w-full rounded-[18px] border-2 border-line bg-surface px-5 py-4 text-xl font-bold outline-none focus:border-violet" />
        <div className="grid gap-3 sm:grid-cols-2">
          <Button type="button" variant="secondary" onClick={() => onFinish({ display_name: name.trim(), avatar_now: true })}>
            {lang === "en" ? "Design my explorer now" : "Créer mon explorateur"}
          </Button>
          <Button type="submit">{lang === "en" ? "See my campaign" : "Voir ma campagne"}</Button>
        </div>
        <p className="text-sm font-semibold text-ink-faint">
          {lang === "en" ? "Your avatar is just for fun. It never affects your results." : "Ton avatar est juste pour le plaisir. Il n'influence jamais tes résultats."}
        </p>
      </form>
    </>
  );
}

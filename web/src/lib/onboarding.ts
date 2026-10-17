// Conversational onboarding with Céleste (blueprint B + Part II R1–R6).
// Every step saves to the server, so closing the browser resumes exactly where the learner was.

export type Step =
  | "language" | "welcome" | "briefing" | "target" | "timing" | "comfort" | "concern"
  | "daily_time" | "preference" | "challenge" | "route" | "explorer" | "campaign";

export interface Answers {
  ui_language?: "en" | "fr";
  knows_exam?: boolean;
  briefing_done?: boolean;
  quiz?: Record<string, string>;
  target_choice?: "nclc_specific" | "nclc7" | "nclc9" | "c1" | "best" | "unsure";
  target_nclc?: number;
  target_by_skill?: { listening: number; reading: number; speaking: number; writing: number };
  exam_window?: "lt1m" | "3m" | "6m" | "later" | "undecided";
  exam_date?: string | null;
  self_rating?: number;
  concern?: "listening" | "reading" | "speaking" | "writing" | "unsure";
  daily_minutes?: 10 | 20 | 30 | 45 | 60;
  preference?: "short" | "conversation" | "explanations" | "timed" | "balanced";
  start_route?: "evaluate" | "train";
  display_name?: string;
  avatar_now?: boolean;
}

export interface OnboardingState {
  step: Step;
  answers: Answers;
  completed: boolean;
  challenge_set?: string;
}

export interface Campaign {
  name: string;
  objective: { nclc: number; nclc_by_skill: Record<string, number> | null; cefr_goal: string };
  start: { provisional: boolean; cefr_low: string; cefr_high: string; basis: string };
  gap: string | null;
  priorities: { skill: string; section: string; reason: string }[];
  rhythm: { daily_minutes: number; weekly_hours: number; plan_mode: string; plan_label: string; exam_window: string };
  route: "evaluate" | "train";
  challenge: { set_id: string; answered: number; correct: number };
  next_steps: { title: string; status: string; link?: string }[];
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail ?? res.statusText);
  return res.json() as Promise<T>;
}

export const onboardingApi = {
  load: () => fetch("/api/onboarding").then((r) => json<OnboardingState>(r)),
  save: (step: Step, answers: Answers) =>
    fetch("/api/onboarding", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ step, answers }) })
      .then((r) => json<OnboardingState>(r)),
  restart: () => fetch("/api/onboarding/restart", { method: "POST" }).then((r) => json<OnboardingState>(r)),
  complete: () => fetch("/api/onboarding/complete", { method: "POST" }).then((r) => json<Campaign>(r)),
  campaign: () => fetch("/api/campaign").then((r) => json<Campaign>(r)),
};

const ORDER: Step[] = ["language", "welcome", "briefing", "target", "timing", "comfort", "concern",
  "daily_time", "preference", "challenge", "route", "explorer", "campaign"];

/** The learner's path: the briefing is skipped by « Je connais déjà l'examen ». */
export function path(a: Answers): Step[] {
  return ORDER.filter((s) => s !== "briefing" || a.knows_exam !== true);
}

export function nextStep(step: Step, a: Answers): Step {
  const p = path(a);
  return p[Math.min(p.indexOf(step) + 1, p.length - 1)];
}

export function prevStep(step: Step, a: Answers): Step | null {
  const p = path(a);
  const i = p.indexOf(step);
  return i > 0 ? p[i - 1] : null;
}

/** Bilingual line: French always shown; English translation shown in English guidance mode. */
export interface Line { fr: string; en: string }

export const L = {
  welcome: {
    fr: "Bienvenue dans TCF Quest ! Je suis Céleste, ta guide. Ensemble, nous allons nous préparer au TCF Canada, étape par étape.",
    en: "Welcome to TCF Quest! I'm Céleste, your guide. Together we'll prepare for the TCF Canada, step by step.",
  },
  briefing: { fr: "Avant de commencer ton aventure, découvrons le défi que tu vas préparer.", en: "Before your adventure starts, let's discover the challenge you're preparing for." },
  target: { fr: "Que veux-tu atteindre au TCF Canada ?", en: "What do you want to reach in the TCF Canada?" },
  timing: { fr: "Quand penses-tu passer le TCF Canada ?", en: "When do you plan to take the TCF Canada?" },
  comfort: { fr: "Comment te sens-tu en français aujourd'hui ?", en: "How comfortable do you feel in French today?" },
  concern: { fr: "Quelle épreuve t'inquiète le plus ?", en: "Which section worries you most?" },
  daily_time: { fr: "Combien de temps peux-tu consacrer à l'expédition chaque jour ?", en: "How much time can you give the expedition each day?" },
  preference: { fr: "Comment préfères-tu t'entraîner ?", en: "How do you prefer to practise?" },
  challenge: { fr: "On commence avec quelques petites épreuves pour découvrir comment tu apprends.", en: "Let's start with a few short tasks to see how you learn." },
  challengeDone: { fr: "Tu viens de toucher aux quatre épreuves du TCF.", en: "You've just had a taste of all four TCF sections." },
  route: { fr: "Maintenant, découvrons tes points forts. Comment veux-tu commencer ?", en: "Now let's find your strengths. How do you want to start?" },
  explorer: { fr: "Dernière chose : comment veux-tu que je t'appelle ?", en: "Last thing: what should I call you?" },
  campaign: { fr: "Voici ta campagne de préparation au TCF Canada.", en: "Here's your TCF Canada preparation campaign." },
} satisfies Record<string, Line>;

/** Céleste's short reaction to the previous answer, shown above the next question. */
export function reaction(step: Step, a: Answers): Line | null {
  switch (step) {
    case "welcome":
      return a.knows_exam ? { fr: "Parfait, on gagne du temps.", en: "Perfect, that saves time." } : { fr: "C'est parti !", en: "Let's go!" };
    case "briefing":
      return { fr: "Bravo, tu connais maintenant le terrain.", en: "Well done, you now know the ground." };
    case "target":
      return a.target_choice === "unsure"
        ? { fr: "Pas de souci : on part sur NCLC 7, tu pourras changer.", en: "No problem: we'll start with NCLC 7, you can change it." }
        : { fr: "C'est noté. On y va étape par étape.", en: "Noted. We'll get there step by step." };
    case "timing":
      return {
        lt1m: { fr: "Alors on se concentre : beaucoup d'entraînement au format de l'examen.", en: "Then we focus: lots of exam-format practice." },
        "3m": { fr: "Trois mois : on alterne méthodes et entraînement chronométré.", en: "Three months: methods and timed practice, side by side." },
        "6m": { fr: "Six mois : de quoi construire des bases solides.", en: "Six months: enough to build solid foundations." },
        later: { fr: "Pas de souci, tu pourras ajouter une date à tout moment.", en: "No problem, you can add a date any time." },
        undecided: { fr: "Pas de souci, tu pourras ajouter une date à tout moment.", en: "No problem, you can add a date any time." },
      }[a.exam_window ?? "undecided"];
    case "comfort":
      return { fr: "Merci ! Ce n'est qu'un point de départ, on mesurera pour de vrai.", en: "Thanks! That's only a starting point; we'll measure for real." };
    case "concern":
      return a.concern && a.concern !== "unsure"
        ? { fr: "On s'en occupera tôt, promis.", en: "We'll tackle it early, promise." }
        : { fr: "Le test nous le dira.", en: "The level check will tell us." };
    case "daily_time": {
      const m = a.daily_minutes ?? 20;
      const h = String(Math.round((m * 5) / 6) / 10).replace(".", ",");
      return { fr: `${m} minutes par jour, environ ${h} h par semaine. La régularité compte plus que l'intensité.`, en: `${m} minutes a day, about ${h.replace(",", ".")} h a week. Steady beats intense.` };
    }
    case "preference":
      return { fr: "Noté. Les quatre compétences restent au programme.", en: "Noted. All four skills stay on the programme." };
    case "challenge":
      return L.challengeDone;
    case "route":
      return a.start_route === "evaluate"
        ? { fr: "Excellent choix. Le test arrive en quatre petites parties.", en: "Great choice. The level check comes in four short parts." }
        : { fr: "On démarre tout de suite. Ton niveau se précisera au fil de l'entraînement.", en: "We start right away. Your level will become clearer as you train." };
    default:
      return null;
  }
}

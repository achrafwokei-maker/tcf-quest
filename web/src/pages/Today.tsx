import { Link, useNavigate } from "react-router-dom";
import { motion, useReducedMotion } from "motion/react";
import { BookOpen, Calendar, Compass, Flame, Headphones, Mic, PenLine, Settings, Target, Zap } from "lucide-react";
import { api } from "../lib/api";
import { useAsync } from "../lib/useAsync";
import { onboardingApi } from "../lib/onboarding";
import { daysUntil, frDate, greeting, nextTrialDate, skillName } from "../lib/labels";
import { Art, Badge, Button, ErrorNote, IconTile, Loading, Panel, Ring } from "../components/ui";
import { AvatarImage } from "../components/AvatarForm";
import { ContinueCard } from "../components/ContinueCard";
import { ThemeToggle } from "../components/ThemeSwitch";
import { JourneyRoad } from "../components/JourneyRoad";
import { journeyApi } from "../lib/journey";

const SKILL_TILES = [
  { skill: "listening", icon: Headphones, color: "var(--cyan)" },
  { skill: "reading", icon: BookOpen, color: "var(--green)" },
  { skill: "speaking", icon: Mic, color: "var(--pink)" },
  { skill: "writing", icon: PenLine, color: "var(--gold)" },
] as const;

const SKILL_LINK = { listening: "/pratique/CO", reading: "/pratique/CE", speaking: "/oral", writing: "/ecrit" } as const;

export function Today() {
  const reduce = useReducedMotion();
  const [state, reload] = useAsync(api.summary);
  const [av] = useAsync(api.avatar);
  const skin = av.status === "ready" ? av.data.avatar?.equipped_skin ?? null : null;
  if (state.status === "loading") return <div className="px-5"><Loading /></div>;
  if (state.status === "error") return <div className="p-5"><ErrorNote error={state.error} onRetry={reload} /></div>;
  const s = state.data;
  const p = s.profile;
  const trial = nextTrialDate();
  const examIn = p.exam_date ? daysUntil(p.exam_date) : null;

  return (
    <div>
      {/* Hero: Paris at night (IMG-001), greeting and avatar stage */}
      <section className="relative mx-3 mt-3 overflow-hidden rounded-[34px] sm:mx-5 sm:mt-5">
        <Art src="/art/img-001-paris-hero.png" alt="Paris by night" position="50% 35%"
          className="absolute inset-0 h-full w-full" />
        <div aria-hidden className="absolute inset-0 bg-gradient-to-b from-[#0f1033]/55 via-transparent to-[#0f1033]/85" />
        <div className="relative flex min-h-[23rem] flex-col justify-between p-5 pb-24 text-white sm:min-h-[26rem] sm:p-8 sm:pb-28">
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs font-extrabold uppercase tracking-[0.14em] text-white/80">{frDate(new Date())}</p>
            <div className="flex gap-2">
              <Badge tone="onDark"><Flame aria-hidden className="size-3.5 text-gold" />{s.streak}</Badge>
              <Badge tone="onDark"><Zap aria-hidden className="size-3.5 text-gold" />{s.xp} XP</Badge>
              <ThemeToggle className="grid size-7 place-items-center rounded-full bg-white/18 text-white backdrop-blur hover:bg-white/30" />
              <Link to="/reglages" aria-label="Settings and Voice Studio" title="Réglages · Voice Studio"
                className="grid size-7 place-items-center rounded-full bg-white/18 text-white backdrop-blur hover:bg-white/30">
                <Settings aria-hidden className="size-4" />
              </Link>
            </div>
          </div>

          <div className="flex items-end justify-between gap-4">
            <div>
              <h1 className="title-poster text-5xl drop-shadow-[0_4px_18px_rgb(0_0_0/0.45)] sm:text-7xl">{greeting(p.display_name)}</h1>
              <p className="mt-2 max-w-md font-semibold text-white/85">
                {s.diagnostic_done ? "Here is today's plan." : "Chapitre II · Paris. Your expedition starts in Belleville."}
              </p>
            </div>
            <AvatarSlot skin={skin} />
          </div>
        </div>
      </section>

      {/* Overlapping sheet with skills and today's mission (reference 2) */}
      <motion.section
        initial={reduce ? false : { y: 24, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1], delay: 0.05 }}
        className="card relative mx-5 -mt-20 p-5 sm:mx-10 sm:p-7"
      >
        <ul className="grid grid-cols-4 gap-2" aria-label="Skills">
          {SKILL_TILES.map(({ skill, icon, color }) => (
            <li key={skill}>
              <Link to={SKILL_LINK[skill]} className="group flex flex-col items-center gap-1.5 rounded-[18px] p-1 text-center">
                <IconTile icon={icon} color={color} className="transition-transform duration-[var(--dur-base)] ease-[var(--ease-bounce)] group-hover:-translate-y-1 group-hover:rotate-[-4deg]" />
                <span className="text-xs font-bold text-ink-soft sm:text-sm">{skillName[skill].en}</span>
              </Link>
            </li>
          ))}
        </ul>

        <div className="my-5 h-px bg-line" />

        <ContinueCard />
        <MiniRoad />
      </motion.section>

      <div className="mt-6 space-y-6 px-5 sm:px-10">
        {!p.exam_window && <UpdateGoalsBanner />}

        <div className="grid gap-4 sm:grid-cols-3">
          <Panel pad="sm" className="flex items-center gap-4">
            <Ring value={s.minutes_today} max={p.daily_minutes} label="Minutes studied today" color="var(--violet)">
              <span className="text-sm font-extrabold">{s.minutes_today}</span>
            </Ring>
            <div>
              <p className="eyebrow">Today's goal</p>
              <p className="text-lg font-extrabold">{p.daily_minutes} min</p>
            </div>
          </Panel>
          <Panel pad="sm" className="flex items-center gap-4">
            <IconTile icon={Calendar} color="var(--blue)" />
            <div>
              <p className="eyebrow">Weekly trial</p>
              <p className="text-lg font-extrabold capitalize">{trial.toLocaleDateString("fr-CA", { weekday: "long" })}</p>
              <p className="text-xs font-semibold text-ink-faint">25–40 min · timed · no hints</p>
            </div>
          </Panel>
          <Panel pad="sm" className="flex items-center gap-4">
            <IconTile icon={Target} color="var(--green)" />
            <div>
              <p className="eyebrow">Target</p>
              <p className="text-lg font-extrabold">{p.goal === "tcf_canada" ? `NCLC ${p.target_nclc}` : p.target_cefr} <span className="text-sm text-ink-faint">· {p.target_cefr} goal</span></p>
              <p className="text-xs font-semibold text-ink-faint">
                {examIn === null ? "No exam date yet" : examIn >= 0 ? `Exam in ${examIn} days` : "Enter your official results"}
              </p>
            </div>
          </Panel>
        </div>

      </div>
    </div>
  );
}

/** The learner's character on the hero; opens the avatar creator and wardrobe. */
function AvatarSlot({ skin }: { skin: string | null }) {
  return (
    <Link to="/avatar"
      className="glass group flex h-36 w-28 shrink-0 flex-col items-center justify-end overflow-hidden rounded-[26px] !border-white/25 !bg-white/12 transition-transform duration-[var(--dur-base)] ease-[var(--ease-bounce)] hover:-translate-y-1 sm:h-44 sm:w-32">
      <AvatarImage skin={skin ?? "a1"} dark className="h-28 w-24 sm:h-36 sm:w-28" />
      <span className="pb-2 text-[0.65rem] font-extrabold uppercase tracking-wider text-white/90">
        {skin ? "Mon avatar" : "Create avatar"}
      </span>
    </Link>
  );
}

/** Shown to learners who onboarded before the conversational flow existed. */
function UpdateGoalsBanner() {
  const navigate = useNavigate();
  async function go() {
    await onboardingApi.restart();
    navigate("/bienvenue");
  }
  return (
    <Panel look="glass" className="flex flex-wrap items-center gap-4">
      <IconTile icon={Compass} color="var(--violet)" size="lg" />
      <div className="min-w-0 flex-1">
        <h2 className="text-lg">Céleste has new questions for you</h2>
        <p className="text-sm text-ink-soft">Your exam timing, the section that worries you and a 2-minute TCF challenge. About 4 minutes; your answers are kept.</p>
      </div>
      <Button onClick={go}>Let's go</Button>
    </Panel>
  );
}

/** A small window of the road around "you are here"; the whole journey is on Mon Aventure. */
function MiniRoad() {
  const [state] = useAsync(journeyApi.map);
  if (state.status !== "ready") return null;
  return (
    <div className="mt-6 border-t border-line pt-4">
      <JourneyRoad chapters={state.data.chapters} current={state.data.current_chapter}
        sideMissions={state.data.side_missions} window={{ before: 1, after: 2 }} />
    </div>
  );
}

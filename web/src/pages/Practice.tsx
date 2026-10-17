import { BookOpen, Feather, Headphones, Languages, Mic, NotebookPen, PenLine, Timer } from "lucide-react";
import { skillName } from "../lib/labels";
import { Link } from "react-router-dom";
import { Play, Scale } from "lucide-react";
import { exercisesApi, SECTION_LABEL } from "../lib/exercises";
import { useAsync } from "../lib/useAsync";
import { Badge, IconTile, Panel } from "../components/ui";

const SKILL_AREAS = [
  { skill: "listening", icon: Headphones, color: "var(--cyan)", detail: "Announcements, interviews, debates. One play in exam mode.", phase: 0, link: "/pratique/CO" },
  { skill: "reading", icon: BookOpen, color: "var(--green)", detail: "From notices to argued articles, increasing difficulty.", phase: 0, link: "/pratique/CE" },
  { skill: "speaking", icon: Mic, color: "var(--pink)", detail: "Tasks T1 to T3 with a local AI examiner, real timings, microphone or typing.", phase: 0, link: "/oral" },
  { skill: "writing", icon: PenLine, color: "var(--gold)", detail: "Tasks T1 to T3 with word counter, timer and local AI feedback.", phase: 0, link: "/ecrit" },
] as const;

const TOOLS = [
  { title: "Académie TCF", icon: Feather, color: "var(--violet)", detail: "Strategies for every section and task", phase: 0, link: "/academie" },
  { title: "Boîte à outils", icon: Languages, color: "var(--blue)", detail: "Frameworks, connectors, grammar lessons", phase: 0, link: "/outils" },
  { title: "Vocabulaire", icon: BookOpen, color: "var(--cyan)", detail: "Useful expressions by function, a few a day", phase: 0, link: "/vocabulaire" },
  { title: "Carnet d'erreurs", icon: NotebookPen, color: "var(--orange)", detail: "Your recurring mistakes, to drill", phase: 0, link: "/carnet" },
  { title: "Examens", icon: Timer, color: "var(--red)", detail: "Weekly four-skill trial, exam rules", phase: 0, link: "/examen" },
];

export function Practice() {
  return (
    <div className="space-y-8 px-5 pt-6 sm:px-10 sm:pt-10">
      <header>
        <p className="eyebrow">Entraînement</p>
        <h1 className="title-poster mt-1 text-5xl sm:text-6xl">Practise one skill at a time</h1>
        <p className="mt-3 max-w-2xl text-ink-soft">
          Training mode gives hints, replays and explanations. Exam mode is strict and quiet, like the real test.
        </p>
      </header>

      <ExerciseSets />

      <div className="grid gap-4 sm:grid-cols-2">
        {SKILL_AREAS.map((a) => {
          const body = (
            <>
              <div className="flex items-start justify-between gap-3">
                <IconTile icon={a.icon} color={a.color} />
                <Badge tone="success">Open</Badge>
              </div>
              <h2 className="title-poster mt-4 text-3xl">{skillName[a.skill].fr}</h2>
              <p className="text-sm text-ink-faint">{skillName[a.skill].en}</p>
              <p className="mt-3 text-ink-soft">{a.detail}</p>
            </>
          );
          return <Link key={a.skill} to={a.link} className="card p-5 transition-transform hover:-translate-y-1 sm:p-6">{body}</Link>;
        })}
      </div>

      <section aria-labelledby="tools">
        <h2 id="tools" className="text-2xl">Tools</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {TOOLS.map((t) => {
            const body = (
              <>
                <div className="flex items-center justify-between">
                  <IconTile icon={t.icon} color={t.color} size="sm" />
                  <Badge tone="success">Open</Badge>
                </div>
                <p className="mt-3 font-semibold">{t.title}</p>
                <p className="text-sm text-ink-faint">{t.detail}</p>
              </>
            );
            return "link" in t && t.link ? (
              <Link key={t.title} to={t.link} className="card p-4 transition-transform hover:-translate-y-1 sm:p-5">{body}</Link>
            ) : (
              <Panel key={t.title} pad="sm">{body}</Panel>
            );
          })}
        </div>
      </section>
    </div>
  );
}

/** Playable exercise sets (milestone 1 preview of the exercise engine). */
function ExerciseSets() {
  const [state] = useAsync(exercisesApi.list);
  const [queue] = useAsync(exercisesApi.review);
  if (state.status !== "ready") return null;
  const sets = state.data.sets.filter((s) => s.context === "practice");
  if (sets.length === 0) return null;
  const toReview = queue.status === "ready" ? queue.data.reports.length : 0;
  return (
    <section aria-labelledby="sets">
      {toReview > 0 && (
        <Link to="/review" className="glass mb-5 flex items-center gap-3 p-4 font-extrabold hover:-translate-y-0.5">
          <Scale aria-hidden className="size-5 text-violet" />
          {toReview} answer{toReview === 1 ? "" : "s"} to review
        </Link>
      )}
      <h2 id="sets" className="text-2xl">Premiers pas</h2>
      <p className="text-sm font-semibold text-ink-soft">Short sets touching all four TCF sections. Pick your level.</p>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {sets.map((s) => (
          <Link key={s.id} to={`/set/${s.id}`}
            className="card group flex items-center gap-4 p-4 transition-transform duration-[var(--dur-base)] ease-[var(--ease-bounce)] hover:-translate-y-1">
            <span className="tile grid size-14 shrink-0 place-items-center rounded-[18px] [--tile:var(--violet)]">
              <Play aria-hidden className="size-6 fill-current" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="font-extrabold">{s.title} · {s.level}</p>
              <p className="text-sm text-ink-faint">{s.items} exercises</p>
              <div className="mt-1.5 flex flex-wrap gap-1">
                {s.sections.map((sec) => <Badge key={sec}>{SECTION_LABEL[sec as keyof typeof SECTION_LABEL]}</Badge>)}
              </div>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}

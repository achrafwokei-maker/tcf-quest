import { Link } from "react-router-dom";
import { ArrowLeft, Play } from "lucide-react";
import { exercisesApi, type SetSummary } from "../lib/exercises";
import { useAsync } from "../lib/useAsync";
import { Badge, ErrorNote, Loading } from "../components/ui";

const GROUP_LABEL: Record<string, string> = {
  CO: "Compréhension orale", CE: "Compréhension écrite",
  "EO-T1": "Expression orale · tâche 1", "EO-T2": "Expression orale · tâche 2", "EO-T3": "Expression orale · tâche 3",
  "EE-T1": "Expression écrite · tâche 1", "EE-T2": "Expression écrite · tâche 2", "EE-T3": "Expression écrite · tâche 3",
};

/** Académie TCF (strategies) and Boîte à outils (frameworks, connectors, grammar): sets grouped by section or category. */
const CONTEXT_GROUP: Record<string, string> = { mission: "Story missions", practice: "Practice sets", academy: "Strategies (Académie)", toolbox: "Lessons (Boîte à outils)" };

export function LibraryPage({ context, section, eyebrow, title, intro }: {
  context?: "academy" | "toolbox"; section?: "CO" | "CE"; eyebrow: string; title: string; intro: string;
}) {
  const [state, reload] = useAsync(exercisesApi.list);
  const all = state.status === "ready" ? state.data.sets : [];
  const sets = section
    ? all.filter((s) => s.sections.includes(section) && ["mission", "practice", "academy", "toolbox"].includes(s.context))
        .map((s) => ({ ...s, group: CONTEXT_GROUP[s.context] }))
    : all.filter((s) => s.context === context);
  const groups = [...new Set(sets.map((s) => s.group ?? "Autres"))];
  return (
    <div className="space-y-6 px-5 pt-6 sm:px-10 sm:pt-10">
      <Link to="/entrainement" className="inline-flex items-center gap-1 text-sm font-extrabold text-ink-soft hover:text-ink">
        <ArrowLeft aria-hidden className="size-4" /> Entraînement
      </Link>
      <header>
        <p className="eyebrow">{eyebrow}</p>
        <h1 className="title-poster mt-1 text-5xl sm:text-6xl">{title}</h1>
        <p className="mt-2 max-w-2xl font-semibold text-ink-soft">{intro}</p>
      </header>
      {state.status === "loading" && <Loading />}
      {state.status === "error" && <ErrorNote error={state.error} onRetry={reload} />}
      {groups.map((g) => (
        <section key={g} aria-label={GROUP_LABEL[g] ?? g}>
          <h2 className="text-xl">{GROUP_LABEL[g] ?? g}</h2>
          <ul className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {sets.filter((s) => (s.group ?? "Autres") === g).map((s: SetSummary) => (
              <li key={s.id}>
                <Link to={`/set/${s.id}`} className="card flex h-full items-center gap-3 p-4 transition-transform hover:-translate-y-1">
                  <span className="tile grid size-11 shrink-0 place-items-center rounded-[14px] [--tile:var(--violet)]"><Play aria-hidden className="size-5 fill-current" /></span>
                  <div className="min-w-0">
                    <p className="font-extrabold">{s.title.replace(/^Académie · /, "")}</p>
                    <div className="mt-1 flex gap-1"><Badge>{s.level}</Badge><Badge>{s.items} exercices</Badge></div>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}

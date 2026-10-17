import { api } from "../lib/api";
import { useAsync } from "../lib/useAsync";
import { skillName } from "../lib/labels";
import { Badge, ErrorNote, Loading, Panel } from "../components/ui";

const CEFR = ["A1", "A2", "B1", "B2", "C1", "C2"];

export function Progress() {
  const [state, reload] = useAsync(api.summary);
  if (state.status === "loading") return <Loading />;
  if (state.status === "error") return <ErrorNote error={state.error} onRetry={reload} />;
  const s = state.data;

  return (
    <div className="space-y-8 px-5 pt-6 sm:px-10 sm:pt-10">
      <header>
        <p className="eyebrow">Ma Progression</p>
        <h1 className="title-poster mt-1 text-5xl sm:text-6xl">Where you stand</h1>
        <p className="mt-3 max-w-2xl text-ink-soft">
          Every number here is a practice estimate with a range, never an official TCF result.
          Three scales are kept apart: CEFR (general level), TCF score, and NCLC (immigration).
        </p>
      </header>

      <Panel>
        <h2 className="text-2xl">Skills (CEFR estimate)</h2>
        <ul className="mt-5 space-y-5">
          {s.skills.map((k) => (
            <li key={k.skill}>
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <p className="font-semibold">
                  {skillName[k.skill].fr} <span className="font-normal text-ink-faint">· {skillName[k.skill].en}</span>
                </p>
                {k.evidence === 0 ? (
                  <Badge>No evidence yet</Badge>
                ) : (
                  <Badge tone="accent">{k.cefr_low}–{k.cefr_high} · {k.confidence} confidence</Badge>
                )}
              </div>
              {/* CEFR ruler: the estimate shows as a band, not a point */}
              <div className="mt-2 grid grid-cols-6 gap-1" aria-hidden>
                {CEFR.map((lvl) => {
                  const lo = k.cefr_low ? CEFR.indexOf(k.cefr_low) : -1;
                  const hi = k.cefr_high ? CEFR.indexOf(k.cefr_high) : -1;
                  const i = CEFR.indexOf(lvl);
                  const inBand = lo >= 0 && i >= lo && i <= hi;
                  return (
                    <div key={lvl}>
                      <div className={inBand ? "tile h-3 rounded-full [--tile:var(--violet)]" : "h-3 rounded-full bg-surface-2"} />
                      <p className="mt-1 text-center text-xs text-ink-faint">{lvl}</p>
                    </div>
                  );
                })}
              </div>
            </li>
          ))}
        </ul>
        <p className="mt-6 text-sm text-ink-faint">
          Updated after every answer, weighted by how strong the evidence is (hints, replays and disputed answers count less or not at all). Speaking and writing stay at low confidence until real spoken and written tasks are assessed.
        </p>
      </Panel>

      <Panel>
        <h2 className="text-2xl">Changes over time</h2>
        <p className="mt-1 text-sm text-ink-faint">
          Weak points being fixed: {s.weaknesses.active} · confirmed fixed on new questions: {s.weaknesses.mastered}.
          Trials and mocks are on your journey (Mon Aventure).
        </p>
        {s.history.length === 0 ? (
          <p className="mt-3 text-sm font-semibold text-ink-soft">No changes yet. Estimates move as you answer.</p>
        ) : (
          <ul className="mt-3 space-y-1.5">
            {s.history.map((h, i) => (
              <li key={i} className="flex flex-wrap justify-between gap-2 text-sm">
                <span className="font-bold">{skillName[h.skill].en}: {h.cefr_low}–{h.cefr_high} <span className="font-semibold text-ink-faint">({h.confidence})</span></span>
                <span className="text-ink-faint">{h.created_at.slice(0, 10)} · {h.source}</span>
              </li>
            ))}
          </ul>
        )}
      </Panel>

      <div className="grid gap-4 sm:grid-cols-3">
        <Panel pad="sm">
          <p className="eyebrow">Open mistakes</p>
          <p className="title-poster mt-2 text-4xl">{s.open_mistakes}</p>
        </Panel>
        <Panel pad="sm">
          <p className="eyebrow">Reviews due</p>
          <p className="title-poster mt-2 text-4xl">{s.due_reviews}</p>
        </Panel>
        <Panel pad="sm">
          <p className="eyebrow">Weekly trials</p>
          <p className="title-poster mt-2 text-4xl">0</p>
        </Panel>
      </div>
    </div>
  );
}

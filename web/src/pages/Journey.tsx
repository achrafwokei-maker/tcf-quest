import { useAsync } from "../lib/useAsync";
import { journeyApi } from "../lib/journey";
import { ContinueCard } from "../components/ContinueCard";
import { JourneyRoad } from "../components/JourneyRoad";
import { ErrorNote, Loading, Panel } from "../components/ui";

/** Mon Aventure: one road from the first day to the TCF Canada. Tap any open checkpoint to start it. */
export function Journey() {
  const [state, reload] = useAsync(journeyApi.map);
  if (state.status === "loading") return <div className="px-5"><Loading /></div>;
  if (state.status === "error") return <div className="p-5"><ErrorNote error={state.error} onRetry={reload} /></div>;
  const j = state.data;
  return (
    <div className="space-y-6 px-4 pt-6 sm:px-8">
      <header className="text-center">
        <p className="eyebrow">Mon Aventure · {Math.round(j.progress * 100)} %</p>
        <h1 className="title-poster mt-1 text-4xl sm:text-5xl">{j.destination}</h1>
      </header>
      <Panel className="mx-auto max-w-xl"><ContinueCard compact /></Panel>
      <JourneyRoad chapters={j.chapters} current={j.current_chapter} sideMissions={j.side_missions} />
      <p className="mx-auto max-w-xl pb-6 text-center text-xs font-semibold text-ink-faint">{j.cefr_note} {j.label}</p>
    </div>
  );
}

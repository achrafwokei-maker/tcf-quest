import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Compass, MapPin } from "lucide-react";
import { useAsync } from "../lib/useAsync";
import { journeyApi, openNode } from "../lib/journey";
import { Button, Loading } from "./ui";

/** The single primary action: where I am, why it matters, what's next, and one button. */
export function ContinueCard({ compact = false }: { compact?: boolean }) {
  const navigate = useNavigate();
  const [state] = useAsync(journeyApi.continue);
  const [error, setError] = useState<string | null>(null);
  if (state.status === "loading") return <Loading />;
  if (state.status === "error") return null;
  const c = state.data;
  async function go() {
    if (!c.node) return navigate("/entrainement");
    try { await openNode(c.node, navigate); } catch (e) { setError((e as Error).message); }
  }
  return (
    <section aria-labelledby="continue-h" className="space-y-3">
      <div className="flex items-start gap-3">
        <span className="tile grid size-12 shrink-0 place-items-center rounded-[16px] [--tile:var(--gold)]"><Compass aria-hidden className="size-6" /></span>
        <div className="min-w-0 flex-1">
          <p className="flex items-center gap-1 text-xs font-extrabold uppercase tracking-wider text-ink-faint">
            <MapPin aria-hidden className="size-3.5" /> {c.where}
          </p>
          <h2 id="continue-h" className={compact ? "text-xl" : "title-poster mt-1 text-3xl sm:text-4xl"}>
            {c.node ? c.node.title : "Free practice"}
            {c.node && <span className="ml-2 align-middle text-sm font-bold text-ink-faint">≈ {c.node.minutes} min</span>}
          </h2>
          <p className="mt-1 text-sm text-ink-soft"><span className="font-extrabold text-ink">Why: </span>{c.why}</p>
          {c.next && <p className="text-xs font-bold text-ink-faint">Then: {c.next}</p>}
        </div>
      </div>
      <Button onClick={go} className="w-full text-lg sm:w-auto">
        Continuer mon parcours <ArrowRight aria-hidden className="size-5" />
      </Button>
      {error && <p className="text-sm font-semibold text-danger">{error}</p>}
      <div className="h-2 overflow-hidden rounded-full bg-surface-2" role="progressbar" aria-label="Journey progress"
        aria-valuenow={Math.round(c.progress * 100)} aria-valuemin={0} aria-valuemax={100}>
        <div className="h-full rounded-full bg-[var(--gold)]" style={{ width: `${Math.round(c.progress * 100)}%` }} />
      </div>
    </section>
  );
}

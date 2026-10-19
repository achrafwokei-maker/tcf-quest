import { useEffect, useState } from "react";
import { RotateCcw } from "lucide-react";
import { Button, Panel } from "./ui";

interface Budget { limited: boolean; resting?: boolean }

/** AI feedback failed. Online, that's usually today's free allowance: say so instead of blaming Ollama. */
export function AiFailedNote({ what, onRetry }: { what: string; onRetry: () => void }) {
  const [budget, setBudget] = useState<Budget | null>(null);
  useEffect(() => { fetch("/api/ai/budget").then((r) => r.json()).then(setBudget).catch(() => setBudget(null)); }, []);
  const resting = budget?.limited && budget.resting;
  return (
    <Panel pad="sm" className="flex flex-wrap items-center gap-3">
      <p className="flex-1 font-semibold">
        {resting
          ? `Your ${what} is saved. Today's free AI feedback is used up; it comes back tomorrow (UTC midnight). Everything else still works.`
          : budget?.limited
            ? `Your ${what} is saved, but the AI couldn't give feedback just now.`
            : `Your ${what} is saved, but the local AI couldn't give feedback (is Ollama running?).`}
      </p>
      {!resting && <Button variant="secondary" onClick={onRetry}><RotateCcw aria-hidden className="size-4" /> Try again</Button>}
    </Panel>
  );
}

import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { NotebookPen, RotateCcw, Sparkles, Timer, Zap } from "lucide-react";
import { exercisesApi, type MissionReport } from "../../lib/exercises";
import { Button, Loading, Meter, Panel } from "../ui";

/** End of a mission or review session: effort (XP, minutes) and evidence (competencies) kept apart. */
export function MissionReportView({ setId, isReview, summary, onContinue, onAgain }: {
  setId: string; isReview: boolean; summary: { items: number; correct_first_try: number };
  onContinue: () => void; onAgain?: () => void;
}) {
  const reduce = useReducedMotion();
  const [report, setReport] = useState<MissionReport | null>(null);

  useEffect(() => {
    exercisesApi.report(setId).then(setReport, () => setReport(null));
  }, [setId]);

  return (
    <div className="mx-auto flex min-h-dvh max-w-xl flex-col gap-5 px-5 py-10">
      <div className="flex flex-col items-center gap-4 text-center">
        <motion.div initial={reduce ? false : { scale: 0.6, rotate: -10, opacity: 0 }} animate={{ scale: 1, rotate: 0, opacity: 1 }}
          transition={{ type: "spring", stiffness: 260, damping: 16 }}
          className="tile grid size-24 place-items-center rounded-[30px] [--tile:var(--gold)]">
          <Sparkles aria-hidden className="size-12" />
        </motion.div>
        <h1 className="title-poster text-5xl">{isReview ? "Révisions faites !" : "Mission accomplie !"}</h1>
        <p className="text-lg font-bold text-ink-soft">{summary.correct_first_try} sur {summary.items} du premier coup.</p>
      </div>

      {!report ? <Loading /> : (
        <>
          <div className="grid grid-cols-3 gap-3">
            <Stat icon={Zap} color="var(--gold)" value={`+${report.xp}`} label="XP" />
            <Stat icon={Timer} color="var(--blue)" value={`${report.minutes}`} label="min" />
            <Stat icon={NotebookPen} color="var(--orange)" value={`${report.mistakes_in_notebook}`} label={isReview ? "still to review" : "to review"} />
          </div>
          <Panel pad="sm">
            <p className="eyebrow">Skills practised</p>
            <p className="text-xs font-semibold text-ink-faint">XP rewards effort. These bars move only with correct answers over several days.</p>
            <ul className="mt-3 space-y-3">
              {report.competencies.map((c) => (
                <li key={c.id}>
                  <div className="mb-1 flex justify-between text-sm font-bold">
                    <span>{c.id}</span>
                    <span className="text-ink-faint">{c.mastered ? "Mastered" : `${Math.round(c.p_known * 100)}%`}</span>
                  </div>
                  <Meter value={Math.round(c.p_known * 100)} max={100} label={c.id} color={c.mastered ? "var(--green)" : "var(--violet)"} />
                </li>
              ))}
            </ul>
          </Panel>
          {report.mistakes_in_notebook > 0 && (
            <p className="text-center text-sm font-semibold text-ink-soft">
              {isReview ? "Each one is scheduled again in your notebook, further apart every time you get it right."
                : "Your mistakes are in your notebook. They come back as short reviews from tomorrow."}
            </p>
          )}
        </>
      )}

      <div className="mt-2 flex flex-wrap justify-center gap-3">
        {onAgain && <Button variant="secondary" onClick={onAgain}><RotateCcw aria-hidden className="size-4" /> Play again</Button>}
        <Button onClick={onContinue}>Continuer</Button>
      </div>
    </div>
  );
}

function Stat({ icon: Icon, color, value, label }: { icon: typeof Zap; color: string; value: string; label: string }) {
  return (
    <Panel pad="sm" className="flex flex-col items-center text-center">
      <Icon aria-hidden className="size-5" style={{ color }} />
      <p className="title-poster mt-1 text-3xl">{value}</p>
      <p className="text-xs font-extrabold text-ink-faint">{label}</p>
    </Panel>
  );
}

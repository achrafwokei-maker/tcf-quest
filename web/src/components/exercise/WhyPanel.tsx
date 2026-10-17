import { useEffect, useRef, useState } from "react";
import { Check, MessageCircle, X } from "lucide-react";
import { exercisesApi, tcfLabel, type WhyInfo } from "../../lib/exercises";
import { Badge, Loading, cx } from "../ui";

/**
 * "Why?" panel: the full explanation of an answered item.
 * Asking the tutor about it needs the local AI and arrives with the AI milestone.
 */
export function WhyPanel({ setId, itemId, onClose }: { setId: string; itemId: string; onClose: () => void }) {
  const [info, setInfo] = useState<WhyInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const close = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    exercisesApi.why(setId, itemId).then(setInfo, (e: Error) => setError(e.message));
  }, [setId, itemId]);

  useEffect(() => {
    close.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "Enter") e.stopPropagation();
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 grid place-items-end bg-black/45 p-0 backdrop-blur-sm sm:place-items-center sm:p-6" onClick={onClose}>
      <div role="dialog" aria-modal="true" aria-labelledby="why-title" onClick={(e) => e.stopPropagation()}
        className="card max-h-[85dvh] w-full max-w-xl overflow-y-auto rounded-b-none p-6 sm:rounded-b-[26px]">
        <div className="flex items-start justify-between gap-3">
          <h2 id="why-title" className="title-poster text-4xl">Pourquoi ?</h2>
          <button ref={close} type="button" onClick={onClose} aria-label="Close"
            className="grid size-10 place-items-center rounded-full text-ink-faint hover:bg-surface-2 hover:text-ink">
            <X aria-hidden className="size-5" />
          </button>
        </div>

        {error && <p role="alert" className="mt-3 font-bold text-danger">{error}</p>}
        {!info && !error && <Loading />}
        {info && (
          <div className="mt-3 space-y-5">
            <div className="flex flex-wrap gap-1.5">
              <Badge tone="accent">Prépare : {tcfLabel(info.tcf_target)}</Badge>
              {info.competencies.map((c) => <Badge key={c}>{c}</Badge>)}
            </div>
            <p className="text-sm font-semibold text-ink-soft">{info.tcf_target.purpose}</p>

            <div>
              <p className="eyebrow">Answer</p>
              <p className="text-lg font-extrabold">{info.correct_answer}</p>
              {info.also_accepted && info.also_accepted.length > 0 && (
                <p className="text-sm text-ink-soft">Also accepted: {info.also_accepted.join(" · ")}</p>
              )}
            </div>

            {info.explanation && (
              <div>
                <p className="eyebrow">The rule</p>
                <p>{info.explanation}</p>
              </div>
            )}

            {info.options && (
              <div>
                <p className="eyebrow mb-2">Each option</p>
                <ul className="space-y-2">
                  {info.options.map((o) => (
                    <li key={o.text} className={cx("rounded-[16px] border-2 px-4 py-2.5", o.correct ? "border-success/60 bg-success/8" : "border-line")}>
                      <p className="flex items-center gap-2 font-extrabold">
                        {o.correct && <Check aria-hidden className="size-4 text-success" strokeWidth={3} />}{o.text}
                      </p>
                      <p className="text-sm text-ink-soft">{o.explanation}</p>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {info.transcript && (
              <div>
                <p className="eyebrow">Transcript</p>
                <p className="italic">« {info.transcript} »</p>
              </div>
            )}

            <div className="rounded-[16px] bg-surface-2 p-4">
              <p className="flex items-center gap-2 font-extrabold"><MessageCircle aria-hidden className="size-4" /> Ask Céleste</p>
              <p className="text-sm text-ink-soft">Follow-up questions to the tutor need the local AI. They arrive with the AI milestone.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Volume2 } from "lucide-react";
import { MicRecorder } from "../components/MicRecorder";
import { EOTaskList } from "./EOPage";
import { speak } from "../lib/speak";
import { Badge, Button, Panel, cx } from "../components/ui";

// Short sentences learners need for speaking tasks 2 and 3 (original).
const SENTENCES = [
  { fr: "Bonjour, je vous appelle au sujet de votre annonce.", task: "EO-T2" },
  { fr: "Pourriez-vous me dire à quelle heure le magasin ouvre ?", task: "EO-T2" },
  { fr: "Est-ce que la livraison est comprise dans le prix ?", task: "EO-T2" },
  { fr: "Je voudrais savoir s'il reste encore des places.", task: "EO-T2" },
  { fr: "À mon avis, le télétravail présente plus d'avantages que d'inconvénients.", task: "EO-T3" },
  { fr: "Cependant, il faut reconnaître que cette solution coûte cher.", task: "EO-T3" },
];

interface Compared { words: { word: string; found: boolean }[]; ratio: number }

/** Expression orale: microphone check and repeat-after-me (content check, not a pronunciation score). */
export function SpeakingPage() {
  const [heard, setHeard] = useState<string | null>(null);
  const [i, setI] = useState(0);
  const [compared, setCompared] = useState<Compared | null>(null);
  const s = SENTENCES[i];

  async function check(text: string) {
    const r = await fetch("/api/speech/compare", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target: s.fr, heard: text }) });
    setCompared(await r.json());
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-5 pt-6 pb-10 sm:px-10">
      <Link to="/entrainement" className="inline-flex items-center gap-1 text-sm font-extrabold text-ink-soft hover:text-ink">
        <ArrowLeft aria-hidden className="size-4" /> Entraînement
      </Link>
      <header>
        <p className="eyebrow">Expression orale</p>
        <h1 className="title-poster mt-1 text-5xl sm:text-6xl">Speaking check</h1>
        <p className="mt-2 font-semibold text-ink-soft">
          Test your microphone, then repeat useful sentences. The app shows which words the recogniser understood.
          That's a check of content, not a pronunciation score: background noise and the recogniser itself also play a part.
        </p>
      </header>

      <Panel>
        <h2 className="text-xl">The three speaking tasks, with an AI examiner</h2>
        <p className="mb-3 text-sm text-ink-soft">Real timings: task 1 in 2 min, task 2 with 2 min of preparation then 3 min 30, task 3 in 4 min 30.</p>
        <EOTaskList />
      </Panel>

      <Panel>
        <h2 className="text-xl">1 · Microphone check</h2>
        <p className="text-sm text-ink-soft">Say: « Bonjour, je m'appelle… et je prépare le TCF Canada. »</p>
        <div className="mt-3"><MicRecorder onResult={(r) => setHeard(r.text)} maxSeconds={20} /></div>
        {heard !== null && <p className="mt-3 rounded-[14px] bg-surface-2 p-3"><span className="eyebrow">Understood</span><br />{heard || "—"}</p>}
      </Panel>

      <Panel>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-xl">2 · Repeat after me</h2>
          <Badge>{i + 1} / {SENTENCES.length} · {s.task}</Badge>
        </div>
        <div className="mt-3 flex items-center gap-3">
          <Button variant="secondary" onClick={() => speak(s.fr, { speaker: "Céleste" })} aria-label="Hear the sentence">
            <Volume2 aria-hidden className="size-4" />
          </Button>
          <p className="text-xl font-extrabold">{s.fr}</p>
        </div>
        <div className="mt-4">
          <MicRecorder key={i} onResult={(r) => void check(r.text)} maxSeconds={20} context="check" refId={`repeat-${i}`}
            prompt="Listen, then say the sentence" />
        </div>
        {compared && (
          <div className="mt-4 space-y-2">
            <p className="text-lg leading-relaxed">
              {compared.words.map((w, k) => (
                <span key={k} className={cx("mr-1.5 font-bold", w.found ? "text-success" : "text-ink-faint line-through")}>{w.word}</span>
              ))}
            </p>
            <p className="text-sm font-semibold text-ink-soft">
              {Math.round(compared.ratio * 100)} % of the words were understood.
              {compared.ratio < 1 && " Grey words weren't recognised: listen again and focus on them."}
            </p>
            <Button onClick={() => { setI((i + 1) % SENTENCES.length); setCompared(null); }}>Next sentence</Button>
          </div>
        )}
      </Panel>
    </div>
  );
}

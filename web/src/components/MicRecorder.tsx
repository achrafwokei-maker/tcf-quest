import { useEffect, useRef, useState } from "react";
import { Keyboard, Mic, Square, X } from "lucide-react";
import { micSupported, startRecording, STATUS_HELP, transcribe, type MicError, type Recording, type Transcript } from "../lib/recorder";
import { Button, Loading, cx } from "./ui";

const MIC_HELP: Record<MicError, string> = {
  denied: "Microphone access was refused. In your browser's address bar, allow the microphone for localhost, then try again. Or type your answer.",
  no_device: "No microphone found. Plug one in, or type your answer.",
  unsupported: "This browser can't record audio. Type your answer instead.",
  failed: "The microphone couldn't start. Try again, or type your answer.",
};

/** Press to record, press to stop → local transcription. Always offers a typed fallback.
 *  `onResult` receives the final text (recognised, corrected or typed) and how it was produced. */
export function MicRecorder({ onResult, maxSeconds = 120, context = "check", refId, prompt = "Press and speak in French" }: {
  onResult: (r: { text: string; source: "speech" | "corrected" | "typed"; transcript: Transcript | null }) => void;
  maxSeconds?: number; context?: string; refId?: string; prompt?: string;
}) {
  const [phase, setPhase] = useState<"idle" | "starting" | "recording" | "processing" | "review" | "typing">("idle");
  const [error, setError] = useState<MicError | null>(null);
  const [seconds, setSeconds] = useState(0);
  const [level, setLevel] = useState(0);
  const [result, setResult] = useState<Transcript | null>(null);
  const [text, setText] = useState("");
  const rec = useRef<Recording | null>(null);

  useEffect(() => () => rec.current?.cancel(), []);
  useEffect(() => {
    if (phase !== "recording") return;
    const tick = setInterval(() => setSeconds((s) => s + 1), 1000);
    const meter = setInterval(() => setLevel(rec.current?.level() ?? 0), 80);
    return () => { clearInterval(tick); clearInterval(meter); };
  }, [phase]);
  useEffect(() => {
    if (phase === "recording" && seconds >= maxSeconds) void stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seconds, phase, maxSeconds]);

  async function start() {
    setError(null); setResult(null); setSeconds(0); setPhase("starting");
    try {
      rec.current = await startRecording();
      setPhase("recording");
    } catch (e) {
      setError(typeof e === "string" ? (e as MicError) : "failed");
      setPhase("idle");
    }
  }

  async function stop() {
    if (!rec.current) return;
    setPhase("processing");
    try {
      const wav = await rec.current.stop();
      rec.current = null;
      const t = await transcribe(wav, context, refId);
      setResult(t);
      setText(t.text);
      setPhase("review");
    } catch {
      setError("failed");
      setPhase("idle");
    }
  }

  async function confirm() {
    const typed = phase === "typing";
    const edited = !typed && result !== null && text.trim() !== result.text.trim();
    if (result && (edited || typed)) {
      await fetch(`/api/speech/recordings/${result.recording_id}`, {
        method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text }) }).catch(() => undefined);
    }
    onResult({ text: text.trim(), source: typed ? "typed" : edited ? "corrected" : "speech", transcript: result });
    setPhase("idle"); setResult(null); setText("");
  }

  const canRecord = micSupported();
  return (
    <div className="space-y-3">
      {(phase === "idle" || phase === "starting" || phase === "recording") && (
        <div className="flex flex-wrap items-center gap-4">
          <button type="button" onClick={phase === "recording" ? stop : start} disabled={!canRecord || phase === "starting"}
            aria-label={phase === "recording" ? "Stop recording" : "Start recording"}
            className={cx("tile relative grid size-20 place-items-center rounded-full transition-transform hover:scale-105 disabled:opacity-40",
              phase === "recording" ? "[--tile:var(--red)]" : "[--tile:var(--pink)]")}>
            {phase === "recording"
              ? <><span aria-hidden className="absolute inset-0 rounded-full ring-4 ring-[var(--red)]/40" style={{ transform: `scale(${1 + level * 0.35})` }} />
                <Square aria-hidden className="size-8 fill-current" /></>
              : <Mic aria-hidden className="size-9" />}
          </button>
          <div className="min-w-0 flex-1">
            <p className="font-extrabold" aria-live="polite">
              {phase === "recording" ? `Recording… ${seconds}s (press to stop)` : phase === "starting" ? "Opening the microphone…" : prompt}
            </p>
            <p className="text-xs font-semibold text-ink-faint">Recorded and transcribed on your Mac only.</p>
          </div>
          <Button variant="quiet" onClick={() => { rec.current?.cancel(); setPhase("typing"); setText(""); }}>
            <Keyboard aria-hidden className="size-4" /> Type instead
          </Button>
        </div>
      )}
      {error && <p className="rounded-[14px] bg-warning/12 px-3 py-2 text-sm font-semibold">{MIC_HELP[error]}</p>}
      {phase === "processing" && <Loading label="Transcribing on your Mac…" />}
      {(phase === "review" || phase === "typing") && (
        <div className="space-y-2">
          {result && result.status !== "ok" && <p className="rounded-[14px] bg-warning/12 px-3 py-2 text-sm font-semibold">{STATUS_HELP[result.status]}</p>}
          <label className="block">
            <span className="eyebrow">{phase === "typing" ? "Type your answer" : "What was understood (you can correct it)"}</span>
            <textarea value={text} onChange={(e) => setText(e.target.value)} lang="fr" rows={3} autoFocus={phase === "typing"}
              className="mt-1 w-full rounded-[16px] border-2 border-line bg-surface p-3 text-lg focus:border-violet focus:outline-none" />
          </label>
          {result?.status === "ok" && <p className="text-xs font-semibold text-ink-faint">Recogniser confidence {Math.round(result.confidence * 100)} % — about the machine, not your pronunciation.</p>}
          <div className="flex flex-wrap justify-end gap-2">
            <Button variant="quiet" onClick={() => { setPhase("idle"); setResult(null); }}><X aria-hidden className="size-4" /> Discard</Button>
            {canRecord && phase === "review" && <Button variant="secondary" onClick={start}><Mic aria-hidden className="size-4" /> Record again</Button>}
            <Button onClick={confirm} disabled={!text.trim()}>Use this answer</Button>
          </div>
        </div>
      )}
    </div>
  );
}

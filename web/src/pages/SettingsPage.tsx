import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Check, Headphones, Play, Snail, Square, Star } from "lucide-react";
import { useAsync } from "../lib/useAsync";
import { setVoiceSettings, speak, stopSpeaking, type VoiceSettings } from "../lib/speak";
import { Badge, Button, ErrorNote, Loading, Panel, cx } from "../components/ui";
import { ThemeChoice } from "../components/ThemeSwitch";
import { AccountPanel } from "../components/AccountPanel";

interface Voice {
  id: string; label: string; gender: "female" | "male"; native: boolean; licence: string;
  cer: number; speed: "native" | "playback"; engine: "pocket" | "piper"; available: boolean;
}
interface VoicesPayload {
  worker_running: boolean; voices: Voice[]; characters: Record<string, string>; settings: VoiceSettings;
}

const SAMPLE = "Bonjour ! Je vous appelle au sujet de la livraison de vendredi. Pourriez-vous me dire à quelle heure le camion arrive ? Merci beaucoup, et bonne journée.";
const SLOTS = [
  { slot: "female", title: "Female voice", who: "Madame Roux, Céleste", gender: "female" },
  { slot: "male", title: "Male voice", who: "M. Delaunay", gender: "male" },
  { slot: "narrator", title: "Narrator", who: "Narratrice, listening stories", gender: null },
] as const;

const fetchVoices = async (): Promise<VoicesPayload> => {
  const r = await fetch("/api/voices");
  if (!r.ok) throw new Error("The local server is not running.");
  return r.json();
};

async function save(changes: Record<string, unknown>): Promise<VoiceSettings> {
  const r = await fetch("/api/voices/settings", {
    method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(changes),
  });
  const s = await r.json();
  setVoiceSettings(s);
  return s;
}

/** Réglages: Voice Studio (voices per character, speed, slow listening mode, listening ratings). */
export function SettingsPage() {
  const [state, reload] = useAsync(fetchVoices);
  const [s, setS] = useState<VoiceSettings | null>(null);
  const [playing, setPlaying] = useState<string | null>(null);
  if (state.status === "loading") return <div className="px-5"><Loading /></div>;
  if (state.status === "error") return <div className="p-5"><ErrorNote error={state.error} onRetry={reload} /></div>;
  const data = state.data;
  const settings = s ?? data.settings;
  const update = async (changes: Record<string, unknown>) => setS(await save(changes));

  async function preview(voice: string, rate?: number) {
    if (playing === voice) {
      stopSpeaking();
      setPlaying(null);
      return;
    }
    setPlaying(voice);
    await speak(SAMPLE, { voice, rate: rate ?? (settings.slow_mode ? settings.slow_speed : settings.speed) });
    setPlaying((p) => (p === voice ? null : p));
  }

  return (
    <div className="space-y-6 px-5 pt-6 sm:px-10 sm:pt-10">
      <Link to="/" className="inline-flex items-center gap-1 text-sm font-extrabold text-ink-soft hover:text-ink">
        <ArrowLeft aria-hidden className="size-4" /> Aujourd'hui
      </Link>
      <header>
        <p className="eyebrow">Réglages</p>
        <h1 className="title-poster mt-1 text-5xl sm:text-6xl">Settings</h1>
        <p className="mt-2 max-w-2xl font-semibold text-ink-soft">
          Pick the French voices you'll hear in missions. Each character keeps the same voice. Everything runs on your Mac, for free.
        </p>
      </header>

      <AccountPanel />

      <Panel>
        <h2 className="text-xl">Appearance</h2>
        <p className="mb-3 text-sm text-ink-soft">Day or night colours. Exam screens follow the same choice.</p>
        <ThemeChoice />
      </Panel>

      {!data.worker_running && (
        <Panel className="border-2 border-warning/40">
          <p className="font-extrabold">The natural voices are not running.</p>
          <p className="text-sm font-semibold text-ink-soft">You'll hear your Mac's built-in voice instead. Restart the app with <code>scripts/dev.sh</code> to start them.</p>
        </Panel>
      )}

      <Panel>
        <h2 className="text-xl">Speed</h2>
        <div className="mt-3 grid gap-5 sm:grid-cols-2">
          <SpeedControl label="Training speed" hint="Used everywhere by default." value={settings.speed} min={0.8} max={1.2}
            onChange={(v) => update({ speed: v })} />
          <SpeedControl label="Slow listening speed" hint="For listening practice." value={settings.slow_speed} min={0.8} max={1}
            onChange={(v) => update({ slow_speed: v })} />
        </div>
        <label className="mt-5 flex cursor-pointer items-center gap-3 rounded-[18px] bg-surface-2 p-4">
          <input type="checkbox" className="size-5 shrink-0 accent-[var(--violet)]" checked={settings.slow_mode}
            onChange={(e) => update({ slow_mode: e.target.checked })} />
          <Snail aria-hidden className="size-5 shrink-0 text-ink-soft" />
          <span>
            <span className="block font-extrabold">Slow listening mode</span>
            <span className="block text-sm font-semibold text-ink-soft">Every voice uses the slow speed until you switch it off. The real exam is at normal speed.</span>
          </span>
        </label>
      </Panel>

      {SLOTS.map(({ slot, title, who, gender }) => (
        <section key={slot} aria-labelledby={`${slot}-h`}>
          <div className="flex flex-wrap items-baseline gap-2">
            <h2 id={`${slot}-h`} className="text-xl">{title}</h2>
            <span className="text-sm font-semibold text-ink-faint">{who}</span>
          </div>
          <ul className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data.voices.filter((v) => !gender || v.gender === gender).map((v) => (
              <VoiceCard key={v.id} v={v} chosen={settings[slot] === v.id} playing={playing === v.id}
                rating={settings.ratings[v.id] ?? 0}
                onChoose={() => update({ [slot]: v.id })} onPreview={() => preview(v.id)}
                onRate={(n) => update({ rating: [v.id, n] })} />
            ))}
          </ul>
        </section>
      ))}

      <Panel look="glass" pad="sm" className="text-sm font-semibold text-ink-soft">
        <p className="flex items-center gap-2 font-extrabold text-ink"><Headphones aria-hidden className="size-4" /> How to judge a voice</p>
        <p className="mt-1">
          Listen with headphones. 5 = sounds like a real French speaker. 4 = natural, small flaws. 3 = clear but a bit robotic or accented.
          Voices marked “English speaker” were recorded in English and may carry an accent in French; trust your ears.
        </p>
      </Panel>
    </div>
  );
}

function SpeedControl({ label, hint, value, min, max, onChange }: {
  label: string; hint: string; value: number; min: number; max: number; onChange: (v: number) => void;
}) {
  const [v, setV] = useState(value);
  return (
    <label className="block">
      <span className="flex justify-between font-extrabold"><span>{label}</span><span>{v.toFixed(2)}×</span></span>
      <input type="range" min={min} max={max} step={0.05} value={v} className="mt-2 w-full accent-[var(--violet)]"
        onChange={(e) => setV(Number(e.target.value))} onPointerUp={() => onChange(v)} onKeyUp={() => onChange(v)} />
      <span className="text-xs font-semibold text-ink-faint">{hint}</span>
    </label>
  );
}

function VoiceCard({ v, chosen, playing, rating, onChoose, onPreview, onRate }: {
  v: Voice; chosen: boolean; playing: boolean; rating: number;
  onChoose: () => void; onPreview: () => void; onRate: (n: number) => void;
}) {
  return (
    <li className={cx("card flex flex-col gap-3 p-4", chosen && "ring-2 ring-violet")}>
      <div className="flex items-start gap-3">
        <button type="button" onClick={onPreview} disabled={!v.available} aria-label={playing ? `Stop ${v.label}` : `Preview ${v.label}`}
          className="tile grid size-12 shrink-0 place-items-center rounded-full disabled:opacity-40 [--tile:var(--blue)]">
          {playing ? <Square aria-hidden className="size-5 fill-current" /> : <Play aria-hidden className="size-5 fill-current" />}
        </button>
        <div className="min-w-0 flex-1">
          <p className="text-lg font-extrabold">{v.label}</p>
          <div className="mt-1 flex flex-wrap gap-1">
            <Badge tone={v.native ? "success" : "warning"}>{v.native ? "French speaker" : "English speaker"}</Badge>
            <Badge>{v.engine === "pocket" ? "Pocket TTS" : "Piper"}</Badge>
          </div>
        </div>
      </div>
      <div className="flex items-center gap-0.5" role="radiogroup" aria-label={`Your rating for ${v.label}`}>
        {[1, 2, 3, 4, 5].map((n) => (
          <button key={n} type="button" role="radio" aria-checked={rating === n} aria-label={`${n} out of 5`} onClick={() => onRate(n)}
            className="rounded p-0.5 text-ink-faint hover:text-gold">
            <Star aria-hidden className={cx("size-5", n <= rating && "fill-gold text-gold")} />
          </button>
        ))}
        <span className="ml-2 text-xs font-bold text-ink-faint">{rating ? `${rating}/5` : "Not rated"}</span>
      </div>
      <p className="text-xs font-semibold text-ink-faint">{v.licence}{!v.available && " · not installed"}</p>
      <Button variant={chosen ? "secondary" : "primary"} onClick={onChoose} disabled={chosen || !v.available} className="min-h-10">
        {chosen ? <><Check aria-hidden className="size-4" /> In use</> : "Use this voice"}
      </Button>
    </li>
  );
}

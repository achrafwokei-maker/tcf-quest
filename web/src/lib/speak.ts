// French speech. First choice: natural local voices (Pocket TTS / Piper) from the API, with the
// text normalised on the server ("/" is never read as "slash"). Fallback: the browser voice,
// reading the same normalised text, with the least robotic French voice available.

export interface VoiceSettings {
  female: string;
  male: string;
  narrator: string;
  speed: number;        // normal training speed, 0.8–1.2
  slow_speed: number;   // listening-practice mode
  slow_mode: boolean;
  ratings: Record<string, number>;
}

export interface SpeakOptions {
  speaker?: string;     // a character name: that character's voice
  voice?: string;       // an explicit voice id (Voice Studio previews)
  rate?: number;        // overrides the saved speed (e.g. the "Slower" button)
}

let settings: VoiceSettings | null = null;
let current: HTMLAudioElement | null = null;
let currentUrl: string | null = null;
let token = 0;

export function setVoiceSettings(s: VoiceSettings) {
  settings = s;
}

async function loadSettings(): Promise<VoiceSettings | null> {
  if (settings) return settings;
  try {
    const r = await fetch("/api/voices");
    if (r.ok) settings = (await r.json()).settings;
  } catch { /* offline: defaults */ }
  return settings;
}

/** The speed to use when the caller doesn't force one: slow listening mode or normal speed. */
export async function preferredRate(): Promise<number> {
  const s = await loadSettings();
  if (!s) return 1;
  return s.slow_mode ? s.slow_speed : s.speed;
}

export function speechAvailable(): boolean {
  return typeof window !== "undefined" && (typeof Audio !== "undefined" || "speechSynthesis" in window);
}

export function stopSpeaking() {
  token++;
  if (current) {
    current.pause();
    current = null;
  }
  if (currentUrl) {
    URL.revokeObjectURL(currentUrl);
    currentUrl = null;
  }
  if (typeof window !== "undefined" && "speechSynthesis" in window) window.speechSynthesis.cancel();
}

/** Speak French text; resolves when finished (or "failed" if no voice could play it). */
export async function speak(text: string, opts: SpeakOptions = {}): Promise<"ended" | "failed"> {
  stopSpeaking();
  const mine = token;
  const rate = opts.rate ?? (await preferredRate());
  const local = await playLocal(text, opts, rate, mine);
  if (local !== "unavailable") return local;
  if (mine !== token) return "ended";
  return speakBrowser(await spokenText(text), rate);
}

async function playLocal(text: string, opts: SpeakOptions, rate: number, mine: number): Promise<"ended" | "failed" | "unavailable"> {
  let res: Response;
  try {
    res = await fetch("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, speaker: opts.speaker, voice: opts.voice, speed: rate }),
    });
  } catch {
    return "unavailable";
  }
  if (!res.ok) return "unavailable";
  const blob = await res.blob();
  if (mine !== token) return "ended";                       // something else started meanwhile
  const url = URL.createObjectURL(blob);
  const el = new Audio(url);
  // Piper slows down natively; Pocket is slowed by the player, keeping the pitch (no "monster voice").
  if (res.headers.get("X-Speed-Applied") !== "1") {
    el.preservesPitch = true;
    el.playbackRate = rate;
  }
  current = el;
  currentUrl = url;
  try {
    await el.play();
  } catch {
    return "unavailable";
  }
  await new Promise<void>((r) => {
    el.onended = () => r();
    el.onpause = () => r();
    el.onerror = () => r();
  });
  return "ended";
}

async function spokenText(text: string): Promise<string> {
  try {
    const r = await fetch("/api/tts/text", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text }),
    });
    if (r.ok) return (await r.json()).spoken;
  } catch { /* server down: minimal local clean-up */ }
  return text.replace(/[*_#`«»]/g, "").replace(/\s*\/\s*/g, " ou ").replace(/…/g, ", ");
}

// Browser fallback: avoid the novelty/robotic macOS voices (Eddy, Flo, Grandpa…), prefer premium ones.
const ROBOTIC = /eddy|flo|grandma|grandpa|reed|rocko|sandy|shelley|jacques/i;

export function bestBrowserVoice(voices: SpeechSynthesisVoice[]): SpeechSynthesisVoice | null {
  const fr = voices.filter((v) => v.lang.replace("_", "-").startsWith("fr"));
  const score = (v: SpeechSynthesisVoice) =>
    (/premium|enhanced|amélioré|natural|neural/i.test(v.name) ? 100 : 0) +
    (v.lang.replace("_", "-") === "fr-FR" ? 10 : 0) +
    (/thomas|amélie|audrey|aurélie|marie|virginie/i.test(v.name) ? 20 : 0) +
    (ROBOTIC.test(v.name) ? -50 : 0) +
    (v.localService ? 1 : 0);
  return fr.sort((a, b) => score(b) - score(a))[0] ?? null;
}

function speakBrowser(text: string, rate: number): Promise<"ended" | "failed"> {
  return new Promise((resolve) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return resolve("failed");
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "fr-FR";
    u.rate = rate;
    const voice = bestBrowserVoice(window.speechSynthesis.getVoices());
    if (voice) u.voice = voice;
    u.onend = () => resolve("ended");
    u.onerror = () => resolve("failed");
    window.speechSynthesis.speak(u);
  });
}

/** Listening items: a pre-recorded file if present, else a local voice. */
export async function playAudio(audio: { text: string; file: string | null; speaker?: string | null }, rate?: number) {
  if (audio.file) {
    try {
      stopSpeaking();
      const el = new Audio(audio.file);
      el.preservesPitch = true;
      el.playbackRate = rate ?? (await preferredRate());
      current = el;
      await el.play();
      await new Promise<void>((r) => (el.onended = () => r()));
      return "ended" as const;
    } catch {
      /* fall back to a voice */
    }
  }
  return speak(audio.text, { speaker: audio.speaker ?? undefined, rate });
}

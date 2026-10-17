import { useState } from "react";
import { Check } from "lucide-react";
import type { AvatarAnswers } from "../lib/api";
import { FACIAL_HAIR, GENDERS, HAIR, HAIR_COLOURS, SKIN_TONES, VIBES, avatarArt } from "../lib/avatar";
import { cx } from "./ui";

export const DEFAULT_AVATAR: AvatarAnswers = {
  gender: "unspecified", hair: "short", hair_colour: "brown", skin_tone: 3,
  facial_hair: "none", glasses: false, vibe: "street", description: "",
};

/** The avatar questions (reference 6 style). Controlled: parent owns the answers. */
export function AvatarForm({ value, onChange }: { value: AvatarAnswers; onChange: (v: AvatarAnswers) => void }) {
  const set = <K extends keyof AvatarAnswers>(k: K, v: AvatarAnswers[K]) => onChange({ ...value, [k]: v });

  return (
    <div className="space-y-6">
      <Group legend="You are">
        <Chips name="gender" options={GENDERS} value={value.gender} onPick={(v) => set("gender", v)} />
      </Group>

      <Group legend="Hair">
        <Chips name="hair" options={HAIR} value={value.hair} onPick={(v) => set("hair", v)} />
        {value.hair !== "bald" && (
          <div className="mt-3 flex flex-wrap gap-2" role="radiogroup" aria-label="Hair colour">
            {HAIR_COLOURS.map((c) => (
              <Swatch key={c.value} name="hair_colour" label={c.label} fill={c.swatch}
                checked={value.hair_colour === c.value} onPick={() => set("hair_colour", c.value)} />
            ))}
          </div>
        )}
      </Group>

      <Group legend="Skin tone">
        <div className="flex flex-wrap gap-2" role="radiogroup" aria-label="Skin tone">
          {SKIN_TONES.map((fill, i) => (
            <Swatch key={fill} name="skin_tone" label={`Tone ${i + 1}`} fill={fill}
              checked={value.skin_tone === i + 1} onPick={() => set("skin_tone", i + 1)} />
          ))}
        </div>
      </Group>

      <div className="grid gap-6 sm:grid-cols-2">
        <Group legend="Facial hair">
          <Chips name="facial_hair" options={FACIAL_HAIR} value={value.facial_hair} onPick={(v) => set("facial_hair", v)} />
        </Group>
        <Group legend="Glasses">
          <Chips name="glasses" options={[{ value: "no", label: "No" }, { value: "yes", label: "Yes" }] as const}
            value={value.glasses ? "yes" : "no"} onPick={(v) => set("glasses", v === "yes")} />
        </Group>
      </div>

      <Group legend="Your style">
        <Chips name="vibe" options={VIBES} value={value.vibe} onPick={(v) => set("vibe", v)} />
      </Group>

      <label className="block">
        <span className="font-extrabold">Describe yourself in a few lines</span>
        <span className="block text-sm text-ink-faint">Personality, hobbies, anything you want your character to show. Optional.</span>
        <textarea
          aria-label="Describe yourself in a few lines (optional)"
          value={value.description}
          maxLength={600}
          rows={3}
          onChange={(e) => set("description", e.target.value)}
          placeholder="Ex. Calm and curious, I love football and cooking, always with headphones on."
          className="mt-2 block w-full resize-y rounded-[18px] border-2 border-line bg-surface-2 px-4 py-3 outline-none focus:border-violet"
        />
        <span className="mt-1 block text-right text-xs font-bold text-ink-faint">{value.description.length} / 600</span>
      </label>
    </div>
  );
}

function Group({ legend, children }: { legend: string; children: React.ReactNode }) {
  return (
    <fieldset>
      <legend className="mb-2 font-extrabold">{legend}</legend>
      {children}
    </fieldset>
  );
}

function Chips<V extends string>({ name, options, value, onPick }: {
  name: string; options: readonly { value: V; label: string }[]; value: V; onPick: (v: V) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((o) => {
        const on = o.value === value;
        return (
          <label key={o.value}
            className={cx(
              "cursor-pointer rounded-full px-4 py-2 text-sm font-extrabold transition-all duration-[var(--dur-fast)]",
              "has-[:focus-visible]:outline-3 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-[var(--focus)]",
              on ? "tile [--tile:var(--violet)]" : "bg-surface-2 text-ink-soft hover:text-ink",
            )}>
            <input type="radio" name={name} checked={on} onChange={() => onPick(o.value)} className="sr-only" />
            {o.label}
          </label>
        );
      })}
    </div>
  );
}

function Swatch({ name, label, fill, checked, onPick }: {
  name: string; label: string; fill: string; checked: boolean; onPick: () => void;
}) {
  return (
    <label title={label}
      className={cx(
        "relative grid size-11 cursor-pointer place-items-center rounded-full ring-offset-2 ring-offset-[var(--surface)] transition-transform",
        "has-[:focus-visible]:ring-3 has-[:focus-visible]:ring-[var(--focus)]",
        checked ? "scale-110 ring-3 ring-violet" : "hover:scale-105",
      )}
      style={{ background: fill }}>
      <input type="radio" name={name} checked={checked} onChange={onPick} className="sr-only" aria-label={label} />
      {checked && <Check aria-hidden className="size-5 text-white drop-shadow" strokeWidth={3} />}
    </label>
  );
}

/** The avatar render for a skin, or a glossy silhouette until the image exists. */
export function AvatarImage({ skin, className, dark }: { skin: string; className?: string; dark?: boolean }) {
  const [missing, setMissing] = useState(false);
  if (missing) {
    const fill = dark ? "rgb(255 255 255 / 0.85)" : "var(--violet)";
    return (
      <svg viewBox="0 0 120 160" role="img" aria-label="Avatar placeholder" className={className}>
        <defs>
          <linearGradient id="av-g" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="white" stopOpacity=".45" />
            <stop offset=".5" stopColor="white" stopOpacity="0" />
          </linearGradient>
        </defs>
        <circle cx="60" cy="50" r="34" fill={fill} opacity=".9" />
        <path d="M14 160c3-44 22-64 46-64s43 20 46 64Z" fill={fill} opacity=".9" />
        <circle cx="60" cy="50" r="34" fill="url(#av-g)" />
      </svg>
    );
  }
  return <img src={avatarArt(skin)} alt="Your avatar" onError={() => setMissing(true)} className={cx("object-contain", className)} draggable={false} />;
}

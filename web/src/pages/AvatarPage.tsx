import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion, useReducedMotion } from "motion/react";
import { ArrowLeft, Check, Lock, Sparkles } from "lucide-react";
import { api, type AvatarAnswers, type AvatarState } from "../lib/api";
import { useAsync } from "../lib/useAsync";
import { avatarPrompt } from "../lib/avatar";
import { AvatarForm, AvatarImage, DEFAULT_AVATAR } from "../components/AvatarForm";
import { Badge, Button, ErrorNote, Loading, Panel, cx } from "../components/ui";

export function AvatarPage() {
  const [state, reload] = useAsync(api.avatar);
  if (state.status === "loading") return <div className="px-5"><Loading /></div>;
  if (state.status === "error") return <div className="p-5"><ErrorNote error={state.error} onRetry={reload} /></div>;
  return <AvatarEditor initial={state.data} />;
}

function AvatarEditor({ initial }: { initial: AvatarState }) {
  const reduce = useReducedMotion();
  const [data, setData] = useState(initial);
  const [answers, setAnswers] = useState<AvatarAnswers>(initial.avatar ?? DEFAULT_AVATAR);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const equipped = data.avatar?.equipped_skin ?? "a1";
  const current = data.skins.find((s) => s.id === equipped)!;

  useEffect(() => setSaved(false), [answers]);

  async function save() {
    setSaving(true);
    setError(null);
    try {
      setData(await api.saveAvatar(answers));
      setSaved(true);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  }

  async function equip(id: string) {
    try {
      setData(await api.equipSkin(id));
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="space-y-6 px-3 pt-3 sm:px-5 sm:pt-5">
      <Link to="/" className="inline-flex items-center gap-1 px-2 pt-2 text-sm font-extrabold text-ink-soft hover:text-ink">
        <ArrowLeft aria-hidden className="size-4" /> Today
      </Link>

      <div className="grid gap-5 lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)]">
        {/* Stage (references 1 and 6) */}
        <section className="night relative overflow-hidden rounded-[34px] p-6 sm:p-8">
          <div aria-hidden className="absolute -right-16 -top-16 size-64 rounded-full bg-pink/30 blur-3xl" />
          <p className="text-xs font-extrabold uppercase tracking-[0.14em] text-white/75">Mon avatar</p>
          <h1 className="title-poster mt-1 text-6xl sm:text-7xl">{current.name}</h1>
          <div className="mt-2 flex gap-2">
            <Badge tone="onDark">Skin {current.level}</Badge>
            <Badge tone="onDark">Your level: {data.reached_level}</Badge>
          </div>
          <motion.div key={equipped} className="relative mx-auto mt-4 h-80 w-60"
            initial={reduce ? false : { scale: 0.92, opacity: 0, y: 12 }} animate={{ scale: 1, opacity: 1, y: 0 }}
            transition={{ type: "spring", stiffness: 260, damping: 20 }}>
            <AvatarImage skin={equipped} dark className="h-full w-full drop-shadow-[0_20px_30px_rgb(0_0_0/0.45)]" />
          </motion.div>
          {!data.avatar && (
            <p className="mt-2 text-center text-sm font-bold text-white/80">Answer the questions to create your character.</p>
          )}
        </section>

        {/* Wardrobe (reference 6) */}
        <Panel look="glass">
          <h2 className="title-poster text-3xl">Garde-robe</h2>
          <p className="text-sm font-semibold text-ink-soft">
            A new outfit unlocks each time your <b>weakest skill</b> reaches the next French level. XP never unlocks skins.
          </p>
          <ul className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
            {data.skins.map((s) => {
              const on = s.id === equipped;
              return (
                <li key={s.id}>
                  <button type="button" disabled={!s.unlocked || !data.avatar} onClick={() => equip(s.id)}
                    aria-pressed={on}
                    aria-label={`${s.name}, ${s.level}${s.unlocked ? "" : ", locked"}`}
                    className={cx(
                      "card relative flex w-full flex-col items-center gap-1 p-3 transition-transform duration-[var(--dur-base)] ease-[var(--ease-bounce)]",
                      s.unlocked && data.avatar ? "hover:-translate-y-1" : "cursor-not-allowed",
                      on && "ring-3 ring-violet",
                    )}>
                    <div className={cx("h-24 w-20", !s.unlocked && "opacity-40 grayscale")}>
                      <AvatarImage skin={s.id} className="h-full w-full" />
                    </div>
                    <span className="text-sm font-extrabold">{s.name}</span>
                    <span className="text-xs font-bold text-ink-faint">{s.unlocked ? `Level ${s.level}` : `Unlocks at ${s.level}`}</span>
                    {!s.unlocked && <Lock aria-hidden className="absolute right-2.5 top-2.5 size-4 text-ink-faint" />}
                    {on && <Check aria-hidden className="absolute right-2.5 top-2.5 size-4 text-violet" strokeWidth={3} />}
                  </button>
                </li>
              );
            })}
          </ul>
        </Panel>
      </div>

      <Panel>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="title-poster text-3xl">{data.avatar ? "Edit my look" : "Create my character"}</h2>
          <Badge tone="accent"><Sparkles aria-hidden className="size-3.5" /> Built from your answers</Badge>
        </div>
        <div className="mt-5"><AvatarForm value={answers} onChange={setAnswers} /></div>

        <details className="mt-6 rounded-[18px] bg-surface-2 p-4">
          <summary className="cursor-pointer font-extrabold">Image prompt for your avatar</summary>
          <p className="mt-2 text-sm text-ink-soft">
            Your character art is made once with an image generator, only after you approve this exact prompt.
          </p>
          <p className="mt-3 rounded-[14px] bg-surface p-3 font-mono text-xs leading-relaxed text-ink-soft">{avatarPrompt(answers, "a1")}</p>
        </details>

        {error && <p role="alert" className="mt-4 font-bold text-danger">{error}</p>}
        <div className="mt-6 flex items-center justify-end gap-3">
          {saved && <span role="status" className="flex items-center gap-1 font-bold text-success"><Check aria-hidden className="size-4" /> Saved</span>}
          <Button onClick={save} busy={saving}>{data.avatar ? "Save my look" : "Create my avatar"}</Button>
        </div>
      </Panel>
    </div>
  );
}

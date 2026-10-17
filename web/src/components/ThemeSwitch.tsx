import { useEffect, useState } from "react";
import { Monitor, Moon, Sun } from "lucide-react";
import { getTheme, setTheme, type ThemePref } from "../lib/theme";
import { cx } from "./ui";

const OPTIONS: { value: ThemePref; label: string; icon: typeof Sun }[] = [
  { value: "light", label: "Day", icon: Sun },
  { value: "dark", label: "Night", icon: Moon },
  { value: "system", label: "Same as my Mac", icon: Monitor },
];

function useTheme(): [ThemePref, (t: ThemePref) => void] {
  const [pref, setPref] = useState<ThemePref>(getTheme);
  useEffect(() => {
    const on = (e: Event) => setPref((e as CustomEvent<ThemePref>).detail);
    window.addEventListener("tcfquest-theme", on);
    return () => window.removeEventListener("tcfquest-theme", on);
  }, []);
  return [pref, setTheme];
}

/** Round button for the Home hero: tap to switch between day and night. */
export function ThemeToggle({ className }: { className?: string }) {
  const [pref, set] = useTheme();
  const dark = pref === "dark" || (pref === "system" && window.matchMedia?.("(prefers-color-scheme: dark)").matches);
  const Icon = dark ? Sun : Moon;
  return (
    <button type="button" onClick={() => set(dark ? "light" : "dark")} aria-label={dark ? "Switch to day mode" : "Switch to night mode"}
      title={dark ? "Day mode" : "Night mode"} className={className}>
      <Icon aria-hidden className="size-4" />
    </button>
  );
}

/** Three-way choice for Settings. */
export function ThemeChoice() {
  const [pref, set] = useTheme();
  return (
    <div role="radiogroup" aria-label="Theme" className="grid grid-cols-3 gap-2">
      {OPTIONS.map(({ value, label, icon: Icon }) => (
        <button key={value} type="button" role="radio" aria-checked={pref === value} onClick={() => set(value)}
          className={cx("flex flex-col items-center gap-1 rounded-[16px] border-2 p-3 text-sm font-extrabold",
            pref === value ? "border-violet bg-surface-2" : "border-line hover:bg-surface-2")}>
          <Icon aria-hidden className="size-5" /> {label}
        </button>
      ))}
    </div>
  );
}

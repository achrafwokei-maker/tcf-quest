// Day / night theme. "system" follows macOS; the choice is remembered on this device only.
export type ThemePref = "system" | "light" | "dark";
const KEY = "tcfquest-theme";

export function getTheme(): ThemePref {
  try {
    const v = localStorage.getItem(KEY);
    return v === "light" || v === "dark" ? v : "system";
  } catch {
    return "system";
  }
}

export function applyTheme(pref: ThemePref) {
  const root = document.documentElement;
  if (pref === "system") root.removeAttribute("data-theme");
  else root.setAttribute("data-theme", pref);
}

export function setTheme(pref: ThemePref) {
  try {
    if (pref === "system") localStorage.removeItem(KEY);
    else localStorage.setItem(KEY, pref);
  } catch { /* private mode: still applies for this visit */ }
  applyTheme(pref);
  window.dispatchEvent(new CustomEvent("tcfquest-theme", { detail: pref }));
}

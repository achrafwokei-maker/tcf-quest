import { NavLink, Outlet, useLocation } from "react-router-dom";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { Map, MessageCircle, PenLine, Sun, TrendingUp } from "lucide-react";
import { cx } from "./ui";

export const NAV = [
  { to: "/", label: "Aujourd'hui", hint: "Today", icon: Sun, color: "var(--gold)" },
  { to: "/aventure", label: "Aventure", hint: "Journey", icon: Map, color: "var(--green)" },
  { to: "/entrainement", label: "Entraînement", hint: "Practice", icon: PenLine, color: "var(--blue)" },
  { to: "/progression", label: "Progression", hint: "Progress", icon: TrendingUp, color: "var(--pink)" },
  { to: "/professeur", label: "Professeur", hint: "AI tutor", icon: MessageCircle, color: "var(--violet)" },
] as const;

/** Game-style shell: full-bleed screens and a floating tab bar on every screen size (reference 2). */
export function AppShell() {
  const location = useLocation();
  const reduce = useReducedMotion();

  return (
    <div className="min-h-dvh">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-50 focus:rounded-full focus:bg-surface focus:px-4 focus:py-2">
        Skip to content
      </a>

      <main id="main" className="mx-auto w-full max-w-6xl pb-32">
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={location.pathname}
            initial={reduce ? false : { opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={reduce ? undefined : { opacity: 0, y: -6 }}
            transition={{ duration: 0.24, ease: [0.22, 1, 0.36, 1] }}
          >
            <Outlet />
          </motion.div>
        </AnimatePresence>
      </main>

      <nav
        aria-label="Main"
        className="glass fixed inset-x-3 bottom-3 z-40 mx-auto grid max-w-xl grid-cols-5 rounded-[28px] px-1.5 py-1.5 pb-[max(0.375rem,env(safe-area-inset-bottom))]"
      >
        {NAV.map(({ to, label, hint, icon: Icon, color }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            title={`${label} · ${hint}`}
            className={({ isActive }) =>
              cx(
                "group flex min-h-14 flex-col items-center justify-center gap-0.5 rounded-[22px] text-[0.68rem] font-extrabold transition-colors",
                isActive ? "text-ink" : "text-ink-faint hover:text-ink-soft",
              )
            }
          >
            {({ isActive }) => (
              <>
                <span
                  className={cx(
                    "grid size-9 place-items-center rounded-[14px] transition-all duration-[var(--dur-base)] ease-[var(--ease-bounce)]",
                    isActive ? "tile -translate-y-1.5 scale-110" : "",
                  )}
                  style={isActive ? { ["--tile" as string]: color } : undefined}
                >
                  <Icon aria-hidden className="size-5" strokeWidth={isActive ? 2.4 : 2} />
                </span>
                <span className="leading-none">{hint}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}

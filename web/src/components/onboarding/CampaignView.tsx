import { Flag, Gauge, ListChecks, Map, Target, Timer } from "lucide-react";
import type { Campaign } from "../../lib/onboarding";
import { Badge, Button, IconTile, Panel } from "../ui";

const SECTION_FR: Record<string, string> = {
  CO: "Compréhension orale", CE: "Compréhension écrite", EO: "Expression orale", EE: "Expression écrite",
};
const SKILL_FR: Record<string, string> = {
  listening: "Compréhension orale", reading: "Compréhension écrite", speaking: "Expression orale", writing: "Expression écrite",
};

/** The personal TCF campaign (Part II R6), honest about what is provisional. */
export function CampaignView({ c, lang, onStart }: { c: Campaign; lang: "en" | "fr"; onStart: () => void }) {
  const en = lang === "en";
  return (
    <div className="space-y-4">
      <div>
        <p className="eyebrow">{en ? "Your TCF Canada campaign" : "Ta campagne TCF Canada"}</p>
        <h1 className="title-poster mt-1 text-5xl">{en ? `Ready, ${c.name}?` : `Prêt·e, ${c.name} ?`}</h1>
      </div>

      <Row icon={Target} color="var(--violet)" title={en ? "Your target" : "Ton objectif"}>
        <p className="text-lg font-extrabold">NCLC {c.objective.nclc}{c.objective.nclc_by_skill ? (en ? " (lowest of your skill targets)" : " (la plus basse de tes cibles)") : ""}</p>
        {c.objective.nclc_by_skill && (
          <p className="text-sm font-semibold text-ink-soft">
            {Object.entries(c.objective.nclc_by_skill).map(([k, v]) => `${SKILL_FR[k]} ${v}`).join(" · ")}
          </p>
        )}
        <p className="text-sm font-semibold text-ink-soft">{en ? "Personal French goal" : "Objectif personnel"} : {c.objective.cefr_goal} {en ? "(tracked separately)" : "(suivi à part)"}</p>
      </Row>

      <Row icon={Gauge} color="var(--blue)" title={en ? "Where you start" : "Ton point de départ"}>
        <p className="flex flex-wrap items-center gap-2 text-lg font-extrabold">
          {en ? "Around" : "Autour de"} {c.start.cefr_low}–{c.start.cefr_high}
          {c.start.provisional && <Badge tone="warning">{en ? "Provisional" : "Provisoire"}</Badge>}
        </p>
        <p className="text-sm font-semibold text-ink-soft">{c.start.basis}</p>
        {c.gap && <p className="text-sm font-semibold text-ink-soft">{en ? "Gap to target:" : "Écart à l'objectif :"} {c.gap}</p>}
      </Row>

      <Row icon={Flag} color="var(--pink)" title={en ? "Your priorities" : "Tes priorités"}>
        <ol className="space-y-2">
          {c.priorities.map((p, i) => (
            <li key={p.skill}>
              <p className="font-extrabold">{i + 1}. {SECTION_FR[p.section]}</p>
              <p className="text-sm font-semibold text-ink-soft">{p.reason}</p>
            </li>
          ))}
        </ol>
      </Row>

      <Row icon={Timer} color="var(--gold)" title={en ? "Your rhythm" : "Ton rythme"}>
        <p className="text-lg font-extrabold">{c.rhythm.daily_minutes} min/{en ? "day" : "jour"} · ≈ {c.rhythm.weekly_hours} h/{en ? "week" : "semaine"}</p>
        <p className="text-sm font-semibold text-ink-soft">{c.rhythm.plan_label}</p>
        <p className="text-sm font-semibold text-ink-faint">{en ? "Counted over 5 study days a week; rest days are part of the plan." : "Calculé sur 5 jours d'étude par semaine ; les jours de repos font partie du plan."}</p>
      </Row>

      <Row icon={ListChecks} color="var(--green)" title={en ? "Next steps" : "Prochaines étapes"}>
        <ul className="space-y-1.5">
          {c.next_steps.map((s) => (
            <li key={s.title} className="flex flex-wrap items-center justify-between gap-2">
              <span className="font-bold">{s.title}</span>
              <Badge tone={s.status === "available" ? "success" : "neutral"}>{s.status}</Badge>
            </li>
          ))}
        </ul>
      </Row>

      <Button className="mt-2 w-full" onClick={onStart}><Map aria-hidden className="size-4" /> {en ? "Start my expedition" : "Commencer l'expédition"}</Button>
    </div>
  );
}

function Row({ icon, color, title, children }: { icon: typeof Target; color: string; title: string; children: React.ReactNode }) {
  return (
    <Panel pad="sm" className="flex gap-4">
      <IconTile icon={icon} color={color} size="sm" />
      <div className="min-w-0 flex-1 space-y-1">
        <p className="eyebrow">{title}</p>
        {children}
      </div>
    </Panel>
  );
}

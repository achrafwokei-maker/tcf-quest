import type { Skill } from "./api";

export const SKILLS: Skill[] = ["listening", "reading", "speaking", "writing"];

export const skillName: Record<Skill, { fr: string; en: string }> = {
  listening: { fr: "Compréhension orale", en: "Listening" },
  reading: { fr: "Compréhension écrite", en: "Reading" },
  speaking: { fr: "Expression orale", en: "Speaking" },
  writing: { fr: "Expression écrite", en: "Writing" },
};

export interface Chapter {
  n: number;
  roman: string;
  title: string;
  place: string;
  levels: string;
}

// Narrative stages, not official TCF levels.
export const CHAPTERS: Chapter[] = [
  { n: 1, roman: "I", title: "Le Premier Pas", place: "Normandie", levels: "A1–A2" },
  { n: 2, roman: "II", title: "La Vie Quotidienne", place: "Paris · Belleville", levels: "A2–B1" },
  { n: 3, roman: "III", title: "La Cité des Idées", place: "Lyon", levels: "B1–B2" },
  { n: 4, roman: "IV", title: "Le Labyrinthe des Arguments", place: "Strasbourg", levels: "B2–C1" },
  { n: 5, roman: "V", title: "La Maîtrise", place: "Pyrénées · l'observatoire", levels: "C1–C2" },
];

export function greeting(name: string, now = new Date()): string {
  const h = now.getHours();
  const word = h < 5 ? "Bonsoir" : h < 18 ? "Bonjour" : "Bonsoir";
  return `${word}, ${name}`;
}

/** The next Sunday (weekly trial day), or today if it is Sunday. */
export function nextTrialDate(now = new Date()): Date {
  const d = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  d.setDate(d.getDate() + ((7 - d.getDay()) % 7));
  return d;
}

export function daysUntil(iso: string, now = new Date()): number {
  const [y, m, d] = iso.split("-").map(Number);
  const target = Date.UTC(y, m - 1, d);
  const today = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
  return Math.round((target - today) / 86_400_000);
}

export const frDate = (d: Date) =>
  d.toLocaleDateString("fr-CA", { weekday: "long", day: "numeric", month: "long" });

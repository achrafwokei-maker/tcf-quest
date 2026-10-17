// Exercise engine client (milestone 1). Answer keys never reach the browser; the server checks.

export interface TcfTarget {
  section: "CO" | "CE" | "EO" | "EE";
  task: string | null;
  purpose: string;
}

export type Stage = "A" | "B" | "C" | "D" | "E" | "F" | "G" | "H";

export interface Speech {
  speaker: string;
  text: string;
  en: string | null;
}

interface ItemCommon {
  id: string;
  level: string;
  instructions: string;
  instructions_en: string | null;
  tcf_target: TcfTarget;
  stage: Stage | null;
  has_hint?: boolean;
  time_limit_s?: number | null;
}

export interface ChoiceItem extends ItemCommon {
  type: "select" | "listen";
  question: string;
  passage: string | null;
  audio: { text: string; file: string | null; speaker?: string | null } | null;
  options: { id: string; text: string }[];
  prompt_line: Speech | null;
}

export interface MultiItem extends ItemCommon {
  type: "multi";
  question: string;
  options: { id: string; text: string }[];
  count: number;
}

export interface CardItem extends ItemCommon {
  type: "card";
  kind: "story" | "method" | "language" | "objective" | "outro";
  title: string;
  body: string | null;
  body_en: string | null;
  lines: Speech[];
  points: string[];
  link: { label: string; to: string } | null;
}

export interface ArrangeItem extends ItemCommon {
  type: "arrange";
  tiles: string[];
  translation: string | null;
}

export interface TypeItem extends ItemCommon {
  type: "type";
  sentence: string;
  base_form: string | null;
  has_hint: boolean;
}

export type Item = ChoiceItem | ArrangeItem | TypeItem | MultiItem | CardItem;

export interface SessionState {
  status: "in_progress" | "completed";
  index: number;
  total: number;
  current_item_id: string | null;
  results: { item_id: string; verdict: Verdict; score: number }[];
  summary: { items: number; correct_first_try: number };
}

/** Keyed items use correct/partial/incorrect/skipped; AI-scored speaking and writing will add the others. */
export type Verdict =
  | "correct" | "partial" | "incorrect" | "skipped" | "seen"
  | "unnatural" | "understood" | "off_task" | "incomplete" | "uncertain";

export type FlagKind = "too_easy" | "too_hard" | "unclear" | "dispute" | "technical";

export interface WhyInfo {
  item_id: string;
  competencies: string[];
  tcf_target: TcfTarget;
  correct_answer: string;
  explanation: string | null;
  options?: { text: string; correct: boolean; explanation: string }[];
  transcript?: string;
  also_accepted?: string[];
  hint?: string | null;
}

export interface ReviewReport {
  id: number;
  kind: FlagKind;
  note: string;
  created_at: string;
  item_id: string;
  set_id: string;
  verdict: string;
  prompt: string | null;
  learner_answer: string;
  expected: string | null;
}

export interface ReviewQueue {
  reports: ReviewReport[];
  items_to_fix: { item_id: string; reasons: string[] }[];
  difficulty_votes: Record<string, { too_easy: number; too_hard: number }>;
}

export interface Feedback {
  attempt_id: number;
  verdict: Verdict;
  score: number;
  note: string | null;
  details: { wrong_positions?: number[]; accent?: boolean; contrast?: string[]; missed?: string[]; extra?: string[] };
  correct_answer: string;
  explanation: string | null;
  correct_explanation?: string;
  chosen_explanation?: string;
  transcript: string | null;
  will_retry: boolean;
  notebook: "opened" | "reopened" | "progress" | "mastered" | null;
  reply: Speech | null;
  state: SessionState;
}

export interface MissionMeta {
  chapter: number;
  story: string;
  objective: string;
  objective_en: string | null;
  minutes: number;
  stage_titles: Partial<Record<Stage, string>>;
}

export interface MissionReport {
  minutes: number;
  xp: number;
  mistakes_in_notebook: number;
  summary: { items: number; correct_first_try: number };
  competencies: { id: string; p_known: number; mastered: boolean }[];
}

export interface Mistake {
  id: number;
  skill: string;
  category: string;
  item_id: string;
  set_id: string | null;
  context: string;
  learner_answer: string;
  correction: string;
  explanation: string;
  recurrence: number;
  status: "open" | "improving" | "mastered";
  interval_days: number;
  next_review: string;
  review_note: string;
  due: boolean;
}

export type WeaknessState = "detected" | "training" | "improving" | "retest_due" | "mastered";

export interface Weakness {
  competency: string;
  skill: string;
  task: string | null;
  category: "grammar" | "spelling" | "vocabulary" | "comprehension" | "expression" | "other";
  state: WeaknessState;
  frequency: number;
  severity: number;
  confidence: "low" | "medium" | "high";
  examples: { item: string; answer: string; correction: string; date: string }[];
  retest_item: string | null;
  needs_content: number;
  rethink: number;
  reopen_count: number;
}

export interface Notebook {
  due_today: number;
  open: Mistake[];
  mastered: Mistake[];
  weaknesses: Weakness[];
}

export interface PlanStep {
  kind: "review" | "mission" | "practice";
  set_id: string;
  title: string;
  level?: string;
  minutes: number;
  partial: boolean;
  status?: "not_started" | "in_progress" | "completed";
  count?: number;
  retests?: number;
  tcf_target?: TcfTarget;
  reason: string;
  improves: string[];
}

export interface Plan {
  date: string;
  minutes_available: number;
  minutes_planned: number;
  welcome_back: boolean;
  days_away: number;
  phase: { weeks_to_exam: number | null; focus: string; label: string; weights: Record<string, number>; note: string };
  diagnostic: { status: "available" | "in_progress" | "completed"; attempt_id: number | null };
  mock: { exam_id: string; title: string; minutes: number; recommended: boolean; status: string; attempt_id: number | null; reason: string } | null;
  weekly_trial: { exam_id: string; title: string; minutes: number; due: boolean; status: string; attempt_id: number | null;
    days_since_last: number | null; reason: string } | null;
  steps: PlanStep[];
  content_exhausted: boolean;
  rethink: string[];
}

export interface Today {
  plan: Plan;
  mission: {
    set_id: string; title: string; level: string; minutes: number; objective: string; objective_en: string | null;
    tcf_target: TcfTarget; reason: string; status: "not_started" | "in_progress" | "completed";
  } | null;
  reviews_due: number;
}

export interface SetPayload {
  set: {
    id: string; title: string; level: string; context: string; tcf_target: TcfTarget;
    mission: MissionMeta | null; items: Record<string, Item>;
  };
  state: SessionState;
}

export interface SetSummary {
  id: string;
  context: string;
  title: string;
  level: string;
  items: number;
  sections: string[];
  group: string | null;
}

export interface AnswerInput {
  item_id: string;
  response: string | string[] | null;
  duration_ms: number;
  hints_used: number;
  plays: number;
  audio_off: boolean;
  skipped?: boolean;
}

export class OutOfSyncError extends Error {
  constructor(public state: SessionState) {
    super("Already answered");
  }
}

async function json<T>(res: Response): Promise<T> {
  if (res.status === 409) {
    const body = await res.json().catch(() => null);
    if (body?.detail?.state) throw new OutOfSyncError(body.detail.state);
    throw new Error(typeof body?.detail === "string" ? body.detail : "Conflict");
  }
  if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail ?? res.statusText);
  return res.json() as Promise<T>;
}

const post = (url: string, body?: unknown) =>
  fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined });

export const exercisesApi = {
  list: () => fetch("/api/sets").then((r) => json<{ sets: SetSummary[] }>(r)),
  load: (id: string) => fetch(`/api/sets/${id}`).then((r) => json<SetPayload>(r)),
  answer: (id: string, a: AnswerInput) => post(`/api/sets/${id}/answer`, a).then((r) => json<Feedback>(r)),
  seen: (id: string, itemId: string) =>
    post(`/api/sets/${id}/answer`, { item_id: itemId }).then((r) => json<{ verdict: "seen"; state: SessionState }>(r)),
  report: (id: string) => fetch(`/api/sets/${id}/report`).then((r) => json<MissionReport>(r)),
  today: (minutes?: number) => fetch(`/api/today${minutes ? `?minutes=${minutes}` : ""}`).then((r) => json<Today>(r)),
  notebook: () => fetch("/api/notebook").then((r) => json<Notebook>(r)),
  understood: (mistakeId: number) => post(`/api/notebook/${mistakeId}/understood`).then((r) => json<Notebook>(r)),
  startReviews: () => post("/api/reviews/start").then((r) => json<{ set_id: string; items: number }>(r)),
  hint: (id: string, itemId: string) =>
    post(`/api/sets/${id}/hint?item_id=${encodeURIComponent(itemId)}`).then((r) => json<{ hint: string | null }>(r)),
  restart: (id: string) => post(`/api/sets/${id}/restart`).then((r) => json<{ state: SessionState }>(r)),
  why: (setId: string, itemId: string) => fetch(`/api/sets/${setId}/why/${itemId}`).then((r) => json<WhyInfo>(r)),
  flag: (attemptId: number, kind: FlagKind, note = "") =>
    post(`/api/attempts/${attemptId}/flags`, { kind, note }).then((r) => json<{ id: number; status: string; evidence_removed: boolean }>(r)),
  review: () => fetch("/api/review").then((r) => json<ReviewQueue>(r)),
  resolve: (flagId: number, action: "accept" | "reject" | "close", note = "") =>
    post(`/api/review/${flagId}/${action}`, { note }).then((r) => json<Record<string, unknown>>(r)),
};

export const SECTION_LABEL: Record<TcfTarget["section"], string> = {
  CO: "Compréhension orale",
  CE: "Compréhension écrite",
  EO: "Expression orale",
  EE: "Expression écrite",
};

export function tcfLabel(t: TcfTarget): string {
  const task = t.task ? ` · Tâche ${t.task.slice(-1)}` : "";
  return `${SECTION_LABEL[t.section]}${task}`;
}

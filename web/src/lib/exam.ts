// Strict exam engine API (weekly trials; later section and full mocks).
import type { Item } from "./exercises";
import type { EOTaskInfo } from "./eo";
import type { WritingTask } from "./writing";

export interface ExamListing {
  exams: { id: string; kind: string; title: string; label: string; status: "available" | "in_progress" | "completed"; blocked_by_seen: string | null;
    attempt_id: number | null; sections: { section: string; limit_s: number }[] }[];
  days_since_last_weekly: number | null; weekly_due: boolean; next_weekly: string | null;
}

export interface ReviewItem {
  item_id: string; level: string; competency: string; question: string; response: string | null; answer: string;
  correct: boolean; answered: boolean; options: { id: string; text: string; explanation: string }[];
  passage: string | null; transcript: string | null;
}

export interface SectionResult {
  section: "CO" | "CE" | "EE" | "EO"; skill: string; timed_out: boolean; time_used_s: number; limit_s: number;
  correct?: number; total?: number; unanswered?: number; review?: ReviewItem[];
  writing_submission_id?: number; writing_submission_ids?: number[]; eo_session_id?: number;
}

export interface ExamReport {
  kind: string; goal: { cefr: string; nclc: number | null }; label: string; complete: boolean;
  skills: { skill: string; section: string; estimate: { cefr_low: string | null; cefr_high: string | null; confidence: string } | null;
    correct?: number; total?: number; adaptive_final_level?: string | null;
    ai?: { status: string; mean?: number; cefr_estimate?: string; agreement?: string } }[];
  strengths: string[]; error_categories: Record<string, string[]>; limits: string[];
  priorities: { skill: string | null; reason: string }[];
  next: { steps: { title: string; minutes: number; reason: string }[]; weekly_trial: { title: string; minutes: number } | null };
  focus?: { skill: string; reason: string }[];
  root_causes?: { competency: string; cause: string; evidence: string }[];
  timing?: { section: string; note: string }[];
  retests?: string[];
}

export interface ExamAttempt {
  id: number; exam_id: string; title: string; label: string; kind: string; status: "in_progress" | "completed";
  section_index: number;
  sections: { section: string; limit_s: number; started: boolean; ended: boolean; timed_out: boolean; items: number | null }[];
  current?: {
    section: "CO" | "CE" | "EE" | "EO"; started: boolean; remaining_s: number;
    item?: Item; position?: number; total?: number; played?: boolean;
    writing_task?: WritingTask; writing_submission_id?: number; writing_tasks?: WritingTask[]; writing_submission_ids?: number[];
    eo_task?: EOTaskInfo; eo_session_id?: number;
  };
  results?: { sections: SectionResult[]; label: string };
  report?: ExamReport;
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api/exams${path}`, { ...init, headers: { "Content-Type": "application/json" } });
  if (!res.ok) {
    const err = new Error((await res.json().catch(() => null))?.detail ?? res.statusText) as Error & { status?: number };
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export const examApi = {
  list: () => call<ExamListing>(""),
  start: (examId: string) => call<ExamAttempt>(`/${examId}/start`, { method: "POST" }),
  get: (aid: number) => call<ExamAttempt>(`/attempts/${aid}`),
  begin: (aid: number) => call<ExamAttempt>(`/attempts/${aid}/begin`, { method: "POST" }),
  play: (aid: number, itemId: string) => call<{ text: string; speaker: string | null }>(`/attempts/${aid}/play`, { method: "POST", body: JSON.stringify({ item_id: itemId }) }),
  answer: (aid: number, itemId: string, response: string | null) =>
    call<ExamAttempt>(`/attempts/${aid}/answer`, { method: "POST", body: JSON.stringify({ item_id: itemId, response }) }),
  finish: (aid: number) => call<ExamAttempt>(`/attempts/${aid}/finish`, { method: "POST" }),
};

export const SECTION_NAME: Record<string, string> = {
  CO: "Compréhension orale", CE: "Compréhension écrite", EE: "Expression écrite", EO: "Expression orale",
};

export const SECTION_RULES: Record<string, string> = {
  CO: "Each recording plays once. Read the question after listening, choose one answer, and move on: you can't go back.",
  CE: "Read each document and choose one answer. You can't go back to a previous question.",
  EE: "Write the task within the word range. The text is submitted automatically when time is up.",
  EO: "The examiner speaks; answer aloud (or type if you can't). The task ends automatically when time is up.",
};

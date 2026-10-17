// Writing studio API (EE T1–T3). AI feedback is an unofficial estimate.

export type EETask = "EE-T1" | "EE-T2" | "EE-T3";

export interface WritingTask {
  id: string; task: EETask; level: string; title: string; prompt: string; recipient: string;
  documents: { title: string; text: string }[]; competencies: string[];
  words: { min: number; max: number }; exam_seconds: number;
  last?: { id: number; status: string; feedback_status: string } | null;
}

export interface Template { title: string; steps: string[]; phrases: string[]; avoid: string }

export interface Correction {
  original: string; corrected: string; explanation: string; category: string;
  kind: "error" | "style"; source: "ai" | "rule";
}

export interface Feedback {
  criteria: Record<string, { label: string; score: number; low: number; high: number; comment: string }>;
  mean: number; agreement: "high" | "low"; corrections: Correction[]; strengths: string[]; priorities: string[];
  revised_version: string; cefr_estimate: string; label: string;
}

export interface Submission {
  id: number; task_id: string; task: EETask; mode: "training" | "exam"; text: string; word_count: number;
  status: "draft" | "submitted"; started_at: string; submitted_at: string | null; time_limit_s: number | null;
  timed_out: number; word_range_ok: number | null; remaining_s: number | null;
  feedback: Feedback | null; feedback_status: "none" | "pending" | "done" | "failed";
  range: { min: number; max: number; count: number; ok: boolean; state: "ok" | "short" | "long" };
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api/writing${path}`, { ...init, headers: { "Content-Type": "application/json" } });
  if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail ?? res.statusText);
  return res.json();
}

export const writingApi = {
  list: () => call<{ tasks: WritingTask[]; templates: Record<EETask, Template> }>(""),
  task: (id: string) => call<{ task: WritingTask; template: Template; history: Partial<Submission>[] }>(`/tasks/${id}`),
  start: (id: string, mode: "training" | "exam") => call<Submission>(`/tasks/${id}/start`, { method: "POST", body: JSON.stringify({ mode }) }),
  get: (sid: number) => call<Submission>(`/submissions/${sid}`),
  save: (sid: number, text: string) => call<Submission>(`/submissions/${sid}`, { method: "PUT", body: JSON.stringify({ text }) }),
  submit: (sid: number) => call<Submission>(`/submissions/${sid}/submit`, { method: "POST" }),
  retry: (sid: number) => call<Submission>(`/submissions/${sid}/feedback`, { method: "POST" }),
};

/** Same rule as the server: a word is a group of characters between spaces containing a letter or digit. */
export function countWords(text: string): number {
  return text.split(/\s+/).filter((t) => /[\p{L}\p{N}]/u.test(t)).length;
}

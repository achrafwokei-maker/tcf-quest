// Speaking tasks EO T1–T3 with the local AI examiner. Feedback = unofficial estimate, no pronunciation score.

export type EOTask = "EO-T1" | "EO-T2" | "EO-T3";

export interface EOTaskInfo {
  id: string; task: EOTask; level: string; title: string; examiner: "Examinateur" | "Examinatrice";
  instructions: string; targets: string[]; prep_s: number; talk_s: number;
  last?: { id: number; status: string; feedback_status: string } | null;
}

export interface Guide { title: string; tips: string[]; phrases: string[] }

export interface Turn {
  role: "examiner" | "learner"; text: string; source?: "speech" | "corrected" | "typed";
  confidence?: number | null; asr_status?: string | null; fallback?: boolean; at: string;
}

export interface EOFeedback {
  criteria: Record<string, { label: string; score: number; low: number; high: number; comment: string }>;
  mean: number; agreement: "high" | "low";
  corrections: { original: string; corrected: string; explanation: string; category: string; kind: "error" | "style"; source: string }[];
  strengths: string[]; priorities: string[]; better_answer: string;
  targets: { text: string; obtained: boolean }[]; cefr_estimate: string; label: string;
  stats: { turns: number; words: number; longest: number; average: number; uncertain_turns: number };
}

export interface EOSession {
  id: number; task_id: string; task: EOTask; mode: "training" | "exam"; status: "prep" | "active" | "ended";
  turns: Turn[]; remaining_s: number; end_reason: string | null; ai_fallbacks: number;
  feedback: EOFeedback | null; feedback_status: "none" | "pending" | "done" | "failed";
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api/eo${path}`, { ...init, headers: { "Content-Type": "application/json" } });
  if (!res.ok) {
    const err = new Error((await res.json().catch(() => null))?.detail ?? res.statusText) as Error & { status?: number };
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export const eoApi = {
  list: () => call<{ tasks: EOTaskInfo[]; guides: Record<EOTask, Guide> }>(""),
  task: (id: string) => call<{ task: EOTaskInfo; guide: Guide; history: unknown[] }>(`/tasks/${id}`),
  start: (id: string, mode: "training" | "exam") => call<EOSession>(`/tasks/${id}/start`, { method: "POST", body: JSON.stringify({ mode }) }),
  get: (sid: number) => call<EOSession>(`/sessions/${sid}`),
  begin: (sid: number) => call<EOSession>(`/sessions/${sid}/begin`, { method: "POST" }),
  turn: (sid: number, body: { text: string; source: string; confidence?: number; asr_status?: string; recording_id?: number }) =>
    call<EOSession>(`/sessions/${sid}/turn`, { method: "POST", body: JSON.stringify(body) }),
  end: (sid: number) => call<EOSession>(`/sessions/${sid}/end`, { method: "POST" }),
  retry: (sid: number) => call<EOSession>(`/sessions/${sid}/feedback`, { method: "POST" }),
};

export const EO_NAME: Record<EOTask, string> = {
  "EO-T1": "Tâche 1 · Entretien dirigé", "EO-T2": "Tâche 2 · Interaction", "EO-T3": "Tâche 3 · Point de vue",
};

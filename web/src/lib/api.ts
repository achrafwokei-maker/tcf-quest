// Thin client for the local API (proxied by Vite from /api to 127.0.0.1:8787).

export type Skill = "listening" | "reading" | "speaking" | "writing";

export interface Profile {
  display_name: string;
  goal: "tcf_canada" | "general";
  target_cefr: "B2" | "C1" | "C2";
  target_nclc: number;
  exam_date: string | null;
  daily_minutes: number;
  hardest_skills: Skill[];
  ui_language: "en" | "fr";
  onboarded_at: string | null;
  exam_window?: string | null;
  plan_mode?: string | null;
  start_route?: string | null;
}

export interface SkillEstimate {
  skill: Skill;
  cefr_low: string | null;
  cefr_high: string | null;
  confidence: "none" | "low" | "medium" | "high";
  evidence: number;
}

export interface Summary {
  profile: Profile;
  xp: number;
  streak: number;
  minutes_today: number;
  skills: SkillEstimate[];
  open_mistakes: number;
  due_reviews: number;
  diagnostic_done: boolean;
  history: { skill: Skill; cefr_low: string; cefr_high: string; confidence: string; source: string; created_at: string }[];
  weaknesses: { active: number; mastered: number };
}

export interface Health {
  ok: boolean;
  schema_version: number;
  ai: { running: boolean; version: string | null; model: string; model_installed: boolean };
}

export type Gender = "woman" | "man" | "nonbinary" | "unspecified";

export interface AvatarAnswers {
  gender: Gender;
  hair: "short" | "medium" | "long" | "curly" | "braids" | "bald";
  hair_colour: "black" | "brown" | "auburn" | "blond" | "grey" | "dyed";
  skin_tone: number;
  facial_hair: "none" | "stubble" | "beard" | "moustache";
  glasses: boolean;
  vibe: "street" | "classic" | "sporty" | "artsy";
  description: string;
}

export interface Avatar extends AvatarAnswers {
  equipped_skin: string;
}

export interface Skin {
  id: string;
  name: string;
  level: string;
  unlocked: boolean;
}

export interface AvatarState {
  avatar: Avatar | null;
  skins: Skin[];
  reached_level: string;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`/api${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiError(0, "The local server is not running.");
  }
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new ApiError(res.status, detail?.detail ?? res.statusText);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<Health>("/health"),
  profile: () => request<{ profile: Profile | null }>("/profile"),
  saveProfile: (p: Omit<Profile, "onboarded_at">) =>
    request<{ profile: Profile }>("/profile", { method: "PUT", body: JSON.stringify(p) }),
  summary: () => request<Summary>("/summary"),
  avatar: () => request<AvatarState>("/avatar"),
  saveAvatar: (a: AvatarAnswers) =>
    request<AvatarState>("/avatar", { method: "PUT", body: JSON.stringify(a) }),
  equipSkin: (skin: string) =>
    request<AvatarState>("/avatar/skin", { method: "PUT", body: JSON.stringify({ skin }) }),
};

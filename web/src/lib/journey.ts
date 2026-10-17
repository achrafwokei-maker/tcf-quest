// The adventure: one journey to TCF Canada readiness (presentation only; levels are measured separately).
import { exercisesApi } from "./exercises";
import { examApi } from "./exam";

export type NodeState = "done" | "in_progress" | "available" | "locked" | "skipped";

export interface JourneyNode {
  ref: string;
  kind: "briefing" | "diagnostic" | "practice" | "mission" | "academy" | "lesson" | "writing" | "speaking" | "boss" | "final" | "review";
  title: string; task?: string; skill?: string | null; level?: string | null; minutes: number;
  state: NodeState; optional?: boolean; rank?: number; route: string; reason: string; hint?: string;
  type?: "listening" | "reading" | "speaking" | "writing" | "strategy" | "revision" | "boss"; recommended?: boolean;
  action?: { type: "start_exam"; exam_id: string } | { type: "start_reviews" } | null;
}

export interface Chapter {
  n: number; title: string; subtitle: string; place: string; goal: string; cefr?: string;
  nodes: JourneyNode[]; boss: JourneyNode | null; unlocked: boolean; complete: boolean; progress: number; upcoming: string[];
}

export interface Journey {
  destination: string; chapters: Chapter[]; current_chapter: number; cefr_note?: string; side_missions: JourneyNode[]; progress: number; label: string;
}

export interface ContinueStep {
  node: JourneyNode | null; chapter: { n: number; title: string; place: string };
  where: string; why: string; next: string | null; progress: number;
}

const get = async <T,>(path: string): Promise<T> => {
  const r = await fetch(`/api/journey${path}`);
  if (!r.ok) throw new Error("The local server is not running.");
  return r.json();
};

export const journeyApi = {
  map: () => get<Journey>(""),
  continue: () => get<ContinueStep>("/continue"),
};

/** Open a node: some need a server action first (start the review session, start an exam). */
export async function openNode(node: JourneyNode, navigate: (to: string) => void) {
  if (node.action?.type === "start_reviews") {
    await exercisesApi.startReviews();
    return navigate("/set/revisions");
  }
  if (node.action?.type === "start_exam") {
    const a = await examApi.start(node.action.exam_id);
    return navigate(`/examen/${a.id}`);
  }
  navigate(node.route);
}

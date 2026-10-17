import { describe, expect, it } from "vitest";
import { nextStep, path, prevStep, reaction } from "./onboarding";

describe("onboarding path", () => {
  it("includes the exam briefing unless the learner already knows the exam", () => {
    expect(path({})).toContain("briefing");
    expect(path({ knows_exam: false })).toContain("briefing");
    expect(path({ knows_exam: true })).not.toContain("briefing");
  });

  it("reaches the first French exercise within 9 decisions on the fast path", () => {
    const p = path({ knows_exam: true });
    expect(p.indexOf("challenge")).toBeLessThanOrEqual(9);
  });

  it("moves forward and back along the learner's own path", () => {
    expect(nextStep("welcome", { knows_exam: true })).toBe("target");
    expect(nextStep("welcome", { knows_exam: false })).toBe("briefing");
    expect(prevStep("target", { knows_exam: true })).toBe("welcome");
    expect(prevStep("language", {})).toBeNull();
    expect(nextStep("campaign", {})).toBe("campaign");
  });

  it("gives a bilingual reaction with the weekly hours", () => {
    const r = reaction("daily_time", { daily_minutes: 20 })!;
    expect(r.fr).toContain("1,7 h");
    expect(r.en).toContain("1.7 h");
  });
});

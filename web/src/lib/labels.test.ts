import { describe, expect, it } from "vitest";
import { daysUntil, greeting, nextTrialDate } from "./labels";

describe("labels", () => {
  it("greets by time of day", () => {
    expect(greeting("Ana", new Date(2026, 9, 16, 9))).toBe("Bonjour, Ana");
    expect(greeting("Ana", new Date(2026, 9, 16, 20))).toBe("Bonsoir, Ana");
  });

  it("finds the next Sunday for the weekly trial", () => {
    // 2026-10-16 is a Friday → Sunday 18th
    expect(nextTrialDate(new Date(2026, 9, 16, 12)).getDate()).toBe(18);
    // On a Sunday, the trial is today
    expect(nextTrialDate(new Date(2026, 9, 18, 12)).getDate()).toBe(18);
  });

  it("counts days to the exam", () => {
    expect(daysUntil("2026-10-26", new Date(2026, 9, 16, 23))).toBe(10);
    expect(daysUntil("2026-10-16", new Date(2026, 9, 16, 1))).toBe(0);
  });
});

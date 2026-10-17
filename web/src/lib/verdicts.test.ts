import { describe, expect, it } from "vitest";
import { BANNED_WORDS, VERDICTS } from "./verdicts";

describe("verdict copy", () => {
  it("covers every verdict the engine can produce", () => {
    expect(Object.keys(VERDICTS).sort()).toEqual(
      ["correct", "incomplete", "incorrect", "off_task", "partial", "seen", "skipped", "uncertain", "understood", "unnatural"],
    );
  });

  it("never uses shaming words", () => {
    for (const v of Object.values(VERDICTS)) {
      const text = `${v.title} ${v.lead ?? ""}`.toLowerCase();
      for (const w of BANNED_WORDS) expect(text).not.toContain(w);
    }
  });

  it("pairs every verdict with an icon and a colour", () => {
    for (const v of Object.values(VERDICTS)) {
      expect(v.icon).toBeTruthy();
      expect(v.tone).toMatch(/^var\(--/);
    }
  });
});

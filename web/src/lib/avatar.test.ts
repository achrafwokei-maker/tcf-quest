import { describe, expect, it } from "vitest";
import type { AvatarAnswers } from "./api";
import { avatarPrompt } from "./avatar";

const base: AvatarAnswers = {
  gender: "man", hair: "short", hair_colour: "black", skin_tone: 4,
  facial_hair: "beard", glasses: false, vibe: "street", description: "",
};

describe("avatarPrompt", () => {
  it("describes the chosen features and the starter outfit", () => {
    const p = avatarPrompt(base);
    expect(p).toContain("a young man");
    expect(p).toContain("medium-brown skin");
    expect(p).toContain("black short hair");
    expect(p).toContain("a neat beard");
    expect(p).toContain("navy hoodie");
    expect(p).not.toContain("glasses,");
    expect(p).toContain("No text, no logos");
  });

  it("uses the outfit of the requested skin", () => {
    expect(avatarPrompt(base, "b1")).toContain("trench coat");
    expect(avatarPrompt(base, "c2")).toContain("constellations");
  });

  it("handles shaved heads, glasses and inclusive genders", () => {
    const p = avatarPrompt({ ...base, gender: "nonbinary", hair: "bald", glasses: true, facial_hair: "none" });
    expect(p).toContain("androgynous");
    expect(p).toContain("a shaved head");
    expect(p).not.toContain("black a shaved head");
    expect(p).toContain("glasses");
  });

  it("quotes the learner's description, collapsed and capped", () => {
    const p = avatarPrompt({ ...base, description: "  Calm,\n curious  " + "x".repeat(400) });
    expect(p).toContain('"Calm, curious ');
    expect(p.match(/"([^"]*)"/)![1].length).toBeLessThanOrEqual(300);
  });
});

import { describe, expect, it } from "vitest";
import { countWords } from "./writing";

describe("countWords (same rule as the server)", () => {
  it("counts groups between spaces that contain a letter or digit", () => {
    expect(countWords("Salut Léa, c'est moi ! Aujourd'hui, j'ai 2 chats — et toi ?")).toBe(10);
    expect(countWords("   ")).toBe(0);
  });
});

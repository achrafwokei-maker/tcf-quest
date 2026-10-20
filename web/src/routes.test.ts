// Guard against dead links: every in-app link written in the code or in the content must match a real route.
import { describe, expect, it } from "vitest";

// Vite loads the files as plain text, so no Node types are needed.
const code = import.meta.glob(["./**/*.ts", "./**/*.tsx", "!./**/*.test.ts"], { query: "?raw", import: "default", eager: true }) as Record<string, string>;
const contentFiles = import.meta.glob("../../content/**/*.json", { query: "?raw", import: "default", eager: true }) as Record<string, string>;

/** Route patterns declared in main.tsx → regexes ("set/:setId" matches "/set/anything"). */
function routes(): RegExp[] {
  const paths = [...code["./main.tsx"].matchAll(/<Route\s+(?:index|path="([^"]*)")/g)].map((m) => m[1] ?? "");
  return paths.filter((p) => p !== "*").map((p) => new RegExp("^/" + p.replace(/:[A-Za-z]+/g, "[^/]+") + "$"));
}
const ok = (link: string) => routes().some((r) => r.test(link.split("?")[0].split("#")[0]));

describe("in-app links", () => {
  it("every to=\"/…\", navigate(\"/…\"), link: \"/…\" in the code points at a real route", () => {
    const bad: string[] = [];
    for (const [f, src] of Object.entries(code)) {
      for (const m of src.matchAll(/(?:\bto=|\bto:\s*|navigate\(|link:\s*|href=)["'`](\/[^"'`$]*)["'`]/g)) {
        if (!m[1].startsWith("/api/") && !ok(m[1])) bad.push(`${f}: ${m[1]}`);   // /api/… = server downloads
      }
    }
    expect(bad).toEqual([]);
  });

  it("every link inside the learning content points at a real route", () => {
    const bad: string[] = [];
    for (const [f, text] of Object.entries(contentFiles)) {
      for (const m of text.matchAll(/"to":\s*"(\/[^"]*)"/g)) {
        if (!m[1].startsWith("/api/") && !ok(m[1])) bad.push(`${f}: ${m[1]}`);   // /api/… = server downloads
      }
    }
    expect(Object.keys(contentFiles).length).toBeGreaterThan(10);
    expect(bad).toEqual([]);
  });

  it("the guard really rejects a link to nowhere", () => {
    expect(ok("/does-not-exist")).toBe(false);
    expect(ok("/set")).toBe(false);
  });

  it("every Practice, Today and journey route used exists", () => {
    for (const link of ["/aventure", "/entrainement", "/progression", "/professeur", "/pratique/CO", "/pratique/CE", "/oral", "/ecrit",
      "/examen", "/academie", "/outils", "/vocabulaire", "/carnet", "/reglages", "/oral/eo1-presentation", "/ecrit/ee1-voisin-fete",
      "/set/belleville-a2", "/set/revisions", "/examen/12", "/bienvenue"]) {
      expect(ok(link), link).toBe(true);
    }
  });
});

import { describe, expect, it } from "vitest";
import { bestBrowserVoice } from "./speak";

const v = (name: string, lang = "fr-FR", localService = true) => ({ name, lang, localService }) as SpeechSynthesisVoice;

describe("bestBrowserVoice", () => {
  it("never picks the robotic novelty voices when a better one exists", () => {
    const voices = [v("Eddy (French (France))"), v("Flo (French (France))"), v("Thomas"), v("Samantha", "en-US")];
    expect(bestBrowserVoice(voices)?.name).toBe("Thomas");
  });
  it("prefers premium/enhanced voices", () => {
    expect(bestBrowserVoice([v("Thomas"), v("Audrey (Premium)")])?.name).toBe("Audrey (Premium)");
  });
  it("falls back to any French voice, or null", () => {
    expect(bestBrowserVoice([v("Eddy (French (France))")])?.name).toBe("Eddy (French (France))");
    expect(bestBrowserVoice([v("Samantha", "en-US")])).toBeNull();
  });
});

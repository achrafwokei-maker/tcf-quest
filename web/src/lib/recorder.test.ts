import { describe, expect, it } from "vitest";
import { encodeWav } from "./recorder";

describe("encodeWav", () => {
  it("writes a 16 kHz mono 16-bit PCM WAV header and clamps samples", async () => {
    const blob = encodeWav(new Float32Array([0, 1, -1, 2]), 16000);
    const v = new DataView(await blob.arrayBuffer());
    const tag = (o: number) => String.fromCharCode(...[0, 1, 2, 3].map((i) => v.getUint8(o + i)));
    expect(tag(0)).toBe("RIFF");
    expect(tag(8)).toBe("WAVE");
    expect(v.getUint16(22, true)).toBe(1);
    expect(v.getUint32(24, true)).toBe(16000);
    expect(v.getUint16(34, true)).toBe(16);
    expect(v.getUint32(40, true)).toBe(8);
    expect(v.getInt16(46, true)).toBe(32767);
    expect(v.getInt16(50, true)).toBe(32767);
  });
});

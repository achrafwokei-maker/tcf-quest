import type { AvatarAnswers } from "./api";

// Options shown in the avatar questions. Labels are what the learner sees; values go to the API.
export const GENDERS = [
  { value: "woman", label: "Woman" },
  { value: "man", label: "Man" },
  { value: "nonbinary", label: "Non-binary" },
  { value: "unspecified", label: "Prefer not to say" },
] as const;

export const HAIR = [
  { value: "short", label: "Short" },
  { value: "medium", label: "Medium" },
  { value: "long", label: "Long" },
  { value: "curly", label: "Curly" },
  { value: "braids", label: "Braids" },
  { value: "bald", label: "Shaved" },
] as const;

export const HAIR_COLOURS = [
  { value: "black", label: "Black", swatch: "#1c1714" },
  { value: "brown", label: "Brown", swatch: "#5b3a24" },
  { value: "auburn", label: "Auburn", swatch: "#8e3b1f" },
  { value: "blond", label: "Blond", swatch: "#d8b25e" },
  { value: "grey", label: "Grey", swatch: "#a8a8b0" },
  { value: "dyed", label: "Bright dye", swatch: "linear-gradient(135deg,#ff5fa2,#7356ff)" },
] as const;

// Six neutral tones, lightest to deepest.
export const SKIN_TONES = ["#f6dcc8", "#e9bf9c", "#cf9a72", "#a8704b", "#7a4e33", "#4e3022"];

export const FACIAL_HAIR = [
  { value: "none", label: "None" },
  { value: "stubble", label: "Stubble" },
  { value: "beard", label: "Beard" },
  { value: "moustache", label: "Moustache" },
] as const;

export const VIBES = [
  { value: "street", label: "Streetwear" },
  { value: "classic", label: "Classic" },
  { value: "sporty", label: "Sporty" },
  { value: "artsy", label: "Artsy" },
] as const;

/** What each skin looks like. The A1 outfit is the starter; the rest are earned. */
export const SKIN_OUTFITS: Record<string, string> = {
  a1: "a soft fuzzy navy hoodie, simple jeans, white sneakers and a small canvas backpack",
  a2: "a striped navy-and-white marinière sweater, a tilted beret, rolled jeans and canvas shoes",
  b1: "a belted beige trench coat over a knit sweater, a soft patterned scarf and leather boots",
  b2: "a sharp tailored blazer with a small gold lapel pin, a crisp shirt and polished shoes",
  c1: "a long fuzzy teal wool coat, round vintage glasses pushed up, and a satchel full of books",
  c2: "a midnight-blue outfit embroidered with gold constellations, a flowing cape and a glowing compass pendant",
};

const GENDER_WORDS: Record<AvatarAnswers["gender"], string> = {
  woman: "a young woman",
  man: "a young man",
  nonbinary: "an androgynous young person",
  unspecified: "a young adult",
};

const HAIR_WORDS: Record<AvatarAnswers["hair"], string> = {
  short: "short hair",
  medium: "medium-length hair",
  long: "long hair",
  curly: "voluminous curly hair",
  braids: "braided hair",
  bald: "a shaved head",
};

const VIBE_WORDS: Record<AvatarAnswers["vibe"], string> = {
  street: "relaxed streetwear attitude",
  classic: "classic, elegant attitude",
  sporty: "sporty, energetic attitude",
  artsy: "creative, artsy attitude",
};

const TONE_WORDS = ["very fair", "fair", "light-medium", "medium-brown", "brown", "deep brown"];

/**
 * Turn the learner's answers into the image prompt for their avatar (references 1 and 6).
 * The free-text description is passed as character hints, never as instructions.
 */
export function avatarPrompt(a: AvatarAnswers, skin = "a1"): string {
  const hairColour = a.hair === "bald" ? "" : a.hair_colour === "dyed" ? "brightly dyed " : `${a.hair_colour} `;
  const features = [
    `${TONE_WORDS[a.skin_tone - 1] ?? "medium"} skin`,
    `${hairColour}${HAIR_WORDS[a.hair]}`.trim(),
    a.facial_hair !== "none" ? (a.facial_hair === "beard" ? "a neat beard" : a.facial_hair) : "",
    a.glasses ? "glasses" : "",
  ].filter(Boolean);
  const description = a.description.trim().replace(/\s+/g, " ").slice(0, 300);

  return [
    `3D stylised collectible designer-doll character of ${GENDER_WORDS[a.gender]}, full body, standing, slightly oversized head, large expressive eyes, small confident half-smile, ${VIBE_WORDS[a.vibe]}.`,
    `Features: ${features.join(", ")}.`,
    description ? `Personality hints from their own words: "${description}".` : "",
    `Outfit: ${SKIN_OUTFITS[skin] ?? SKIN_OUTFITS.a1}.`,
    "Tactile textures (fuzzy fabric, soft matte skin), soft studio lighting, clean pale lavender gradient background, high-end toy render quality. No text, no logos. Portrait 3:4.",
  ].filter(Boolean).join(" ");
}

export const avatarArt = (skin: string) => `/art/avatar-${skin}.png`;

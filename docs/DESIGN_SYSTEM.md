# Design system

> **Redesign in progress (2026-10-16).** The game-style direction below replaces "Carnet d'expédition". The tokens further down still describe the old style until the reskin lands.

## New direction: a fun French adventure game

| Ref | What we take from it | Where it is used |
| --- | --- | --- |
| 1 · Designer dolls (Bloom, Mimi, Poppy…) | Stylised 3D characters, oversized heads, fuzzy tactile clothes, attitude; bold condensed poster type | Avatar, characters, skin cards, achievement posters |
| 2 · Game store app | Hero art at the top, white rounded cards overlapping it, colourful category icons, horizontal carousels of bright cards, bottom tab bar with a raised active icon | Home and overall navigation |
| 3 · Language app (dark) | Circular player with progress ring, step dots, waveform | Listening and speaking screens |
| 4 · Level map | Top-down painted world, glowing golden path, numbered nodes, locked nodes, stars | Journey map, applied to France |
| 5 · Paris at night | Deep blue/violet sky, warm gold lights, pink moon glow, painterly detail | Palette, backgrounds, hero art |
| 6 · PicaVerse | Glossy glass panels, soft gradients, avatar showcase and wardrobe grid | Avatar creator and wardrobe |

Rules kept from before: exam mode stays plain and quiet; lesson text stays highly readable (no text over busy art); one clear next action per screen; reduced-motion respected; no text inside generated images.

## Built so far (2026-10-16)

Source of truth: `web/src/styles/tokens.css` and `web/src/components/ui.tsx`.

- **Themes:** light = bright game UI on lavender (refs 2, 6); dark = Paris night (refs 3, 5). Follows the system setting.
- **Palette:** violet (primary), blue, cyan, gold, orange, pink, green, red; one colour per chapter (Normandie green, Paris orange, Lyon blue, Strasbourg pink, Pyrénées gold).
- **Type:** Anton for poster titles (`.title-poster`, uppercase), Nunito for everything you read. Both OFL, self-hosted.
- **Surfaces:** `.card` (solid white sheet), `.glass` (glossy blurred panel), `.tile` (glossy gradient tile with a highlight), `.night` (night-sky stage).
- **Components:** Button (glossy pill), Panel (card | glass), IconTile, Meter, Ring (circular progress), Badge, Upcoming, Art (generated image with a painted fallback), CompassMark.
- **Navigation:** floating glass tab bar on every screen size; active tab pops up as a coloured tile.
- **Home:** hero art (IMG-001) with poster greeting, streak/XP chips and avatar slot → overlapping sheet with four skill tiles and today's mission → chapter mission carousel → goal ring, weekly trial, target.
- **Journey:** map artwork (IMG-002) with nodes placed by % (`SPOTS` in `Journey.tsx`), glowing gold travelled path, pin on the current chapter, locks ahead, horizontal scroll on phones.
- **Kept:** exam mode will stay plain; reduced motion respected; focus rings; no text in generated art.


## Art direction (moved from CLAUDE.md)

**Changed 2026-10-16 to a fun game style** (replaces "Carnet d'expédition"; see docs/DESIGN_SYSTEM.md and the reference notes there):

- Characters: stylised 3D "designer doll" avatars, oversized heads, fuzzy/tactile clothes, bold poster typography (reference 1).
- World: Paris-at-night painterly palette, deep blue/violet with warm gold and pink light (reference 5).
- Navigation and screens: game-store layout, hero art on top, rounded overlapping cards, colourful category icons, carousels, bottom tab bar (reference 2).
- Progress map: top-down illustrated map of France with a glowing path, numbered and locked level nodes (reference 4).
- Avatar creator and wardrobe: glossy glass panels (reference 6). Audio and speaking screens: circular player and waveform (reference 3).
- The learner builds an avatar at onboarding (questions + a short self-description), starts with a basic skin, and earns new skins by reaching French levels (mastery, never XP).
- Still true: exam mode stays plain and quiet; lesson text stays highly readable; no text baked into generated images (labels are added in code).

**Image generation:** ChatGPT and Nano Banana (Google Flow) may be used during development, never inside the app. **Every image needs the learner's approval before it is generated:** add it to docs/IMAGE_REQUESTS.md, ask, wait for a yes.

Five chapters = five places in France. First mission: « Le Marché de Belleville » (Chapter 2, Paris, B1, speaking-focused).

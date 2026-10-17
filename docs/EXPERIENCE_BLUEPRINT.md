# TCF Quest: Experience Blueprint

Status: **approved 2026-10-16**, with the learner's notes integrated as **Part II** (Part II wins wherever the two differ). Companion name: **Céleste** (approved).

This document describes how TCF Quest behaves from the learner's point of view: what happens on first launch, how the app gets to know the learner, how it teaches, how it reacts, and how the learner progresses. It is behaviour, not visual design. Colours, art and layout follow `DESIGN_SYSTEM.md`.

French examples are original. Nothing here copies another product's characters, text or layout; the references were used only for interaction ideas.

---

## 0. Summary and what changes

### The idea in one paragraph

TCF Quest feels like a short, friendly conversation that turns into a game, and underneath it runs a serious exam-preparation engine. A companion, **Céleste** (a young cartographer who maps the French-speaking world), asks one question at a time. Within about three minutes the learner is answering real French, gets an immediate, kind reaction, and sees a personal roadmap. From then on, every visit opens on **one next mission** chosen by the engine from the learner's weakest skill, available time and exam date. Story, characters and rewards make people come back; diagnostics, mastery tracking and exam-format practice make coming back worth it.

### How the current app compares (examined 2026-10-16)

| Area | Current app | Blueprint | Why change |
| --- | --- | --- | --- |
| First screen | Asks for a name in a form | Language of guidance, then Céleste says hello | Asking for data before giving value is friction |
| Onboarding | 5 form steps, several questions per step, no French at all | ~9 short steps, one decision each, a real French challenge by minute 3 | First success before any effort |
| Avatar | Mandatory step with 7 questions + paragraph | Optional quick pick after the first challenge; full creator later on `/avatar` | Fun, not a gate; avoids a long form early |
| Level | Self-reported "hardest skills" only | Self-rating used only to pick the first challenge; route choice between quick diagnostic and guided start; level always labelled provisional until measured | Self-rating is not evidence |
| Home | A dashboard (stats, cards, carousel) | Opens on today's mission, with why, how long and what it improves; stats move below | "Always know what to do next" |
| Missions | Not built (disabled button) | Exercise engine with 9 types, shared feedback loop | Core of the experience |
| Speaking | Not built | Turn-based voice with clear states, keyboard fallback, transcript review | Speaking is TCF Quest's main difference |
| Streak | Daily streak (counter) | Weekly rhythm with built-in rest days, no punishment | Daily streaks create guilt and backlog anxiety |
| Reminders | None | Offered after the first mission, with a chosen time; respected if refused | Ask only once value is shown |

What stays: the five tabs, the France map, chapters, avatar and skins earned by mastery, the local AI stack, the honesty rules (estimates with ranges, CEFR/TCF/NCLC kept apart, exam mode separate).

---

## A. Interaction principles

Each principle has a rule the build can be checked against.

1. **One thing at a time.** Every screen in onboarding and in a mission asks for one decision or one answer. *Rule:* no screen has more than one primary button; questions have at most 6 choices.
2. **Value before data.** The learner does French before giving a name, an avatar or a permission. *Rule:* first French interaction happens before any free-text field; median time to the first answered item ≤ 2 minutes.
3. **React within a heartbeat.** Every tap gets an immediate visible response. *Rule:* keyed answers are checked locally in < 100 ms; anything slower (AI, speech) shows a progress state within 300 ms and an estimate of the wait.
4. **Correct feels good, wrong feels safe.** Success is confirmed clearly; mistakes are explained, never mocked, and become future review. *Rule:* no hearts or lives; no negative sounds louder than positive ones; every incorrect answer shows the correct form and a one-line reason.
5. **The next step is always obvious.** Every screen has one clearly primary next action, and Home always opens on "today's mission". *Rule:* a returning learner can start learning in one tap.
6. **Say why.** Every recommendation carries a reason in plain words ("Speaking is your lowest skill and limits your NCLC"). *Rule:* every mission card has a `reason` field; the planner may not produce a mission without one.
7. **Effort and ability are different things.** XP, streaks and stamps reward effort. Levels, unlocks and skins require demonstrated mastery. *Rule:* no code path converts XP into a level, unlock or skin (already tested for skins).
8. **Honest numbers.** Levels are estimates with a range and a confidence word; nothing claims to be an official TCF result. *Rule:* every level display has a label, a range and "estimate".
9. **Progressive disclosure.** Features appear when they become useful (map after the first mission, wardrobe after the first skin is close, exam simulator after chapter II). *Rule:* the first session shows at most 3 new concepts: mission, feedback, path.
10. **Never lose work.** Every answer is saved the moment it is submitted; writing drafts save as you type. *Rule:* refreshing or closing the browser at any point resumes at the same exercise.
11. **The learner is in control.** Narration can be muted, the companion shortened, speaking replaced by typing, goals changed, the diagnostic retaken. *Rule:* every setting that affects study is reachable in two taps from the profile.
12. **Training and exam are different worlds.** Training is warm, hinted and story-driven. Exam mode is plain, timed, unhinted and silent. *Rule:* the exam runner shares no animations, companion lines or rewards with training.

---

## B. Onboarding flow

### B.1 Recommended sequence

Target: **first French answer by ~2 minutes, roadmap by ~6–8 minutes.** Every step autosaves; a "Continue later" link sits on every step; Back is always available.

> **Revised by Part II (R1).** The sequence below is the approved one. Steps 1b, 4b and 6b are new and detailed in Part II; step 2 (motivation) is folded into step 3.

| # | Step | One decision | Skip? | Time |
| --- | --- | --- | --- | --- |
| 0 | Guidance language | English or Français | No (one tap) | 5 s |
| 1 | Welcome | « Découvrir le TCF Canada » / « Je connais déjà l'examen » | No | 15 s |
| 1b | **Exam briefing** (interactive, 4 short cards + 2 quiz questions + the route of preparation) | Next / skip anytime | Yes ("Je connais déjà l'examen") | 2–3 min |
| 3 | Target (TCF-first) | NCLC 7 / NCLC 9+ / strong C1 / highest possible / per-skill targets / not sure | Yes ("Not sure" → NCLC 7) | 20 s |
| 4 | Exam timing | Within 1 month / 3 months / 6 months / later / undecided (+ optional exact date) | Yes | 15 s |
| 5 | Comfort with French | Five descriptions | No (it picks the first challenge) | 15 s |
| 4b | **Section of concern** | Listening / Reading / Speaking / Writing / Not sure | Yes | 10 s |
| 6 | Daily time | 10 / 20 / 30 / 45 / 60+ min | No (default 20) | 10 s |
| 6b | **Learning preference** | Short exercises / AI conversations / guided explanations / timed practice / balanced | Yes (balanced) | 10 s |
| 7 | First TCF mini-challenge | 3–4 TCF-flavoured exercises | Each item skippable | 2–3 min |
| 8 | Starting route | « Évaluer mon niveau » (recommended) / « Commencer mon entraînement » | No | 20 s |
| 9 | Your explorer | Name + quick avatar pick | Yes, both | 30 s |
| 10 | Personal TCF campaign | Start today's mission | No | 45 s |

Timing: with the briefing, the first French answer comes at ~4–5 minutes; without it, ~2 minutes. The briefing is interactive (quiz), so it still feels like doing, not reading.

**Moved out of onboarding (on purpose):**
- *Microphone permission* is requested at the first speaking exercise, with an explanation, never during onboarding.
- *Reminders* are offered at the end of the first mission (section C), after the learner has felt the value.
- *Detailed avatar creator* stays on `/avatar`; onboarding offers only presets.
- *Preferred study time* is asked together with reminders, because that is the only place it is used.
- *Hardest skills* (current step) is dropped: the first challenge and diagnostic measure it; asking it adds a question with little value.

### B.2 Step by step

Format for each step: **Sees** (conceptually) · **Céleste says** · **Input** · **After** · **Saved** · **Why** · **Skip** · **Personalization** · **Exit and return**.

Céleste's lines are shown in the guidance language chosen at step 0; French lines always appear in French with the translation underneath for A1–A2 learners. Examples below are given in English guidance mode with the French Céleste uses.

#### Step 0 · Guidance language
- **Sees:** the TCF Quest mark and two large buttons.
- **Céleste says:** nothing yet (she appears at step 1). Text: "Choose the language for explanations. You'll learn in French either way."
- **Input:** English · Français.
- **After:** the whole interface switches immediately; the choice can be changed anytime in Settings.
- **Saved:** `ui_language`.
- **Why:** beginners need explanations they understand; advanced learners prefer full immersion.
- **Skip:** no (one tap).
- **Personalization:** sets the "French immersion dial" start (section F.6).
- **Exit and return:** resumes here.

#### Step 1 · Welcome
- **Sees:** Céleste on the night map of France, a short line, one button.
- **Céleste says:** « Bonjour ! Moi, c'est Céleste. » *Hi! I'm Céleste. I draw the maps of this expedition. Together, we'll take your French all the way to the TCF Canada, one short mission a day.*
- **Input:** "Let's go" (primary). Secondary: a small 🔊 to hear the line (generated voice).
- **After:** Céleste: « C'est parti ! » and step 2 slides in.
- **Saved:** `onboarding_step = 2`, `onboarding_started_at`.
- **Why:** sets tone and promise in under 15 seconds; no marketing page.
- **Skip:** no.
- **Personalization:** none.
- **Exit and return:** resumes at step 2 with « Re-bonjour ! On continue ? »

#### Step 2 · Motivation
- **Sees:** a question and 6 choices, each with a small icon.
- **Céleste says:** *What brings you to French?*
- **Input (one choice):** TCF Canada / immigration · Work in French · Studies · Speak with confidence · Reach an advanced level · Just exploring.
- **After:** a one-line reaction tailored to the choice, then auto-advance after 1 s (or tap):
  - Immigration: *Great choice. The TCF Canada reports a separate result for each of the four skills, so we'll keep all four strong.* (No eligibility advice is ever given.)
  - Speak with confidence: *Then we'll talk a lot. And the TCF will reward it: speaking is one of the four scores.*
- **Saved:** `motivation`.
- **Why:** makes the experience feel personal; drives example themes (work vs studies vs daily life).
- **Skip:** "Just exploring".
- **Personalization:** picks story flavour and example topics; never changes the exam focus.
- **Exit and return:** resumes here with the previous choice preselected.

#### Step 3 · Target
- **Sees:** a question and 4 choices; a small "What's the difference?" link.
- **Céleste says:** *What do you want to reach?*
- **Input:** A TCF Canada result (for immigration) · B2 · C1 · C2 (long term) · I'm not sure yet.
  - If "TCF Canada result": follow-up chips on the same screen: **NCLC 7** (minimum for Express Entry) · **NCLC 9** (more points) · **NCLC 10** (≈ C1) · Not sure.
- **"What's the difference?"** opens a 3-line explainer: *CEFR (A1–C2) describes your French in general. The TCF Canada gives a score per skill. Canada converts those scores to NCLC levels. We track all three separately and always show which one we mean.*
- **After:** *NCLC 9 it is. That's roughly a strong B2 in every skill. We'll get there step by step.*
- **Saved:** `target_nclc` (default 7 if CEFR or "not sure"), `target_cefr` (default C1 if TCF chosen).
- **Why:** gives every later recommendation a destination.
- **Skip:** "Not sure" → NCLC 7 and C1, both editable on the roadmap.
- **Personalization:** sets the planner's gap calculation and the roadmap milestones.
- **Exit and return:** resumes here.

#### Step 4 · Exam date
- **Sees:** three choices.
- **Céleste says:** *Do you have a TCF date?*
- **Input:** Yes, I have a date (date picker appears) · Not yet · I'm not sure I'll take it.
- **After:**
  - Date < 8 weeks away: *Then we'll focus: shorter story, more exam-style practice.* (sets sprint mode)
  - Date ≥ 8 weeks: *Plenty of time to build solid skills.*
  - Not yet: *No problem. You can add it anytime.*
- **Saved:** `exam_date`, `sprint_mode`.
- **Why:** the date changes the plan's mix (section H.5).
- **Skip:** "Not yet".
- **Personalization:** exam proximity weighting.
- **Exit and return:** resumes here.

#### Step 5 · Comfort with French
- **Sees:** five choices, each with a tiny French example so the learner can recognise their level.
- **Céleste says:** *How comfortable do you feel in French today?*
- **Input:**
  1. I'm just beginning. *(e.g. « Bonjour, merci »)*
  2. I understand basic French. *(« Je voudrais un café »)*
  3. I can handle everyday conversations. *(« Mon train a du retard, je vais arriver vers midi. »)*
  4. I can discuss familiar topics confidently. *(« À mon avis, le télétravail a plus d'avantages que d'inconvénients. »)*
  5. I can communicate about complex subjects. *(« Bien que cette réforme soit contestée, elle répond à un besoin réel. »)*
- **After:** *Thanks! Let's try a few quick ones together. No pressure, this isn't a test.*
- **Saved:** `self_rating` (1–5). **Not** written to the skill estimates.
- **Why:** chooses the band of the first challenge so it is neither humiliating nor boring.
- **Skip:** no; it is one tap and needed for step 7.
- **Personalization:** first-challenge band: 1–2 → A1–A2 set, 3 → A2–B1 set, 4–5 → B1–B2 set.
- **Exit and return:** resumes here.

#### Step 6 · Daily time
- **Sees:** 10 / 20 / 30 / 45 / 60+ minutes, with a one-line consequence under each.
- **Céleste says:** *How much time can you give the expedition each day?*
- **Input:** one choice; default highlighted: 20.
- **After:** *20 minutes a day is about 2 h 20 a week. Steady beats heroic.*
- **Saved:** `daily_minutes`.
- **Why:** sizes daily missions; avoids plans the learner can't keep.
- **Skip:** default 20.
- **Personalization:** mission length and number of review items per day.
- **Exit and return:** resumes here.

#### Step 7 · First challenge ("Premiers pas")
- **Sees:** 4–5 short exercises in the normal exercise player (section E), with a small progress bar.
- **Céleste says (before):** *Here's how we'll learn: you try, I react, we go on.*
- **Content:** chosen from the band set at step 5. Each item is checked instantly with full feedback.

  *A1–A2 set:*
  1. **Listen and choose.** Audio: « Bonjour, je m'appelle Léa. » → *Hello, my name is Léa.* / *Goodbye, Léa.* / *Léa is my friend.*
  2. **Arrange the words.** Target: « Je voudrais un café, s'il vous plaît. » Tiles: je · voudrais · un · café · s'il · vous · plaît, plus distractors *veux*, *une*.
  3. **Type the missing word.** « Nous ___ à Paris. » (verb *habiter*) → **habitons**.
  4. **Select the meaning.** « Où est la gare ? » → *Where is the station?*
  5. **Optional: say it.** « Bonne journée ! » with a "Try speaking" button and a "Not now" link.

  *B1–B2 set:*
  1. **Listen and choose.** « Désolée, le train de 8 h 15 est supprimé à cause d'une grève. » → Pourquoi le train ne part-il pas ? *À cause d'une grève.* / *Il est en retard.* / *Il est complet.*
  2. **Arrange the words.** « Si j'avais su, je serais venu plus tôt. »
  3. **Type the missing word.** « Il faut que tu ___ demain. » (venir) → **viennes**.
  4. **Read and choose.** A 3-line notice from a residents' association about bike parking; question on its purpose.
  5. **Optional: say it.** « Je vous appelle au sujet de ma commande. »

- **Adaptive rule:** two wrong answers in a row → next item drops one band; two right with no hints in the A1–A2 set → offer *"That was easy? Want a harder one?"*
- **After:** a summary card: *4 sur 5 ! You understood a station announcement and built a conditional sentence.* No CEFR level is shown.
- **Saved:** each answer as an `attempt` with `context = onboarding`. These count as **weak evidence** only (training mode, few items).
- **Why:** the first success; teaches the controls; gives the engine a first signal.
- **Skip:** each item has "Skip"; skipping all still continues.
- **Personalization:** nudges the recommended route at step 8.
- **Exit and return:** resumes at the next unanswered item.

#### Step 8 · Starting route
- **Sees:** two large choices with benefits and limits, one marked "Recommended for you".
- **Céleste says:** *How do you want to start?*
- **Input:**
  - **Discover my level** · *About 25 minutes, in 4 short parts you can spread over the week. Gives you a real starting estimate per skill and lets you skip what you already know.*
  - **Start learning now** · *Jump into your first mission. We'll measure your level little by little as you go. Your starting point stays provisional for now.*
- **Recommendation rule (revised, R1):** « Évaluer mon niveau » is recommended by default, presented as four short parts. Only self-rating 1 ("I understand very little French") recommends « Commencer mon entraînement », because a diagnostic would mostly confirm "beginner" and discourage.
- **After:** either the first diagnostic part starts after step 10, or the first mission does.
- **Saved:** `start_route`.
- **Why:** the learner chooses between accuracy now and fun now, with the trade-off explained.
- **Skip:** no, but either path leads to the other later (the guided path schedules diagnostic parts into the first week).
- **Exit and return:** resumes here.

#### Step 9 · Your explorer
- **Sees:** a name field and 8 preset explorer avatars (varied, no inference from answers), plus "Create my own later".
- **Céleste says:** *Last thing: what should I call you?* Then *Pick an explorer, or design your own later.*
- **Input:** name (optional, 1–40 chars); one preset or "later".
- **After:** *Enchantée, Alex !*
- **Saved:** `display_name` (if left empty, the app says "Explorer", a neutral word), `avatar_preset`.
- **Why:** identity is fun and motivating once the learner has invested a little.
- **Skip:** both parts.
- **Personalization:** cosmetic only; never used for assessment. The app never guesses appearance, gender or personality from answers.
- **Exit and return:** resumes here.

#### Step 10 · Roadmap
- **Sees:** a vertical summary that scrolls naturally:
  1. **Where you start:** "Provisional: around A2–B1" (from challenge + self-rating, wide range, labelled *provisional*) or "Measured: listening B1, reading B2…" after the diagnostic.
  2. **Your target:** NCLC 9 (and personal goal C1).
  3. **Main priorities** (max 3): e.g. *Speaking practice · Listening speed · Verb tenses*.
  4. **First chapter:** Chapitre II, La Vie Quotidienne (Paris, Belleville).
  5. **Today's mission:** title, length, skill, reason.
  6. **Next milestone:** *Complete 3 missions and your first weekly trial (Sunday).*
- **Céleste says:** *Here's your map. Today's mission takes about 12 minutes.*
- **Input:** "Start today's mission" (primary) · "Later" (goes to Home).
- **Saved:** `onboarded_at`, first `study_plan`.
- **Why:** turns answers into a visible plan and a single next action.
- **Exit and return:** Home shows the same mission.

### B.3 Branching summary

```
0 language → 1 welcome → 2 motivation → 3 target ─┬─ TCF chosen → NCLC chips
                                                   └─ CEFR / not sure → defaults NCLC 7
→ 4 exam date ─┬─ < 8 weeks → sprint_mode = on
               └─ otherwise → off
→ 5 comfort (1–5) → picks challenge band
→ 6 daily time
→ 7 first challenge (adaptive band)
→ 8 route ─┬─ Discover → diagnostic part 1 right after step 10
           └─ Guided  → first mission; diagnostic parts scheduled in week 1
→ 9 explorer (optional) → 10 roadmap → mission
```

### B.4 Data saved during onboarding

| Field | Step | Used by |
| --- | --- | --- |
| `ui_language` | 0 | All text, immersion dial |
| `motivation` | 2 | Story flavour, example topics |
| `target_nclc`, `target_cefr` | 3 | Planner gap, roadmap |
| `exam_date`, `sprint_mode` | 4 | Planner mix, countdown |
| `self_rating` | 5 | First challenge band, route recommendation (never estimates) |
| `daily_minutes` | 6 | Mission size, review quota |
| onboarding `attempt` rows | 7 | Weak evidence, provisional range |
| `start_route` | 8 | Diagnostic scheduling |
| `display_name`, `avatar_preset` | 9 | Cosmetic |
| `onboarding_step`, timestamps | all | Resume |
| `onboarded_at`, first `study_plan` | 10 | Home |

---

## C. First-session storyboard (first 10–15 minutes)

Learner: Alex, self-rating 3 ("everyday conversations"), target NCLC 9, no exam date, 20 min/day, chooses "Start learning now".

| Time | What happens | What the learner feels |
| --- | --- | --- |
| 0:00 | Picks English for explanations. Céleste: « Bonjour ! Moi, c'est Céleste. » | Welcomed, no form |
| 0:20 | Motivation: immigration. *Your lowest skill counts the most, so we'll keep all four strong.* | "This app knows my situation" |
| 0:40 | Target NCLC 9; exam date "Not yet"; comfort 3; 20 minutes | Quick, light |
| 1:30 | **First challenge** (A2–B1 set). Item 1: hears « Mon train a du retard, je vais arriver vers midi. » and picks the meaning. Instant ✓ and *Bien joué ! « avoir du retard » = to be late (for transport).* | First success at ~1:40 |
| 2:30 | Arranges « Est-ce que vous pourriez répéter, s'il vous plaît ? »; misplaces *pourriez*. Feedback shows the right order and: *In questions with « est-ce que », the order stays subject + verb.* Saved for review. | Mistake felt safe |
| 3:30 | Types « Hier, nous ___ (aller) au marché. » → writes *allés*. Partial: *Close! With « nous » you need the auxiliary too: « sommes allés ».* | Learns something |
| 4:00 | Optional speaking item. Taps "Not now". No permission asked. | No pressure |
| 4:20 | Summary: *3 sur 4. You understood an announcement and built a polite question.* | Competent |
| 4:40 | Route: chooses "Start learning now". | In control |
| 5:00 | Name "Alex", picks a preset explorer. *Enchantée, Alex !* | Ownership |
| 5:30 | Roadmap: *Provisional start: around A2–B1. Target NCLC 9. Priorities: speaking, listening, past tenses.* First mission: **Le Marché de Belleville (A2 version), 12 min, speaking. Why: speaking is the skill most learners lose NCLC points on, and we haven't heard you yet.** | Clear path |
| 6:00 | **Mission starts.** Intro: an illustrated market street, narration: « Samedi matin, au marché de Belleville. Madame Roux, la fromagère, a l'air inquiète… » | Story, curiosity |
| 6:40 | Objective card: *Today: explain a problem politely on the phone (« Je voudrais… », « Pourriez-vous… »).* | Knows the goal |
| 7:00 | Listening: dialogue between Madame Roux and a customer; question: *What is missing this morning?* → *la livraison de comté*. ✓ | |
| 8:00 | Mini-lesson (30 s): *Polite requests: « Je voudrais savoir… », « Pourriez-vous me rappeler ? » The conditionnel softens a request.* Two tap examples with audio. | Short, useful |
| 8:40 | Arrange: « Pourriez-vous me rappeler avant midi ? » ✓ | |
| 9:20 | Fill in: « Je ___ savoir si la livraison arrive aujourd'hui. » (vouloir, polite) → *voudrais*. ✓ | |
| 10:00 | **First speaking.** Céleste: *Now you talk. I'll need your microphone, only while you hold the button. Recordings stay on this Mac.* Learner allows the browser prompt. Repeats « Je vous appelle au sujet de la livraison. » Transcript shown, ✓ *Clear and complete.* | Speaking feels doable |
| 11:00 | **Apply:** leave a 30-second voicemail for the supplier (A2 version: guided with 3 prompts on screen: who you are · the problem · what you'd like). AI feedback: task done ✓, 1 correction, 1 better phrasing. | Real communication |
| 12:30 | Mastery check: 2 quick items mixing today's forms. | |
| 13:00 | **Mission complete.** Madame Roux: « Merci, vous m'avez sauvé la matinée ! » Stamp "Belleville" lands on the map. +XP (effort), *Competency « demande polie » : getting stronger (2 of 5 pieces of evidence).* | Accomplishment |
| 13:30 | **Reminders offer:** *Want a nudge tomorrow at the same time? I'll only remind you about your mission and reviews.* Choices: time chip (suggested: now, 19:30) · "No thanks". | Asked after value |
| 14:00 | Next step card: *Tomorrow: « Le Bus de 8 h » (listening, 10 min). Your 2 review items will be in the warm-up.* Diagnostic part 1 also suggested: *Optional today: 6-minute listening check to sharpen your plan.* | Knows what's next |

**Why the first mission is Belleville at A2 here:** the mission exists in three versions of the same story (A1, A2, B1; section G.4). The learner always gets the story, at a level that lets them succeed.

---

## D. Navigation and screen inventory

Five tabs (decided): **Aujourd'hui · Aventure · Entraînement · Progression · Professeur**. Missions, exercises and exams open full-screen over the tabs (the tab bar hides) so the learner focuses.

### D.1 Onboarding (full-screen, no tabs)
| Screen | Purpose | Main interactions |
| --- | --- | --- |
| Guidance language | Pick explanation language | Two buttons |
| Céleste conversation steps (1–6, 8–10) | One question each | Choice chips, back, continue later |
| First challenge | First success | Exercise player |
| Roadmap | Plan reveal | Start mission / later |

### D.2 Aujourd'hui (Home)
| Screen / element | Purpose | Interactions |
| --- | --- | --- |
| Today's mission card (top) | The one next action: title, skill, minutes, reason | Start · "Swap" (shows 2 alternatives) · "Shorter today" (10-minute version) |
| Review strip | Due reviews (max 10/day) | Start review |
| Week rhythm | Days studied this week vs goal, rest days | Tap → week view |
| Next event | Weekly trial / boss date | Tap → details |
| Avatar slot | Identity, next skin progress | → Avatar page |
| Céleste note (optional, 1 line) | Context ("Welcome back!") | Dismiss |

### D.3 Aventure
| Screen | Purpose | Interactions |
| --- | --- | --- |
| France map | Chapters, current position | Tap region |
| Chapter path | Ordered nodes (missions, reviews, checkpoints, boss) with states | Tap node → mission sheet |
| Mission sheet | Goal, length, skills, state, best result | Start / Practise again / Locked reason |
| Boss gate | Requirements and readiness | Start boss (when unlocked) |
| Chapter test-out | Skip a chapter by demonstrating mastery | Start test-out |

### D.4 Entraînement (free practice)
| Screen | Purpose | Interactions |
| --- | --- | --- |
| Practice hub | Four skills + grammar, vocabulary, mistakes, simulator | Pick |
| Skill practice | Exercise sets by task type and level | Training / Exam mode toggle |
| Mistake notebook | Recurring mistakes grouped by category | Drill one · Mark understood · See examples |
| Vocabulary review | Spaced cards from missions | Review |
| Writing studio | TCF writing tasks T1–T3 | Write, save draft, submit |
| Speaking studio | Free conversation scenarios, examiner tasks | Pick scenario |
| Simulator lobby | Full or section exams, rules | Start (unlocks after chapter II checkpoint or on request) |
| Exam runner | Strict exam conditions | Answer, timer |
| Exam report | Per-skill estimates, review | Review items, add to plan |

### D.5 Progression
| Screen | Purpose | Interactions |
| --- | --- | --- |
| Skills overview | Four skills: CEFR range + confidence, TCF estimate range when enough evidence, NCLC equivalent | Tap skill → details |
| Skill detail | Trend, evidence count, strongest/weakest competencies | Practise this |
| Weekly reports | History of weekly trials | Open report |
| Monthly review | Larger milestones, readiness | Open |
| Goals | Change target, exam date, daily time | Edit (plan recalculates) |

### D.6 Professeur
| Screen | Purpose | Interactions |
| --- | --- | --- |
| Tutor chat | Ask questions in text; context-aware | Type, ask "why?" from any feedback |
| Role-play picker | Scenarios by level (café, gare, entretien d'embauche, visite d'appartement, débat, oral du TCF) | Start |
| Conversation | Turn-based voice/text dialogue | Speak, type, replay, end |
| Conversation review | Transcript + corrections | Save corrections to notebook |
| AI status | Ollama / speech engines | Help |

### D.7 Shared overlays
Exercise player · feedback sheet · "Report a problem" sheet · microphone permission explainer · reminders offer · settings (language, narration, immersion dial, corrections timing, data backup, retake diagnostic) · avatar and wardrobe.

---

## E. Exercise interaction specification

### E.1 Shared lifecycle (all exercise types)

```
presented → answering → submitted → checking → feedback(correct | partial | incorrect | uncertain) → continue
                ↑                                   │
                └──────────── retry (if allowed) ───┘
```

- **Presented:** prompt, media and instructions appear; audio autoplays once in training if the learner has autoplay on (default on, off if narration muted).
- **Answering:** the primary button reads **Vérifier** (Check) and stays disabled until an answer exists. Enter key submits.
- **Submitted:** the answer is saved immediately (`attempt` row with response, time taken, hints used, mode).
- **Checking:** keyed items are checked locally (< 100 ms). AI-checked items show "Céleste is reading your answer…" with an estimate, cancellable.
- **Feedback:** a bottom sheet (colour + icon + words, never colour alone) with: verdict, correct answer, one-line reason, optional "Why?" (opens the tutor with this item as context), "Report a problem". The primary button becomes **Continuer**.
- **Retry policy:** in lessons, an incorrect keyed item is re-queued once at the end of the mission (with a variant if one exists). Speaking and writing can be retried immediately once. No retries in exam mode.
- **Can't listen / can't speak now:** two toggles in the player. When on, audio items are replaced by text equivalents and speaking items by typing, for 15 minutes. These attempts are tagged so they don't count as listening/speaking evidence.
- **Keyboard and screen reader:** every interaction has a keyboard path (tiles selectable by number keys, arrows to reorder); audio has a transcript button after answering; feedback is announced politely (`aria-live`).
- **Hints:** max one per item in training ("Show first letter", "Show the rule", "Slow audio"). A hinted correct answer counts as weaker evidence (×0.5).
- **XP:** +10 per answered item, +5 bonus for a correct first try, +20 for mission completion. XP never unlocks anything.
- **Evidence:** every attempt updates the competency mastery (section H.2), its skill's evidence count (exam/no-hint attempts only for level estimates) and, if wrong, the mistake notebook.

### E.2 Answer-checking rules for typed French

| Case | Example | Verdict |
| --- | --- | --- |
| Case and outer punctuation | « habitons. » vs « Habitons » | Correct |
| Apostrophe styles | s'il / s’il | Correct |
| Missing accent that does not change the word | *ete* for *été* | Correct with a note: *Watch the accent: « été ».* |
| Accent that changes the word | *a* for *à*, *ou* for *où*, *du* for *dû* | Incorrect, with the contrast explained |
| Agreement or conjugation error | *allé* for *allés*, *vient* for *vienne* | Incorrect (or partial if the stem is right) |
| Typo of one letter in a long word (≥ 7 letters), not a grammar ending | *restaurent* for *restaurant* | Partial: *Almost: « restaurant ».* |
| Listed alternative | *voudrais* / *souhaiterais* | Correct |
| Unknown but possibly valid alternative | — | Incorrect for now, with "I think my answer should be accepted" prominent |

### E.3 Exercise types

**1 · Select the correct answer (read)**
- *Objective:* recognise meaning, form or usage.
- *Instructions:* « Choisissez la bonne réponse. »
- *Interaction:* 2–4 options; one tap selects, Vérifier submits.
- *Correct:* ✓ + 1-line why if the item has a teaching point.
- *Incorrect:* shows correct option and why the chosen distractor is wrong (each distractor has its own explanation in content).
- *Hints/retry:* no hint; re-queued once.
- *Accessibility:* options are buttons with full text; keys 1–4.
- *Scoring:* binary.
- *Done when:* answered.
- *Errors:* none expected.
- *Engine:* competency mastery; reading evidence only if the item is a reading item.

**2 · Listen and choose**
- *Objective:* understand spoken French (gist, detail, inference).
- *Instructions:* « Écoutez et choisissez. »
- *Interaction:* play (autoplay once); replay ×2 in training; 0.75× "slow" in training only; options appear after the first play ends (prevents reading-first).
- *Correct / incorrect:* as type 1, plus the transcript is revealed with the key phrase highlighted.
- *Hints:* slow audio counts as a hint.
- *Accessibility:* "Can't listen now" replaces with a transcript-based reading item (tagged as reading).
- *Errors:* audio fails → retry once, then show transcript and mark the attempt "audio-failed" (no listening evidence).
- *Engine:* listening evidence weighted by difficulty and number of plays (1 play = full, 2 = 0.8, 3+ or slow = 0.5).

**3 · Arrange the words**
- *Objective:* word order, syntax, chunks.
- *Instructions:* « Remettez les mots dans l'ordre. »
- *Interaction:* tap tiles into the answer line; tap a placed tile to send it back; drag to reorder; "Clear"; 1–3 distractor tiles above A2.
- *Correct:* ✓ + the sentence plays as audio.
- *Incorrect:* shows the correct sentence with misplaced tiles highlighted; explains the rule (e.g. pronoun before verb: « je **le** vois »).
- *Alternatives:* content lists valid orders (« Demain, je pars » / « Je pars demain »).
- *Accessibility:* number keys pick tiles; Backspace removes the last.
- *Scoring:* binary; partial if only one tile is swapped (counts 0.5).
- *Engine:* grammar competencies tagged on the item.

**4 · Type the missing word**
- *Objective:* active recall of form (conjugation, agreement, preposition, vocabulary).
- *Instructions:* « Complétez la phrase. » + base form in brackets when needed: « Il faut que tu ___ (venir). »
- *Interaction:* text field; an accent bar (é è ê à ç ô û ï œ) for keyboards without French layout.
- *Checking:* rules in E.2.
- *Hint:* first letter, or the rule.
- *Engine:* strongest evidence among keyed types (recall > recognition), weight ×1.2.

**5 · Repeat a spoken sentence**
- *Objective:* produce a model sentence aloud; build confidence and fluency.
- *Instructions:* « Écoutez, puis répétez. »
- *Interaction:* model audio → hold-to-talk or tap-to-start/tap-to-stop → transcript → feedback.
- *Checking:* compare the transcript to the target, word by word, ignoring punctuation and case.
  - All words matched → ✓ *Clear and complete.*
  - 1–2 words differ → *We heard « … ». If that's not what you said, the recogniser may have missed it.* Offer "Try again" or "Continue".
  - Recogniser low confidence (section F.4) → *I couldn't hear clearly.* Retry; after 2 failed tries, offer "Continue without speaking" (no penalty).
- *What we never do:* claim a pronunciation error from a transcription mismatch. Feedback speaks about **what was understood**, not about the learner's accent (section J).
- *Engine:* "speaking production" evidence is light (repetition ≠ free speech); counts toward fluency practice only.

**6 · Interactive conversation**
- *Objective:* real spoken interaction in a situation, at the learner's level.
- *Flow:* section F.
- *Scoring:* per learner turn, the AI rates task relevance, comprehensibility, grammar, vocabulary range on a 0–3 scale, with a confidence flag. Summary at the end.
- *Done when:* the scenario goal is reached (e.g. "you booked a table") or after N turns (A2: 4, B1: 6, B2+: 8), or the learner ends it.
- *Engine:* speaking evidence (medium weight; AI-rated, so marked `ai_scored`); errors go to the notebook with the learner's original sentence.

**7 · Reading comprehension**
- *Objective:* understand written texts of growing complexity (notice → email → article → opinion piece), matching TCF reading task types.
- *Interaction:* text on top (scrollable), 1–4 questions below; on phones the text collapses to a "Show text" button while answering.
- *Hints:* "Highlight where the answer is" (training only; counts as hint).
- *Engine:* reading evidence weighted by text level and time spent vs target time.

**8 · Writing challenge**
- *Objective:* produce a text for a task (message, article, argued opinion), TCF T1–T3 style.
- *Interaction:* prompt + word counter with target range (shown as a band) + optional timer; draft autosaves every 5 s; submit.
- *Feedback (AI, rubric-bound):* the learner's text stays visible; feedback shows 2–3 **strengths**, 2–3 **priority fixes** (each: the original phrase, a correction, the rule), and one **improved model paragraph**. Acceptable alternative phrasings are not "corrected"; style suggestions are labelled "optional".
- *Scoring:* rubric 0–3 on task completion, coherence, vocabulary, grammar; an estimated range out of 20 appears only after ≥ 3 calibrated tasks.
- *Errors:* AI unavailable → the text is saved and queued; *Your text is safe. Feedback will be ready when the local AI is back.*
- *Engine:* writing evidence (`ai_scored`), mistakes to notebook.

**9 · TCF-style exam task**
- *Objective:* rehearse the exact format: timing, instructions, single audio play, no help.
- *Interaction:* exam runner only; plain interface; timer; no feedback until the end.
- *Scoring:* keyed items exact; productive tasks rubric-scored after the section.
- *Engine:* highest-weight evidence for estimates (section H.1).

### E.4 How missions vary by focus

The 10-part structure (intro → objective → demo → exercise → feedback → harder exercise → context → mastery check → summary → next step) is the default. Each focus changes its centre of gravity:

| Focus | Demo | Exercises | Context | Mastery check |
| --- | --- | --- | --- | --- |
| Grammar | 30-second rule card with 2 audio examples | Arrange → type the form → choose the right form | Short dialogue using the form | 3 mixed recall items |
| Listening | Pre-listening: 3 key words | Listen-and-choose (gist) → detail → inference | Longer audio scene | 2 new items, single play |
| Reading | Strategy tip (« repérez les connecteurs ») | Short text → longer text | Realistic document | 2 questions, timed |
| Writing | Model text with structure highlighted | Arrange paragraph order → complete connectors | Write the task | AI rubric |
| Speaking | Model answer audio | Repeat → guided answer (3 prompts) | Conversation | One free answer, AI rubric |
| Story mission | Narrated scene | Mixed skills following the plot | Character conversation | Mixed |

---

## Feedback system (detail)

### Verdicts

| Verdict | When | What the learner sees | Evidence |
| --- | --- | --- | --- |
| **Correct** | Matches key or listed alternative | ✓ *Bien joué !* + optional 1-line point; continue | Full |
| **Correct but unnatural** | Speaking/writing: grammatical, understood, but not what a native would say | ✓ *Correct.* + *More natural: « Je voudrais savoir où en est ma commande. »* | Full for grammar; style noted |
| **Understandable, grammatically wrong** | Meaning gets through, form is wrong | ◐ *Understood!* + correction + rule | Partial (0.5) |
| **Correct but off-task** | Good French that doesn't answer the question | ◐ *Nice sentence, but the question was about the delivery time.* | Partial (0.3) |
| **Incomplete but promising** | Started well, missing a required part | ◐ *Good start. You still need to say what you'd like her to do.* | Partial (0.5) |
| **Incorrect** | Wrong answer or not understandable | ✗ *Not quite.* + correct answer + reason | None (mistake saved) |
| **Uncertain** | Speech recognition unsure, AI low confidence | ? *I'm not sure I heard you right.* + retry | None |

Tone rules: no exclamation-heavy praise loops; never "wrong!", never sarcasm; corrections start with what worked when something did.

### Learner feedback buttons (on every feedback sheet, behind "…")

| Button | Effect |
| --- | --- |
| Too easy | Planner raises difficulty for this competency by one step; 3 "too easy" in a week on a chapter → offer test-out |
| Too hard | Next items in this competency drop one step; an explanation card is inserted |
| I didn't understand the explanation | Opens the tutor with this item; the explanation is flagged for rewrite if ≥ 2 reports |
| My answer should be accepted | Attempt marked `disputed`, removed from evidence until reviewed; goes to the content review queue |
| Technical problem | Attempt marked `technical`, removed from evidence; logs audio/speech status |

**Review queue:** disputed items are reviewed by the learner (and later a teacher) in a simple local list: accept the answer as a new alternative (evidence restored as correct) or reject with a reason. An item with ≥ 3 accepted disputes is flagged "needs rewrite".

---

## F. Speaking and AI companion experience

### F.1 The conversation loop (what the learner experiences)

Example: **« Au café »** (A2), character **Malik**, a waiter in Belleville.

1. **Scene card** (3 s): *Goal: order a drink and ask for the bill.*
2. **Character speaks.** Text appears as the audio plays (karaoke-style highlight in training): « Bonjour ! Qu'est-ce que je vous sers ? »
3. **Replay** available (training: unlimited; exam: none). A "🐢 slower" option in training.
4. **Your turn.** The mic button pulses gently and the label changes to **À vous !** Nothing records yet.
5. **Recording.** Hold-to-talk (default) or tap-to-start/stop (setting). While recording: a live level meter, an elapsed timer, a red dot, "Release to send". Auto-stop after 45 s (A2) / 90 s (B2+).
6. **Processing.** "Listening to you…" (speech-to-text, target < 3 s) then "Malik is thinking…" (AI, target < 6 s). Steps are shown so the wait feels purposeful.
7. **Transcript.** The learner's words appear in their bubble: « Je voudrais un café crème, s'il vous plaît. » A small "Not what I said?" link sits under it.
8. **Reply.** Malik answers in character, adapted to level: « Très bien, un café crème. Avec ceci ? » Audio plays.
9. **Corrections.** Depending on the learner's setting:
   - *During* (default A1–A2): a small badge on the learner's bubble, e.g. ◐ *« un café crème » ✓ · try « Je voudrais… » → good!* Tap to expand.
   - *After* (default B1+): nothing during the chat; a review at the end.
10. **End.** When the goal is reached: Malik closes the scene (« Voilà l'addition. Bonne journée ! »), then the **conversation review**: transcript, 2–4 corrections with rules, 1 better phrasing per learner turn where useful, scores (task, clarity, grammar, vocabulary) as words, and "Save to notebook".

### F.2 Problems and how the experience handles them

| Situation | What the learner sees | What happens underneath |
| --- | --- | --- |
| **Mic permission never asked** | First speaking item shows an explainer: *I need your microphone to hear you. It only records while you hold the button, and recordings stay on this Mac.* → "Allow microphone" · "Type instead" | Browser prompt only after "Allow" |
| **Permission denied** | *No problem, you can type your answers. You can turn the microphone on later in Settings.* All speaking items switch to typed mode | `mic = denied`; typed answers don't count as speaking evidence; Home suggests re-enabling once a week, not more |
| **Mic hardware fails / no input** | *I can't hear anything from your microphone.* → "Test microphone" (shows a level meter) · "Type instead" | No attempt saved |
| **Empty recording** (silence) | *I didn't catch anything. Try again, a bit closer to the mic?* | Not saved as an attempt |
| **Background noise** | *There's a lot of noise around you. Want to try again or type?* | Detected by low speech probability + high noise level |
| **Recogniser uncertain** | *I'm not sure I heard you right. Here's what I got: « … ».* → "That's right" · "Try again" · "Type what I said" | Low-confidence attempts never count as errors |
| **Wrong transcript** | Learner taps "Not what I said?" → re-record or type the intended sentence | Feedback runs on the corrected text; flagged `typed_correction` (no pronunciation inference) |
| **Slow AI** (> 6 s) | *Malik is still thinking…* with a cancel; > 20 s: *The AI is slow right now.* → "Wait" · "Skip this turn" | Request continues in background |
| **Ollama unavailable** | *The tutor is resting. You can still do missions with checked answers.* Conversation scenarios show "Needs local AI" | Health check; keyed exercises unaffected |
| **Speech engine unavailable** | Speaking items switch to typing automatically with a notice | Same as denied, temporary |
| **TTS unavailable** | Character lines show as text; pre-generated mission audio still plays | Cached audio is preferred everywhere |
| **Restart** | "Restart scene" in the menu: confirms, clears turns, same goal | Previous session saved as abandoned |
| **Interruption** (tab closed mid-conversation) | On return: *Continue your conversation with Malik?* → Continue · Start over | Turns saved after each exchange |
| **Corrections after the conversation** | Review screen, also reachable later from Professeur → History | Stored with model + prompt version |

### F.3 Content vs pronunciation (non-negotiable)

- **Content evaluation** (what was said: task, grammar, vocabulary, coherence) uses the transcript and is reliable enough for practice feedback.
- **Pronunciation evaluation** (how it sounded) is **not** offered in v1. A transcription mismatch is reported as "*I heard…*", never as "*you pronounced it wrong*". Pronunciation drills with real phoneme analysis are a v2 item and need a tool validated on French first.

### F.4 Recogniser confidence (technical rule, plain words)

The speech-to-text engine reports how sure it is. If the average confidence is low, or the "no speech" probability is high, the turn is marked **uncertain**: shown to the learner, never counted as a mistake, never used for scoring.

### F.5 The companion system

**Céleste**, a cartographer, is the single guide. Other characters belong to the story and to practice:

| Role | Who | Appears | Voice |
| --- | --- | --- | --- |
| Onboarding guide, learning guide, narrator | **Céleste** | Onboarding, mission intros, objective cards, summaries, Home note | Warm, brief, a little playful |
| Practice partners | Story characters per chapter: Madame Roux (fromagère), Malik (serveur), Inès Haddad (journaliste), Théo Lambert (animateur radio), Bastien (débatteur) | Missions and role-plays | In character, level-adapted |
| Exam coach | **Céleste** in "coach" mode | Before/after trials, bosses, simulator lobby | Calm, factual |
| Examiner | **M. Delorme** | Boss and exam speaking tasks only | Neutral, formal, never encouraging mid-task |

**When Céleste speaks:** onboarding steps; mission start (1 line); objective (1 line); after a mission (1–2 lines); first time a feature appears; when the learner seems stuck (rule below); welcome back after ≥ 3 days.

**When she stays silent:** during exercises (feedback sheets speak instead); during exams; during conversations with other characters; whenever narration is set to "minimal".

**Length:** ≤ 2 sentences, ≤ 25 words per message; one idea per message.

**Register:** Céleste says **tu** (a friendly companion). Story characters say **vous** in service and formal situations (shop, phone, interview) and **tu** among friends, so the learner hears both registers in context. The examiner always says **vous**.

**Immersion dial (guidance language changes with level):**

| Estimated level | Céleste's language (if guidance = English) |
| --- | --- |
| A1 | English, with short French greetings and key words |
| A2 | Mix: French first line, English explanation |
| B1 | French by default, English on tap ("Translate") |
| B2+ | French only; explanations in simple French |

The learner can override the dial in Settings.

**Avoiding repetition:** each message type has a pool of ≥ 8 variants; the last 20 lines shown are remembered and not reused; lines can reference real context (*« Deuxième mission cette semaine ! »*, *« La dernière fois, le subjonctif t'a résisté. Revanche ? »*).

**Context memory:** Céleste's lines are generated from a template plus facts (last mission, streak week, weakest skill, recent mistake category), not free AI chat, so they stay short, accurate and fast. The AI is used only in conversations and explanations.

**Frustration handling:**
- 2 wrong answers in a row on the same competency → *Let me show you a trick.* + a 20-second rule card, then an easier variant.
- 3 in a row → *This one is tricky. Let's park it for later.* The item goes to review; the mission continues with something achievable.
- Mission accuracy < 50% → the summary is gentle (*Tough one today. It's saved, and we'll come back to it with more help.*) and the next mission is set one step easier.
- The learner taps "Too hard" twice in a session → Céleste offers a shorter mission or a review session.

**Muting:** Settings → Narration: Full (voice + text) · Text only · Minimal (only essential instructions). A mute toggle also sits in the mission menu.

---

## G. Adventure progression

### G.1 Chapters and their educational objectives

Chapters are story stages that map to CEFR bands and TCF skills. They are **not** official levels.

| Chapter | Place | Band | Can-do objectives (examples) | TCF link |
| --- | --- | --- | --- | --- |
| I · Le Premier Pas | Normandie | A1–A2 | Introduce yourself; numbers, times, prices; present tense of common verbs; understand slow simple announcements | Easiest listening/reading items; speaking T1 basics |
| II · La Vie Quotidienne | Paris, Belleville | A2–B1 | Explain a problem politely; passé composé vs imparfait; understand everyday dialogues and notices; write a short message | Writing T1 (message); speaking T1–T2 |
| III · La Cité des Idées | Lyon | B1–B2 | Give and justify an opinion; connectors (« pourtant », « en revanche »); understand radio interviews; write an article | Writing T2; speaking T2–T3; mid-band MCQs |
| IV · Le Labyrinthe des Arguments | Strasbourg | B2–C1 | Argue and counter-argue; subjonctif, concession; compare two documents; understand debates | Writing T3; speaking T3; upper-band MCQs |
| V · La Maîtrise | Pyrénées, observatoire | C1–C2 | Nuance, abstraction, register shifts; dense texts; long argued speech | NCLC 10 territory; beyond the exam |

Each chapter has **10–14 path nodes** built from ~20–30 competencies.

### G.2 Node types on a chapter path

| Node | Purpose | Recommended / optional |
| --- | --- | --- |
| Story mission | Plot + mixed skills (e.g. Le Marché de Belleville) | Recommended |
| Skill lesson (listening, reading, speaking, writing, grammar, vocabulary) | Focused practice of 2–4 competencies | Recommended |
| Review | Mistakes and fading competencies from this chapter | Inserted automatically when due |
| Checkpoint | 10-minute mastery check of a chapter segment | Recommended (gates the boss) |
| Recovery | Targeted practice after a failed checkpoint/boss | Appears only when needed |
| Side quest | Optional extra stories, culture, Québec French | Optional |
| Boss | Chapter-level exam-format challenge | Required to open the next region |

### G.3 Node states and rules

| State | Rule to enter it |
| --- | --- |
| **Locked** | Its prerequisite node is not completed, and no test-out covers it |
| **Available** | Prerequisite completed, or chapter tested out, or recommended by the planner as recovery |
| **In progress** | Started; resumable at the exact step |
| **Completed** | All steps finished (any score). Gives XP. Unlocks the next node. |
| **Mastered** | Completed **and** its competencies reach mastery (p ≥ 0.85, ≥ 5 attempts over ≥ 2 days, ≥ 1 without hints) |
| **Needs review** | Mastered/completed, but a competency's review date has passed or recent accuracy dropped below 70% |

- Completing ≠ mastering: the path lets learners move on after completing (so nobody is stuck), but the **boss** opens only when ≥ 80% of the chapter's competencies are mastered and all checkpoints are passed (≥ 70%).
- **Test-out:** at any chapter start, "I already know this" opens a 12-minute chapter test. ≥ 80% overall with ≥ 70% in each skill → the chapter is "charted": nodes become optional, the boss stays available as a challenge, the next chapter opens. Fails → no penalty; the result places the learner on the right node.
- **Revisit:** completed nodes can be replayed anytime ("Practise again"); replays give reduced XP and normal mastery evidence (with new item variants where available).
- **Free practice** (Entraînement) is always open regardless of the path.

### G.4 One story, three levels

Story missions exist in up to three versions (e.g. Le Marché de Belleville A1 / A2 / B1): same plot and characters, different language load and task. The planner serves the version matching the learner's current estimate for the mission's main skill. This lets every learner enjoy the same story without being blocked or bored.

### G.5 Weekly trial, chapter boss, full exam: three different things

| | Weekly trial | Chapter boss | Full TCF practice exam |
| --- | --- | --- | --- |
| Purpose | Check recent learning; update the plan | Prove chapter-level ability; open the next region | Rehearse the real exam; readiness estimate |
| When | Once a week (default Sunday, learner can move it) | When unlocked (G.3) | On demand after chapter II, every 3–4 weeks suggested, weekly in the last month before an exam date |
| Length | 20–30 min | 30–40 min | ~2 h 45 (or one section at a time) |
| Content | Mixed items from this week's competencies + 1 short productive task | Exam-format tasks themed on the chapter (« Le Conseil de quartier » for speaking T3) | Exact TCF Canada structure (verified against FEI before release) |
| Story | Light framing (Céleste: « Petit bilan de la semaine ») | Story framing before and after; examiner M. Delorme during | None: plain interface, official-style instructions |
| Help | No hints; untimed except the productive task | No hints; timed per task | No hints; strict timing; one audio play |
| Feedback | Immediately after: per-skill change, top 3 mistakes, next week's focus | Pass/fail per skill with reasons; recovery missions if failed | After the whole exam: per-skill estimate with range, pacing, item review |
| Retry | Next week | After recovery missions; different items | Another form after 2 weeks |

Rewards: trial → XP + "week completed" stamp; boss → region unlocked + chapter stamp + (if level threshold reached) skin progress; exam → no game rewards (deliberately).

### G.6 Rewards

- **XP:** effort (items, missions, streak weeks). Shown, never spent, never unlocks.
- **Stamps:** places visited on the map (missions completed in a region).
- **Skins:** earned when the weakest skill reaches a level (already built).
- **Achievements:** real behaviour only: "First conversation", "10 speaking missions", "A mistake category cleared", "First full exam".

---

## H. Personalization logic

### H.1 Evidence the engine uses

| Evidence | Source | Weight for skill estimates |
| --- | --- | --- |
| Exam-mode items (simulator, bosses) | Keyed / rubric | 1.0 |
| Diagnostic items | Keyed / rubric | 1.0 |
| Weekly trial items | Keyed / rubric | 0.8 |
| Mission items without hints | Keyed | 0.4 |
| Mission items with hints or replays | Keyed | 0.2 |
| AI-scored speaking/writing in missions | Rubric (AI) | 0.3, and only when the AI's two scorings agree |
| Onboarding challenge | Keyed | 0.1 |
| Self-rating | Learner | 0 (only picks starting content) |

Item difficulty is attached to every keyed item (CEFR band + within-band step). Easy items barely move an advanced estimate: an item counts toward a level only if its difficulty is within one band of that level. **Answering 100 A2 items correctly never produces a B2 estimate.**

### H.2 Three models (plain words)

1. **Skill estimate** (4 skills, separate): a level range and confidence, computed from weighted evidence. Range narrows as evidence grows. Confidence words: *very rough* (< 10 weighted items), *rough* (10–30), *fair* (30–80), *good* (> 80 incl. ≥ 1 exam-mode set).
2. **Competency mastery** (~150 competencies): probability the learner knows it; rises with correct unhinted answers, falls with errors; mastered at ≥ 0.85 with ≥ 5 attempts over ≥ 2 days.
3. **Review schedule** (mistakes, vocabulary, mastered competencies): spaced repetition; each item has a next-review date that grows after successes and shrinks after failures.

### H.3 The planner (decides today's mission)

Every day (and after each mission) it scores candidate activities:

```
skill priority = gap_to_target (in NCLC steps) × 2
               + 1.5 if it is the lowest skill
               + 0.5 × days since last practised (max 3)
               + exam proximity bonus for exam-format practice (H.5)
```

- Weekly time split: lowest skill ≈ 40%; others share the rest; **no skill below 10%** (keeps all four alive because the lowest NCLC skill decides eligibility).
- Inside a skill, it picks competencies that are *available* on the path, not mastered, and due, preferring those linked to recent mistakes.
- Difficulty targets **70–80% success** in training: two sessions > 85% → one step harder; two < 60% → one step easier.
- Mission length fits `daily_minutes`: a 20-minute day = warm-up review (≤ 4 min) + one mission (12–15 min).
- The reason string is built from the top factor: *Speaking is 2 steps below your target and is your lowest skill.*

### H.4 Worked examples

**Strong reader, weak speaker.** Diagnostic: reading B2 (≈ NCLC 8), listening B1+, writing B1, speaking A2+ (low confidence). Target NCLC 9.
- Week 1 split: speaking 40%, writing 25%, listening 25%, reading 10%.
- Today's mission: a speaking story mission (B1 version) + 3 review items from speaking mistakes (« je suis allé » vs « j'ai allé »).
- Reading still appears twice a week (timed TCF-style texts) so it doesn't fade.
- Week 3: speaking rises to B1 (fair confidence). Planner: speaking 30%, writing 35% (now the lowest), listening 25%, reading 10%. Céleste: *Your speaking moved up a step. Writing is now your lowest, so we'll shift some time there.*

**Beginner with an exam in 5 months.** Guided start; provisional A1–A2. Missions mostly chapter I–II; diagnostic parts scheduled on days 2, 4, 6, 8 (one skill each, 6–8 min). After them, the provisional label is removed and the plan rebalances.

**Advanced learner bored by easy content.** Self-rating 5, challenge 5/5 on B1–B2, picks "Discover my level". Diagnostic places reading/listening at C1, writing B2, speaking B2. Chapters I–III are charted automatically after a test-out; the path starts in chapter IV. "Too easy" twice → the planner jumps a difficulty step.

### H.5 Exam date effects

| Time to exam | Plan mix |
| --- | --- |
| No date / > 6 months | Learning-first: story missions 70%, exam-format 30% |
| 2–6 months | Balanced: 50 / 50; a full simulation every 4 weeks |
| 4–8 weeks (sprint mode) | Exam-first: exam-format 70%; weekly section simulations; pacing drills |
| Final 14 days | Review mode: simulations, templates for writing T1–T3, speaking warm-ups, no new grammar; rest day before the exam |

### H.6 Daily, weekly and monthly rhythm

**Daily (Home opens on):** today's mission (title, skill, minutes, reason), a review strip (max 10 items), yesterday's result in one line (*Hier : 2 nouvelles formes maîtrisées*), and what finishing unlocks (*Finish to open « Le Bus de 8 h »*).

**Weekly:** Monday: the week's objectives (3 lines, e.g. *Speaking: give a reason with « parce que / car »*). Sunday (movable): weekly trial → report → next week's plan with what changed and why.

**Monthly:** a review page: per-skill change over 4 weeks, weakest skill trend, chapter progress, distance to target NCLC, progress toward C1/C2 shown separately, and one suggestion (*Try a full simulation this month*).

**Missed days, without punishment:**
- The rhythm is **weekly**: "4 of 5 study days this week" instead of a fragile daily counter. Two rest days per week are built in; a learner who studies 5 days keeps a perfect week.
- No backlog: reviews are capped at 10 per day, oldest-due first; the rest wait, without a growing red number.
- After ≥ 3 days away: Céleste: *Contente de te revoir ! Let's warm up with a short one.* The next mission is 10 minutes and starts with the 3 most important reviews.
- After ≥ 14 days: a 5-minute "refresh check" (keyed items from mastered competencies) adjusts mastery so the plan doesn't assume knowledge that faded.

### H.7 Reminders and motivation

- **When asked:** at the end of the first completed mission (never during onboarding). *Want a reminder tomorrow? I'll only write about your mission or reviews.* Time chip (default: the time they just studied) · days · "No thanks".
- **Local-first reality:** TCF Quest runs in a browser on the Mac. Browser notifications work while the browser is open; in-app reminders appear when the app is opened. Reminders are honest about this in Settings. (A desktop wrapper or mobile app could deliver real push later.)
- **Types:** daily mission (at the chosen time) · reviews due (max once a day, only if ≥ 5 due) · weekly trial day (once) · milestones (boss unlocked, new skin reachable).
- **Tone rules:** no guilt (*You're losing your streak!* is banned), no fake urgency, max 1 notification a day, quiet hours respected (default 21:30–08:00), easy off switch in every message.
- **Refused:** never asked again automatically; a quiet "Turn on reminders" stays in Settings.

---

## I. States, transitions and data

### I.1 Learner-level states

```
onboarding_not_started → onboarding_in_progress(step n) → onboarding_complete
    → profile_provisional ──(all 4 diagnostic parts done, or ≥ 30 weighted items per skill)──→ profile_assessed
```

| State | Saved | On return |
| --- | --- | --- |
| Onboarding not started | nothing | Step 0 |
| Onboarding in progress | `onboarding_step`, all answers so far | Same step, answers preselected, « Re-bonjour ! » |
| Onboarding complete | `onboarded_at`, plan | Home |
| Diagnostic incomplete | finished parts, next part id | Home suggests the next part (never forces it) |
| Profile provisional | estimates flagged `provisional` | Estimates shown with "provisional" |
| Profile assessed | estimates with confidence | Normal display |

### I.2 Mission and exercise states

```
mission: locked → available → in_progress(step k) → completed → mastered
                                              ↘ abandoned (resumable)      ↘ needs_review → (review done) → mastered

exercise: presented → awaiting_answer → submitted → feedback_shown → (continue | retry)
```

| User action | Saved immediately |
| --- | --- |
| Opens a mission | `mission_progress.status = in_progress`, `step = 0` |
| Submits an answer | `attempt` row (response, time, hints, mode, verdict), mastery update, mistake upsert, `mission_progress.step` |
| Types in a writing task | draft every 5 s (`writing_submission.status = draft`) |
| Finishes a speaking turn | turn appended to `speaking_session.turns` (text, audio path, confidence) |
| Completes a mission | status, score, `xp_event`, `study_day.minutes`, unlock checks |
| Taps "Too hard / easy / dispute / technical" | `feedback_flag` row linked to the attempt |
| Changes goal / exam date / daily time | profile, then plan recomputed; Céleste explains what changed |
| Retakes the diagnostic | old results kept in `progress_history`; new results replace current estimates only when complete |

### I.3 Recovery

| Event | Behaviour |
| --- | --- |
| Browser refresh | Returns to the same screen and exercise; unanswered item re-presented; answered items not repeated |
| App/browser closes unexpectedly | Same as refresh on next launch; *On reprend où on en était ?* |
| Microphone fails | F.2; typed mode; no evidence lost |
| Ollama unavailable | Keyed missions work; AI-dependent steps show "needs local AI" with a "Skip for now" that keeps the mission completable; writing/speaking queued for feedback |
| Speech engine unavailable | Speaking → typing with notice |
| Audio playback fails | Retry once; then transcript; attempt tagged (no listening evidence); exam mode: item voided and reported |
| Goals change | Plan recomputed; path unchanged (mastery is mastery) |
| Diagnostic repeated | Allowed every 30 days or on request with a warning that frequent retakes add noise |

### I.4 New data needed (beyond the current schema)

`onboarding_step`, `motivation`, `self_rating`, `start_route`, `sprint_mode`, `narration_mode`, `corrections_timing`, `immersion_override`, `reminder_settings`; `attempt.verdict`, `attempt.evidence_weight`, `attempt.flags`; `feedback_flag` table; `diagnostic_part` table; `item_variant` link in content; `companion_line_log` (last 20 lines).

---

## J. Educational quality safeguards

| Risk | Safeguard |
| --- | --- |
| Misleading level estimates | Weighted evidence (H.1); difficulty-bounded counting; ranges + confidence words; "provisional" label until assessed; levels move up only after evidence holds on two separate days |
| Points mistaken for ability | XP/streaks/stamps never feed levels, unlocks or skins (tested in code) |
| Unreliable speech evaluation | Content-only feedback; uncertain turns never count; no pronunciation claims in v1; transcript always visible and correctable |
| AI feedback errors | Rubric-bound prompts; two scorings, disagreement → low confidence and not used for estimates; every AI output stored with model + prompt version; "golden" sample set re-run after any prompt change; dispute button |
| Poor questions | Every keyed item: verified answer key, explanation per distractor, level tag, competency tag; automatic checks (one correct answer, no duplicate options); disputes → review queue; items with high dispute or abnormal error rates retired |
| False exam readiness | "Ready" claimed only when target is met in **two consecutive full simulations**, all four skills; every estimate says "Not an official TCF result"; TCF score ranges shown only after calibration items exist |
| Exam format drift | Exam config versioned and verified against FEI before the simulator ships; unverified facts labelled |
| Memorised items inflating scores | Bosses and simulations use items never shown in practice; item exposure tracked |
| Copyright | Original content only; no official TCF questions |

---

## K. MVP experience (smallest complete journey)

**Goal:** prove that the first 15 minutes work end to end and that the learner wants to come back tomorrow.

Included:
1. **Onboarding steps 0–10** with Céleste (text + optional voice), autosave and resume.
2. **First challenge** with two bands (A1–A2, B1–B2), 5 items each, exercise types 1–5 (select, listen, arrange, type, repeat).
3. **Route choice**: "Start learning now" fully working; "Discover my level" with **one** working diagnostic part (listening, ~6 min, adaptive over 3 difficulty steps). Other parts show as "coming soon" in the plan.
4. **Roadmap** (provisional start, target, priorities, first mission, next milestone).
5. **One story mission, « Le Marché de Belleville »**, in **A2 and B1** versions: intro, objective, listening, mini-lesson, arrange, type, repeat-after-me, 30-second voicemail with AI content feedback, mastery check, summary.
6. **Feedback system**: all verdicts, "Why?", dispute/technical flags.
7. **Speaking**: turn-based recording, local Whisper transcript with confidence, typed fallback, permission flow, empty/noise/uncertain handling.
8. **Mistake notebook** (auto-filled) and review strip.
9. **Saved progress** and exact resume after refresh.
10. **Chapter II path** with 6 nodes (Belleville, 2 skill lessons, 1 review, 1 checkpoint, boss locked) and the **next recommended mission** with a reason.
11. **Reminders offer** after the first mission (in-app + browser notification).

Excluded from the MVP (on purpose): full 4-part diagnostic, free conversation role-plays (Professeur), writing studio, weekly trial, bosses, simulator, monthly review, test-out, more chapters.

---

## L. User acceptance scenarios

**1 · Beginner who struggles (« Je commence »)**
- Picks comfort 1; gets the A1–A2 challenge; misses 2 in a row → item 3 drops to the easiest variant; ends 3/5.
- Summary is positive and specific (*You recognised a greeting and built a polite request*).
- Route recommendation: "Start learning now". Roadmap: *Provisional: around A1*. First mission: Belleville **A2** with maximum support (English guidance, slow audio offered, guided voicemail). An A1 version and chapter I lessons come after the MVP.
- *Accept if:* no screen shows a level label without "provisional"; no failure screen; next mission is easier than the challenge.

**2 · Intermediate learner preparing the TCF (B1, exam in 4 months)**
- Comfort 3; challenge B1–B2 4/5; picks "Discover my level"; listening part places B1 (rough).
- Roadmap: priorities speaking/writing (not yet measured → treated as unknown, planner schedules their diagnostic parts on days 2 and 4).
- *Accept if:* the plan shows the measured skill with a range and the others as "not measured yet"; Belleville B1 is served.

**3 · Advanced learner with weak speaking**
- Comfort 5; listening/reading C1 on the diagnostic; speaking conversation shows short, hesitant turns (B1, low confidence).
- Planner: speaking 40%; chapters I–II charted after test-out; speaking missions served at B1 while reading items stay at C1.
- *Accept if:* the learner is never forced through A2 reading; speaking practice dominates week 1; Céleste explains why.

**4 · Learner who denies the microphone**
- At the first speaking item, taps "Allow", then denies in the browser.
- *No problem, you can type your answers.* Speaking items become typed for the rest of the session; the mission still completes; the roadmap notes *Speaking not measured yet: needs microphone.* Once a week Home offers *Want to try speaking today?*
- *Accept if:* no blocked mission, no repeated permission prompts, typed answers not counted as speaking evidence.

**5 · Returning learner who missed 6 days**
- Opens the app: *Contente de te revoir !* No red counters. Week rhythm shows last week 2/5 and this week fresh.
- Today: 10-minute mission + top 3 reviews (from 23 due, capped). Mastery of 2 old competencies drops after the refresh check; the planner re-inserts one review node.
- *Accept if:* the first action takes one tap, the session is ≤ 12 minutes, no guilt wording anywhere.

---

## M. Implementation order (after approval)

Each milestone ends working, tested and committed.

| # | Milestone | Acceptance criteria |
| --- | --- | --- |
| 1 | **Content format + exercise engine (keyed types 1–4)** | JSON schema for items/missions with keys, alternatives, distractor explanations, competencies; player handles types 1–4 with the shared lifecycle; E.2 checking rules unit-tested; every submit saved; refresh resumes |
| 2 | **Feedback system** | All verdicts render; "Why?" placeholder; dispute/technical flags stored and removed from evidence; tone rules reviewed |
| 3 | **New onboarding (steps 0–10) + first challenge** | One decision per step; autosave/resume at every step tested; first French answer reachable in < 2 min; replaces current onboarding; existing profile kept |
| 4 | **Belleville A2 + B1 (keyed parts) + mistake notebook + review strip** | Mission completes end to end without AI; mistakes appear in the notebook; reviews scheduled; XP/minutes saved |
| 5 | **Speaking pipeline (types 5 and the voicemail task)** | Local Whisper transcription with confidence; permission flow; empty/noise/uncertain paths; typed fallback; no recording leaves the Mac |
| 6 | **AI content feedback (Ollama)** | Rubric-bound feedback for the voicemail; double scoring + agreement check; graceful degradation when Ollama is off |
| 7 | **Roadmap, Home "today's mission", chapter II path, planner v1** | Reason on every mission; 70–80% difficulty targeting; next mission changes after a weak/strong session (tested with fixtures) |
| 8 | **Listening diagnostic part + provisional/assessed profile** | Adaptive 3-step listening check; estimates with range and confidence words; "provisional" labels everywhere until assessed |
| 9 | **Céleste lines, narration settings, immersion dial, reminders offer** | Line pools with no repeats in last 20; mute/minimal modes; reminders asked only after the first mission; refusal respected |
| 10 | **MVP acceptance run** | Scenarios L1–L5 pass in the browser; first-session storyboard completes in ≤ 15 minutes |

Then: remaining diagnostic parts → weekly trial → role-plays in Professeur → writing studio → checkpoints/boss → simulator → monthly review.

---

## Conclusion

### 1. Recommended experience structure
A conversational onboarding with one companion (Céleste), a first French success within two minutes, a clear route choice, then a daily loop that always opens on one reasoned mission. Story missions (one story, several levels) sit on a chapter path across France; a separate, plain exam world measures readiness. Effort is rewarded with XP and stamps; ability is proven by mastery and assessments.

### 2. Highest-priority improvements over the current app
1. Replace the form onboarding with the conversational flow and a first challenge.
2. Build the exercise engine and feedback system (the heart of the experience).
3. Make Home open on today's mission with its reason, not on stats.
4. Make the avatar optional and later; drop the "hardest skills" question.
5. Replace the daily streak with a weekly rhythm and capped reviews.

### 3. Proposed first-session journey
Language → welcome → motivation → target → exam date → comfort → daily time → 4–5 French exercises → route choice → name and avatar (optional) → roadmap → Le Marché de Belleville (level-matched) → completion → reminders offer → tomorrow's mission. About 15 minutes.

### 4. Smallest complete experience to build first
Section K: onboarding + first challenge + route choice (one diagnostic part) + roadmap + Belleville A2/B1 with listening, keyed exercises, repeat-after-me and an AI-checked voicemail + feedback + mistake notebook + saved progress + chapter II path + next mission.

### 5. Decisions requiring approval
See the list in chat (also tracked in `DECISIONS.md` once answered).

---
---

# Part II · the learner's notes integrated (2026-10-16)

Where Part II and Part I differ, **Part II wins**. The companion is **Céleste** (the notes' planning name "Camille" was not kept).

> Note: the source notes were cut off in section 16 ("Boîte à outils", at "Generated French audio…"). Everything up to that point is integrated; the rest is pending.

## R1 · TCF Canada identity (non-negotiable)

TCF Quest is a **TCF Canada preparation academy wrapped in an adventure**, not a general French course.

**Rule:** every mission, lesson, exercise set, strategy card, conversation scenario and toolbox entry carries a tag:

```
tcf_target: { section: CO | CE | EO | EE, task?: EO-T1 | EO-T2 | EO-T3 | EE-T1 | EE-T2 | EE-T3, purpose: "…one line…" }
```

- The tag is shown to the learner on every mission card: *Prépare : Expression orale · Tâche 2*.
- Content without a tag cannot be published (content check fails).
- Grammar and vocabulary appear **only as support** for a tagged purpose. Example: the subjonctif is introduced in « Exprimer un doute ou une nécessité » (EO-T3, EE-T3), not as "Chapter 7: the subjunctive".
- Conversations prepare the communicative demands of EO tasks (answering about oneself, obtaining information, defending a view), never chit-chat for its own sake.
- **Core loop** for every meaningful activity: *Understand → Learn → Practise → Apply → Feedback → Revise → Demonstrate mastery → Advance.*

## R2 · Act One, "The Awakening": welcome and exam briefing (steps 1 and 1b)

### Step 1 · Welcome
- **Companion:** « Bienvenue dans TCF Quest ! Je suis Céleste, ta guide. Ensemble, nous allons nous préparer au TCF Canada, étape par étape. » (translation underneath for A1–A2 guidance)
- **Choices:** « Découvrir le TCF Canada » (primary) · « Je connais déjà l'examen ».
- "Je connais déjà" skips to step 3; the briefing stays available in Entraînement → Académie TCF → "L'examen en 5 minutes", and Céleste mentions it once later if the learner's first mini-challenge shows confusion about the format.

### Step 1b · Exam briefing (interactive)
- **Opening:** « Avant de commencer ton aventure, découvrons le défi que tu vas préparer. »
- **Card 1 · What is the TCF Canada?** *A French test from France Éducation international, used in Canadian immigration and citizenship procedures. It gives you a separate result for each of four skills.* Link: "What TCF Quest is not": *TCF Quest is not an official test centre. Our results are practice estimates.*
- **Card 2 · Five things not to mix up** (tap each to flip):
  1. The **official TCF Canada** (only a test centre gives it).
  2. **CEFR levels A1–C2** (a general scale of French ability).
  3. **NCLC levels** (Canada's scale; TCF results convert to them).
  4. **Your personal target** (what you aim for).
  5. **TCF Quest practice results** (unofficial estimates to guide training).
- **Card 3 · The four sections** (swipe through):

| Section | Format | Time | In plain words |
| --- | --- | --- | --- |
| Compréhension orale | 39 MCQ | 35 min | Listen to recordings, each played **once**; answer questions |
| Compréhension écrite | 39 MCQ | 60 min | Read texts; meaning, details, intentions, implied information |
| Expression écrite | 3 tasks | 60 min | Write a message (60–120 words), an account with commentary (120–150), a comparison of two viewpoints (120–180) |
| Expression orale | 3 tasks | 12 min incl. Task 2 preparation | Directed interview (~2 min) · interaction where you ask questions (~5 min 30 incl. 2 min prep) · defend a viewpoint (~4 min 30) |

  Total **2 h 47**, all four sections compulsory. *(Verified against the FEI TCF Canada page on 2026-10-16; see `TCF_SPECIFICATION.md`. Never mixed with TCF Québec, TCF Tout Public, DELF, DALF or TCF IRN.)*
- **Card 4 · Quiz (2 questions, format only, not French level):**
  - « Quelle épreuve te demande de défendre une opinion à l'oral ? » → Compréhension orale / Compréhension écrite / Expression écrite / **Expression orale** ✓ *Exactement : c'est la tâche 3 de l'expression orale.*
  - « Combien de temps dure l'examen complet ? » → 1 h 30 / **2 h 47** / 4 h ✓ *Oui : 2 h 47, avec quatre épreuves obligatoires.*
- **Card 5 · The promise and the route:** « Notre objectif est simple : comprendre l'examen, apprendre les bonnes méthodes, nous entraîner régulièrement et mesurer tes progrès jusqu'au jour du TCF Canada. » Then the six-step route, shown as a short vertical path the learner will see again on the campaign screen:
  1. Comprendre l'examen ✓ (just done)
  2. Découvrir ton niveau
  3. Apprendre les méthodes
  4. Entraîner les quatre compétences
  5. Passer des tests réguliers
  6. Préparer l'examen complet
- **Saved:** `exam_briefing_done`, quiz answers (format knowledge, not French evidence).
- **Why:** gives every later activity a reason; differentiates TCF Quest from general apps.

## R3 · Onboarding questions, revised

**Step 3 · Target** — « Que veux-tu atteindre au TCF Canada ? »
- Choices: Un niveau NCLC précis pour mon projet · NCLC 7 dans les quatre compétences · NCLC 9 ou plus · Une solide performance de niveau C1 · Le meilleur niveau possible · Je ne sais pas encore.
- "Un niveau NCLC précis" and an "Advanced" link open **per-skill targets** (e.g. CO 9, CE 9, EE 8, EO 8).
- C1 is stored as `target_cefr`; the NCLC target defaults to 9 for "C1" and "best possible", 7 for "not sure". CEFR and NCLC are never converted into each other in the UI; both are shown, labelled.
- Companion never says what a level allows for immigration: *I can't tell you which result your application needs; check the official IRCC requirements. I'll help you reach the target you set.*
- **Saved:** `target_nclc` (global or per skill), `target_cefr`.

**Step 4 · Exam timing** — « Quand penses-tu passer le TCF Canada ? »
- Choices: Dans moins d'un mois · Dans 3 mois · Dans 6 mois · Plus tard · Je n'ai pas encore décidé. Optional "I have an exact date" link.
- Effects (replaces H.5 boundaries): < 1 month → final-review mode; ≤ 3 months → sprint (exam-format 70%); ≤ 6 months → balanced; later/undecided → learning-first.
- Never promises a level by a date. If the gap looks large for the time (e.g. self-rating 2, NCLC 9, < 3 months): *That's an ambitious timeline. We'll focus on what moves your results most, and you can adjust your date anytime.*
- **Saved:** `exam_window`, `exam_date?`, `plan_mode`.

**Step 4b · Section of concern** — « Quelle épreuve t'inquiète le plus ? »
- Choices: Compréhension orale · Compréhension écrite · Expression orale · Expression écrite · Je ne sais pas.
- **Saved:** `concern_section`. **Used for:** the order of diagnostic parts (the concerning one first, so worry is replaced by facts early), the tone of the first explanations, and one sentence on the campaign screen. **Never** used as a measurement; all four skills are still diagnosed.

**Step 6b · Learning preference** — « Comment préfères-tu t'entraîner ? »
- Choices: Beaucoup d'exercices courts · Plus de conversations orales avec l'IA · Plus d'explications guidées · Plus d'entraînement chronométré · Un bon équilibre.
- **Guardrail:** the preference shifts the **format mix by at most 20%** inside each mission (e.g. more conversation turns, fewer drills). It never removes a skill, never lowers exam-format practice below its plan-mode minimum, and never skips the four-skill weekly trial.
- **Saved:** `learning_preference`.

## R4 · The first TCF mini-challenge (replaces step 7 content)

Opening: « On commence avec quelques petites épreuves pour découvrir comment tu apprends. » Four items, each in a TCF section's style, at the band chosen by comfort:

| # | Section flavour | A1–A2 band | B1–B2 band |
| --- | --- | --- | --- |
| 1 | **CO**: short conversation, what was understood | At a bakery: « Deux croissants, s'il vous plaît. – Ça fait 2 euros 40. » → *What does the customer buy?* | Phone message: « Bonjour, c'est Julie. La réunion de jeudi est déplacée à vendredi, même heure. Rappelle-moi si ça te pose problème. » → *Qu'apprend-on sur la réunion ?* |
| 2 | **CE**: short text, one question | A gym notice: « Fermé le lundi. Ouvert de 7 h à 21 h du mardi au samedi. » → *When can you go on Monday?* | Neighbourhood notice about a bike-lane project with « en revanche » → *Quelle est la position de l'association ?* |
| 3 | **EE**: choose the right opening for a message | To a friend: *Salut Marc !* vs *Madame, Monsieur,* | To a landlord: « Madame, » / « Coucou ! » / « Salut la proprio ! » |
| 4 | **EO** (optional, mic): repeat a sentence | « Je voudrais des informations, s'il vous plaît. » | « Pourriez-vous me préciser les horaires du cours ? » |

Item 4 has "Not now" and never blocks; the mic explainer appears only if the learner taps "Try speaking". Feedback is immediate; the summary names the sections: *Tu viens de toucher aux quatre épreuves du TCF.* Not a level.

## R5 · Act Two, "Discover your starting point": the diagnostic

Companion: « Maintenant, découvrons tes points forts et les compétences à améliorer pour le TCF Canada. » Choices: **« Évaluer mon niveau »** (recommended; R1 rule) · « Commencer mon entraînement » (provisional path, diagnostic later).

Four parts, 6–8 minutes each, any order (the concerning section first by default), can be spread over week 1. Each part is adaptive over 3 difficulty steps (start in the band from self-rating; two correct → up, two wrong → down).

| Part | Measures | Item types | Scoring |
| --- | --- | --- | --- |
| **CO** | Main idea, specific detail, speaker intention, implicit information, natural speech | Original recordings, single play, MCQ | Keyed |
| **CE** | General meaning, key information, intention/viewpoint, inference, complex argument | Original texts, MCQ | Keyed |
| **EO** | Relevance, coherence, vocabulary, grammar, asking appropriate questions, developing ideas; fluency indicators only where measurable (speech rate, pauses), never pronunciation | 3 short tasks: answer about yourself (T1-like), ask 3 questions in a situation (T2-like), give and justify a view (T3-like) | AI rubric ×2 with agreement check |
| **EE** | Task completion, structure, cohesion, grammar, vocabulary, register, clarity | 1 short message (T1-like, 60–80 words) + 1 short opinion paragraph (60–80 words) | AI rubric ×2 with agreement check |

**Report** (per skill, separate): CEFR range + confidence word + what it means for the exam.

> Compréhension orale : **B1** (fiable à peu près) · Compréhension écrite : **B2** (fiable à peu près) · Expression orale : **A2–B1** (estimation prudente) · Expression écrite : **B1** (estimation prudente)
> *Ta priorité : l'expression orale. C'est elle qui t'éloigne le plus de ton objectif NCLC 9. Bonne nouvelle : ta compréhension écrite est solide, on ne te fera pas refaire des lectures faciles.*

No TCF score or NCLC is shown from the diagnostic alone; NCLC equivalents appear only as "target vs estimated band" with a clear "estimate" label, and only for skills with "fair" confidence or better.

## R6 · Act Three: the personal TCF campaign (replaces step 10 "Roadmap")

Generated after the diagnostic (or provisionally after the mini-challenge). Sections, each one tap to expand:

1. **Ton objectif:** e.g. NCLC 9 in all four skills (per-skill if set); personal goal C1.
2. **Où tu en es:** four skill estimates (or "provisional").
3. **L'écart:** per skill, current band vs target band, as steps (*Expression orale : 2 étapes*).
4. **Tes priorités** (max 3), each with a reason.
5. **Ton rythme:** daily minutes → weekly hours; the plan mode (learning-first / balanced / sprint / final review).
6. **Cette semaine:** 3 weekly goals tied to tasks, e.g. *EO-T2 : poser 5 types de questions différents.*
7. **Ce mois-ci:** 1–2 milestones, e.g. *Premier test blanc d'expression orale (12 min) le 30 octobre.*
8. **Langue à consolider:** grammar and expressions needed for the priorities (from the Boîte à outils), e.g. *Questions avec inversion · Connecteurs d'opposition.*
9. **Méthodes à apprendre:** strategy cards from the Académie, e.g. *Utiliser les 2 minutes de préparation (EO-T2).*
10. **Entraînement chronométré:** when timed practice starts and scales up.
11. **Tests:** weekly trial day; planned mock exams (dates).

Explanation line from the companion: « Ton expression orale est actuellement ta priorité. Cette semaine, nous allons travailler les questions, la structure des réponses et la spontanéité. »

The campaign **updates automatically** after every weekly trial, mock exam or goal change, with a short "what changed and why" note. It is never a fixed list of generic lessons.

## R7 · Act Four: the adventure, « La Route du TCF Canada »

The learner travels toward **Le Grand TCF**. Chapters are learning environments and game stages; they never award official results. A learner can enter an advanced chapter directly by demonstrating ability (test-out, G.3), and does **not** need C2 to be ready for their own target.

| Chapter | TCF focus | Boss |
| --- | --- | --- |
| I · Le Premier Pas (Normandie) | Essential communication; simple CO/CE; common question structures; short messages (EE-T1 basics); understanding exam instructions; first simple TCF-style tasks from day one | Short guided assessment of essential communication and comprehension |
| II · La Vie Quotidienne (Paris, Belleville) | Everyday conversations; asking for information (EO-T2 foundations); announcements (CO); practical texts (CE); clear messages (EE-T1); describing experiences with the right tenses (EE-T2, EO-T1); question patterns | Interaction-focused series of TCF-style tasks |
| III · La Cité des Idées (Lyon) | Longer conversations; expressing and supporting opinions (EO-T3 foundations); detailed questions; organised accounts (EE-T2); connectors; speaker intentions | **Timed** four-skill assessment |
| IV · Le Labyrinthe des Arguments (Strasbourg) | Complex CO; written arguments and comparing viewpoints (EE-T3); defending positions (EO-T3); long structured answers; grammatical precision; register; exam techniques; time pressure | Challenging, **unseen** four-skill practice assessment |
| V · La Maîtrise (Pyrénées) | Nuance and implicit meaning; sophisticated argumentation; precise expression; complex grammar; spontaneous communication; consistent performance under time pressure; final weakness reduction | **Le Grand TCF**: full examination simulation(s) |

## R8 · Four independent skill tracks on one map

- Each chapter's path is built from nodes tagged by skill (CO, CE, EO, EE) plus mixed story missions.
- **Each skill has its own track level**, from its own estimate. A learner can be on chapter IV reading nodes and chapter II speaking nodes at the same time; the map shows a small marker per skill (four coloured pins) instead of one position.
- The **adventure position** (which region you are "in" for the story) follows the learner's **lowest** track, so the story and the exam priority stay aligned; stronger tracks show their nodes in later regions as "unlocked ahead".
- Story missions use the version (G.4) matching each part's skill: in one mission, the reading part may be B2 while the speaking part is B1.
- Adventure progress (regions, stamps, XP) and demonstrated proficiency (estimates, mastery) are stored and shown separately.

## R9 · The daily mission template (canonical, replaces E.4's default)

Every mission card states: **Mission · Prépare (section + task) · Objectif · Durée.**

Example: **« Défendre une opinion »** · Prépare : *Expression orale, tâche 3* · Objectif : *organiser et défendre un point de vue* · Durée : *25 min*.

| Stage | What happens | Example (Défendre une opinion, B1) | Evidence |
| --- | --- | --- | --- |
| **A · Échauffement** (warm-up) | 2–5 due reviews from the notebook | Fix « Je pense que c'est **plus meilleur** » → « meilleur » | Review results |
| **B · Méthode** (strategy) | One strategy card from the Académie | *Structure d'un point de vue : position → raison → exemple → nuance → conclusion* (R11, EO-T3) | None (no credit for reading) |
| **C · Langue** (language support) | Only the language this task needs | Connectors of justification and nuance: « en effet », « cependant », « il faut néanmoins reconnaître que » | Mastery of 2–3 competencies |
| **D · Pratique** (interactive practice) | 3–6 short exercises | Choose the connector; order the parts of an argument; listen and identify the speaker's argument; pick the strongest of three answers | Keyed |
| **E · Conversation IA** | Practise aloud with a character | Bastien asks: « Le télétravail devrait-il devenir la norme ? » and follows up: « Et pour les jeunes salariés ? » | AI rubric (weak weight) |
| **F · Application TCF** | Short exam-style task, hints reduced or removed | 2-minute timed answer to a new topic, no expression list visible | AI rubric (medium weight) |
| **G · Retour** (feedback) | Done well · to improve · better expression · *Did you answer the actual question?* · technique to practise again | *Tu as donné un exemple concret, bravo. Ta conclusion manquait. Essaie : « Tout bien considéré, … »* | — |
| **H · Fin de mission** | XP, mastery evidence, notebook, daily goal, next recommendation | *Prochaine étape : une nuance en plus, demain.* | — |

**Rule:** mastery credit comes only from stages D, E and F (answers). Reading stage B or C earns nothing; finishing the mission without answering earns completion XP only.

Variants: a **listening** mission puts a CO strategy in B (« repérer la reformulation ») and replaces E with a longer audio scene; a **writing** mission replaces E with a guided draft and F with a timed EE task; short days (10 min) keep A, D and a mini F only.

## R10 · Académie TCF, « Méthodes et Stratégies »

A dedicated module in **Entraînement** (and fed into missions at stage B). Strategies are grouped by section; each card has eight parts:

1. Explanation · 2. Why it helps · 3. Worked example · 4. Guided exercise · 5. Independent application · 6. Common mistakes · 7. Review card (spaced) · 8. Timed challenge (when relevant).

| Section | Strategy cards (first set) |
| --- | --- |
| **CO** | Know the four official item patterns (image + spoken options; spoken question + spoken replies; dialogue; long monologue) · Find the purpose of the conversation · Catch the key details (who, when, how much) · Follow natural speech (elisions, « j'sais pas ») · Recognise paraphrase (the answer rarely repeats the audio's words) · Speaker intention (complain, advise, refuse…) · Listen for meaning, don't translate word by word · Handle uncertainty (eliminate, then choose; never leave blank) · Stay focused with a single play · Spot distractors (words heard ≠ correct answer) |
| **CE** | Purpose of a text (inform, persuade, warn) · Locate the evidence before answering · Paraphrase recognition · Author's intention · Explicit vs implicit · Unknown words from context · Distractors · Time management (≈ 1 min 30 per question on average; move on and come back) · Don't waste time taking notes in MCQ sections (official FEI advice) |
| **EO** | Understand the question · Answer directly first · Ask good follow-up questions · Use the 2 minutes of T2 preparation · Structure an opinion · Develop with an example · Agree/disagree politely · Reformulate when stuck · Coherence under time pressure · Recover after hesitation (« Comment dire… ») · Clarity and register |
| **EE** | Analyse the instructions · Identify the reader · Choose the register · Plan before writing · Organise ideas · Respect the word count · Logical structure · Compare viewpoints faithfully · Use examples · Proofread checklist · Manage 60 minutes across three tasks (suggested: T1 15 min, T2 20 min, T3 25 min) |

- **Honesty rule:** no "guaranteed trick". Each card says what it helps with and its limits.
- **Training vs exam:** cards, transcripts and replays exist in training; exam mode reproduces official restrictions.
- **Strategy notebook:** searchable; cards the learner has used, with their own success rate per strategy and the next review date. Céleste suggests a card when a matching mistake pattern appears (e.g. many CO errors on distractor options → "Spot distractors").
- Example card (CO · Spot distractors): *Explanation:* the wrong options often reuse words you heard. *Worked example:* audio « Je pensais prendre le train, mais finalement j'y vais en voiture » → option "Il prend le train" contains *train*, but it is wrong. *Guided exercise:* 3 items with the trap highlighted after answering. *Independent:* 3 items without help. *Common mistake:* choosing the option that "sounds like" the audio.

## R11 · Speaking masterclass (Expression orale)

### EO-T1 · Entretien dirigé (~2 min, no preparation)
- **Covers:** introducing yourself, studies and work, interests, daily life, plans, unexpected follow-ups, expanding beyond one-line answers.
- **Language supports** (not a script): « Je m'appelle… » · « Actuellement, je… » · « J'ai choisi… parce que… » · « Pendant mon temps libre… » · « À l'avenir, j'aimerais… »
- **Progression (7 steps):** 1 hear example questions → 2 understand the question (choose what it asks) → 3 build a short answer (tiles + speaking) → 4 improve it (add a reason, a detail) → 5 answer without the example → 6 surprise follow-ups from the examiner character (« Et pourquoi ce choix ? ») → 7 timed 2-minute simulation.
- **Anti-recitation check:** the AI flags answers that ignore the question or reuse a memorised block (high overlap with the learner's earlier answers to different questions): *You answered a different question. The examiner asked about your weekend, not your job.*

### EO-T2 · Exercice en interaction (~5 min 30, including 2 min preparation)
- **Covers:** understanding the situation, finding what information is missing, planning questions, correct question forms, clarification, natural follow-ups, reacting to unexpected answers, keeping the exchange going.
- **Question toolbox:** « Pourriez-vous me préciser… ? » · « Est-ce que vous pourriez m'expliquer… ? » · « J'aimerais savoir si… » · « Quels sont les horaires… ? » · « Combien cela coûte-t-il ? » · « Y a-t-il des conditions particulières ? » · « Serait-il possible de… ? »
- **Training mission example:** *You want to join a French course.* AI character: Mme Lefèvre, course administrator. Preparation (2 min): the learner lists information to obtain (dates, price, level test, certificate, online option); the app shows a checklist they tick as they ask. Interaction: the character answers and sometimes adds a surprise (« Attention, le cours du soir est complet. ») to train reactions.
- **Feedback:** relevance of questions, variety of forms (direct, est-ce que, inversion, indirect), clarity, follow-ups, how the learner handled the surprise; *Questions asked: 6 · forms used: 3 · surprise handled: yes.*
- **Strict timed simulation** without coaching: 2 min prep timer → 3 min 30 interaction → feedback only after.

### EO-T3 · Expression d'un point de vue (~4 min 30, no preparation)
- **Training scaffold** (flexible, not an official format): 1 position → 2 reason → 3 develop → 4 concrete example → 5 other perspective or qualification → 6 conclusion.
- **Expression library:** Opinion « À mon avis… », « Selon moi… », « Je considère que… » · Justification « En effet… », « car… », « Cela s'explique par… » · Example « Par exemple… », « Prenons le cas de… » · Nuance « Cependant… », « En revanche… », « Il faut néanmoins reconnaître que… » · Conclusion « En définitive… », « Pour conclure… », « Tout bien considéré… »
- **Natural use vs inserted phrases:** a lesson contrasts two answers, one that stacks connectors without content and one that uses two connectors with real ideas; the feedback rubric rewards ideas linked logically, not connector counts.
- **Progression:** supported short answers (scaffold visible) → scaffold hidden → harder topics (society, work, environment, technology) → spontaneous follow-ups from the examiner (« Mais certains disent que… ») → relevant examples required → strict time limits.
- **Evaluation rule:** the rubric scores the language actually produced (task, coherence, range, accuracy), never "used the template".

## R12 · Writing masterclass (Expression écrite)

| Task | Length | Trains | Reusable structure (adapt, never copy) |
| --- | --- | --- | --- |
| **EE-T1 · Message** | 60–120 words | Understand the prompt; identify the recipient; register; give the requested information; describe/explain/recount; close appropriately | Greeting → reason for writing → information/details → request or next step → closing (« À bientôt », « Cordialement ») |
| **EE-T2 · Account / experience with commentary** | 120–150 words | Describe an experience; narrate clearly; sequence; reactions; consequences; add a comment or argument; past tenses | Context → events in order (« D'abord… Ensuite… Pendant cette expérience… Finalement… ») → reaction → what it taught (« Cette situation m'a permis de… ») |
| **EE-T3 · Compare two viewpoints** | 120–180 words | Understand two short documents; identify each viewpoint; compare faithfully; summarise without distorting; give own opinion; support it; conclude | Introduce the issue → viewpoint 1 → viewpoint 2 → their difference → your position → justification → conclusion |

*(Word counts verified against FEI on 2026-10-16.)* **Hard rule from FEI:** a writing paper can be rated "A1 non atteint" if any task misses its word range, is off-topic or is not done. So the word counter turns amber below the minimum and above the maximum, training feedback always flags it, and exam mode warns before submitting a task outside its range.

**Writing interaction:** prompt + word counter (target band shown) + timer. Training mode offers a side panel: strategy card · useful expressions · grammar support · task checklist (*recipient? register? all information asked? closing?*). Exam mode hides the panel.

**After submission** (original text stays visible, feedback alongside): task relevance · word-count compliance · structure analysis · grammar corrections (each with the rule) · vocabulary suggestions · cohesion feedback · a stronger example response **with the changes explained** · personalised revision recommendations (linked toolbox entries and strategy cards). The app never silently replaces the learner's text with an AI version.

**EE-T3 fidelity check:** the AI compares the learner's summary of each document with the source and flags distortions (*Document 2 does not say remote work should be banned; it says it should be limited.*).

## R13 · Boîte à outils TCF (toolbox)

Grammar and expressions organised **by exam usefulness**, not as an encyclopedia.

| Category | Contents | Mainly serves |
| --- | --- | --- |
| Poser des questions | Question words; formal vs informal; inversion; indirect questions; clarification requests | EO-T2 |
| Raconter | Passé composé; imparfait; plus-que-parfait when useful; chronological markers | EO-T1, EE-T2 |
| Donner son opinion | Opinion structures; cause and consequence; agreement/disagreement; conditional; concession; nuance | EO-T3, EE-T3 |
| Organiser un texte | Logical connectors; paragraphing; register; reformulation; cohesion | EE-T1–T3 |
| Précision avancée | Subjonctif; complex sentences; relative clauses; precise vocabulary; nominalisation; modality; formal register | EO-T3, EE-T3 (B2+) |

Each tool has: an explanation · examples · generated French audio … **(notes cut off here; remaining fields pending from the learner)**. Until then, the planned fields are: examples in TCF contexts, a 3-item check, links to missions and strategy cards that use it, and a spaced review card.

## R14 · Changes to the MVP and build order

**MVP (section K) changes:**
- Add **steps 1/1b**: welcome choice and the interactive exam briefing (cards + 2-question quiz + the six-step route).
- Add **steps 4b and 6b** (concern, preference).
- **First mini-challenge** uses the four TCF-flavoured items of R4 (both bands).
- **Belleville becomes an EO-T2 mission:** instead of a voicemail, the learner **phones the supplier** (AI character) to obtain information: why the delivery is late, when it will arrive, whether it can come before noon. A2 version: question prompts and a checklist visible; B1 version: checklist only. Tagged *Prépare : Expression orale · Tâche 2*. It follows the R9 template (A–H).
- The **campaign screen** (R6) replaces the roadmap, with provisional values where the diagnostic is incomplete.
- One **Académie card** used inside Belleville (EO · "Use the 2 minutes of preparation"), and the Académie section visible with that single card.

**Milestone 0 status: done 2026-10-16** (see `TCF_SPECIFICATION.md`). Findings that change the product: retake wait is 20 days; the writing word ranges are pass/fail requirements; four listening item patterns; the FEI sample page's "structures de la langue" section is not part of TCF Canada.

**Build order (section M) changes:**
- **Milestone 0 (new) · Verify TCF Canada facts** against the current FEI TCF Canada page and official sample tests: section formats, timings, total, word counts per writing task, EO task durations and preparation time. Store them in a versioned exam config; any unverifiable item stays labelled.
- Milestone 1 adds the `tcf_target` tag to the content schema, with a check that rejects untagged content.
- Milestone 3 includes the briefing and the revised questions.
- Milestone 4 builds Belleville as the EO-T2 interaction (keyed parts first), milestone 6 adds the AI interaction and its feedback (questions asked, forms used, surprise handled).
- After the MVP, the next order becomes: remaining diagnostic parts → campaign updates from weekly trials → **Speaking masterclass T1–T3** → **Writing masterclass T1–T3** → Académie (all sections) → Boîte à outils → bosses → Le Grand TCF simulator.

## R15 · Navigation update

**Entraînement** now contains, in this order: **Académie TCF** (strategies) · **Masterclass orale** (T1, T2, T3) · **Masterclass écrite** (T1, T2, T3) · **Boîte à outils** · the four skill practice areas · mistake notebook · simulator (Le Grand TCF). The other tabs are unchanged.

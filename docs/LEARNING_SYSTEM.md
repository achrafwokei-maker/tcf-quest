# Learning system

Rules decide; AI explains. Full rationale: `blueprint.md` section 6. This file is the build spec.

## Daily mission cycle

Warm-up (due mistakes and vocabulary) → Learn (micro-lesson) → Practise (graded drills) → Apply (one TCF-style task) → Feedback → Complete (progress, XP, next step). Length follows the learner's daily minutes.

## Skill estimates

- Per skill: CEFR low–high range + confidence (none/low/medium/high) + evidence count.
- Only exam-mode or no-hint attempts move estimates. Ranges widen with little evidence. A level rises only when evidence holds on a second occasion.
- Shown as "practice estimate", never as an official result. CEFR, TCF score and NCLC are always labelled separately.

## Mastery (per competency)

Bayesian-knowledge-tracing style update of `p_known` after each attempt. Mastered at p ≥ 0.85 with ≥ 5 attempts over ≥ 2 different days. Hints and retries count as weaker evidence.

## Mistake notebook and spaced review

Each wrong answer or AI-flagged error becomes (or increments) a `mistake` row: skill, category, context, learner answer, correction, explanation, recurrence. Review uses an SM-2 style schedule (ease, interval, next_review). Status: open → improving → mastered.

## Planner

Priority per skill = gap to target × weight for "lowest skill" + small weight for time since practised. Weakest skill ≈ 40% of weekly time; no skill below 10%. Weekly trial results reweight the next week.

## Progression

XP rewards effort (missions, streak days) and never unlocks content. Regions, bosses and missions unlock when their competencies are mastered. Failing a boss gives a diagnosis, 3–5 recovery missions, and a retry with different items.

## Content rules

Original content only. Every multiple-choice item has a verified key and an explanation. AI-drafted items are not used for scoring until reviewed.

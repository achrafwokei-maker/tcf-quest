# TCF Canada specification

**Verified 2026-10-16** against the official sources below (milestone 0). Machine-readable versions: `content/exam/tcf-canada.v1.json` and `content/exam/ircc-tcf-nclc.v1.json`, checked by `server/tests/test_exam_config.py`. Re-check every quarter and before any simulator release; bump the config version when anything changes.

Sources:
- France Éducation international, [TCF Canada](https://www.france-education-international.fr/test/tcf-canada) (format, tasks, word counts, administration)
- France Éducation international, [Exemples d'épreuves du TCF](https://www.france-education-international.fr/test/exemples-epreuves-tcf) (item formats; covers all TCF versions)
- IRCC, [Express Entry: Language test results](https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/express-entry/documents/language-test.html) (TCF → NCLC table, page modified 2026-10-16)

Only TCF Canada. Never mix in TCF Québec, TCF IRN, TCF Tout Public, DELF or DALF rules. The FEI sample page includes a "Maîtrise des structures de la langue" section that **does not exist in TCF Canada**.

## Format (4 compulsory sections, 2 h 47 in total)

| Section | Format | Time | Scale |
| --- | --- | --- | --- |
| Compréhension orale | 39 MCQ, 4 choices (A–D), one correct; progressive difficulty; **each recording played once**; question asked after the audio | 35 min | 331–699 |
| Compréhension écrite | 39 MCQ, 4 choices, one correct; progressive difficulty | 60 min | 331–699 |
| Expression écrite | 3 tasks | 60 min | 0–20 |
| Expression orale | 3 tasks, face to face with an examiner | 12 min (incl. 2 min preparation) | 0–20 |

### Listening item patterns (from the official examples; our items are original)
1. An image, four **spoken** statements: pick the one matching the image.
2. A spoken question, four **spoken** replies: pick the appropriate reply.
3. A short dialogue, a spoken question, four **written** answers.
4. A longer monologue or interview, a spoken question, four written answers.

### Writing tasks

| Task | What | Words |
| --- | --- | --- |
| EE-T1 | Message to one or more recipients (status given): describe, recount and/or explain | **60–120** |
| EE-T2 | Article, letter or note for several recipients: account of an experience or a story, with comments, opinions or arguments toward a goal | **120–150** |
| EE-T3 | Text (newspaper, website, colleague, manager…) comparing two viewpoints on a social issue from two documents, then giving one's own opinion | **120–180** |

**Hard rule:** the whole writing paper can be rated **"A1 non atteint"** if writing is illegible (paper), **any task misses its required word count**, the production is off-topic, or a task is not done. TCF Quest treats the word range as a requirement, not a suggestion.

### Speaking tasks

| Task | What | Time | Preparation |
| --- | --- | --- | --- |
| EO-T1 · Entretien dirigé | Exchange with someone you don't know (the examiner) | 2 min | none |
| EO-T2 · Exercice en interaction | Obtain information in an everyday situation; roles given in the instructions | 5 min 30 | 2 min (included) |
| EO-T3 · Expression d'un point de vue | Speak spontaneously, continuously and convincingly on a question chosen by the examiner | 4 min 30 | none |

Assessed abilities (FEI): talk about yourself and your environment; ask questions suited to the situation; give an opinion, pros and cons, agree/disagree; clear, structured argument in a suitable style; develop complex topics and conclude.

## Administration

- Retakes: unlimited, but **20 days** between sittings (not 30, as some sites say).
- Results: within 15 working days; certificate valid **2 years** from issue.
- Computer-based sittings exist for all sections except speaking.
- Re-correction of speaking and writing is suspended for sessions from 1 September 2026, with resumption planned for autumn 2027.
- Official preparation advice: know the format and the sitting procedure, study the examples, immerse yourself in French; during the test, listen carefully to instructions, stay focused in listening, **don't waste time taking notes in the MCQ sections**, manage time, and complete all three writing tasks.

## IRCC TCF Canada → NCLC (canada.ca, page modified 2026-10-16)

| NCLC | Reading | Listening | Writing | Speaking |
| --- | --- | --- | --- | --- |
| 10+ | 549–699 | 549–699 | 16–20 | 16–20 |
| 9 | 524–548 | 523–548 | 14–15 | 14–15 |
| 8 | 499–523 | 503–522 | 12–13 | 12–13 |
| 7 | 453–498 | 458–502 | 10–11 | 10–11 |
| 6 | 406–452 | 398–457 | 7–9 | 7–9 |
| 5 | 375–405 | 369–397 | 6 | 6 |
| 4 | 342–374 | 331–368 | 4–5 | 4–5 |

IRCC: results must be under 2 years old when the Express Entry profile is created and when the PR application is submitted. TCF Quest shows NCLC only as "estimated", never gives eligibility advice.

## Modes

- **Training:** hints, replays, transcripts, explanations.
- **Exam:** exact timings, one audio play, no hints, no note-taking prompts in MCQ sections, results only at the end, plain interface; writing word ranges enforced as in the real test.

## Honesty rules

Original items only, never copied or "leaked" questions. No precise TCF score from raw percentages; practice results and estimated ranges are labelled "Not an official TCF result".

"""Learning content: schema, validation and loading.

Content lives in /content as version-controlled JSON. Every exercise set and every item
must carry a `tcf_target` tag (TCF Canada identity rule): content without it is rejected.
"""

from __future__ import annotations

import json
import random
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, model_validator

CONTENT_DIR = Path(__file__).resolve().parents[2] / "content"
SETS_DIR = CONTENT_DIR / "sets"

Section = Literal["CO", "CE", "EO", "EE"]
Task = Literal["EO-T1", "EO-T2", "EO-T3", "EE-T1", "EE-T2", "EE-T3"]
Level = Literal["A1", "A2", "B1", "B2", "C1", "C2"]
ReviewStatus = Literal["draft", "reviewed"]     # only reviewed items may serve retests and assessments
Pool = Literal["training", "assessment"]         # assessment items are reserved: never shown in training
LEVEL_DIFFICULTY = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 5}


class TcfTarget(BaseModel):
    section: Section
    task: Task | None = None
    purpose: str = Field(min_length=8)

    @model_validator(mode="after")
    def task_matches_section(self):
        if self.task and not self.task.startswith(self.section):
            raise ValueError(f"task {self.task} does not belong to section {self.section}")
        return self


class Option(BaseModel):
    id: str
    text: str
    explanation: str = Field(min_length=3)  # why this option is right or wrong


class Audio(BaseModel):
    text: str                      # transcript; also used for interim browser speech
    file: str | None = None        # pre-generated audio in web/public/audio (later milestones)
    speaker: str | None = None     # character voice for local TTS (tts.CHARACTERS)


Stage = Literal["A", "B", "C", "D", "E", "F", "G", "H"]  # daily mission template (blueprint Part II R9)


class Speech(BaseModel):
    """A line said by a character, shown as a bubble and read aloud."""
    speaker: str
    text: str
    en: str | None = None


class ItemBase(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9-]+$")
    tcf_target: TcfTarget
    level: Level
    competencies: list[str] = Field(min_length=1)    # the first one is the primary (weakness key)
    instructions: str
    difficulty: int | None = Field(default=None, ge=1, le=5)   # default: from the CEFR level
    hint: str | None = None                                   # guided practice: a hint costs half the evidence
    time_limit_s: int | None = Field(default=None, ge=10, le=600)  # timed challenge (training: auto-skip at zero)
    review_status: ReviewStatus | None = None                 # default: the set's
    pool: Pool = "training"
    instructions_en: str | None = None
    stage: Stage | None = None


class ChoiceItem(ItemBase):
    """Types 1 (select) and 2 (listen): pick one option."""
    type: Literal["select", "listen"]
    question: str
    passage: str | None = None     # a text to read (CE items)
    audio: Audio | None = None
    options: list[Option] = Field(min_length=2, max_length=4)
    answer: str
    prompt_line: Speech | None = None   # what a character says before the learner answers
    reply: Speech | None = None         # the character's reply, shown after answering (guided dialogues)

    @model_validator(mode="after")
    def check(self):
        ids = [o.id for o in self.options]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate option ids")
        if len({o.text.strip().lower() for o in self.options}) != len(ids):
            raise ValueError("duplicate option texts")
        if self.answer not in ids:
            raise ValueError("answer is not one of the options")
        if self.type == "listen" and self.audio is None:
            raise ValueError("listen items need audio")
        return self


class ArrangeItem(ItemBase):
    """Type 3: put word tiles in order. answers[0] is the canonical order; others are valid alternatives."""
    type: Literal["arrange"]
    answers: list[list[str]] = Field(min_length=1)
    distractors: list[str] = Field(default_factory=list, max_length=3)
    translation: str | None = None
    explanation: str

    @model_validator(mode="after")
    def check(self):
        from .checking import normalize  # same comparison as the answer checker

        canonical = sorted(normalize(t) for t in self.answers[0])
        for alt in self.answers[1:]:
            if sorted(normalize(t) for t in alt) != canonical:
                raise ValueError("alternative orders must use exactly the same tiles")
        return self


class TypeItem(ItemBase):
    """Type 4: type the missing word(s). The sentence contains one ___ gap."""
    type: Literal["type"]
    sentence: str
    base_form: str | None = None   # e.g. the infinitive shown in brackets
    answers: list[str] = Field(min_length=1)
    hint: str | None = None
    explanation: str

    @model_validator(mode="after")
    def check(self):
        if self.sentence.count("___") != 1:
            raise ValueError("sentence must contain exactly one ___ gap")
        return self


class MultiItem(ItemBase):
    """Pick every correct option (e.g. the information to obtain in a speaking task 2)."""
    type: Literal["multi"]
    question: str
    options: list[Option] = Field(min_length=3, max_length=6)
    answers: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def check(self):
        ids = [o.id for o in self.options]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate option ids")
        if not set(self.answers) <= set(ids) or len(self.answers) == len(ids):
            raise ValueError("answers must be some (not all) of the options")
        return self


class CardLink(BaseModel):
    label: str
    to: str = Field(pattern=r"^/[a-z0-9/_-]*$")     # an in-app route, e.g. /oral/eo2-belleville


class CardItem(BaseModel):
    """Not scored: story scenes, method cards, language cards (stages B, C, H)."""
    id: str = Field(pattern=r"^[a-z0-9-]+$")
    type: Literal["card"]
    tcf_target: TcfTarget
    level: Level
    stage: Stage | None = None
    kind: Literal["story", "method", "language", "objective", "outro"]
    title: str
    body: str | None = None
    body_en: str | None = None
    lines: list[Speech] = Field(default_factory=list)
    points: list[str] = Field(default_factory=list)       # bullet points (method steps, expressions)
    link: CardLink | None = None                          # e.g. "Now do the real task"

    @model_validator(mode="after")
    def has_content(self):
        if not (self.body or self.lines or self.points):
            raise ValueError("a card needs a body, lines or points")
        return self


Item = Annotated[Union[ChoiceItem, ArrangeItem, TypeItem, MultiItem, CardItem], Field(discriminator="type")]


class MissionMeta(BaseModel):
    chapter: int = Field(ge=1, le=5)
    story: str                       # story id shared by all level versions (G.4)
    objective: str
    objective_en: str | None = None
    minutes: int = Field(ge=3, le=60)
    stage_titles: dict[Stage, str] = Field(default_factory=dict)


class ExerciseSet(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9-]+$")
    version: int = Field(ge=1)
    title: str
    level: str
    context: Literal["onboarding", "practice", "mission", "diagnostic", "review", "exam", "academy", "toolbox"] = "practice"
    group: str | None = None          # academy/toolbox: section or category used for grouping on screen
    tcf_target: TcfTarget
    mission: MissionMeta | None = None
    review_status: ReviewStatus = "draft"
    items: list[Item] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_ids(self):
        ids = [i.id for i in self.items]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate item ids")
        if self.context == "mission" and self.mission is None:
            raise ValueError("mission sets need mission metadata")
        if not any(i.type != "card" for i in self.items):
            raise ValueError("a set needs at least one scored item")
        return self


def validate_file(path: Path) -> ExerciseSet:
    data = json.loads(path.read_text())
    s = ExerciseSet.model_validate(data)
    if s.id != path.stem:
        raise ValueError(f"{path.name}: id '{s.id}' must match the file name")
    return s


@lru_cache(maxsize=None)
def all_sets() -> dict[str, ExerciseSet]:
    return {p.stem: validate_file(p) for p in sorted(SETS_DIR.glob("*.json"))}


def get_set(set_id: str) -> ExerciseSet | None:
    return all_sets().get(set_id)


def item_by_id(s: ExerciseSet, item_id: str):
    return next((i for i in s.items if i.id == item_id), None)


def public_item(item) -> dict:
    """What the browser may see: no answer keys, no explanations, tiles shuffled."""
    base = {
        "id": item.id, "type": item.type, "level": item.level, "stage": item.stage,
        "instructions": getattr(item, "instructions", None), "instructions_en": getattr(item, "instructions_en", None),
        "tcf_target": item.tcf_target.model_dump(),
    }
    if isinstance(item, CardItem):
        base |= {"kind": item.kind, "title": item.title, "body": item.body, "body_en": item.body_en,
                 "lines": [l.model_dump() for l in item.lines], "points": item.points,
                 "link": item.link.model_dump() if item.link else None}
    else:
        base |= {"has_hint": bool(getattr(item, "hint", None)) or isinstance(item, ArrangeItem),
                 "time_limit_s": item.time_limit_s}
    if isinstance(item, MultiItem):
        base |= {"question": item.question, "options": [{"id": o.id, "text": o.text} for o in item.options],
                 "count": len(item.answers)}
    elif isinstance(item, ChoiceItem):
        base |= {
            "question": item.question, "passage": item.passage,
            "audio": item.audio.model_dump() if item.audio else None,
            "options": [{"id": o.id, "text": o.text} for o in item.options],
            "prompt_line": item.prompt_line.model_dump() if item.prompt_line else None,
        }
    elif isinstance(item, ArrangeItem):
        tiles = list(item.answers[0]) + list(item.distractors)
        random.Random(item.id).shuffle(tiles)  # same order on every load (resume-safe)
        base |= {"tiles": tiles, "translation": item.translation}
    elif isinstance(item, TypeItem):
        base |= {"sentence": item.sentence, "base_form": item.base_form, "has_hint": True}
    return base


def scored(items) -> list:
    return [i for i in items if i.type != "card"]


def difficulty(item) -> int:
    return item.difficulty or LEVEL_DIFFICULTY[item.level]


def review_status(s: ExerciseSet, item) -> str:
    return getattr(item, "review_status", None) or s.review_status


def playable(s: ExerciseSet) -> list:
    """Items shown when this set is played: assessment items stay reserved outside diagnostics."""
    if s.context in ("diagnostic", "exam"):
        return list(s.items)
    return [i for i in s.items if getattr(i, "pool", "training") != "assessment"]


def fresh_items(competency: str, exclude: set[str], section: str | None = None, near: int = 3) -> list[tuple[str, object]]:
    """Unseen, reviewed training items that practise `competency`, best match first, as (set_id, item).
    Used to confirm improvement on a question the learner has never answered (transfer, not memory)."""
    found = []
    for s in all_sets().values():
        if s.context == "review":
            continue
        for i in scored(s.items):
            if (competency in i.competencies and i.id not in exclude and i.pool == "training"
                    and review_status(s, i) == "reviewed"):
                rank = (0 if i.competencies[0] == competency else 1,
                        0 if section is None or i.tcf_target.section == section else 1,
                        abs(difficulty(i) - near), i.id)
                found.append((rank, s.id, i))
    return [(sid, i) for _, sid, i in sorted(found, key=lambda t: t[0])]


def split_composite(item_id: str) -> tuple[str, str] | None:
    """Review sessions copy items as '<set>--<item>'; return (set_id, item_id)."""
    if "--" not in item_id:
        return None
    set_id, original = item_id.split("--", 1)
    return set_id, original


def resolve_item(set_id: str | None, item_id: str):
    """Find an item by the ids stored on an attempt, including review-session copies."""
    composite = split_composite(item_id)
    if composite:
        set_id, item_id = composite
    s = get_set(set_id) if set_id else None
    return (s, item_by_id(s, item_id)) if s else (None, None)

"""French text → spoken text, for text-to-speech only. The displayed text is never changed.

Why: TTS engines read what they are given. Symbols like « / », « … », Markdown stars or
« M. » come out as "slash", "point point point" or "M point". This module prepares a
separate, natural spoken version and splits it into short sentences.
"""

from __future__ import annotations

import re

# ---------- numbers in words (French, 0 – 999 999 999) ----------

_UNITS = ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix",
          "onze", "douze", "treize", "quatorze", "quinze", "seize"]
_TENS = {2: "vingt", 3: "trente", 4: "quarante", 5: "cinquante", 6: "soixante"}


def _below_100(n: int) -> str:
    if n <= 16:
        return _UNITS[n]
    if n < 20:
        return "dix-" + _UNITS[n - 10]
    tens, unit = divmod(n, 10)
    if tens in (7, 9):                              # soixante-dix…, quatre-vingt-dix…
        base = "soixante" if tens == 7 else "quatre-vingt"
        rest = 10 + unit
        if tens == 7 and unit == 1:
            return "soixante et onze"
        return f"{base}-{_below_100(rest)}"
    if tens == 8:
        return "quatre-vingts" if unit == 0 else f"quatre-vingt-{_UNITS[unit]}"
    word = _TENS[tens]
    if unit == 0:
        return word
    if unit == 1:
        return f"{word} et un"
    return f"{word}-{_UNITS[unit]}"


def _below_1000(n: int) -> str:
    hundreds, rest = divmod(n, 100)
    if hundreds == 0:
        return _below_100(rest)
    head = "cent" if hundreds == 1 else f"{_UNITS[hundreds]} cent"
    if rest == 0:
        return head + ("s" if hundreds > 1 else "")
    return f"{head} {_below_100(rest)}"


def number_words(n: int) -> str:
    if n < 0:
        return "moins " + number_words(-n)
    if n < 1000:
        return _below_1000(n)
    if n < 1_000_000:
        thousands, rest = divmod(n, 1000)
        if thousands == 1:
            head = "mille"
        else:
            words = _below_1000(thousands)
            # « deux cents » and « quatre-vingts » lose their s before « mille »
            if words.endswith("cents") or words.endswith("vingts"):
                words = words[:-1]
            head = f"{words} mille"
        return head if rest == 0 else f"{head} {_below_1000(rest)}"
    millions, rest = divmod(n, 1_000_000)
    head = f"{number_words(millions)} million" + ("s" if millions > 1 else "")
    return head if rest == 0 else f"{head} {number_words(rest)}"


_MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
           "septembre", "octobre", "novembre", "décembre"]
_FRACTIONS = {"1/2": "un demi", "1/3": "un tiers", "2/3": "deux tiers", "1/4": "un quart", "3/4": "trois quarts"}
_PER = {"h": "heure", "j": "jour", "jour": "jour", "an": "an", "mois": "mois", "semaine": "semaine",
        "kg": "kilo", "km": "kilomètre", "l": "litre", "personne": "personne", "pers": "personne", "nuit": "nuit"}
_ABBREVIATIONS = [
    (r"\bMM\.\s", "Messieurs "), (r"\bM\.\s", "Monsieur "), (r"\bMmes\b", "Mesdames"), (r"\bMme\b", "Madame"),
    (r"\bMlle\b", "Mademoiselle"), (r"\bDr\b\.?", "Docteur"), (r"\bPr\b\.?", "Professeur"),
    (r"\betc\.", "et cetera"), (r"\bp\. ?ex\.", "par exemple"), (r"\benv\.", "environ"),
    (r"\bc\.-à-d\.", "c'est-à-dire"), (r"\bn°\s?", "numéro "), (r"\bN°\s?", "numéro "),
    (r"\bTél\.?\s?", "téléphone "), (r"\bcf\.", "voir"),
]


def _ordinal(m: re.Match) -> str:
    n = int(m.group(1))
    if n == 1:
        return "première" if m.group(2) in ("re", "ère") else "premier"
    word = number_words(n)
    if word.endswith("e"):
        word = word[:-1]
    if word.endswith("f"):
        word = word[:-1] + "v"
    if word.endswith("q"):
        word += "u"
    return word + "ième"


def _price(m: re.Match) -> str:
    euros, cents = int(m.group(1)), m.group(2)
    if not cents:
        return f"{number_words(euros)} euro" + ("s" if euros > 1 else "")
    cents = int(cents.ljust(2, "0"))
    return f"{number_words(euros)} euro{'s' if euros > 1 else ''} {number_words(cents)}"


def _time(m: re.Match) -> str:
    hours, minutes = int(m.group(1)), m.group(2)
    out = f"{number_words(hours)} heure" + ("s" if hours > 1 else "")
    if minutes and int(minutes):
        out += f" {number_words(int(minutes))}"
    return out


def _date(m: re.Match) -> str:
    day, month, year = int(m.group(1)), int(m.group(2)), m.group(3)
    if not (1 <= day <= 31 and 1 <= month <= 12):
        return m.group(0)
    d = "premier" if day == 1 else number_words(day)
    out = f"{d} {_MONTHS[month - 1]}"
    if year:
        y = int(year)
        out += " " + number_words(y)
    return out


def _decimal(m: re.Match) -> str:
    return f"{number_words(int(m.group(1)))} virgule {number_words(int(m.group(2)))}" if not m.group(2).startswith("0") \
        else f"{number_words(int(m.group(1)))} virgule " + " ".join(number_words(int(c)) for c in m.group(2))


def to_speech(text: str) -> str:
    """Return the natural spoken version of a French text."""
    t = text
    t = re.sub(r"_{2,}", " … ", t)                                      # gaps first (before Markdown rules)

    # Markdown and formatting artifacts
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    t = re.sub(r"`([^`]*)`", r"\1", t)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", t)                      # images
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)                     # links → their text
    t = re.sub(r"<[^>]+>", " ", t)                                     # html tags
    t = re.sub(r"^\s{0,3}#{1,6}\s*", "", t, flags=re.M)                # headings
    t = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s+", "", t, flags=re.M)         # list bullets
    t = re.sub(r"(\*\*|__|\*|_)(?=\S)(.+?)(?<=\S)\1", r"\2", t)          # bold/italic
    t = re.sub(r"https?://\S+|www\.\S+|\S+@\S+\.\w+", " ", t)          # URLs and e-mails are not read

    # Quotes, dashes, brackets
    t = t.replace("«", " ").replace("»", " ").replace("“", " ").replace("”", " ").replace('"', " ")
    t = re.sub(r"^\s*[—–-]\s+", "", t, flags=re.M)                     # dialogue dash at line start
    t = re.sub(r"\s[—–]\s", ", ", t)
    t = re.sub(r"[()\[\]]", ", ", t)
    t = t.replace(";", ",")

    # Ellipses (gaps were turned into ellipses above)
    t = t.replace("...", "…")
    t = re.sub(r"\s*…\s*(?=[?!.,:]|$)", "", t)                          # « Pourquoi… ? » → « Pourquoi ? »
    t = re.sub(r"\s*…\s*", ", ", t)

    # Abbreviations
    for pattern, spoken in _ABBREVIATIONS:
        t = re.sub(pattern, spoken, t)

    # Dates, times, prices, units, fractions, slashes (order matters)
    t = re.sub(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", _date, t)
    t = re.sub(r"\b(\d{1,2}) ?h ?(\d{2})?\b(?![a-zà-ÿ])", _time, t)
    t = re.sub(r"\b(\d+)(?:,(\d{1,2}))? ?€", _price, t)
    t = re.sub(r"€", " euros ", t)
    t = re.sub(r"\bkm/h\b", "kilomètres-heure", t)
    for frac, spoken in _FRACTIONS.items():
        t = re.sub(rf"(?<![\d/]){re.escape(frac)}(?![\d/])", spoken, t)
    t = re.sub(r"/\s?(h|j|jour|an|mois|semaine|kg|km|l|personne|pers|nuit)\b",
               lambda m: f" par {_PER[m.group(1)]}", t)
    t = re.sub(r"\bet/ou\b", "et ou", t)
    t = re.sub(r"([?!.])\s*/\s*", r"\1 ", t)                          # « Quand ? / Où ? »: a list, just pause
    t = re.sub(r"\s*/\s*", " ou ", t)                                   # word/word, « … ? / … ? »
    t = re.sub(r"(\d+) ?%", lambda m: f"{number_words(int(m.group(1)))} pour cent", t)
    t = re.sub(r"(\d+) ?kg\b", lambda m: f"{number_words(int(m.group(1)))} kilos", t)
    t = re.sub(r"(\d+) ?km\b", lambda m: f"{number_words(int(m.group(1)))} kilomètres", t)
    t = re.sub(r"(\d+) ?min\b", lambda m: f"{number_words(int(m.group(1)))} minutes", t)
    t = re.sub(r"(\d+) ?°C?", lambda m: f"{number_words(int(m.group(1)))} degrés", t)
    t = t.replace("&", " et ").replace("+", " plus ").replace("=", " égale ")

    # Ordinals and remaining numbers
    t = re.sub(r"\b(\d+)(er|re|ère|e|ème)\b", _ordinal, t)
    t = re.sub(r"\b(\d+),(\d+)\b", _decimal, t)
    t = re.sub(r"\b(\d{1,3}(?:[  ]\d{3})+)\b", lambda m: number_words(int(re.sub(r"\D", "", m.group(1)))), t)
    t = re.sub(r"\b\d+\b", lambda m: number_words(int(m.group(0))), t)

    # Clean up punctuation and spacing
    t = re.sub(r"[*#|~^]", " ", t)
    t = re.sub(r"\s+([,.!?:])", r"\1", t)
    t = re.sub(r"([,:])(?=\S)", r"\1 ", t)
    t = re.sub(r"(,\s*){2,}", ", ", t)
    t = re.sub(r"^[\s,]+", "", t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\s*\n\s*", " ", t).strip(" ,")
    t = re.sub(r"\s*([?!:])", r" \1", t)                                # French space before ? ! :
    t = re.sub(r"\s*:$", "", t)                                          # a dangling colon (e.g. a removed URL)
    if t and t[-1] not in ".!?":
        t += "."
    return t


def sentences(text: str, max_chars: int = 220) -> list[str]:
    """Split spoken text into short sentences so engines keep natural intonation and pauses."""
    spoken = to_speech(text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-ÖØ-Þ«])", spoken)
    out: list[str] = []
    for p in parts:
        while len(p) > max_chars:                                         # very long sentence: cut at a comma
            cut = p.rfind(", ", 0, max_chars)
            if cut <= 0:
                break
            out.append(p[:cut].strip() + ",")
            p = p[cut + 2:]
        if p.strip():
            out.append(p.strip())
    return out

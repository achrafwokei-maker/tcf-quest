"""Speech normalisation: the spoken version must never read symbols aloud."""

import pytest

from tcfquest.tts_text import number_words, sentences, to_speech


@pytest.mark.parametrize("n,words", [
    (0, "zéro"), (1, "un"), (16, "seize"), (17, "dix-sept"), (21, "vingt et un"), (22, "vingt-deux"),
    (70, "soixante-dix"), (71, "soixante et onze"), (77, "soixante-dix-sept"), (80, "quatre-vingts"),
    (81, "quatre-vingt-un"), (91, "quatre-vingt-onze"), (99, "quatre-vingt-dix-neuf"), (100, "cent"),
    (101, "cent un"), (200, "deux cents"), (201, "deux cent un"), (1000, "mille"), (2026, "deux mille vingt-six"),
    (200000, "deux cent mille"), (80000, "quatre-vingt mille"), (1_500_000, "un million cinq cent mille"),
])
def test_number_words(n, words):
    assert number_words(n) == words


@pytest.mark.parametrize("text,spoken", [
    # slashes
    ("Pourquoi… ? / Quand… ? / À quelle heure… ?", "Pourquoi ? Quand ? À quelle heure ?"),
    ("Vous venez ? / Oui, demain.", "Vous venez ? Oui, demain."),
    ("Cher étudiant/étudiante,", "Cher étudiant ou étudiante."),
    ("Vous pouvez payer par carte et/ou en espèces.", "Vous pouvez payer par carte et ou en espèces."),
    ("Le loyer est de 850 €/mois.", "Le loyer est de huit cent cinquante euros par mois."),
    ("Limitée à 30 km/h.", "Limitée à trente kilomètres-heure."),
    ("Ajoutez 1/2 litre de lait.", "Ajoutez un demi litre de lait."),
    ("Rendez-vous le 16/10/2026.", "Rendez-vous le seize octobre deux mille vingt-six."),
    # ellipses and gaps
    ("Je voudrais savoir…", "Je voudrais savoir."),
    ("Pourriez-vous me dire… ?", "Pourriez-vous me dire ?"),
    ("Nous ___ à Paris.", "Nous, à Paris."),
    # abbreviations, times, prices, ordinals
    ("M. Delaunay et Mme Roux arrivent.", "Monsieur Delaunay et Madame Roux arrivent."),
    ("Le train de 8 h 15 est supprimé.", "Le train de huit heures quinze est supprimé."),
    ("Il arrive vers 11 h.", "Il arrive vers onze heures."),
    ("Ça fait 2,40 €.", "Ça fait deux euros quarante."),
    ("C'est le 1er étage, au 3e bureau.", "C'est le premier étage, au troisième bureau."),
    ("J'ai besoin de 20 kg de comté.", "J'ai besoin de vingt kilos de comté."),
    # formatting artifacts
    ("**Attention** : lisez *bien* la consigne.", "Attention : lisez bien la consigne."),
    ("- Bonjour !\n- Bonjour, Madame.", "Bonjour ! Bonjour, Madame."),
    ("Voir [le site](https://example.com) pour plus d'infos.", "Voir le site pour plus d'infos."),
    ("« Vous tombez bien ! » dit-elle.", "Vous tombez bien ! dit-elle."),
    ("Info : https://www.france-education-international.fr/test/tcf-canada", "Info."),
])
def test_to_speech(text, spoken):
    assert to_speech(text) == spoken


def test_symbols_never_survive():
    nasty = "Prix : 3/4 du total / 12 % / **gras** / _x_ / # titre / n° 5 / A&B / ___"
    out = to_speech(nasty)
    for sym in ["/", "*", "#", "_", "&", "%", "°"]:
        assert sym not in out, (sym, out)


def test_display_text_is_untouched():
    original = "Pourquoi… ? / Quand… ?"
    to_speech(original)
    assert original == "Pourquoi… ? / Quand… ?"


def test_sentences_are_short_and_complete():
    text = "Bonjour ! Mon fournisseur, c'est M. Delaunay. Il livre le vendredi soir."
    assert sentences(text) == ["Bonjour !", "Mon fournisseur, c'est Monsieur Delaunay.", "Il livre le vendredi soir."]
    long = "Il faut " + ", ".join(["un mot de plus"] * 30) + "."
    assert all(len(s) <= 221 for s in sentences(long))

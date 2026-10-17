"""Answer-checking rules from blueprint section E.2."""

from tcfquest.checking import check_arrange, check_choice, check_typed, normalize


def v(response, answers):
    return check_typed(response, answers).verdict


def test_case_punctuation_and_apostrophes_do_not_matter():
    assert v("Habitons.", ["habitons"]) == "correct"
    assert v("  s’il   vous plaît ", ["s'il vous plaît"]) == "correct"
    assert normalize("« Bonjour ! »") == "bonjour"


def test_alternatives_are_accepted():
    assert v("souhaiterais", ["voudrais", "souhaiterais"]) == "correct"


def test_missing_accent_that_does_not_change_the_word_is_correct_with_note():
    r = check_typed("ete", ["été"])
    assert r.verdict == "correct" and "accent" in r.note.lower()


def test_accent_that_changes_the_word_is_incorrect():
    for given, target in [("a", "à"), ("ou", "où"), ("du", "dû"), ("la", "là")]:
        r = check_typed(given, [target])
        assert r.verdict == "incorrect", (given, target)
        assert "accent changes the meaning" in r.note


def test_accent_rule_inside_a_phrase():
    assert v("je vais a paris", ["je vais à paris"]) == "incorrect"
    assert v("il etait la", ["il était là"]) == "incorrect"      # là vs la
    assert v("nous etions contents", ["nous étions contents"]) == "correct"


def test_wrong_ending_is_partial():
    r = check_typed("vient", ["viennes"])
    assert r.verdict == "partial"
    assert check_typed("allé", ["allés"]).verdict == "partial"
    assert check_typed("habitez", ["habitons"]).verdict == "partial"


def test_one_letter_typo_in_long_word_is_partial_but_not_in_ending():
    assert check_typed("restaurent", ["restaurant"]).verdict == "partial"
    assert check_typed("rstaurant", ["restaurant"]).verdict == "partial"


def test_wrong_word_and_empty_are_incorrect():
    assert v("mangeons", ["habitons"]) == "incorrect"
    assert v("", ["habitons"]) == "incorrect"
    assert v("   ", ["habitons"]) == "incorrect"


def test_choice():
    assert check_choice("b", "b").verdict == "correct"
    assert check_choice("a", "b").verdict == "incorrect"


def test_arrange_exact_alternative_swap_and_wrong():
    answers = [["Je", "serais", "venu", "plus", "tôt", "si", "j'avais", "su."],
               ["Si", "j'avais", "su,", "je", "serais", "venu", "plus", "tôt."]]
    assert check_arrange(["si", "j'avais", "su", "je", "serais", "venu", "plus", "tôt"], answers).verdict == "correct"
    assert check_arrange(answers[0], answers).verdict == "correct"
    swapped = ["Je", "serais", "venu", "tôt", "plus", "si", "j'avais", "su."]
    r = check_arrange(swapped, answers)
    assert r.verdict == "partial" and r.details["wrong_positions"] == [3, 4]
    assert check_arrange(["Je", "venu", "serais", "plus", "si", "tôt", "j'avais", "su."], answers).verdict == "incorrect"
    assert check_arrange(["Je", "aurais"], answers).verdict == "incorrect"

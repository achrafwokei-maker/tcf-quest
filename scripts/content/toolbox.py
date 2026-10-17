"""Generate the Boîte à outils lessons (content/sets/outil-*.json). Original content.
Each lesson: a card (what / when / when not / example) + an adaptation exercise (gap) + a practice question.
Competencies match the weakness keys so the planner can assign them and they can serve as unseen retests."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "content" / "sets"


def lesson(id, group, title, sec, task, comp, what, when, when_not, example, gap, mcq, level="B1"):
    tcf = {"section": sec, **({"task": task} if task else {}), "purpose": f"Boîte à outils: {title}."}
    sentence, answers, base, gexpl = gap
    q, opts, ans = mcq
    return {"id": f"outil-{id}", "version": 1, "title": title, "review_status": "reviewed", "level": level,
            "context": "toolbox", "group": group, "tcf_target": tcf, "items": [
                {"id": f"o-{id}-fiche", "type": "card", "tcf_target": tcf, "level": level, "kind": "method", "title": title,
                 "stage": "B", "points": [f"Ce que c'est : {what}", f"Quand l'utiliser : {when}", f"Quand l'éviter : {when_not}", f"Exemple : {example}"]},
                {"id": f"o-{id}-adapter", "type": "type", "tcf_target": tcf, "level": level, "competencies": [comp], "stage": "D",
                 "instructions": "Complétez la phrase.", "instructions_en": "Fill in the gap.", "sentence": sentence,
                 "answers": answers, **({"base_form": base} if base else {}), "explanation": gexpl},
                {"id": f"o-{id}-pratique", "type": "select", "tcf_target": tcf, "level": level, "competencies": [comp], "stage": "E",
                 "instructions": "Choisissez la bonne réponse.", "question": q,
                 "options": [{"id": k, "text": t, "explanation": e} for k, t, e in opts], "answer": ans},
            ]}


L = [
 lesson("questions-t2", "Cadres de réponse", "Poser des questions (tâche 2)", "EO", "EO-T2", "eo.question-polie",
        "trois formes de question : est-ce que, inversion, question indirecte.", "pour varier et rester poli au téléphone.",
        "n'utilisez pas « est-ce que » dans une question indirecte.", "« Pourriez-vous me dire à quelle heure vous fermez ? »",
        ("Je voudrais savoir ___ le parking est gratuit.", ["si"], None, "Indirect yes/no question: « savoir si »."),
        ("Quelle question est correcte ?", [("a", "« Je voudrais savoir quand est-ce que vous ouvrez. »", "No « est-ce que » after « savoir »."),
          ("b", "« Je voudrais savoir quand vous ouvrez. »", "Yes."), ("c", "« Je voudrais savoir quand ouvrez-vous. »", "No inversion in indirect questions."),
          ("d", "« Je voudrais savoir que vous ouvrez. »", "« que » doesn't ask.")], "b")),
 lesson("plan-t3", "Cadres de réponse", "Plan d'argumentation (tâche 3)", "EO", "EO-T3", "eo.argumenter",
        "opinion → argument 1 + exemple → argument 2 + exemple → concession → conclusion.", "pour parler 4 minutes de façon organisée.",
        "ne récitez pas un texte appris : adaptez-le à la question posée.", "« À mon avis, … D'une part… Par exemple… D'autre part… Certes… mais… En conclusion… »",
        ("Certes, le vélo est écologique, ___ il est dangereux en hiver.", ["mais"], None, "« Certes… mais »: concession then your point."),
        ("Que faut-il dire en premier ?", [("a", "Votre opinion.", "Yes: start with a clear position."), ("b", "Une anecdote sans rapport.", "Off-topic."),
          ("c", "La conclusion.", "Comes last."), ("d", "« Je ne sais pas. »", "No position.")], "a")),
 lesson("intro-conclusion", "Cadres de réponse", "Introduire et conclure (écrit)", "EE", "EE-T3", "ee.structure",
        "une phrase d'introduction qui présente le sujet et une conclusion qui reprend votre position.", "en tâche 2 et 3 surtout.",
        "pas de longue introduction générale : chaque mot compte dans la fourchette.", "« La question du télétravail divise. … En somme, un modèle hybride me semble le plus juste. »",
        ("___ somme, je pense qu'il faut limiter le temps d'écran.", ["En", "en"], None, "« En somme » introduces a conclusion."),
        ("Quelle phrase est une bonne conclusion ?", [("a", "« Pour toutes ces raisons, je reste favorable au télétravail partiel. »", "Yes: restates the position."),
          ("b", "« Le télétravail existe. »", "Not a conclusion."), ("c", "« Ensuite, il y a le prix. »", "Adds a new point."), ("d", "« Merci. »", "Not a conclusion.")], "a")),
 lesson("connecteurs-opposition", "Connecteurs", "Connecteurs d'opposition", "EE", None, "gram.connecteur-opposition",
        "mais, cependant, pourtant, en revanche, alors que, bien que (+ subjonctif).", "pour comparer deux points de vue ou nuancer.",
        "« bien que » demande le subjonctif ; « malgré » est suivi d'un nom.", "« Bien que ce soit cher, cela vaut la peine. » / « Malgré le prix, … »",
        ("___ le froid, nous sommes sortis.", ["Malgré", "malgré"], None, "« Malgré » + noun."),
        ("Complétez : « Il est fatigué ___ il a dormi dix heures. »", [("a", "alors qu'", "Yes: contrast between two facts."), ("b", "donc", "Consequence."),
          ("c", "parce qu'", "Cause."), ("d", "ensuite", "Sequence.")], "a")),
 lesson("connecteurs-logiques", "Connecteurs", "Cause, conséquence, addition", "EE", None, "ee.connecteurs",
        "car, parce que, puisque / donc, c'est pourquoi, ainsi / de plus, en outre.", "pour enchaîner vos idées en tâche 2 et 3.",
        "ne commencez pas une phrase par « car ».", "« Le loyer est élevé ; c'est pourquoi beaucoup partagent un appartement. »",
        ("Il pleuvait, ___ nous sommes restés à la maison.", ["donc"], None, "« donc »: consequence."),
        ("Quel connecteur ajoute un argument ?", [("a", "De plus", "Yes: addition."), ("b", "Pourtant", "Opposition."), ("c", "Car", "Cause."), ("d", "Bref", "Summary.")], "a")),
 lesson("registre", "Registre", "Tu ou vous ? Formel ou amical ?", "EE", "EE-T1", "ee.registre",
        "le registre s'adapte au destinataire : ami (tu, familier), inconnu ou supérieur (vous, formel).", "dans chaque message de la tâche 1.",
        "ne mélangez pas tu et vous dans le même message.", "« Salut Léa, tu viens samedi ? » / « Madame, pourriez-vous me confirmer… »",
        ("Madame, pourriez-___ me rappeler demain ?", ["vous"], None, "Formal recipient: « vous »."),
        ("Vous écrivez à un ami. Quelle formule de fin ?", [("a", "« À bientôt ! »", "Yes: friendly."), ("b", "« Veuillez agréer mes salutations distinguées. »", "Too formal."),
          ("c", "« Cordialement, Monsieur. »", "Formal."), ("d", "« Respectueusement. »", "Formal.")], "a")),
 lesson("elision", "Grammaire", "L'élision : j', l', qu', s'il", "EE", None, "orth.orthographe",
        "devant une voyelle ou un h muet, je → j', le/la → l', que → qu', si il → s'il.", "toujours, à l'écrit comme à l'oral.",
        "pas d'élision devant un h aspiré (le héros) ni avec « si elle ».", "« J'habite ici. » / « Je pense qu'il viendra. » / « S'il pleut… »",
        ("Je ___ aime beaucoup ce quartier.", ["l'"], None, "« le » + vowel → « l' »."),
        ("Quelle phrase est correcte ?", [("a", "« Si il fait beau, on sort. »", "« si il » → « s'il »."), ("b", "« S'il fait beau, on sort. »", "Yes."),
          ("c", "« Si'l fait beau, on sort. »", "Wrong apostrophe."), ("d", "« Sil fait beau, on sort. »", "Missing apostrophe.")], "b")),
 lesson("a-ou-accents", "Grammaire", "a/à, ou/où, et/est", "EE", None, "orth.accents",
        "a = verbe avoir, à = préposition ; ou = choix, où = lieu/temps ; et = addition, est = verbe être.", "dans chaque texte : ce sont des erreurs fréquentes et visibles.",
        "remplacez par « avait », « ou bien » ou « était » pour vérifier.", "« Il a rendez-vous à 9 h. » / « Où habites-tu ? »",
        ("Je vais ___ Montréal demain.", ["à"], None, "Preposition « à » (not the verb « a »)."),
        ("Complétez : « Tu préfères le thé ___ le café ? »", [("a", "ou", "Yes: a choice."), ("b", "où", "Place/time."), ("c", "et", "Addition, not a choice."), ("d", "est", "Verb.")], "a")),
 lesson("passe-imparfait", "Grammaire", "Passé composé ou imparfait ?", "EE", "EE-T2", "gram.temps-du-passe",
        "passé composé : action terminée, ponctuelle ; imparfait : décor, habitude, description.", "dans tout récit (tâche 2, entretien).",
        "n'utilisez pas l'imparfait pour une suite d'actions (« je me levais, je partais » = habitude).", "« Il faisait nuit quand le train est arrivé. »",
        ("Quand j'étais petit, je ___ au parc tous les jours.", ["jouais"], "jouer", "Habit in the past → imparfait."),
        ("Complétez : « Hier, je ___ mes clés et je suis rentré à pied. »", [("a", "perdais", "Imperfect: not a single completed action."), ("b", "ai perdu", "Yes: completed action."),
          ("c", "perds", "Present."), ("d", "perdrai", "Future.")], "b")),
 lesson("accord", "Grammaire", "Accords sujet-verbe et adjectifs", "EE", None, "gram.accord",
        "le verbe s'accorde avec son sujet ; l'adjectif avec le nom (genre et nombre).", "à chaque relecture : c'est souvent ce qui fait perdre des points.",
        "attention au sujet éloigné : « Les enfants de ma voisine sont… »", "« Les employés étaient gentils. » / « une ville animée »",
        ("Les cours de yoga ___ compris dans le prix.", ["sont"], "être", "Plural subject « les cours » → « sont »."),
        ("Quelle phrase est correcte ?", [("a", "« Les gens est accueillants. »", "« les gens » is plural."), ("b", "« Les gens sont accueillants. »", "Yes."),
          ("c", "« Les gens sont accueillant. »", "Adjective agreement missing."), ("d", "« Les gens êtes accueillants. »", "Wrong person.")], "b")),
 lesson("conditionnel-politesse", "Grammaire", "Le conditionnel de politesse", "EO", "EO-T2", "gram.conditionnel-politesse",
        "je voudrais, pourriez-vous, j'aimerais, serait-il possible de…", "pour demander poliment (tâche 2, messages formels).",
        "pas besoin de le répéter dans chaque phrase : variez.", "« Serait-il possible de visiter l'appartement jeudi ? »",
        ("Bonjour, je ___ réserver une table pour deux.", ["voudrais", "souhaiterais", "aimerais"], "vouloir", "Polite request: « je voudrais »."),
        ("Quelle demande est la plus polie ?", [("a", "« Donnez-moi le prix. »", "Imperative: too direct."), ("b", "« Pourriez-vous m'indiquer le prix ? »", "Yes: conditional."),
          ("c", "« Le prix ! »", "Rude."), ("d", "« Je veux le prix. »", "Too direct.")], "b")),
 lesson("gestion-temps", "Temps", "Gérer son temps le jour J", "CE", None, "ce.gestion-temps",
        "un budget par épreuve : CO ~ 55 s par question, CE ~ 1 min 30, EE : environ 15/20/25 min pour T1/T2/T3.",
        "en entraînement chronométré et à l'examen.", "ne bloquez jamais sur une question : choisissez, notez mentalement, avancez.",
        "En compréhension écrite, après 2 minutes sur une question, choisissez la meilleure option et passez à la suivante.",
        ("En CE, on a environ une minute et ___ par question.", ["demie"], None, "60 min / 39 questions ≈ 1 min 30 (une minute et demie)."),
        ("Vous bloquez sur une question de CE depuis 3 minutes. Que faites-vous ?", [("a", "Je choisis la meilleure option et je passe.", "Yes: protect the time for easier questions."),
          ("b", "Je relis tout le texte encore deux fois.", "Costs too much time."), ("c", "Je laisse vide et j'attends.", "An answer is better than none."), ("d", "J'abandonne l'épreuve.", "No.")], "a")),
]
for s in L:
    (OUT / f"{s['id']}.json").write_text(json.dumps(s, ensure_ascii=False, indent=2))
print(len(L), "lessons")

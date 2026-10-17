"""Generate the Académie TCF strategy modules (content/sets/acad-*.json). Original content.
Run: python3 scripts/content/academy.py  (then the content validator runs in the test suite)."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "content" / "sets"


def opt(k, t, e):
    return {"id": k, "text": t, "explanation": e}


def item(id, typ, sec, task, level, comps, q, opts, ans, stage, purpose, hint=None, timed=None, audio=None, passage=None, speaker="Narratrice"):
    it = {"id": id, "type": typ, "tcf_target": {"section": sec, **({"task": task} if task else {}), "purpose": purpose},
          "level": level, "competencies": comps, "instructions": "Choisissez la bonne réponse." if typ == "select" else "Écoutez et choisissez.",
          "question": q, "options": [opt(*o) for o in opts], "answer": ans, "stage": stage}
    if hint: it["hint"] = hint
    if timed: it["time_limit_s"] = timed
    if audio: it["audio"] = {"text": audio, "speaker": speaker}
    if passage: it["passage"] = passage
    return it


def card(id, sec, task, kind, title, points=None, body=None, stage="B", link=None, purpose="Strategy lesson (Académie TCF)."):
    c = {"id": id, "type": "card", "tcf_target": {"section": sec, **({"task": task} if task else {}), "purpose": purpose},
         "level": "B1", "kind": kind, "title": title, "stage": stage}
    if points: c["points"] = points
    if body: c["body"] = body
    if link: c["link"] = link
    return c


def module(id, title, sec, task, level, items):
    return {"id": id, "version": 1, "title": title, "review_status": "reviewed", "level": level, "context": "academy",
            "group": task or sec, "tcf_target": {"section": sec, **({"task": task} if task else {}),
                                                 "purpose": f"Académie TCF: strategy for {task or sec}, with guided, independent and timed practice."},
            "items": items}


M = []

# ---------- CO: distractors, one play ----------
M.append(module("acad-co", "Académie · Compréhension orale", "CO", None, "A2–B2", [
    card("aco-methode", "CO", None, "method", "Une seule écoute : la méthode", points=[
        "Avant l'audio : lisez la question et devinez ce qu'il faut entendre (une heure ? une raison ? un avis ?).",
        "Pendant : écoutez l'idée principale, puis le détail demandé. Ne notez pas tout.",
        "Méfiez-vous des mots entendus mot pour mot : le bon choix est souvent une reformulation.",
        "Les pièges : l'ancienne information (« au début… »), la mauvaise personne, un chiffre voisin.",
        "Si vous hésitez, éliminez d'abord ce qui n'est pas dit, puis choisissez et passez à la suite."]),
    card("aco-exemple", "CO", None, "language", "Exemple de piège", stage="C", body=
        "Audio : « Au départ, je voulais un appartement en ville, mais finalement j'ai choisi une maison à la campagne. » "
        "Question : Où habite-t-elle ? « En ville » a été entendu… mais c'est l'ancienne idée. La bonne réponse : à la campagne."),
    item("aco-guide-1", "listen", "CO", None, "A2", ["co.information-cle", "co.distracteur"], "Quand le cours a-t-il lieu ?",
         [("a", "Mardi.", "Mardi was the old day."), ("b", "Jeudi.", "Yes: « finalement, ce sera jeudi »."), ("c", "Tous les jours.", "Not said."), ("d", "Lundi.", "Not said.")],
         "b", "D", "One play: separate old and new information.", hint="Listen for « finalement »: the old day is a trap.",
         audio="Le cours de yoga devait avoir lieu mardi, mais finalement, ce sera jeudi, à la même heure."),
    item("aco-guide-2", "listen", "CO", None, "B1", ["co.intention", "co.distracteur"], "Pourquoi l'homme appelle-t-il ?",
         [("a", "Pour réserver une table.", "He already has a reservation."), ("b", "Pour annuler sa réservation.", "He keeps it."),
          ("c", "Pour changer le nombre de personnes.", "Yes: four instead of two."), ("d", "Pour se plaindre.", "No complaint.")],
         "c", "D", "Identify the purpose of a call.", hint="He doesn't cancel: listen to the number of people.",
         audio="Bonsoir, j'ai réservé une table pour deux personnes ce soir, à 20 heures. Est-ce qu'on pourrait être quatre finalement ?", speaker="M. Delaunay"),
    item("aco-auto-1", "listen", "CO", None, "B1", ["co.point-de-vue", "co.distracteur"], "Que pense-t-elle du film ?",
         [("a", "Elle l'a adoré du début à la fin.", "She found the start slow."), ("b", "Elle l'a trouvé ennuyeux.", "The ending changed her mind."),
          ("c", "Elle l'a finalement apprécié.", "Yes: « la fin m'a vraiment convaincue »."), ("d", "Elle ne l'a pas vu.", "She saw it.")],
         "c", "E", "Overall opinion after a concession.",
         audio="Le début du film était un peu lent, je l'avoue, mais la fin m'a vraiment convaincue. Je le recommande.", speaker="Madame Roux"),
    item("aco-auto-2", "listen", "CO", None, "B2", ["co.inference", "co.distracteur"], "Que comprend-on ?",
         [("a", "Le projet est abandonné.", "It's postponed, not abandoned."), ("b", "Le projet est reporté faute d'argent.", "Yes: the budget isn't ready, so later."),
          ("c", "Le projet commence demain.", "No."), ("d", "Le projet est terminé.", "No.")],
         "b", "E", "Implicit meaning: postponement and its cause.",
         audio="On aurait aimé lancer le chantier ce printemps, mais tant que le budget n'est pas voté, on ne peut rien faire. Ce sera sans doute pour l'automne."),
    item("aco-chrono", "listen", "CO", None, "B1", ["co.information-cle", "co.distracteur"], "Combien coûte le billet pour un étudiant ?",
         [("a", "20 $.", "That's the full price."), ("b", "12 $.", "Yes: « douze dollars pour les étudiants »."), ("c", "8 $.", "Not said."), ("d", "Gratuit.", "Free is for under-12s.")],
         "b", "F", "Timed: numbers and categories.", timed=45,
         audio="L'entrée coûte vingt dollars, douze dollars pour les étudiants, et c'est gratuit pour les moins de douze ans."),
]))

# ---------- CE: evidence, implicit meaning, time ----------
M.append(module("acad-ce", "Académie · Compréhension écrite", "CE", None, "A2–B2", [
    card("ace-methode", "CE", None, "method", "Lire pour répondre", points=[
        "Lisez d'abord la question : elle dit quoi chercher (un détail, le but, l'opinion).",
        "Trouvez la phrase-preuve dans le texte. Si aucune phrase ne prouve une option, elle est fausse.",
        "Attention aux connecteurs : « mais, cependant, pourtant » annoncent souvent l'idée importante.",
        "Pour l'opinion de l'auteur, regardez la conclusion et les mots qui jugent (heureusement, hélas…).",
        "Temps : environ 1 min 30 par question au TCF. Si un mot est inconnu, devinez-le grâce au contexte."]),
    card("ace-exemple", "CE", None, "language", "Exemple : la phrase-preuve", stage="C", body=
        "Texte : « Certes, le télétravail fait gagner du temps. Cependant, il isole les nouveaux employés. » "
        "Question : Que pense l'auteur ? La preuve est après « Cependant » : il voit surtout un risque d'isolement."),
    item("ace-guide-1", "select", "CE", None, "B1", ["ce.point-de-vue", "gram.connecteur-opposition"], "Que pense l'auteur des trottinettes électriques ?",
         [("a", "Elles sont parfaites.", "He sees a problem."), ("b", "Elles sont pratiques mais posent un problème de sécurité.", "Yes: after « pourtant »."),
          ("c", "Il faut les interdire.", "He asks for rules, not a ban."), ("d", "Personne ne les utilise.", "Not said.")],
         "b", "D", "Find the idea after the connector.", hint="Read what comes after « pourtant ».",
         passage="Les trottinettes électriques sont rapides et pratiques en ville. Pourtant, sans règles claires, elles mettent en danger les piétons sur les trottoirs."),
    item("ace-guide-2", "select", "CE", None, "B1", ["ce.vocabulaire-contexte", "ce.inference"], "Dans le texte, « bénévole » veut dire :",
         [("a", "Payé à l'heure.", "The text says they aren't paid."), ("b", "Qui travaille sans être payé.", "Yes: « sans recevoir de salaire »."),
          ("c", "Malade.", "No."), ("d", "Étudiant.", "No.")],
         "b", "D", "Guess an unknown word from context.", hint="Look at the end of the same sentence.",
         passage="Le festival fonctionne grâce à deux cents bénévoles, qui donnent de leur temps sans recevoir de salaire."),
    item("ace-auto-1", "select", "CE", None, "B1", ["ce.intention", "ce.information-cle"], "Quel est le but de ce message ?",
         [("a", "Inviter les voisins à une fête.", "No party."), ("b", "Prévenir d'une coupure d'eau.", "Yes."),
          ("c", "Demander de l'argent.", "No."), ("d", "Annoncer des travaux de peinture.", "It's plumbing work.")],
         "b", "E", "Identify the purpose of a notice.",
         passage="Avis aux résidents : en raison de travaux de plomberie, l'eau sera coupée mardi de 9 h à 13 h. Merci de prévoir des réserves."),
    item("ace-auto-2", "select", "CE", None, "B2", ["ce.inference", "ce.point-de-vue"], "Que suggère l'auteure ?",
         [("a", "Les applications de méditation sont inutiles.", "She doesn't say useless."), ("b", "Une application ne remplace pas un vrai changement d'habitudes.", "Yes: implicit in the last sentence."),
          ("c", "Il faut méditer plusieurs heures par jour.", "No."), ("d", "Les applications sont trop chères.", "Price isn't discussed.")],
         "b", "E", "Implicit meaning in a conclusion.",
         passage="Les applications de méditation promettent la sérénité en dix minutes par jour. Encore faut-il éteindre son téléphone ensuite, ce que peu d'utilisateurs font."),
    item("ace-chrono", "select", "CE", None, "B1", ["ce.document-pratique", "ce.information-cle"], "Où peut-on garer son vélo gratuitement ?",
         [("a", "Au sous-sol.", "The basement costs 2 $."), ("b", "Devant l'entrée principale.", "Yes: « gratuit devant l'entrée principale »."), ("c", "Sur le toit.", "Not mentioned."), ("d", "Nulle part.", "No.")],
         "b", "F", "Timed: find a detail fast.", timed=60,
         passage="Stationnement vélos : gratuit devant l'entrée principale ; 2 $ par jour au sous-sol (surveillé)."),
]))

# ---------- EO-T1 ----------
M.append(module("acad-eo1", "Académie · Expression orale, tâche 1", "EO", "EO-T1", "A2–B1", [
    card("aeo1-methode", "EO", "EO-T1", "method", "Entretien dirigé : développer chaque réponse", points=[
        "Répondez, puis ajoutez un détail : pourquoi, depuis quand, un exemple (la règle « réponse + 2 »).",
        "Variez les temps : présent pour aujourd'hui, passé composé pour une expérience, futur pour vos projets.",
        "Si vous ne comprenez pas : « Pardon, pouvez-vous répéter / reformuler ? » C'est permis et naturel.",
        "Évitez les réponses d'un mot et les textes appris par cœur : l'examinateur relance."]),
    card("aeo1-exemple", "EO", "EO-T1", "language", "Exemple : réponse + 2", stage="C", body=
        "Question : Vous aimez votre ville ? — Faible : « Oui. » — Bien : « Oui, beaucoup. J'habite à Montréal depuis deux ans, "
        "et ce que j'aime le plus, ce sont les festivals d'été. Par exemple, l'an dernier, je suis allé au festival de jazz. »"),
    item("aeo1-guide-1", "select", "EO", "EO-T1", "A2", ["eo.developper-reponse", "eo.parler-de-soi"], "Quelle réponse développe le mieux ?",
         [("a", "« Je travaille. »", "Too short."), ("b", "« Je suis infirmière depuis cinq ans, dans un hôpital. J'aime aider les gens, même si les horaires sont difficiles. »", "Yes: answer + reason + nuance."),
          ("c", "« Infirmière. »", "One word."), ("d", "« Je ne sais pas. »", "No answer.")],
         "b", "D", "Answer + 2 details.", hint="Look for the answer with a reason and a detail."),
    item("aeo1-guide-2", "select", "EO", "EO-T1", "A2", ["eo.interaction", "eo.reformuler"], "Vous n'avez pas compris la question. Que dites-vous ?",
         [("a", "« Quoi ? »", "Too abrupt for an examiner."), ("b", "« Pardon, pourriez-vous répéter la question, s'il vous plaît ? »", "Yes: polite and natural."),
          ("c", "Rien, vous attendez.", "Silence loses time."), ("d", "« Je ne parle pas français. »", "No.")],
         "b", "D", "Ask for repetition politely.", hint="Politeness + conditional."),
    item("aeo1-auto-1", "select", "EO", "EO-T1", "B1", ["eo.temps-verbaux", "gram.futur"], "Pour parler de vos projets, quelle phrase est correcte ?",
         [("a", "« L'année prochaine, je vais commencer une formation en informatique. »", "Yes: futur proche, correct."),
          ("b", "« L'année prochaine, j'ai commencé une formation. »", "Past tense for a future plan."),
          ("c", "« L'année prochaine, je commençais une formation. »", "Imperfect: wrong."), ("d", "« L'année prochaine, je commencer une formation. »", "Infinitive without auxiliary.")],
         "a", "E", "Future for plans."),
    item("aeo1-chrono", "select", "EO", "EO-T1", "B1", ["eo.developper-reponse", "eo.exemplifier"], "Quel ajout rend la réponse « J'aime cuisiner » plus riche ?",
         [("a", "« … c'est tout. »", "Ends the answer."), ("b", "« … surtout des plats de mon pays, par exemple le couscous du vendredi en famille. »", "Yes: specific example."),
          ("c", "« … oui. »", "Adds nothing."), ("d", "« … je ne sais pas pourquoi. »", "Weakens the answer.")],
         "b", "F", "Timed: add an example quickly.", timed=30),
    card("aeo1-application", "EO", "EO-T1", "outro", "À vous : l'entretien réel", stage="H",
         body="Faites une tâche 1 complète avec l'examinatrice (2 minutes), puis lisez le retour.",
         link={"label": "Faire la tâche 1", "to": "/oral/eo1-presentation"}),
]))

# ---------- EO-T2 ----------
M.append(module("acad-eo2", "Académie · Expression orale, tâche 2", "EO", "EO-T2", "A2–B1", [
    card("aeo2-methode", "EO", "EO-T2", "method", "Obtenir des informations en 3 min 30", points=[
        "Préparation (2 min) : listez 6 à 8 questions selon une grille : prix, horaires, lieu, conditions, ce qui est compris, alternatives.",
        "Ouverture polie : « Bonjour, je vous appelle au sujet de… »",
        "Une question à la fois, et réagissez à chaque réponse (« D'accord », « Ah, c'est dommage ! »).",
        "Variez les formes : est-ce que, inversion (« Pourriez-vous… ? »), question indirecte (« Je voudrais savoir si… »).",
        "Face à un imprévu, demandez une solution. Terminez par un résumé et des remerciements."]),
    card("aeo2-exemple", "EO", "EO-T2", "language", "Trois façons de demander", stage="C", points=[
        "Est-ce que le cours est ouvert aux débutants ?", "Le cours est-il ouvert aux débutants ?", "Je voudrais savoir si le cours est ouvert aux débutants."]),
    item("aeo2-guide-1", "select", "EO", "EO-T2", "A2", ["eo.question-polie", "gram.question-indirecte"], "Quelle question indirecte est correcte ?",
         [("a", "« Je voudrais savoir si la piscine est ouverte le dimanche. »", "Yes: « si » + indicative."),
          ("b", "« Je voudrais savoir est-ce que la piscine est ouverte. »", "No « est-ce que » in indirect questions."),
          ("c", "« Je voudrais savoir la piscine est-elle ouverte. »", "No inversion in indirect questions."), ("d", "« Je voudrais savoir que la piscine est ouverte. »", "« que » doesn't ask.")],
         "a", "D", "Indirect question form.", hint="Indirect yes/no questions use « si »."),
    item("aeo2-guide-2", "select", "EO", "EO-T2", "B1", ["eo.reaction-imprevu", "eo.interaction"], "On vous dit que le cours est complet. Quelle réaction est la meilleure ?",
         [("a", "« Bon, au revoir. »", "Ends without a solution."), ("b", "« Ah, c'est dommage ! Est-ce qu'il y a une liste d'attente ou un autre horaire ? »", "Yes: reacts and asks for an alternative."),
          ("c", "« Ce n'est pas possible ! »", "Not constructive."), ("d", "« D'accord. »", "Misses the chance to solve it.")],
         "b", "D", "Handle a surprise.", hint="React, then ask for an alternative."),
    item("aeo2-auto-1", "select", "EO", "EO-T2", "B1", ["eo.preparation-t2", "eo.obtenir-information"], "Vous louez un vélo. Quelle question oubliez-vous dans cette liste : prix, horaires, caution ?",
         [("a", "Le casque est-il fourni ?", "Yes: what's included is a key category."), ("b", "Quelle est votre couleur préférée ?", "Irrelevant."),
          ("c", "Vous aimez le vélo ?", "Personal, not information."), ("d", "Il fait beau ?", "Small talk.")],
         "a", "E", "Complete the preparation grid."),
    item("aeo2-chrono", "select", "EO", "EO-T2", "B1", ["eo.cloture-resume", "eo.interaction"], "Comment clore l'échange ?",
         [("a", "« Si je comprends bien, c'est 45 $ par mois, sans engagement. Merci beaucoup pour ces informations, bonne journée ! »", "Yes: summary + thanks."),
          ("b", "« OK. »", "Too abrupt."), ("c", "Raccrocher.", "No closure."), ("d", "« Je vous rappellerai peut-être, ou pas. »", "Impolite.")],
         "a", "F", "Timed: close with a summary.", timed=30),
    card("aeo2-application", "EO", "EO-T2", "outro", "À vous : l'appel réel", stage="H",
         body="Préparez-vous 2 minutes puis appelez le club de sport : 3 min 30 pour obtenir toutes les informations.",
         link={"label": "Faire la tâche 2", "to": "/oral/eo2-club-sport"}),
]))

# ---------- EO-T3 ----------
M.append(module("acad-eo3", "Académie · Expression orale, tâche 3", "EO", "EO-T3", "B1–B2", [
    card("aeo3-methode", "EO", "EO-T3", "method", "Défendre un point de vue en 4 min 30", points=[
        "Première phrase : votre opinion claire (« À mon avis, … »).",
        "Deux arguments, chacun avec un exemple concret tiré de la vie (« Par exemple, dans mon quartier… »).",
        "Une concession pour nuancer : « Certes…, mais… ».",
        "Réagissez aux relances de l'examinateur : il veut voir si vous pouvez préciser, pas changer d'avis.",
        "Conclusion courte qui reprend votre position."]),
    card("aeo3-exemple", "EO", "EO-T3", "language", "Connecteurs utiles", stage="C", points=[
        "D'abord / ensuite / enfin", "D'une part… d'autre part…", "Par exemple / prenons le cas de…", "Certes… mais… / Il est vrai que… cependant…", "En conclusion / Pour toutes ces raisons…"]),
    item("aeo3-guide-1", "select", "EO", "EO-T3", "B1", ["eo.argumenter", "eo.nuancer"], "Quelle phrase introduit une concession ?",
         [("a", "« Certes, la voiture est pratique, mais elle pollue beaucoup. »", "Yes: « Certes… mais »."), ("b", "« La voiture pollue. »", "A plain statement."),
          ("c", "« Donc la voiture est pratique. »", "« Donc » concludes."), ("d", "« Par exemple, ma voiture. »", "An example, not a concession.")],
         "a", "D", "Concession structure.", hint="Look for « certes »."),
    item("aeo3-guide-2", "select", "EO", "EO-T3", "B1", ["eo.exemplifier", "eo.argumenter"], "Quel exemple soutient le mieux l'argument « Le télétravail fait gagner du temps » ?",
         [("a", "« Ma sœur gagnait deux heures de transport par jour quand elle travaillait chez elle. »", "Yes: concrete, related."),
          ("b", "« Le temps, c'est important. »", "Too general."), ("c", "« J'aime mon bureau. »", "Unrelated."), ("d", "« Beaucoup de gens travaillent. »", "Unrelated.")],
         "a", "D", "Choose a concrete example.", hint="The best example is specific and directly linked."),
    item("aeo3-auto-1", "select", "EO", "EO-T3", "B2", ["eo.reaction-relance", "eo.nuancer"], "L'examinateur relance : « Mais on dit que cela isole les gens. » Quelle réponse est la meilleure ?",
         [("a", "« C'est vrai pour certains, notamment les nouveaux employés. C'est pourquoi je défends un modèle hybride, avec deux jours au bureau. »", "Yes: acknowledges, nuances, keeps a position."),
          ("b", "« Non. »", "No development."), ("c", "« Vous avez raison, je change d'avis. »", "No need to abandon your view."), ("d", "« Je ne sais pas. »", "No answer.")],
         "a", "E", "Respond to a challenge."),
    item("aeo3-chrono", "select", "EO", "EO-T3", "B1", ["eo.argumenter", "eo.structure"], "Quelle première phrase est la meilleure ?",
         [("a", "« À mon avis, il faut limiter les voitures en centre-ville, pour deux raisons. »", "Yes: clear opinion + announces the plan."),
          ("b", "« Euh… c'est compliqué. »", "No position."), ("c", "« Les voitures existent depuis longtemps. »", "Off-topic start."), ("d", "« Je n'ai pas de voiture. »", "Personal, no opinion.")],
         "a", "F", "Timed: open with a clear opinion.", timed=30),
    card("aeo3-application", "EO", "EO-T3", "outro", "À vous : le point de vue réel", stage="H",
         body="Défendez votre opinion sur le télétravail pendant 4 min 30, avec les relances de l'examinatrice.",
         link={"label": "Faire la tâche 3", "to": "/oral/eo3-teletravail"}),
]))

# ---------- EE-T1/T2/T3 ----------
for task, title, comp, methode, exemple, g1, g2, a1, ch, link in [
    ("EE-T1", "Message (60–120 mots)", "ee.message-informer",
     ["Formule d'appel adaptée (tu/vous).", "Une phrase pour la raison du message.", "Traitez TOUS les points de la consigne, dans l'ordre.",
      "Une demande ou une proposition concrète.", "Formule de fin et signature. Comptez vos mots : 60 à 120."],
     "Consigne : invitez un collègue et donnez l'heure et le lieu. Un bon message cite l'heure, le lieu, demande une réponse, puis se termine par « À bientôt, Sara ».",
     ("Quelle formule convient pour écrire à votre propriétaire ?", [("a", "« Salut ! »", "Too familiar."), ("b", "« Madame, Monsieur, »", "Yes: formal."), ("c", "« Coucou ! »", "Too familiar."), ("d", "« Yo, »", "No.")], "b", "Formal recipient → formal greeting."),
     ("Il manque un point de la consigne (proposer une date). Quelle phrase l'ajoute ?", [("a", "« Je te propose samedi 14, vers 18 h. »", "Yes: a concrete date."), ("b", "« À bientôt. »", "Closing only."), ("c", "« Merci. »", "No date."), ("d", "« J'espère que ça va. »", "No date.")], "a", "Check every point."),
     ("Quelle fin de message formel est correcte ?", [("a", "« Je vous prie d'agréer, Madame, mes salutations distinguées. »", "Yes: formal closing."), ("b", "« Bisous ! »", "Familiar."), ("c", "« Bye. »", "No."), ("d", "« À plus. »", "Familiar.")], "a"),
     ("Votre message a 52 mots. Que faites-vous ?", [("a", "Ajouter un détail utile pour dépasser 60 mots.", "Yes: below 60 can make the paper « A1 non atteint »."), ("b", "Rien, c'est assez.", "Too short."), ("c", "Supprimer la signature.", "Shorter still."), ("d", "Écrire en majuscules.", "Irrelevant.")], "a"),
     "/ecrit/ee1-voisin-fete"),
    ("EE-T2", "Récit (120–150 mots)", "ee.recit-commentaire",
     ["Situez : quand, où, avec qui.", "Racontez dans l'ordre : passé composé pour les actions, imparfait pour le décor.",
      "Ajoutez vos commentaires : ce que vous avez ressenti, pensé.", "Terminez par le but demandé : conseiller, recommander, convaincre.", "120 à 150 mots."],
     "« Il faisait beau (décor, imparfait) quand nous sommes arrivés (action, passé composé). D'abord… ensuite… finalement… Je vous recommande… »",
     ("Quelle phrase utilise bien les temps du récit ?", [("a", "« Il pleuvait quand je suis sorti. »", "Yes: imparfait (décor) + passé composé (action)."), ("b", "« Il a plu quand je sortais toujours. »", "Tenses swapped."), ("c", "« Il pleut quand je suis sorti. »", "Present doesn't fit."), ("d", "« Il pleuvra quand je suis sorti. »", "Future doesn't fit.")], "a", "Imparfait for background, passé composé for actions."),
     ("Quel connecteur montre la chronologie ?", [("a", "« Ensuite »", "Yes."), ("b", "« Pourtant »", "Opposition."), ("c", "« Donc »", "Consequence."), ("d", "« Car »", "Cause.")], "a", "Sequence connectors."),
     ("La consigne demande de conseiller les lecteurs. Quelle phrase finale convient ?", [("a", "« Je vous conseille vivement de réserver à l'avance. »", "Yes: gives advice."), ("b", "« C'était hier. »", "No advice."), ("c", "« Il faisait chaud. »", "Description."), ("d", "« Fin. »", "No.")], "a"),
     ("Vous n'avez écrit que le récit, sans commentaire. Que manque-t-il ?", [("a", "Votre avis ou ce que vous avez ressenti.", "Yes: the task asks for comments."), ("b", "Un titre en anglais.", "No."), ("c", "Plus de dates.", "Not the issue."), ("d", "Rien.", "Comments are required.")], "a"),
     "/ecrit/ee2-premier-jour"),
    ("EE-T3", "Points de vue (120–180 mots)", "ee.comparer-points-de-vue",
     ["Une phrase d'introduction : le sujet.", "Reformulez le document 1 (sans copier).", "Reformulez le document 2 avec un connecteur d'opposition.",
      "Donnez votre opinion avec un argument et un exemple.", "Conclusion courte. 120 à 180 mots."],
     "« Le premier document affirme que le télétravail améliore la qualité de vie. En revanche, le second souligne qu'il isole les employés. Pour ma part, … »",
     ("Quelle phrase reformule au lieu de copier ?", [("a", "Document : « Le télétravail isole. » → « Selon le second auteur, travailler chez soi coupe des collègues. »", "Yes: same idea, new words."), ("b", "« Le télétravail isole. »", "Copied."), ("c", "« Le document dit : “Le télétravail isole.” »", "Copied in quotes."), ("d", "« Le télétravail, isole. »", "Copied.")], "a", "Rephrase the documents."),
     ("Quel connecteur oppose les deux documents ?", [("a", "« En revanche »", "Yes."), ("b", "« De plus »", "Addition."), ("c", "« Ainsi »", "Consequence."), ("d", "« D'abord »", "Sequence.")], "a", "Opposition connector."),
     ("Où placer votre opinion personnelle ?", [("a", "Après avoir présenté les deux points de vue.", "Yes: compare first, then give your view."), ("b", "Dans la première phrase uniquement.", "Comparison comes first."), ("c", "Nulle part.", "It's required."), ("d", "À la place du document 2.", "Both documents are needed.")], "a"),
     ("Vous avez écrit 195 mots. Que faites-vous ?", [("a", "Supprimer une phrase pour revenir sous 180 mots.", "Yes: above 180 is outside the range."), ("b", "Rien.", "Over the limit."), ("c", "Ajouter une conclusion.", "Longer still."), ("d", "Enlever l'opinion.", "It's required.")], "a"),
     "/ecrit/ee3-teletravail"),
]:
    n = task[-1]
    M.append(module(f"acad-ee{n}", f"Académie · Expression écrite, tâche {n}", "EE", task, "A2–B2", [
        card(f"aee{n}-methode", "EE", task, "method", f"{title} : la méthode", points=methode),
        card(f"aee{n}-exemple", "EE", task, "language", "Exemple", stage="C", body=exemple),
        item(f"aee{n}-guide-1", "select", "EE", task, "B1", [comp], g1[0], g1[1], g1[2], "D", "Guided practice.", hint=g1[3]),
        item(f"aee{n}-guide-2", "select", "EE", task, "B1", [comp], g2[0], g2[1], g2[2], "D", "Guided practice.", hint=g2[3]),
        item(f"aee{n}-auto-1", "select", "EE", task, "B1", [comp], a1[0], a1[1], a1[2], "E", "Independent practice."),
        item(f"aee{n}-chrono", "select", "EE", task, "B1", [comp, "ee.longueur"], ch[0], ch[1], ch[2], "F", "Timed: word-range decision.", timed=30),
        card(f"aee{n}-application", "EE", task, "outro", "À vous : la tâche réelle", stage="H",
             body="Écrivez la tâche complète dans le studio d'écriture, puis lisez le retour.", link={"label": f"Écrire la tâche {n}", "to": link}),
    ]))

for m in M:
    (OUT / f"{m['id']}.json").write_text(json.dumps(m, ensure_ascii=False, indent=2))
print(len(M), "modules,", sum(len(m["items"]) for m in M), "items")

"""Weekly trials 3 and 4 (reserved, original). Run: python3 scripts/content/bank_trials.py"""
import json
from pathlib import Path
from bank_lib import build

R, D, N = "Madame Roux", "M. Delaunay", None

T3 = [
 ("CO", ("A2", "co.annonce", "Où les clients doivent-ils aller ?", "Le rayon des fruits et légumes est temporairement déplacé au fond du magasin, près des caisses libre-service.", N,
   ("Au fond du magasin.", "« déplacé au fond du magasin »."), [("À l'entrée.", "Not said."), ("Au premier étage.", "Not said."), ("Dans un autre magasin.", "It's in the same shop.")])),
 ("CO", ("A2", "co.dialogue-quotidien", "Que prend la cliente ?", "— Vous désirez ? — Un thé vert, s'il vous plaît. Ah non, finalement, un chocolat chaud. — Très bien.", R,
   ("Un chocolat chaud.", "She changes her mind: « finalement, un chocolat chaud »."), [("Un thé vert.", "Her first choice, then changed."), ("Un café.", "Not mentioned."), ("Un thé et un chocolat.", "Only one drink.")])),
 ("CO", ("B1", "co.message-telephonique", "Que demande la secrétaire ?", "Bonjour monsieur Bouchard, ici le cabinet du docteur Martel. Pourriez-vous nous envoyer une copie de votre carte d'assurance avant votre rendez-vous de jeudi ? Merci.", R,
   ("D'envoyer un document avant jeudi.", "« nous envoyer une copie de votre carte d'assurance avant… jeudi »."), [("D'annuler le rendez-vous.", "The appointment stays."), ("De venir plus tôt.", "Not asked."), ("De payer par téléphone.", "Not asked.")])),
 ("CO", ("B1", "co.consequence", "Qu'est-ce qui change pour les usagers ?", "En raison de travaux, la station Berri sera fermée ce week-end. Des autobus de remplacement circuleront entre les stations voisines.", N,
   ("Ils prendront un autobus de remplacement.", "« Des autobus de remplacement circuleront »."), [("Le métro est gratuit.", "Not said."), ("Toutes les stations ferment.", "Only one station."), ("Les travaux sont terminés.", "They take place this weekend.")])),
 ("CO", ("B1", "co.intention", "Pourquoi Julie appelle-t-elle son collègue ?", "Salut Marc, c'est Julie. Je n'arrive pas à ouvrir le fichier de la présentation de demain. Tu pourrais me le renvoyer dans un autre format ?", R,
   ("Pour qu'il lui renvoie un fichier.", "« Tu pourrais me le renvoyer dans un autre format ? »."), [("Pour annuler la présentation.", "The presentation is still tomorrow."), ("Pour l'inviter à déjeuner.", "No."), ("Pour lui demander de présenter.", "Not asked.")])),
 ("CO", ("B2", "co.point-de-vue", "Quelle est l'opinion de l'invité sur les livres audio ?", "On oppose souvent livre audio et lecture. Pour moi, c'est un faux débat : écouter un roman pendant mon trajet, c'est toujours entrer dans une histoire. Simplement, je retiens mieux les textes difficiles sur papier.", D,
   ("Ils sont une vraie façon de lire, avec des limites pour les textes difficiles.", "Yes: « faux débat… je retiens mieux les textes difficiles sur papier »."), [("Ce n'est pas de la lecture.", "He calls that a false debate."), ("Ils remplacent totalement le papier.", "He still prefers paper for hard texts."), ("Il ne les écoute jamais.", "He listens during his commute.")])),
 ("CO", ("B2", "co.inference", "Que laisse entendre la responsable ?", "Le nouveau logiciel est arrivé lundi. Officiellement, tout le monde est formé. Dans les faits, la moitié de l'équipe continue d'utiliser l'ancien tableur, et je les comprends.", R,
   ("La formation n'a pas suffi.", "Officially trained, but half still use the old tool."), [("Le logiciel n'est pas encore arrivé.", "It arrived on Monday."), ("Toute l'équipe utilise le nouveau logiciel.", "Half don't."), ("Elle veut punir l'équipe.", "She understands them.")])),
 ("CO", ("C1", "co.nuance", "Quelle est la thèse du chercheur ?", "Ce n'est pas la technologie qui isole, mais l'usage qu'on en fait. Le même téléphone qui coupe un dîner de famille permet à une grand-mère de voir ses petits-enfants chaque semaine. Interdire serait plus simple que d'éduquer, mais moins efficace.", D,
   ("L'éducation aux usages vaut mieux que l'interdiction.", "Yes: « Interdire serait plus simple que d'éduquer, mais moins efficace »."), [("La technologie isole toujours.", "He says it depends on use."), ("Il faut interdire les téléphones.", "He finds banning less effective."), ("Les grands-mères utilisent trop le téléphone.", "An example, not the thesis.")])),
 ("CE", ("A2", "ce.document-pratique", "Quand peut-on déposer les vêtements ?", "Collecte de vêtements pour l'hiver : dépôt au sous-sol de la mairie, du lundi au mercredi, de 10 h à 16 h. Vêtements propres seulement.", N,
   ("Du lundi au mercredi, de 10 h à 16 h.", "Yes, as written."), [("Tous les jours.", "Only Monday to Wednesday."), ("Le week-end.", "Not mentioned."), ("Le soir après 16 h.", "It closes at 16 h.")])),
 ("CE", ("A2", "ce.message", "Que propose Nadia ?", "Coucou Emma ! Il fait beau dimanche, on pourrait faire un pique-nique au parc Lafontaine ? J'apporte les sandwichs, tu prends les boissons ? Bises, Nadia", N,
   ("Un pique-nique dimanche.", "Yes: « on pourrait faire un pique-nique »."), [("Un restaurant samedi.", "No."), ("Une visite de musée.", "No."), ("De rester à la maison.", "No.")])),
 ("CE", ("B1", "ce.information-cle", "Que doit faire un nouvel abonné ?", "Bienvenue à la médiathèque ! Pour activer votre carte, présentez-vous à l'accueil avec une preuve de résidence de moins de trois mois. Votre carte vous donne accès aux livres, aux films et aux ateliers.", N,
   ("Présenter une preuve de résidence récente.", "Yes: « preuve de résidence de moins de trois mois »."), [("Payer un abonnement mensuel.", "Not mentioned."), ("Suivre un atelier obligatoire.", "Workshops are optional."), ("Envoyer un courriel.", "Not asked.")])),
 ("CE", ("B1", "ce.idee-principale", "Quel est le sujet principal de l'article ?", "Dans plusieurs écoles du quartier, les élèves cultivent un potager sur le toit. Au-delà des légumes, les enseignants observent que les enfants goûtent plus volontiers des aliments qu'ils ont eux-mêmes fait pousser.", N,
   ("Les effets positifs d'un potager scolaire.", "Yes: children taste what they grow."), [("La vente de légumes par les écoles.", "Not mentioned."), ("Les toits dangereux des écoles.", "No."), ("Le manque d'enseignants.", "No.")])),
 ("CE", ("B1", "ce.inference", "Selon le règlement, que peut faire un locataire ?", "Règlement de l'immeuble : les vélos sont acceptés dans les appartements, mais interdits dans les couloirs et l'ascenseur. Un local à vélos fermé à clé est disponible au rez-de-chaussée.", N,
   ("Garder son vélo dans son appartement.", "Yes: « acceptés dans les appartements »."), [("Laisser son vélo dans le couloir.", "Forbidden."), ("Prendre l'ascenseur avec son vélo.", "Forbidden."), ("Garer son vélo dans le hall.", "Not allowed: use the locked room.")])),
 ("CE", ("B2", "ce.point-de-vue", "Quelle est la position de l'auteur ?", "On célèbre la gratuité des musées le premier dimanche du mois. Fort bien. Mais si les salles sont pleines ce jour-là et vides le reste du temps, c'est peut-être que le problème n'est pas seulement le prix : c'est aussi la façon dont on donne envie d'y entrer.", N,
   ("La gratuité ne suffit pas à attirer le public.", "Yes: « le problème n'est pas seulement le prix »."), [("Les musées devraient être plus chers.", "No."), ("La gratuité est une mauvaise idée.", "He accepts it (« Fort bien »)."), ("Les musées sont toujours vides.", "Full on free days.")])),
 ("CE", ("B2", "ce.intention", "Quel est l'objectif de ce courriel ?", "Madame, suite à notre entretien de mardi, je vous confirme mon vif intérêt pour le poste. Vous trouverez ci-joint les références demandées. Je reste disponible pour tout complément d'information.", N,
   ("Confirmer son intérêt et transmettre des documents.", "Yes: interest confirmed, references attached."), [("Refuser un poste.", "The opposite."), ("Demander un premier entretien.", "The interview already took place."), ("Se plaindre d'un retard.", "No complaint.")])),
 ("CE", ("C1", "ce.nuance", "Que reproche l'auteure aux classements des villes « où il fait bon vivre » ?", "Ces palmarès mesurent ce qui se compte : salaires, espaces verts, temps de trajet. Ce qui fait pourtant qu'on s'attache à un lieu, la qualité des liens de voisinage par exemple, échappe largement aux statistiques, et donc au classement.", N,
   ("Ils négligent ce qui ne se mesure pas facilement.", "Yes: what makes us attached to a place escapes statistics."), [("Ils exagèrent les salaires.", "Not said."), ("Ils ignorent les espaces verts.", "Green spaces are measured."), ("Ils sont faits par des voisins.", "No.")])),
]
T4 = [
 ("CO", ("A2", "co.information-cle", "À quelle heure part le bateau ?", "Le bateau pour l'île partira à 15 h 30. Les passagers doivent être à l'embarcadère quinze minutes avant le départ.", N,
   ("À 15 h 30.", "« partira à 15 h 30 »."), [("À 15 h 15.", "That's when to arrive."), ("À 16 h.", "Not said."), ("À 13 h 30.", "Not said.")])),
 ("CO", ("A2", "co.dialogue-quotidien", "Pourquoi l'homme ne peut-il pas venir ?", "— Tu viens au match ce soir ? — J'aimerais bien, mais je dois garder ma petite sœur. — Dommage !", D,
   ("Il garde sa sœur.", "« je dois garder ma petite sœur »."), [("Il travaille.", "Not said."), ("Il est malade.", "Not said."), ("Il n'aime pas le sport.", "He'd like to come.")])),
 ("CO", ("B1", "co.annonce", "Que se passe-t-il pour les visiteurs ?", "Mesdames et messieurs, en raison de l'orage, le festival en plein air est suspendu pendant une heure. Les spectateurs sont invités à se mettre à l'abri sous les tentes.", N,
   ("Ils doivent s'abriter sous les tentes.", "« invités à se mettre à l'abri sous les tentes »."), [("Le festival est annulé.", "Suspended for an hour."), ("Ils doivent rentrer chez eux.", "No."), ("Le concert continue.", "Suspended.")])),
 ("CO", ("B1", "co.message-telephonique", "Que propose le magasin ?", "Bonjour, ici le magasin Électro Plus. Le lave-vaisselle que vous avez commandé est en rupture de stock. Nous pouvons vous proposer un modèle équivalent au même prix, livrable dès jeudi.", D,
   ("Un autre modèle au même prix.", "« un modèle équivalent au même prix »."), [("Un remboursement immédiat.", "Not offered."), ("Une livraison aujourd'hui.", "From Thursday."), ("Une réduction de prix.", "Same price.")])),
 ("CO", ("B1", "co.point-de-vue", "Que pense Léa du covoiturage ?", "Au début, je trouvais ça compliqué de m'organiser avec d'autres. Maintenant, je fais du covoiturage tous les jours : j'économise de l'argent et les trajets passent plus vite en discutant.", R,
   ("Elle en est contente aujourd'hui.", "Saves money, journeys feel shorter."), [("Elle le trouve toujours compliqué.", "That was at the start."), ("Elle a arrêté.", "She does it every day."), ("Elle préfère conduire seule.", "No.")])),
 ("CO", ("B2", "co.idee-principale", "Quelle est l'idée principale de la chronique ?", "On imagine souvent que le multitâche fait gagner du temps. En réalité, passer sans cesse d'une tâche à l'autre a un coût : il faut chaque fois quelques minutes pour retrouver sa concentration. Faire une chose à la fois est souvent plus rapide.", D,
   ("Faire une chose à la fois est plus efficace.", "Yes: switching tasks has a cost."), [("Le multitâche fait gagner du temps.", "That's the belief it rejects."), ("Il faut travailler plus longtemps.", "Not said."), ("La concentration est inutile.", "No.")])),
 ("CO", ("B2", "co.inference", "Que comprend-on à propos du projet de piscine ?", "La piscine devait ouvrir cet été. Le chantier avance, nous dit-on. Mais à ce jour, aucune entreprise n'a encore été choisie pour la toiture.", N,
   ("L'ouverture cet été semble peu probable.", "No roofing company chosen yet."), [("La piscine est déjà ouverte.", "No."), ("Le chantier est abandonné.", "It's said to progress."), ("La toiture est terminée.", "Not even started.")])),
 ("CO", ("C1", "co.nuance", "Quelle est la position de l'économiste ?", "Augmenter le salaire minimum ne détruit pas automatiquement des emplois, contrairement à ce qu'on entend. Tout dépend du rythme : une hausse progressive et annoncée laisse aux petites entreprises le temps de s'adapter.", D,
   ("Une hausse progressive et prévisible est possible sans dégâts.", "Yes: « Tout dépend du rythme »."), [("Toute hausse détruit des emplois.", "He contests that."), ("Il faut supprimer le salaire minimum.", "No."), ("Les petites entreprises ne s'adaptent jamais.", "They can, with time.")])),
 ("CE", ("A2", "ce.document-pratique", "Combien coûte une place pour un enfant ?", "Cinéma du Parc — Tarifs : adulte 13 $, étudiant 10 $, enfant (moins de 12 ans) 8 $. Mardi : 7 $ pour tous.", N,
   ("8 $ (sauf le mardi).", "Yes: child price, 7 $ on Tuesdays."), [("13 $.", "Adult price."), ("10 $.", "Student price."), ("Gratuit.", "Not free.")])),
 ("CE", ("A2", "ce.message", "Pourquoi Omar écrit-il ?", "Bonjour Madame Lefebvre, mon fils Adam est malade et ne pourra pas venir à l'école aujourd'hui. Il reviendra probablement jeudi. Cordialement, Omar Haddad", N,
   ("Pour signaler l'absence de son fils.", "Yes."), [("Pour inscrire son fils.", "No."), ("Pour demander un rendez-vous.", "No."), ("Pour se plaindre de l'école.", "No.")])),
 ("CE", ("B1", "ce.information-cle", "Que doit faire le participant inscrit ?", "Merci pour votre inscription à la course du 12 mai. Votre dossard sera à retirer la veille, au gymnase municipal, entre 14 h et 19 h, sur présentation d'une pièce d'identité.", N,
   ("Retirer son dossard la veille avec une pièce d'identité.", "Yes."), [("Venir le jour même à 7 h.", "It's the day before."), ("Payer sur place.", "Not mentioned."), ("Envoyer une photo.", "Not asked.")])),
 ("CE", ("B1", "ce.inference", "Selon l'offre, qui peut obtenir la réduction ?", "Offre spéciale : 20 % de réduction sur l'abonnement annuel pour les étudiants et les plus de 65 ans, sur présentation d'un justificatif. Offre non cumulable.", N,
   ("Un étudiant avec sa carte.", "Yes: students with proof."), [("Toute personne qui le demande.", "Only students and over-65s."), ("Un enfant de 10 ans.", "Not in the categories."), ("Un étudiant qui a déjà une autre réduction.", "Not cumulative.")])),
 ("CE", ("B1", "ce.idee-principale", "Que montre l'article ?", "Depuis que la bibliothèque prête aussi des outils (perceuses, scies, échelles), le nombre d'emprunteurs a doublé. Beaucoup expliquent qu'ils n'utilisent ces objets que deux ou trois fois par an.", N,
   ("Le prêt d'outils répond à un besoin réel.", "Yes: borrowers doubled."), [("Les outils sont trop chers à la bibliothèque.", "They're lent."), ("Plus personne ne lit.", "Not said."), ("Les outils sont souvent volés.", "Not said.")])),
 ("CE", ("B2", "ce.point-de-vue", "Quelle est la position de l'auteure ?", "Interdire les devoirs à la maison ? L'idée séduit. Mais pour certains élèves, ces exercices sont le seul moment où ils révisent avec calme. Plutôt que de les supprimer, raccourcissons-les et veillons à ce qu'ils soient faisables sans aide.", N,
   ("Il faut réduire les devoirs plutôt que les supprimer.", "Yes: « raccourcissons-les »."), [("Il faut interdire les devoirs.", "She rejects a ban."), ("Les devoirs doivent être plus longs.", "The opposite."), ("Les parents doivent faire les devoirs.", "Should be doable without help.")])),
 ("CE", ("B2", "ce.intention", "Que fait la société dans cette lettre ?", "Madame, nous avons bien reçu votre réclamation. Après vérification, une erreur de facturation a effectivement eu lieu. Le montant de 42 $ vous sera remboursé sous dix jours. Nous vous prions d'accepter nos excuses.", N,
   ("Elle reconnaît une erreur et rembourse.", "Yes."), [("Elle refuse la réclamation.", "It accepts it."), ("Elle demande un paiement.", "No."), ("Elle annonce une hausse de prix.", "No.")])),
 ("CE", ("C1", "ce.nuance", "Quel est le ton du texte ?", "La municipalité a inauguré en grande pompe une piste cyclable de trois cents mètres qui ne relie rien à rien. Gageons qu'avec un tel réseau, la voiture tremble pour son avenir.", N,
   ("Ironique.", "Yes: « la voiture tremble pour son avenir » mocks a useless path."), [("Enthousiaste.", "The praise is mocking."), ("Neutre.", "Clearly critical."), ("Triste.", "Mocking, not sad.")])),
]
print(build("trial-3", "Épreuve hebdomadaire 3", "A2–C1", T3, "Weekly partial simulation 3."))
print(build("trial-4", "Épreuve hebdomadaire 4", "A2–C1", T4, "Weekly partial simulation 4."))

root = Path(__file__).resolve().parents[2] / "content"
w = json.loads((root / "writing/ee-tasks.json").read_text())
w["tasks"] += [
 {"id": "ee2-trial-3", "task": "EE-T2", "level": "B1", "pool": "assessment", "title": "Un atelier marquant",
  "prompt": "Le centre communautaire de votre quartier vous demande d'écrire un court article pour son bulletin : racontez un atelier ou un cours que vous avez suivi (cuisine, langue, sport…), dites ce qui vous a plu ou déplu, et encouragez (ou non) les lecteurs à s'inscrire.",
  "recipient": "les lecteurs du bulletin du quartier", "competencies": ["ee.recit-commentaire", "gram.temps-du-passe"]},
 {"id": "ee1-trial-4", "task": "EE-T1", "level": "B1", "pool": "assessment", "title": "Un objet oublié",
  "prompt": "Vous avez oublié un sac dans le train hier. Écrivez un message au service des objets trouvés : décrivez le sac et son contenu, précisez le trajet et l'heure, et demandez comment le récupérer.",
  "recipient": "le service des objets trouvés (vous)", "competencies": ["ee.message-decrire", "ee.registre"]},
]
(root / "writing/ee-tasks.json").write_text(json.dumps(w, ensure_ascii=False, indent=2))
s = json.loads((root / "speaking/eo-tasks.json").read_text())
s["tasks"] += [
 {"id": "eo1-trial-3", "task": "EO-T1", "level": "B1", "pool": "assessment", "title": "Parler de soi", "examiner": "Examinateur",
  "instructions": "L'examinateur vous pose des questions sur vous, vos habitudes et vos projets. Répondez avec des détails.",
  "opening": "Bonjour. Pour commencer, parlez-moi un peu de vous, s'il vous plaît.",
  "questions": ["Qu'est-ce que vous aimez faire pendant votre temps libre ?", "Décrivez-moi le quartier où vous habitez.", "Quel métier aimeriez-vous faire dans cinq ans ?", "Racontez-moi un bon souvenir d'enfance.", "Pourquoi avez-vous choisi le Canada ?"],
  "competencies": ["eo.parler-de-soi", "eo.developper-reponse"]},
 {"id": "eo3-trial-4", "task": "EO-T3", "level": "B2", "pool": "assessment", "title": "Apprendre en ligne", "examiner": "Examinatrice",
  "instructions": "Répondez à la question et défendez votre point de vue avec des arguments et des exemples. L'examinatrice peut vous demander de préciser ou de nuancer.",
  "opening": "Selon vous, peut-on apprendre aussi bien en ligne qu'en classe ?",
  "challenges": ["Et pour les enfants, votre réponse est-elle la même ?", "Ne manque-t-il pas le contact humain avec un professeur ?"],
  "competencies": ["eo.argumenter", "eo.nuancer"]},
]
(root / "speaking/eo-tasks.json").write_text(json.dumps(s, ensure_ascii=False, indent=2))
e = json.loads((root / "exams/exams.json").read_text())
label = "Partial simulation: shorter than the real TCF Canada, same rules (one listening, no help, strict timers)."
e["exams"] += [
 {"id": "weekly-3", "kind": "weekly", "title": "Épreuve hebdomadaire 3", "set": "trial-3", "label": label,
  "sections": [{"section": "CO", "minutes": 8}, {"section": "CE", "minutes": 12}, {"section": "EE", "writing_task": "ee2-trial-3", "minutes": 20}, {"section": "EO", "eo_task": "eo1-trial-3"}]},
 {"id": "weekly-4", "kind": "weekly", "title": "Épreuve hebdomadaire 4", "set": "trial-4", "label": label,
  "sections": [{"section": "CO", "minutes": 8}, {"section": "CE", "minutes": 12}, {"section": "EE", "writing_task": "ee1-trial-4", "minutes": 15}, {"section": "EO", "eo_task": "eo3-trial-4"}]},
]
(root / "exams/exams.json").write_text(json.dumps(e, ensure_ascii=False, indent=2))
print("tasks and exams added")

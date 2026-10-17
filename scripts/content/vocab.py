"""Generate content/vocab/vocab.json: original vocabulary cards grouped by communicative function,
each tied to the TCF task it serves. Run: python3 scripts/content/vocab.py"""
import json
from pathlib import Path

F = [
 ("demander", "Demander poliment", "EO", "EO-T2", "Polite requests and questions on the phone or in person.", [
  ("pourriez-vous", "could you (polite request)", "Pourriez-vous me dire à quelle heure vous ouvrez ?", "A2"),
  ("je voudrais savoir si", "I would like to know whether", "Je voudrais savoir si le cours est ouvert aux débutants.", "A2"),
  ("serait-il possible de", "would it be possible to", "Serait-il possible de visiter l'appartement jeudi ?", "B1"),
  ("auriez-vous", "would you have", "Auriez-vous une chambre libre pour ce week-end ?", "B1"),
  ("est-ce que ... est compris", "is ... included", "Est-ce que le petit-déjeuner est compris dans le prix ?", "A2"),
  ("un renseignement", "a piece of information", "Je vous appelle pour un renseignement.", "A2"),
  ("je me permets de", "I take the liberty of (formal)", "Je me permets de vous contacter au sujet de votre annonce.", "B1"),
  ("auriez-vous l'amabilité de", "would you be so kind as to", "Auriez-vous l'amabilité de me rappeler demain ?", "B2")]),
 ("opinion", "Donner son opinion", "EO", "EO-T3", "Stating and defending a point of view.", [
  ("à mon avis", "in my opinion", "À mon avis, le télétravail présente plus d'avantages que d'inconvénients.", "A2"),
  ("je pense que", "I think that", "Je pense que les transports publics devraient être gratuits.", "A2"),
  ("selon moi", "according to me", "Selon moi, il faut limiter le temps d'écran des enfants.", "B1"),
  ("pour ma part", "for my part", "Pour ma part, je préfère travailler au bureau.", "B1"),
  ("je suis convaincu(e) que", "I am convinced that", "Je suis convaincue que la formation continue est essentielle.", "B2"),
  ("il me semble que", "it seems to me that", "Il me semble que cette mesure est trop rapide.", "B1"),
  ("je suis tout à fait d'accord", "I completely agree", "Je suis tout à fait d'accord avec cette idée.", "A2"),
  ("je ne partage pas cet avis", "I don't share that view", "Je ne partage pas cet avis, car les coûts sont trop élevés.", "B2")]),
 ("nuancer", "Nuancer et opposer", "EE", "EE-T3", "Comparing two viewpoints and adding nuance.", [
  ("en revanche", "on the other hand", "Le premier texte est optimiste ; en revanche, le second est critique.", "B1"),
  ("cependant", "however", "Le projet est ambitieux ; cependant, son coût reste élevé.", "B1"),
  ("alors que", "whereas", "Certains aiment la ville alors que d'autres préfèrent la campagne.", "B1"),
  ("certes ... mais", "admittedly ... but", "Certes, la voiture est pratique, mais elle pollue.", "B1"),
  ("bien que (+ subjonctif)", "although", "Bien que ce soit cher, cela vaut la peine.", "B2"),
  ("malgré", "despite", "Malgré le froid, nous sommes sortis.", "B1"),
  ("pourtant", "yet / and yet", "Il a étudié ; pourtant, il a échoué.", "B1"),
  ("néanmoins", "nevertheless", "Le plan est simple ; néanmoins, il demande du temps.", "B2")]),
 ("raconter", "Raconter", "EE", "EE-T2", "Telling an experience in order, with time markers.", [
  ("d'abord", "first", "D'abord, je suis allé à la banque.", "A2"),
  ("ensuite", "then", "Ensuite, j'ai pris le métro.", "A2"),
  ("finalement", "finally", "Finalement, tout s'est bien passé.", "A2"),
  ("pendant que", "while", "Pendant que je cuisinais, mon ami est arrivé.", "B1"),
  ("à ce moment-là", "at that moment", "À ce moment-là, le téléphone a sonné.", "B1"),
  ("le lendemain", "the next day", "Le lendemain, nous sommes retournés au marché.", "A2"),
  ("soudain", "suddenly", "Soudain, il s'est mis à pleuvoir.", "B1"),
  ("au bout de", "after (a length of time)", "Au bout de deux heures, le bus est enfin arrivé.", "B1")]),
 ("cause", "Cause et conséquence", "EE", "EE-T3", "Explaining why something happens and what follows.", [
  ("parce que", "because", "Je suis en retard parce que le bus n'est pas passé.", "A2"),
  ("à cause de", "because of (negative)", "À cause de la neige, le train est annulé.", "B1"),
  ("grâce à", "thanks to", "Grâce à cette formation, j'ai trouvé un emploi.", "B1"),
  ("donc", "so / therefore", "Il pleut, donc nous restons à la maison.", "A2"),
  ("c'est pourquoi", "that is why", "Le loyer est élevé ; c'est pourquoi beaucoup partagent un appartement.", "B1"),
  ("puisque", "since (known reason)", "Puisque tu as le temps, aide-moi.", "B1"),
  ("par conséquent", "as a result", "Les ventes ont baissé ; par conséquent, l'entreprise recrute moins.", "B2"),
  ("en raison de", "due to (formal)", "En raison de travaux, la rue est fermée.", "B2")]),
 ("formel", "Écrire un message formel", "EE", "EE-T1", "Openings, closings and requests in formal messages.", [
  ("madame, monsieur,", "Dear Sir or Madam,", "Madame, Monsieur, je vous écris au sujet de ma réservation.", "A2"),
  ("je vous écris pour", "I am writing to you to", "Je vous écris pour signaler un problème.", "A2"),
  ("je vous prie de bien vouloir", "please kindly (formal)", "Je vous prie de bien vouloir me confirmer la date.", "B2"),
  ("dans l'attente de votre réponse", "awaiting your reply", "Dans l'attente de votre réponse, je vous remercie.", "B1"),
  ("cordialement", "kind regards", "Cordialement, Sara Martin", "A2"),
  ("veuillez agréer, madame, monsieur, mes salutations distinguées", "yours faithfully", "Veuillez agréer, Madame, Monsieur, mes salutations distinguées.", "B2"),
  ("ci-joint", "attached", "Vous trouverez ci-joint mon curriculum vitæ.", "B1"),
  ("suite à", "following (formal)", "Suite à notre conversation, je vous confirme mon intérêt.", "B1")]),
 ("telephone", "Au téléphone", "EO", "EO-T2", "Opening, handling and closing a phone call.", [
  ("allô, ici", "hello, this is", "Allô, ici Sara Martin, je vous appelle au sujet de l'annonce.", "A2"),
  ("je vous appelle au sujet de", "I'm calling about", "Je vous appelle au sujet de ma commande.", "A2"),
  ("pouvez-vous répéter", "can you repeat", "Pardon, pouvez-vous répéter, s'il vous plaît ?", "A2"),
  ("ne quittez pas", "please hold", "Ne quittez pas, je vous passe le service.", "B1"),
  ("laisser un message", "to leave a message", "Je voudrais laisser un message pour M. Roux.", "A2"),
  ("rappeler", "to call back", "Pouvez-vous me rappeler avant midi ?", "A2"),
  ("si je comprends bien", "if I understand correctly", "Si je comprends bien, la livraison arrive mardi.", "B1"),
  ("merci pour ces informations", "thank you for this information", "Merci pour ces informations, bonne journée !", "A2")]),
 ("echange", "Gérer l'échange", "EO", "EO-T1", "Rephrasing, buying time and clarifying in a conversation.", [
  ("autrement dit", "in other words", "Autrement dit, vous préférez rester en ville.", "B1"),
  ("c'est-à-dire", "that is to say", "Je travaille de nuit, c'est-à-dire de 22 h à 6 h.", "B1"),
  ("comment dire", "how shall I put it", "C'était, comment dire, très surprenant.", "B1"),
  ("par exemple", "for example", "J'aime le sport, par exemple le vélo.", "A2"),
  ("pouvez-vous reformuler", "can you rephrase", "Pardon, pouvez-vous reformuler la question ?", "B1"),
  ("je n'ai pas bien compris", "I didn't quite understand", "Je n'ai pas bien compris la dernière partie.", "A2"),
  ("ce que je veux dire, c'est que", "what I mean is that", "Ce que je veux dire, c'est que le prix compte moins.", "B2"),
  ("pour résumer", "to sum up", "Pour résumer, je suis favorable à ce projet.", "B1")]),
 ("quotidien", "La vie quotidienne", "CO", "CO", "Everyday words for housing, work and services, often heard in listening items.", [
  ("un loyer", "rent", "Le loyer est de 900 dollars par mois.", "A2"),
  ("les charges", "utilities / service charges", "Le chauffage est compris dans les charges.", "B1"),
  ("un préavis", "notice (period)", "Il faut donner un préavis de trois mois.", "B2"),
  ("un rendez-vous", "an appointment", "J'ai rendez-vous chez le médecin à dix heures.", "A2"),
  ("une réclamation", "a complaint", "Il a fait une réclamation auprès du magasin.", "B1"),
  ("un remboursement", "a refund", "Vous obtiendrez un remboursement sous dix jours.", "B1"),
  ("une facture", "an invoice / a bill", "Je n'ai pas reçu la facture du mois dernier.", "A2"),
  ("l'embauche", "hiring", "L'entreprise a gelé l'embauche cette année.", "B2")]),
]

cards = []
for fid, label, sec, task, blurb, items in F:
    for n, (fr, en, ex, lvl) in enumerate(items):
        cards.append({"id": f"{fid}-{n + 1:02d}", "function": fid, "fr": fr, "en": en, "example": ex, "level": lvl,
                      "tcf_target": {"section": sec, **({"task": task} if task != sec else {}),
                                     "purpose": f"{label}: vocabulary used in TCF {task}."}})
out = {"version": 1, "review_status": "reviewed",
       "functions": [{"id": f[0], "label": f[1], "task": f[3], "blurb": f[4]} for f in F], "cards": cards}
Path(__file__).resolve().parents[2].joinpath("content/vocab/vocab.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
print(len(cards), "cards,", len(F), "functions")

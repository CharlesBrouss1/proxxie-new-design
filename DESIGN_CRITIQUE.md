# Design critique · Proxxie

Revue autonome du 21 mai. Lentille : « le parcours doit etre le plus simple, fluide et indispensable pour un parent d'ado et son ado ». Objectif produit rappelé : le parent crée un compte, ajoute des documents, passe les tests à la place de son ado, invite l'ado (compte relié), puis prend des RDV d'accompagnement payant, et revient régulièrement.

Cette note classe ce qui marche, les frictions du tunnel, et une liste priorisée. Elle ne touche pas au code (sauf le fix mobile déjà livré en PR #45).

---

## 1. Ce qui marche déjà bien

- **Direction artistique forte et cohérente.** Fraunces + Inter, palette crème/encre/bleu/orange, cartes arrondies. L'identité tient sur toutes les pages. C'est rare et précieux à ce stade.
- **Le rapport est le bon centre de gravité.** « Le rapport Proxxie combine ces 12 tests » est la promesse claire. La page Rapport est dense mais lisible, avec sections, versions, plan d'action.
- **Le parcours en 5 étapes** (Proxxie Parcours.html) raconte une histoire : tests → activités → rapport → coach → suite. C'est le bon squelette narratif.
- **La dualité parent/ado** (tu/vous, données partagées, comparaison Big Five) est une vraie idée différenciante, pas un gadget.
- **Mobile** : plus aucun débordement horizontal (PR #45). Base saine pour le trafic téléphone, qui sera majoritaire chez les parents.

---

## 2. Frictions majeures du tunnel (par ordre d'impact)

### F1 · Le premier écran ne dit pas quoi faire MAINTENANT
Le Dashboard ouvre sur beaucoup de contenu (analyse, tests, activités, valeurs, conversion) mais l'œil ne sait pas où aller en premier. Pour un parent qui arrive, il faut **une seule action évidente** au-dessus de la ligne de flottaison : « Commencez par le test X » ou « Ajoutez le 1er bulletin ». Le checklist d'onboarding existe (« 4 actions pour bien démarrer ») mais il est noyé dans le flux. Il devrait être le héros tant qu'il n'est pas terminé, puis disparaître.

> Recommandation : un seul « next best action » dynamique, plein cadre, qui change selon l'état (0 test → lance un test ; tests faits → invite l'ado ; ado relié → prends RDV). Tout le reste passe sous le pli.

### F2 · La bascule « parent passe les tests POUR l'ado » n'est pas matérialisée
Le produit repose sur l'idée que le parent répond d'abord. Mais rien dans l'UI ne dit explicitement « vous répondez à la place d'Arthur » ni ne gère le moment du transfert (« maintenant, laissez Arthur refaire ce test de son point de vue »). C'est le cœur du modèle et c'est implicite.

> Recommandation : un bandeau de contexte persistant sur les tests (« Vous répondez pour Arthur · basculer en mode ado ») et un état visible « répondu par le parent / répondu par l'ado / les deux » qui alimente directement la page comparaison.

### F3 · L'invitation de l'ado est une étape clé sans moment fort
Le compte relié et le `linkCode` existent dans le localStorage, mais l'invitation n'a pas de écran dédié vendeur. C'est le pivot entre « outil du parent » et « outil de la famille ». Aujourd'hui c'est une ligne de checklist.

> Recommandation : un écran d'invitation avec aperçu de ce que l'ado va voir, le bénéfice (« compare ta vision à celle de tes parents »), et un code/lien à partager en un geste. Mesurer ce taux comme métrique nord.

### F4 · La conversion vers l'accompagnement payant arrive sans préparation émotionnelle
Le CTA payant s'adapte au rôle et au nombre de tests passés (bien). Mais le passage « gratuit → payant » a besoin d'une page de valeur : qui est le coach, à quoi ressemble une séance, témoignages, ce que le parent repart avec. Le hub Coach (Proxxie Coach.html) est bon mais c'est un hub de gestion, pas une page de vente.

> Recommandation : avant le premier RDV, intercaler une page « voici ce que l'accompagnement change » avec preuve sociale et garantie. Le RDV de cadrage gratuit comme produit d'appel.

### F5 · Aucune raison forte de REVENIR
La vision insiste : « ils doivent revenir régulièrement ». Or rien ne crée le rappel. Pas de « quoi de neuf depuis ta dernière visite », pas de notification de jalon Parcoursup, pas de relance « le bulletin du T3 est dispo ? ». Le XP existe mais ne tisse pas un fil temporel.

> Recommandation (chantier) : un fil « Depuis ta dernière visite » en haut du Dashboard + des déclencheurs calendaires (dates Parcoursup, échéances). C'est ce qui transforme l'outil de « consulté une fois » à « indispensable ».

---

## 3. Remarques design page par page

**Dashboard**
- Trop de sections de même poids visuel. Hiérarchiser : 1 action héros, puis progression, puis le reste en accordéons/replié.
- La carte d'analyse et la grille de valeurs se ressemblent ; risque de confusion. Différencier par la forme, pas seulement le contenu.

**Parcours**
- Excellente colonne vertébrale. Le hub coach (étape 04) est très riche · attention à ne pas en faire un deuxième dashboard. Le garder en « aperçu + lien vers Coach ».
- Les étapes verrouillées (opacity 0.55) sont bien, mais ajouter « ce qu'il faut faire pour débloquer » au survol/clic.

**Rapport**
- Page la plus aboutie. La timeline de versions est une super idée de réassurance (« ça vit, ça progresse »).
- Le mode démo (« Voici un exemple ») doit etre ultra clair pour ne pas faire croire que ce sont les vraies données de l'enfant.

**Tests / Test**
- La liste des 12 tests est longue. Regrouper visuellement (personnalité / neuro-atypies / valeurs) avec des sections repliables, et marquer nettement « fait par parent / par ado / à faire ».
- Un test = un engagement de temps : afficher la durée estimée et la progression globale (« 3/12, ~25 min restantes »).

**Comparaison (parent vs ado)**
- Idée forte. La rendre émotionnelle, pas seulement analytique : « là où vous vous rejoignez », « là où Arthur vous surprend ». C'est un moment de conversation familiale, pas un graphe.

**Compte**
- Page utilitaire correcte. Y rapatrier la gestion du lien ado, le mode démo/perso, et l'abonnement newsletter en un endroit clair.

**Ressources Hub**
- Joli, mais quel rôle dans le tunnel ? Si c'est de la rétention/SEO, lier chaque ressource à l'étape du parcours concernée (« à lire avant le RDV de cadrage »).

---

## 4. Détails de finition à corriger

- **Em-dashes dans les `<title>` des bundles** : « Tableau de bord — Proxxie ». Le tiret cadratin est partout dans les titres d'onglet. À remplacer par « · » pour respecter la règle de style. (Repérable : `grep -l "—" *.html`.)
- **Trois implémentations de navigation** (DashHeader, ShellHeader, topnav standalone) sur ~13 fichiers. Dette qui ralentit chaque changement. Chantier de refactor à planifier (header unique).
- **États vides** : que voit un tout nouveau compte (0 test, 0 doc) ? Vérifier que chaque page a un état vide qui guide au lieu d'afficher des cadres vides.
- **Upload de documents** : aujourd'hui surtout cosmétique. C'est pourtant une promesse centrale (« ajouter des bulletins »). Vraie UX d'upload + accusé de réception à prévoir.

---

## 5. Liste priorisée pour la suite

| Prio | Chantier | Pourquoi | Effort |
|------|----------|----------|--------|
| P0 | « Next best action » unique sur le Dashboard | Débloque l'activation, réduit la confusion d'entrée | M |
| P0 | Matérialiser « je réponds pour mon ado » + état par rôle sur les tests | Cœur du modèle, aujourd'hui implicite | M |
| P1 | Écran d'invitation ado vendeur | Pivot famille, métrique nord | M |
| P1 | Page de valeur avant le RDV payant | Convertit gratuit → payant | M |
| P1 | Fil « Depuis ta dernière visite » + déclencheurs calendaires | Crée le retour récurrent = indispensabilité | L |
| P2 | Regroupement + durée/progression sur la liste de tests | Réduit l'abandon en cours de parcours | S |
| P2 | Refactor header unique (3 → 1) | Dette qui freine tout le reste | M |
| P2 | Nettoyer les em-dashes des titres + états vides | Finition / cohérence | S |
| P3 | Vraie UX d'upload de documents | Tient une promesse centrale | L |

---

## 6. Livré cette session

- **PR #45 · fix mobile** : zéro débordement horizontal sur les 17 pages à 375px. Pages standalone corrigées par media queries (`minmax(0,1fr)` + `min-width:0` + topnav scrollable) ; pages bundle corrigées par `_patch_mobile_bundles.py` qui injecte un `<style>` mobile dans le `<head>` du template (idempotent).
- À merger dans l'ordre : **#43** (consolidation #35-42 → main), puis **#44** (fluidity wiring), puis **#45** (mobile, basé sur #44).

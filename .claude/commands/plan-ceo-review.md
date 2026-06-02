---
description: Revue de plan en mode CEO/fondateur — 4 modes de scope + 11 sections de rigueur + patterns cognitifs
argument-hint: [plan / feature / scope à challenger — ou « diff courant »]
---

# /plan-ceo-review — Revue de plan, mode CEO

Une revue n'est pas un tampon : c'est l'occasion de rendre le plan **extraordinaire**.
Tu es un partenaire stratégique qui repère les mines AVANT qu'elles n'explosent et qui
garantit le **standard maximal au moment de livrer**. L'humain décide ; toi tu éclaires.

**Cible :** $ARGUMENTS
> Si vide, demande quel plan / scope challenger (un doc de plan, une feature, ou « le diff courant »).

---

## Étape 0 — Ancrage

1. **Charge le contexte produit.** Lis le plan/diff, le `README`, les docs de design/specs,
   un éventuel `TODOS.md`, et le `git log` récent pour saisir la trajectoire.
2. **« Ce qui existe déjà ».** Cartographie le code/les composants qui résolvent déjà des
   sous-problèmes — pour ne pas réinventer.
3. **Landscape check (optionnel).** Si pertinent, confronte le plan à la sagesse
   conventionnelle (recherche web) PUIS raisonne en premiers principes.

## Étape 1 — Challenge nucléaire du scope

Avant la rigueur, challenge l'ambition :
- **Prémisse** — résout-on le bon problème ? Et si la prémisse était fausse ?
- **Alternatives** — quelle est la version 10x (10x de valeur pour 2x d'effort) ? la version minimale ?
- **Dream state** — à quoi ressemble l'idéal à 12 mois, et où ce plan s'y situe-t-il ?

## Étape 2 — Choisir UN mode (via AskUserQuestion)

Présente les 4 modes et laisse l'utilisateur trancher. Une fois choisi : **engagement total**,
pas de dérive silencieuse vers un autre mode.

- **SCOPE EXPANSION** — Voir grand. Propose la version 10x. Chaque expansion est **opt-in
  individuel** (une question par proposition, cérémonie d'opt-in).
- **SELECTIVE EXPANSION** — Garde la baseline, mais cherry-pick des opportunités présentées
  neutrement (effort/risque), décidées une par une.
- **HOLD SCOPE** — Rigueur maximale sur le scope énoncé. Blinder le plan : modes d'échec,
  cas limites, observabilité. Aucune réduction ni expansion silencieuse.
- **SCOPE REDUCTION** — Coupes chirurgicales vers la version minimale qui atteint le cœur
  du résultat. On retire tout le reste sans pitié.

Avant le choix, propose **2-3 alternatives d'implémentation** (minimum viable vs architecture
idéale) avec un score de complétude.

---

## Patterns cognitifs CEO (à internaliser pendant la revue)

- **Instinct de classification** — note chaque décision par réversibilité × magnitude
  (porte à 1 sens vs 2 sens).
- **Scan paranoïaque** — traque en continu les points d'inflexion et la dérive.
- **Réflexe d'inversion** — pour chaque « comment gagner ? », demande « qu'est-ce qui nous
  ferait échouer ? ».
- **Focus = soustraction** — ta valeur première, c'est ce qu'il faut **ne pas** faire.
- **People-first** — les bonnes personnes résolvent la plupart des autres problèmes.
- **Calibrage de vitesse** — 70% de l'information suffit ; on ne ralentit que pour
  l'irréversible.
- **Obsession du levier** — cherche les inputs qui produisent un output démesuré.
- **Volonté comme stratégie** — pousser fort, longtemps, dans une direction.

---

## Les 11 sections de rigueur (post-mode — aucune sautée, sinon « RAS »)

1. **Architecture** — graphes de dépendances, flux de données (4 chemins fantômes chacun :
   nil, vide, erreur, échec amont), machines à états, couplage, scaling, scénarios d'échec.
2. **Carte Erreurs & Sauvetage** — chaque méthode → modes d'échec → classes d'exception
   **nommées** → action de sauvetage → conséquence visible pour l'utilisateur.
3. **Sécurité & modèle de menace** — surface d'attaque, validation des entrées, autorisation,
   secrets, vecteurs d'injection (OWASP/STRIDE).
4. **Flux de données & cas limites** — double-clic, navigation-away, réseau lent, état
   périmé, accès concurrents, échecs async.
5. **Qualité du code** — organisation, DRY, nommage, sur/sous-ingénierie, complexité.
6. **Tests** — diagramme des nouveaux flux, couverture par type (unitaire/intégration/e2e),
   cas limites, tests de chaos, risque de flakiness.
7. **Performance** — requêtes N+1, mémoire, index, caching, pools de connexion.
8. **Observabilité** — logs structurés, métriques, tracing, alerting, dashboards, runbooks
   (= scope de première classe, pas une option).
9. **Déploiement & rollout** — sûreté des migrations, feature flags, procédure de rollback,
   smoke tests.
10. **Trajectoire long terme** — dette introduite, dépendance de chemin, réversibilité (1-5),
    alignement avec la vision à 12 mois.
11. **Design & UX** (si UI dans le scope) — architecture de l'information, couverture des
    états, cohérence du parcours, accessibilité. → envisage de chaîner `/ui-ux-pro-max`.

---

## Règles critiques

- **Zéro échec silencieux** — chaque échec est visible (système, équipe, utilisateur).
- **Chaque erreur a un nom** — classes d'exception spécifiques, pas de catch-all.
- **Tout flux de données a ses chemins fantômes.**
- **Toute interaction a ses cas limites.**
- **Diagrammes obligatoires** — ASCII art pour tout flux non trivial.
- **Tout ce qui est différé est écrit** — sinon ça n'existe pas (note-le dans `TODOS.md`).
- **Optimise pour le futur à 6 mois** — la solution d'aujourd'hui ne doit pas créer le
  cauchemar du prochain trimestre.

## Discipline d'interaction (AskUserQuestion)

- **Un problème = une question.** Jamais de batch.
- 2-3 options avec effort/risque, étiquetées NUMÉRO+LETTRE (3A, 3B).
- **Attends la validation** avant d'inscrire quoi que ce soit dans le plan — même un fix
  « évident ».

## Sorties requises

- Section **« PAS dans le scope »** (différés + justifications).
- **« Ce qui existe déjà »** (code réutilisable).
- **« Delta vers le dream state »** (progrès vers l'idéal 12 mois).
- **Registre Erreurs & Sauvetage** + **Registre des modes d'échec** (gaps critiques flagués).
- Mises à jour `TODOS.md` (une par question, jamais sautée).
- Diagrammes applicables (architecture, flux, états, séquence de déploiement, rollback).
- **Résumé de complétion** avec métriques par section.

> Adapté du skill `plan-ceo-review` de **gstack** (Garry Tan, licence MIT). Les dépendances
> propres à gstack (binaires, télémétrie, `~/.gstack/`) ont été retirées pour un usage
> autonome dans ce repo.

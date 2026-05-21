# Phase 3 · Page Parcours d'orientation

> Branch · `feat/phase-3-parcours-page`
> Depends on · Phase 2 (nav restructure) merged
> Source plan · [PARCOURS_ORIENTATION_PLAN.md](../PARCOURS_ORIENTATION_PLAN.md)

## Objectif

Créer la page `Proxxie Parcours.html` avec une timeline linéaire en 5 étapes, et y migrer le TestsPanel (déjà dans Dashboard) + le contenu Coach.

## Livrables

### A. Squelette Proxxie Parcours.html

Nouveau bundle Pretext (ou page standalone selon décision tech) avec·

```
DashHeader (4 onglets, Parcours actif)
Hero
  - Eyebrow "Mon parcours d'orientation"
  - Titre Fraunces "Là où tu en es, là où tu vas" (ado) / "Le parcours d'Arthur" (parent)
  - Jauge horizontale de progression globale
  - Sub-pitch "5 étapes · X% complet"

5 stages verticalement empilés (cartes rectangulaires)·
  01  Profil OCEAN-X (Big Five)
  02  Tests psychométriques (10 autres)
  03  Activités guidées (réflexions + quiz + découvertes)
  04  Séances avec ton coach (Charles)
  05  Bilan & vœux Parcoursup

Sidebar facultative droite (desktop) · "Activité récente"
Footer gamification · XP cumulé · niveau actuel · prochains badges
```

### B. Migration TestsPanel → Parcours stage 02

Le `TestsPanel` actuel sur le dashboard (composant ajouté par `_patch_tests_panel.py`) est déplacé vers le stage 02 de Parcours. Sur le dashboard, il devient un raccourci court · "Continuer mon parcours →".

### C. Migration contenu Coach → Parcours stage 04

L'onglet Coach n'existe plus (Phase 2). Le contenu (RDV à venir, séances passées, messagerie, replays, notes coach) migre vers le stage 04 de Parcours.

`Proxxie Coach.html` reste accessible mais redirige vers `Proxxie Parcours.html#stage-04`.

## Affordance parent vs ado

| Élément | Ado | Parent |
|---------|-----|--------|
| Stage 01 OCEAN-X · résultats | Visible + détaillé | **Visible + détaillé** (pour comparer) |
| Stage 02 Tests · statut | Visible + actionnable | Visible read-only |
| Stage 02 Tests · résultats | Visible + détaillé | **Visible + détaillé** |
| Stage 03 Activités · liste | Visible + actionnable | Visible read-only |
| Stage 03 Activités · contenu | Visible | **JAMAIS** (méta seulement) |
| Stage 04 Coaching | Visible + actionnable | Visible + actionnable |
| Stage 05 Bilan | Visible | Visible |

## Tests d'acceptation

- [ ] `Proxxie Parcours.html` charge, DashHeader visible, Parcours onglet actif
- [ ] Hero affiche jauge avec X% calculé (depuis localStorage `proxxie.tests.*` + `proxxie.docs.*`)
- [ ] 5 cartes étapes visibles, chacune avec numéro grand, titre, statut badge, description, CTA
- [ ] Stage 02 contient les 11 tests (migration TestsPanel)
- [ ] Stage 04 contient les RDV coach
- [ ] Dashboard a maintenant un raccourci compact vers Parcours au lieu du TestsPanel intégral
- [ ] Mode parent · activités stage 03 = meta only
- [ ] Tone tu/vous adapté
- [ ] Visite `Proxxie Coach.html` → redirect vers `Proxxie Parcours.html#stage-04`
- [ ] Responsive · timeline stack en mobile, sidebar masquée

## Out of scope (déféré à Phase 4-5)

- Implémentation détaillée des activités (modèle polymorphe, pages de réflexion/quiz/découverte)
- Page Bilan stage 05 (juste le placeholder)
- Bookmarks Parcoursup avancés
- Compare flow depuis Parcours

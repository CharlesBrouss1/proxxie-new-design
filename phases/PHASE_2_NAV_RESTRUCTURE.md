# Phase 2 · Nav restructure (4 onglets + fusion Rapport)

> Branch · `feat/phase-2-nav-restructure`
> Depends on · Phase 1 (feat/test-in-context-fix) merged
> Source plan · [PARCOURS_ORIENTATION_PLAN.md](../PARCOURS_ORIENTATION_PLAN.md)

## Objectif

Restructurer la navigation du dashboard connecté de 5 onglets à 4, en supprimant Rapport (fusionné dans Documents) et en absorbant Coach dans le futur onglet Parcours (créé en Phase 3).

## Livrables

### A. Modification du DashHeader

Le `DashHeader` (composant React inline dans l'asset `5a278f70` de Proxxie Dashboard.html) passe de·

```
Tableau de bord · Documents · Rapport · Coach · Ressources
```

à·

```
Tableau de bord · Parcours · Documents · Ressources
```

Notes·
- L'onglet Parcours pointe vers `Proxxie Parcours.html` qui n'existe pas encore (créé en Phase 3). Pour Phase 2 seul, le lien peut pointer vers un placeholder ou être désactivé.
- Coach est retiré du nav · pendant Phase 2, le lien `Proxxie Coach.html` reste accessible directement mais n'apparaît plus dans le header.
- Rapport est retiré du nav · voir section B.

Nouveau patch script · `_patch_dash_header_v2.py` (extends pattern existant).

### B. Fusion Rapport + Documents

`Proxxie Documents.html` gagne une section "Rapport" en haut, avant la liste des documents uploadés·

```
Hero
  - Eyebrow "Documents"
  - Titre "Tes documents et ton rapport" (ado) / "Les documents et le rapport de votre ado" (parent)

Section 1 · LE RAPPORT (intégré au top)
  - Card large : "Rapport en cours · v3 · mis à jour le 18 mai"
  - Tabs internes · "Vue d'ensemble · Profil · Métiers · Lycées · Vœux Parcoursup"
  - Contenu migré depuis Proxxie Rapport.html
  - CTA · "Exporter en PDF"

Section 2 · TES DOCUMENTS UPLOADÉS
  - DocsCompletenessPanel existant
  - Liste des documents uploadés
  - Zone de drop pour upload

Section 3 · PARTAGES & EXPORTS
  - Liens de partage générés (nominatifs, expirables)
  - Historique des exports PDF
```

Nouveau patch script · `_patch_documents_with_rapport.py`.

### C. Redirect bookmarks Rapport

`Proxxie Rapport.html` ne disparait pas (bookmarks externes), mais redirige vers `Proxxie Documents.html#rapport` au load via un `<meta http-equiv="refresh">` ou JS.

Nouveau patch script · `_patch_rapport_redirect.py` (ou édition directe du HTML).

## Tests d'acceptation

- [ ] Dashboard nav · seulement 4 onglets visibles, ordre · Tableau de bord, Parcours, Documents, Ressources
- [ ] Clic "Parcours" → page placeholder (ou désactivé proprement) en attendant Phase 3
- [ ] Clic "Documents" → page Documents avec section Rapport en haut
- [ ] Visite directe `Proxxie Rapport.html` → redirect vers `Proxxie Documents.html#rapport`
- [ ] Tone tu/vous adapté sur les nouvelles copies
- [ ] Le runtime tu/vous (`_patch_role_runtime.py`) couvre les nouvelles strings
- [ ] Pas de babel parse error

## Out of scope (déféré à Phase 3+)

- Création de `Proxxie Parcours.html`
- Migration du TestsPanel vers Parcours stage 02
- Migration du contenu Coach vers Parcours stage 04

# Phase 5 · Bilan final & vœux Parcoursup

> Branch · `feat/phase-5-bilan`
> Depends on · Phase 4 (activités) merged
> Source plan · [PARCOURS_ORIENTATION_PLAN.md](../PARCOURS_ORIENTATION_PLAN.md)

## Objectif

Implémenter le stage 05 du Parcours · le Bilan final qui consolide profil OCEAN-X + tests + activités + sessions coach + vœux Parcoursup, dans une page partageable + export PDF.

## Livrables

### A. Page Proxxie Bilan.html (ou stage 05 expansé inline dans Parcours)

```
DashHeader (Parcours actif, breadcrumb "Parcours > Bilan")
Hero
  - Eyebrow "Bilan final"
  - Titre Fraunces "Ton bilan d'orientation" (ado) / "Le bilan d'Arthur" (parent)
  - Date génération + version
  - CTA "Exporter en PDF" + "Partager (lien expirable)"

Section 1 · Profil consolidé
  - Big Five OCEAN-X radar
  - Tests psychométriques synthétisés (RIASEC, MBTI, etc.)
  - Forces · 3-5 traits dominants
  - Points d'attention · 1-2 zones à surveiller

Section 2 · Métiers compatibles
  - Top 5 métiers recommandés (croisement tests + activités + bulletins)
  - Pour chaque · description, secteurs porteurs, formations Parcoursup

Section 3 · Vœux Parcoursup recommandés
  - Liste 8-12 vœux par catégorie (sélectif / sécurisant / opportunistes)
  - Pour chaque · établissement, lien fiche, statut (à candidater / à étudier)

Section 4 · Lettres de motivation (templates)
  - Templates par filière, à personnaliser

Section 5 · Plan d'action
  - 5-7 actions concrètes ordonnées (JPO à visiter, devoirs à rendre, lettres à envoyer)
```

### B. Déverrouillage du Bilan

Le Bilan stage 05 est verrouillé tant que·
- Stage 01 (OCEAN-X) = done
- Stage 02 (tests psychométriques) ≥ 5 tests passés
- Stage 04 (séances coach) ≥ 1 séance faite

Affichage verrouillé · card grise avec progress bar "X / 7 conditions remplies" + liste des actions manquantes.

### C. Format livrable

Décision plan · page web nominale partageable (lien expirable 30 jours) + bouton "Exporter en PDF" comme secondaire.

#### Lien partageable
- Génération via `proxxie.bilan.shareLinks[]`
- Token JWT-like dans l'URL
- Expiration configurable (7 j / 30 j / 90 j)
- Révocation 1 clic depuis Documents (déjà existant pour rapport · réutiliser le pattern)

#### Export PDF
- Bouton qui lance impression navigateur avec stylesheet print optimisée
- OU génération côté serveur (out of scope pour mockup, mock seulement)

### D. Side effects sur la gamification

À la complétion du Bilan·
- Badge "Carte complète" 🌟 débloqué
- +200 XP gagnés (le plus gros gain du parcours)
- Animation de célébration sur le dashboard au retour

### E. Patch script

`_patch_bilan.py` qui·
- Crée `Proxxie Bilan.html` à partir du squelette dashboard
- Modifie le stage 05 du Parcours pour soit linker vers cette page, soit l'expand inline (à décider)
- Ajoute la logique de verrou/déverrouillage
- Ajoute le générateur de lien partageable

## Tests d'acceptation

- [ ] Stage 05 du Parcours verrouillé si conditions pas remplies, message explicite
- [ ] Stage 05 du Parcours accessible une fois les 3 conditions remplies
- [ ] Page Bilan affiche les 5 sections complètes
- [ ] Mode ado/parent · même contenu (tone tu/vous adapté)
- [ ] Bouton "Exporter en PDF" lance impression
- [ ] Bouton "Partager" génère un lien expirable, affiché dans une modal
- [ ] Liens partagés visibles dans Documents (réutilise pattern existant)
- [ ] Complétion du Bilan déverrouille badge "Carte complète"
- [ ] Pas de babel parse error

## Décisions ouvertes (à trancher pendant l'implem)

- Lien expirable · format token (UUID, JWT, hashids ?)
- Export PDF · client-side (CSS print) ou server-side (mockup) ?
- Page Bilan = page séparée ou stage 05 expand inline du Parcours ?
- Si une condition de verrou n'est pas remplie · placeholder ou rien ?

## Out of scope (déféré à V2)

- Mise à jour automatique du bilan quand l'ado ajoute des données
- Notification email / SMS au parent quand le bilan est généré
- Annotations parent sur le bilan
- Versioning du bilan (history des versions)
- Partage public (paramétrable, en plus de nominatif)

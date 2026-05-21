# Phase 4 · Activités guidées (modèle polymorphe + 3 prototypes)

> Branch · `feat/phase-4-activities`
> Depends on · Phase 3 (Parcours page) merged
> Source plan · [PARCOURS_ORIENTATION_PLAN.md](../PARCOURS_ORIENTATION_PLAN.md)

## Objectif

Implémenter le modèle de données activités polymorphes (mix réflexion écrite + mini-quiz + découverte) et 3 pages prototypes, puis remplir le stage 03 du Parcours avec une vraie liste d'activités actionables.

## Livrables

### A. Modèle data activité polymorphe

Schema localStorage·

```javascript
proxxie.activities = {
  "act-001": {
    id: "act-001",
    type: "reflection" | "quiz" | "discovery",
    title: "...",
    description: "...",
    durationMin: 10,
    category: "orientation" | "soft-skills" | "wellbeing",
    status: "todo" | "in_progress" | "done" | "validated_by_coach",
    completedAt: "ISO timestamp",
    // Type-specific fields·
    answers: {...},    // pour reflection
    score: 0-100,      // pour quiz
    progress: 0-100,   // pour discovery (% playback/scroll)
    coachNote: "..."   // optionnel
  },
  ...
}
```

### B. 3 pages prototypes (1 par type)

#### B1. Activity Reflection · `Proxxie Activite Reflexion.html`
- Page Pretext avec DashHeader (sticky, Parcours actif)
- Question ouverte + textarea (autosave dans `localStorage.proxxie.activities.{id}.answers`)
- Bouton "Soumettre"
- À la soumission · status → "done", redirect vers Parcours stage 03 avec toast

Exemples de prompts·
- "Tes 3 métiers d'envie et pourquoi"
- "Décris une journée idéale dans 10 ans"
- "Qu'est-ce qui te fait te lever le matin avec énergie ?"

#### B2. Activity Quiz · `Proxxie Activite Quiz.html`
- Page Pretext avec DashHeader
- Quiz interactif (drag/drop OU multi-step questions)
- Computation du score à la fin
- Status → "done" + score, redirect

Exemple · "Classe ces métiers par ordre d'intérêt"

#### B3. Activity Discovery · `Proxxie Activite Decouverte.html`
- Page Pretext avec DashHeader
- Vidéo embed OU article scrollable OU audio player
- Tracking progression (% playback ou % scroll)
- Status → "done" à 90% complétion, redirect

Exemple · "Vidéo · Devenir ingénieur en 2030 (8 min)"

### C. Migration stage 03 du Parcours

Le stage 03 "Activités guidées" liste les activités disponibles par catégorie·
- Orientation (4-6 activités)
- Soft skills (3-5 activités)
- Bien-être (2-3 activités)

Chaque activité = card avec·
- Icône type (📝 / 🎯 / 🎬)
- Titre
- Durée estimée
- Statut badge
- CTA (variable)

Côté parent · seulement méta visible (jamais le contenu des réponses).

### D. Patch script

`_patch_activities.py` qui·
- Crée 3 templates de pages Pretext (réflexion, quiz, découverte) en repartant du squelette tests existant
- Modifie le stage 03 de Parcours pour lister les activités depuis `proxxie.activities`
- Ajoute la logique de save mirror + redirect (similaire à phase 1 sur les tests)

## Tests d'acceptation

- [ ] 3 pages prototypes chargent avec DashHeader
- [ ] Activity Reflection · textarea sauvegardée toutes les X sec dans localStorage
- [ ] Activity Quiz · score calculé et stocké
- [ ] Activity Discovery · % de progression tracké
- [ ] Soumission redirect vers Parcours stage 03 avec toast (réutilise _patch_test_completed_toast pattern)
- [ ] Stage 03 du Parcours affiche les activités par catégorie
- [ ] Mode parent · cards activités affichent meta seulement, pas les réponses
- [ ] Tone tu/vous adapté
- [ ] Pas de babel parse error

## Décisions ouvertes (à trancher pendant l'implem)

- Activity timing · timer visible ou non ?
- Quiz scoring · binaire (juste/faux) ou pondéré ?
- Discovery type d'embed · YouTube/Vimeo ? Lecteur custom ?
- Mode parent · "Encourager" button qui envoie un nudge à l'ado ?

## Out of scope (déféré à Phase 5)

- Validation coach des activités (status `validated_by_coach`)
- Système de recommandation IA (quelle activité proposer ensuite)
- Achievements / badges spécifiques aux activités

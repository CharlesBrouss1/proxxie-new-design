# Plan d'harmonisation Dashboard v2 ↔ Homepage Proxxie

Référence vivante : https://charlesbrouss1.github.io/proxxie-new-design/Proxxie%20Home.html
Cible : `Proxxie-Dashboard-v2.html` (+ `Proxxie-Parcours-v3.html` qui hérite du même header)

Objectif : continuité visuelle totale. Le parent qui passe de la Homepage au Dashboard ne doit voir aucun saut visuel : même logo, même rail de container, même grammaire d'icônes, même hiérarchie de boutons.

---

## 1. Tokens CSS à aligner dans `:root`

### Ajouts
```css
--r-2xl: 44px;
```

### Modifications (fallbacks de la charte Proxxie)
```css
--font-display: "Mulish", "Goldplay", system-ui, sans-serif;
--font-body:    "Montserrat", system-ui, sans-serif;
--font-num:     "Fraunces", "Museo", Georgia, serif;
```

### Container
```css
.shell { max-width: 1240px; }  /* était 1180px */
```

### Conservés (additions légitimes de l'app, à remonter dans la Homepage à terme)
```css
--c-green:      #22A06B;
--c-green-tint: rgba(34,160,107,.12);
```

---

## 2. Header : remplacement complet

### 2.1 Logo SVG inline (réutilise le path du favicon Homepage)

```html
<a class="logo" href="/" aria-label="Proxxie · Accueil">
  <svg class="logo__mark" viewBox="0 0 32 32" width="28" height="28" aria-hidden="true">
    <rect width="32" height="32" rx="7" fill="#1320CE"/>
    <path d="M8 11 L16 21 L24 11" stroke="#FFFFFF" stroke-width="4.5"
          stroke-linecap="round" stroke-linejoin="round" fill="none"/>
    <path d="M12 13 L16 18 L20 13" stroke="#B0D0F7" stroke-width="3.2"
          stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  </svg>
  <span class="logo__wordmark">Proxxie</span>
</a>
```

```css
.logo {
  display: inline-flex; align-items: center; gap: 10px;
  font-family: var(--font-display); font-weight: 800;
  font-size: 18px; letter-spacing: -0.015em; color: var(--c-ink);
}
.logo__mark { display: block; flex-shrink: 0; }
.logo__wordmark { line-height: 1; }
```

Identique au favicon de la Homepage, juste agrandi avec wordmark Mulish 800.

### 2.2 Sticky top (mode prototype vs prod)

```css
.app-header { position: sticky; top: 0; z-index: 50; /* … */ }
body.is-prototype .app-header { top: 42px; }
```

Activer `<body class="is-prototype">` pour la maquette uniquement.

### 2.3 Icônes header en SVG inline (suppression des emojis)

Set d'icônes outline 1.5px, 18×18, color = `currentColor`.

```html
<button class="icon-btn" aria-label="Notifications">
  <svg viewBox="0 0 24 24" width="18" height="18" fill="none"
       stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
    <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/>
    <path d="M10 21a2 2 0 0 0 4 0"/>
  </svg>
</button>

<button class="icon-btn" aria-label="Aide">
  <svg viewBox="0 0 24 24" width="18" height="18" fill="none"
       stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="12" cy="12" r="9"/>
    <path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.7.4-1 .9-1 1.7v.5"/>
    <circle cx="12" cy="17.5" r=".5" fill="currentColor"/>
  </svg>
</button>
```

À étendre pour les ~20 emojis du contenu (📅 → calendar, 🧩 → puzzle, 🔓 → lock-open, etc.).
Livrable : un commentaire `<!-- ICON LIBRARY -->` en haut du fichier listant les 20 paths SVG.

### 2.4 Sélecteur d'enfant : état "non synchronisé"

```html
<button class="child-switch__btn">
  <span class="child-switch__avatar">L</span>
  <span class="child-switch__name">Louise</span>
  <span class="child-switch__sync-warn" title="compte non lié" aria-label="compte non lié"></span>
  <span class="child-switch__chev">▾</span>
</button>
```

```css
.child-switch__sync-warn {
  width: 8px; height: 8px; border-radius: 99px;
  background: var(--c-orange);
  margin-left: 4px;
}
```

### 2.5 Tap targets et a11y

```css
@media (max-width: 860px) {
  .app-header__inner { min-height: 56px; }
  .nav a, .icon-btn, .avatar { min-height: 44px; }
}
nav.nav { } /* + aria-label="Navigation principale" sur le HTML */
.nav a.is-active { /* + aria-current="page" sur le HTML */ }
.icon-btn[aria-label] { /* remplacer tous les title= par aria-label= */ }
```

### 2.6 Responsive (calé sur la Homepage)

| Viewport | Comportement |
|---|---|
| ≥1025px | Logo · sélecteur · nav 4-liens · 2 icon-btn · avatar |
| 860–1024px | Idem, `padding: 0 24px` sur `.shell` |
| 520–860px | Nav 4-liens cachée dans le header, **bottom-nav apparaît** |
| <520px | Icon-btn "Aide" caché, gap réduit, bottom-nav sticky |

```css
@media (max-width: 860px) {
  .app-header .nav { display: none; }
  .bottom-nav { display: flex; }
}
```

### 2.7 Bottom-nav mobile

```html
<nav class="bottom-nav" aria-label="Navigation mobile">
  <a href="#" aria-current="page"><svg>…</svg> Tableau</a>
  <a href="#"><svg>…</svg> Parcours</a>
  <a href="#"><svg>…</svg> Documents</a>
  <a href="#"><svg>…</svg> Ressources</a>
</nav>
```

```css
.bottom-nav {
  display: none;
  position: fixed; bottom: 0; left: 0; right: 0; z-index: 60;
  background: rgba(255,255,255,.96); backdrop-filter: blur(12px);
  border-top: 1px solid var(--c-line);
  padding: 6px 0 max(6px, env(safe-area-inset-bottom));
  justify-content: space-around;
}
.bottom-nav a {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  font-size: 11px; font-weight: 600; color: var(--c-muted);
  padding: 8px 12px; min-height: 44px;
}
.bottom-nav a[aria-current="page"] { color: var(--c-blue-deep); }
```

---

## 3. Slop à éliminer dans le contenu

### 3.1 Border-left coloré sur card
```css
/* SUPPRIMER */
.card--featured { border-left: 3px solid var(--c-blue); }
/* À LA PLACE : accent par chip ou eyebrow */
.card--featured .eyebrow { color: var(--c-orange); }
```

### 3.2 27 emojis à remplacer par SVG

Mapping suggéré :
| Emoji | Icône SVG |
|---|---|
| 📅 | calendar |
| 🧩 | puzzle-piece |
| 🔓 | lock-open |
| 📬 | inbox |
| 💡 | lightbulb |
| 📕 📚 | book |
| 🔔 | bell |
| 📄 📝 📑 | file-text |
| 🧪 | flask |
| 👤 | user |
| 🎯 | target |
| 🔒 | lock |
| 💬 | message-circle |
| 🌟 | star |
| 🤝 | handshake |
| 🔢 | hash |
| 🖼 | image |
| 📊 | bar-chart |
| 📰 | newspaper |
| 🎓 | graduation-cap |
| 🌱 | sprout |
| 🎙 | mic |
| 📎 | paperclip |
| 🪞 | mirror (custom — square + reflexion line) |
| 🏗 | construction (custom — crane silhouette) |

Livrable séparé recommandé : `proxxie-icons.html` ou bloc `<defs>` en haut du fichier avec tous les `<symbol>`, référencés par `<use href="#icon-calendar">`.

---

## 4. Application en miroir sur `Proxxie-Parcours-v3.html`

Le fichier Parcours v3 partage le même `:root`, même `.app-header`, même `.nav`. Toutes les modifs ci-dessus s'appliquent à l'identique. Liste de checkpoints :

- [ ] Mêmes tokens `:root`
- [ ] Logo SVG inline identique
- [ ] Icônes SVG identiques (cloche, aide, avatar, chevron)
- [ ] Mêmes media queries 860 / 520
- [ ] Bottom-nav inclus (avec `is-active` sur "Parcours")
- [ ] Tap targets 44px
- [ ] `aria-label` au lieu de `title`
- [ ] Suppression des emojis (le fichier en contient probablement aussi, à audit)

---

## 5. NOT in scope (différé)

- **Remonter `--c-green` dans la Homepage live** : nécessite déploiement GitHub Pages, à faire à la prochaine release Homepage.
- **Pages Documents et Ressources** : seuls Dashboard v2 (parent + enfant) et Parcours v3 sont audités ici.
- **DESIGN.md formel** : recommandé de créer un fichier source-of-truth dans une étape ultérieure (`/design-consultation`).
- **Refonte des `.dropdown` du sélecteur d'enfant** : on garde le style actuel, alignement charte non-bloquant.
- **Hover/focus animations détaillées** : 12ms ease in/out par défaut, ajustements au polish.

---

## 6. What already exists

- **Stack typographique** : Mulish 400-800 + Montserrat 400-600 + Fraunces 400-600 (opsz 9..144). Déjà chargée correctement via `fonts.googleapis.com/css2`.
- **Palette** : 12 variables couleur, identiques côté Homepage et Dashboard à 13 variables près (+green).
- **Échelle border-radius** : sm/md/lg/xl déjà cohérents. Seul `--r-2xl: 44px` manque dans Dashboard.
- **Shadows** : sm/md/lg identiques entre les deux.
- **Pattern `.shell`** : convention déjà partagée, seul le `max-width` diffère.
- **`.chip`, `.eyebrow`, `.btn`** : nomenclature alignée, prête à harmoniser sans rename.
- **Sticky `app-header` avec backdrop-blur** : pattern de la Homepage déjà repris dans le Dashboard.

---

## 7. TODOS.md (à reporter ailleurs)

| What | Why | Pros | Cons | Depends on |
|---|---|---|---|---|
| Créer un set d'icônes SVG Proxxie partagé | Évite la dérive emoji et garantit un langage visuel unique pour Home + app | Cohérence visuelle, +scan rapide, livrable réutilisable | ~4h de tracing, doit être maintenu | Validation des 20 icônes |
| Ajouter `--c-green` à la Homepage | Clôt le diff de tokens entre les deux applis | Aucun token "exclusif Dashboard" | Demande un déploiement Pages | Aucune |
| Créer un `DESIGN.md` formel | Source de vérité unique pour la charte (couleurs, typo, spacing, motion) | Évite la dérive, on calibre sur le doc plutôt que sur un HTML | ~2h à rédiger | Aucune |
| Onboarding inscription Home → Dashboard | La 1ère vue après inscription doit être ciblée (Pas "Bonjour Julie" sec) | Premier instant clé de la rétention | Demande arbitrage produit | Backend signup flow |
| Skeleton loaders sur Dashboard | Évite le flash blanc en arrivant de la Homepage | Transition perçue plus fluide | ~1h à specifier | Aucune |

---

## 8. GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 0 | — | non lancé (scope produit clair) |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 0 | — | non applicable (pas de back-end) |
| Design Review | `/plan-design-review` | UI/UX gaps | 1 | CLEAR (FULL) | score 5/10 → 9/10, 27 emojis identifiés, 4 décisions ancrées |
| DX Review | `/plan-devex-review` | DX gaps | 0 | — | non applicable |
| Codex Review | `/codex review` | 2nd opinion | 0 | — | non lancé (skill flag opt-in) |

**UNRESOLVED** : 0 décision bloquante.
**VERDICT** : DESIGN PLAN CLEARED — prêt pour implémentation côté HTML.

---

## Completion Summary

```
+====================================================================+
|         DESIGN PLAN REVIEW — COMPLETION SUMMARY                    |
+====================================================================+
| System Audit         | Pas de DESIGN.md · 2 fichiers HTML scope    |
| Step 0               | 5/10 initial · focus continuité totale      |
| Pass 1  (Info Arch)  | 7/10 → 9/10                                 |
| Pass 2  (States)     | 4/10 → 8/10                                 |
| Pass 3  (Journey)    | 5/10 → 8/10                                 |
| Pass 4  (AI Slop)    | 7/10 → 9/10                                 |
| Pass 5  (Design Sys) | 6/10 → 9/10                                 |
| Pass 6  (Responsive) | 5/10 → 8/10                                 |
| Pass 7  (Decisions)  | 5 résolus, 0 différé                        |
+--------------------------------------------------------------------+
| NOT in scope         | écrit (5 items)                             |
| What already exists  | écrit                                       |
| TODOS.md updates     | 5 items proposés                            |
| Approved Mockups     | 0 (alignement sur référence vivante)        |
| Decisions made       | 9 décisions ancrées dans le plan            |
| Decisions deferred   | 0                                           |
| Overall design score | 5/10 → 8.5/10                               |
+====================================================================+
```

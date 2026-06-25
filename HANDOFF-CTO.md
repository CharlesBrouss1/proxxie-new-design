# Passation CTO · Proxxie (prototype → prod)

> But de ce document · donner à un CTO/dev tout ce qu'il faut pour reprendre le
> travail et l'amener en production. Lis la section 2 en premier · elle évite la
> plus grosse erreur possible.

---

## 1. Accès

| Quoi | Où |
|---|---|
| Repo | https://github.com/CharlesBrouss1/proxxie-new-design (PUBLIC, branche `main`) |
| Site live (prototype) | https://charlesbrouss1.github.io/proxxie-new-design/Proxxie%20Home.html |
| Page « tous les tests » | https://charlesbrouss1.github.io/proxxie-new-design/Proxxie%20Tests.html |
| Déploiement | GitHub Pages, auto sur push `main` via `.github/workflows/pages-deploy.yml` |

Note · le repo est **public**. Rien de confidentiel n'y est stocké (pas de
données utilisateur, pas de clé), mais à vérifier avant d'ouvrir le développement.

---

## 2. À LIRE EN PREMIER · ce que ce repo est, et n'est PAS

**C'est un prototype cliquable haute fidélité, pas une base de code de production.**

- ~70 pages HTML autonomes. Chaque page (ex · `Proxxie Tests.html`, 1,8 Mo) est
  un **bundle** · du React compilé en un seul fichier HTML avec CSS/JS/SVG/données
  inline. Ce ne sont pas des sources éditables à la main.
- L'état vit en `localStorage` (clés `proxxie.*`). **Aucun backend, aucune auth,
  aucune base de données.**
- Les bundles sont ensuite mutés par **81 scripts Python de patch** (`_*.py`) qui
  font de l'injection de chaînes sur le HTML. Une CI (`patches.yml` + `tests/test_patcher.py`
  + `_design_fixes.py --strict`) garde ces patchs contre la dérive.
- Le multi-enfant se fait en **dupliquant un dossier entier** (`louise/`) par enfant.

**Conséquence pour le CTO · ne pas productionniser les fichiers HTML bundlés.**
Ce sont des artefacts jetables. Le prototype EST la spec produit · il sert de
référence visuelle et fonctionnelle. La prod se **reconstruit** selon
`BACKEND_SPEC.md` (voir section 4).

Pourquoi le proto ne peut pas accueillir un vrai parent (résumé de `BACKEND_SPEC.md`) ·
1. Données en `localStorage` · inacceptable pour bulletins scolaires + marqueurs
   sensibles (TDAH, Autisme, Anxiété, DYS, HPI) = blocage RGPD immédiat.
2. Pas de compte, pas d'auth, pas d'isolement parent A / parent B.
3. Pages = bundles statiques mutés par 81 scripts · non maintenable à l'échelle.
4. Multi-enfant par duplication de dossier · ne scale pas, fuite par URL devinable.

---

## 3. Les specs prod sont déjà écrites (le vrai livrable)

Tout le travail de cadrage produit/archi est dans ces 5 docs à la racine ·

| Doc | Contenu |
|---|---|
| **`BACKEND_SPEC.md`** | Le plan de passage en prod · stack, modèle de données, auth, RGPD, estimation. **Le document central.** |
| **`COMPARAISON_SPEC.md`** | Feature parent↔ado · le parent répond « à la place de », l'ado passe les vrais tests, comparaison + capture de lead. Besoin d'un KV cross-device (codes `PXC-XXXX`). |
| **`PARCOURS_ORIENTATION_PLAN.md`** | Refonte de la nav du dashboard connecté · 4 onglets, page Parcours (timeline 5 étapes), fusion Rapport+Documents. |
| **`HARMONISATION-PLAN.md`** | Continuité visuelle dashboard ↔ homepage · tokens CSS, header, charte. |
| **`DESIGN_CRITIQUE.md`** | Revue design. |

---

## 4. Stack cible recommandée (extrait de `BACKEND_SPEC.md`)

| Couche | Choix | Pourquoi |
|---|---|---|
| Frontend | Next.js 14 (App Router) | Migration douce depuis le proto React, SSR |
| Backend | Routes API Next.js | Suffisant pour MVP ; sortir vers Fastify/NestJS en V2 si volume |
| DB | PostgreSQL · Supabase EU ou Neon EU | RGPD, RLS pour scoping par parent, JSONB pour answers/scores |
| Fichiers | Scaleway Object Storage ou Cloudflare R2 (EU) | S3-compatible, chiffrement au repos, URLs signées |
| Auth | Magic link (NextAuth ou Lucia) | Pas de mot de passe parent, OTP email |
| Hébergement | Vercel (région EU) ou Cloudflare Pages | Latence FR OK |
| Email | Postmark ou Resend (EU) | Magic links, exports rapport |
| Monitoring | Sentry + logs structurés (pino) | Erreurs + audit |

**Estimation `BACKEND_SPEC.md`** · 11 à 14 semaines (1 dev full-time) ou
6 à 9 semaines (2 devs).

---

## 5. Couche LLM (comparaison)

- Lecture des écarts profil parent/ado générée par **Claude (modèle `claude-opus-4-8`)**.
- Pattern · **generate-once + cache + fallback** (pas d'appel LLM à chaque vue).
- **Clé API côté serveur uniquement.** En prod, l'appel passe par une route API,
  jamais depuis le client. Le proto ne contient qu'un seul `fetch(` ; tout le
  reste est statique.

---

## 6. Charte / design system

Palette OFFICIELLE (charte PDF) · **bleue**
- Bleu primaire `#1320CE`, bleu clair `#487AFF`
- Orange `#FD6936`, jaune `#F5EB3F`, crème `#EEE6D9`
- Fond proto · `#F7F2E9`

Typo (fallbacks charte, cf. `HARMONISATION-PLAN.md`) ·
- Display · Mulish / Goldplay
- Body · Montserrat
- Numérique · Fraunces / Museo

---

## 7. Modèle de données du proto (clés `localStorage` à porter en DB)

- `proxxie.role` · parent / ado (role-scoped, `?role=`)
- `proxxie.tests.{id}.{role}` · statut d'un test (`done`, FROID/TIÈDE/CHAUD)
- `proxxie.tests.{id}.{role}.results` · objet de scores propre au barème du test

Important (`COMPARAISON_SPEC.md` §2.1) · aujourd'hui seul Big Five écrit des
`results` structurés, les autres tests n'écrivent que `"done"`. La fondation de
la comparaison = faire écrire des `results` structurés à **chaque** test. À porter
tel quel dans le schéma Postgres (JSONB).

---

## 8. Hygiène repo à traiter avant reprise

- Fichiers non suivis présents dans le working tree · backups `*.bak-*` et scripts
  loose (`_extract_panel.py`, `_survey_compare.py`, `_survey_strings.py`).
  À committer ou supprimer pour partir propre.
- 81 scripts `_*.py` · ils ne servent QU'AU prototype (patch des bundles). Ils ne
  sont **pas** à porter en prod. Ils documentent par contre les correctifs
  appliqués (utile comme historique de décisions).

---

## 9. Ordre de reprise suggéré

1. Lire `BACKEND_SPEC.md` en entier.
2. Cloner le proto live comme référence d'UX (ne pas réutiliser le code bundlé).
3. Scaffold Next.js 14 + Postgres EU + magic link.
4. Porter le modèle de données (section 7), avec `results` structurés pour tous les tests.
5. Implémenter la comparaison parent↔ado (`COMPARAISON_SPEC.md`) + couche LLM serveur (section 5).
6. Reconstruire le dashboard connecté selon `PARCOURS_ORIENTATION_PLAN.md`.
7. RGPD · chiffrement, consentement, rétention, hébergement EU dès le départ (données sensibles).

# Backend spec · le vrai produit Proxxie

> Document de spec pour passer du prototype HTML+Pretext+patches à un vrai produit
> qui peut faire travailler de vraies familles. Suite logique du Pont validé dans
> la PR #87 (cartes/modales/rapport pilotés par un objet `child`).
>
> Source · /plan-ceo-review et /plan-eng-review · 2026-05.

## 1. Pourquoi ce doc

Le Pont a validé l'UX du gating Hybride (FROID/TIÈDE/CHAUD, rapport verrouillé +
sample, garde anti-mensonge sur les %) sur **des données mockées**. Le contrat
`child` est figé. Mais le prototype actuel ne peut pas accueillir un vrai parent
parce que :

1. Les données vivent en `localStorage` · inacceptable pour des bulletins
   d'élève + des marqueurs sensibles (TDAH, Autisme, Anxiété, DYS, HPI) =
   blocage RGPD immédiat.
2. Il n'y a pas de compte, pas d'auth, pas d'isolement parent A vs parent B.
3. Les pages sont des bundles HTML statiques mutés par 40 scripts Python
   d'injection de chaînes · impossible à maintenir à l'échelle d'un produit.
4. Le multi-enfant se fait en **dupliquant un dossier entier** (`louise/`)
   par enfant. Ne scale pas, et c'est une fuite par URL devinable.

Ce doc dit comment combler le fossé. Estimation totale · **11 à 14 semaines
avec 1 dev full-time**, ou **6 à 9 semaines avec 2 devs**.

## 2. Stack recommandée

| Couche | Choix | Pourquoi |
|---|---|---|
| Frontend | **Next.js 14** (App Router) | Écosystème mainstream FR, SSR, écosystème Vercel/Cloudflare, migration douce depuis le proto React |
| Backend | Routes API Next.js (co-localisées) | Suffisant pour MVP. Si volume, sortir vers Fastify/NestJS en V2 |
| DB | **PostgreSQL** sur Supabase EU ou Neon EU | RGPD friendly, RLS pour scoping par parent, JSONB pour les blobs (answers, scores) |
| Stockage fichiers | **Scaleway Object Storage** ou Cloudflare R2 (EU) | S3-compatible, chiffrement au repos, URLs signées courte durée |
| Auth | **Magic link** (NextAuth ou Lucia) | Pas de mot de passe pour les parents (UX + sécurité). OTP email |
| Hébergement app | Vercel (EU region) ou Cloudflare Pages | Le bundle Next sort en edge, latence FR ok |
| Email transactionnel | Postmark ou Resend (EU) | Magic links, notifications, exports rapport |
| Monitoring | Sentry + logs structurés (pino → Logtail/Axiom EU) | Erreurs + audit |

**Règle non négociable · tout le stack hébergé en UE.** RGPD + transferts hors-UE
= cadre Schrems II, complications légales. Évite US-only (Vercel a des régions EU,
Supabase Frankfurt, Cloudflare a EU edges).

## 3. Modèle de données (PostgreSQL)

```sql
-- comptes
users (
  id UUID PK,
  email CITEXT UNIQUE NOT NULL,
  role ENUM('parent','enfant','coach','admin') NOT NULL,
  created_at, last_login_at
)

families (
  id UUID PK,
  parent_user_id UUID FK users,
  created_at
)

children (
  id UUID PK,
  family_id UUID FK families,
  user_id UUID FK users NULL,        -- si l'ado a son compte
  prenom TEXT NOT NULL,
  classe TEXT,                       -- '3eme','2nde','1ere','terminale','postbac'
  created_at,
  UNIQUE (family_id, prenom)
)

-- profil progression
profiles (
  child_id UUID PK FK children,
  etapes JSONB NOT NULL DEFAULT '{}'::jsonb,  -- {prenom:true, classe:true, ...}
  complet INT GENERATED ALWAYS AS (jsonb_array_length(...)) STORED,
  updated_at
)

-- tests psychométriques
tests (
  id UUID PK,
  child_id UUID FK children,
  kind TEXT NOT NULL,                -- 'ocean','riasec','mbti',...
  statut ENUM('todo','wip','done'),
  answers JSONB,                     -- {q1:'a',q2:'b',...}
  scores JSONB,                      -- {O:72,C:60,...} pour OCEAN
  started_at, completed_at,
  UNIQUE (child_id, kind)            -- 1 entry par (enfant, test)
)

-- documents (bulletins + autres)
documents (
  id UUID PK,
  child_id UUID FK children,
  kind ENUM('bulletin','devoir','lettre_motiv','cv','autre'),
  trimestre TEXT NULL,               -- T1/T2/T3 si kind=bulletin
  annee TEXT NULL,                   -- 2024-25
  filename TEXT,
  storage_key TEXT NOT NULL,         -- chemin S3
  size_bytes INT,
  mime TEXT,
  uploaded_at,
  virus_scanned_at NULL,
  virus_status ENUM('pending','clean','infected')
)

-- recommandations métiers/parcours (cache des calculs du moteur)
metiers_recos (
  child_id UUID PK FK children,
  items JSONB NOT NULL,              -- [{nom,score?,source,sec,growth}, ...]
  source ENUM('estime','confirme'),
  generated_at,
  version INT                        -- bump quand le moteur change
)

parcours_recos (
  child_id UUID PK FK children,
  items JSONB NOT NULL,
  source ENUM('estime','confirme'),
  generated_at, version
)

-- rapports
rapports (
  id UUID PK,
  child_id UUID FK children,
  etat ENUM('verrouille','apercu','complet'),
  version INT,
  generated_at,
  pdf_storage_key TEXT NULL,         -- export PDF cacheable
  shareable_token TEXT NULL          -- lien partage expirable (nominatif)
)

-- consentements parentaux RGPD
consents (
  id UUID PK,
  parent_user_id UUID FK users,
  child_id UUID FK children,
  type ENUM('data_processing','sensitive_tests','document_upload','sharing'),
  granted_at,
  revoked_at NULL,
  evidence JSONB                     -- ip, ua, version CGU acceptée
)

-- coaching
coach_sessions (
  id UUID PK,
  child_id UUID FK children,
  coach_user_id UUID FK users,
  scheduled_at, completed_at NULL, duration_min,
  notes TEXT,                        -- visible parent
  recording_url TEXT NULL
)

-- audit trail (lecture/écriture donnée mineur)
audit_logs (
  id UUID PK,
  actor_user_id UUID FK users,
  action TEXT,                       -- 'read.child','update.profile','download.bulletin',...
  target_type TEXT,                  -- 'child','document','rapport'
  target_id UUID,
  ip INET, user_agent TEXT,
  ts TIMESTAMPTZ DEFAULT now()
)
```

**Indexation** · `children(family_id)`, `documents(child_id, kind)`,
`tests(child_id, kind)`, `audit_logs(actor_user_id, ts DESC)`.

**RLS (Row Level Security) PostgreSQL** · activer sur toutes les tables.
Politique par défaut · un user lit/écrit uniquement les rows liés à sa
`family_id` (ou son `user_id` pour `users`). Coach lit les rows des
familles auxquelles il est assigné. Admin a tout.

## 4. Contrat API (mappe sur `child` du Pont)

Le shape JSON renvoyé par l'API est **exactement le shape `child`** que le
prototype lit déjà. Comme ça la migration front est mécanique.

```
GET  /api/children/:id
  → {
      id, prenom, classe,
      profil: { complet: 0..6 },
      ocean:  { statut: 'todo|wip|done', scores: {O,C,E,A,N} | null },
      documents: { bulletins: N, autres: N },
      metiers:   [{ nom, score?, source: 'estime|confirme' }],
      parcours:  [{ nom }],
      rapport:   { etat: 'verrouille|apercu|complet', version }
    }

GET  /api/children          → liste enfants de la famille
POST /api/children          → crée un enfant (prenom, classe)
PATCH /api/children/:id/profile  → updates etapes (déclenche recalc stage)

POST /api/children/:id/tests/ocean  → body: {answers}
  → calcul scores, persist, mise à jour ocean.statut='done', recalc metiers

POST /api/children/:id/documents    → multipart upload
  → store S3, queue virus scan, recalc rapport.etat si bulletins>=2

GET  /api/children/:id/rapport
  → si etat='complet': { sections, pdf_url }
    sinon: { etat, raison, sample_url (pointe sur le sample Léa) }

POST /api/auth/magic-link  { email }
GET  /api/auth/callback?token=...
```

**Dérivation du stage** · côté serveur uniquement (single source of truth).
Même logique que `_pxStage` du Pont :

```ts
function deriveStage(child) {
  if (child.ocean.statut !== 'done') return 'FROID';
  if (child.documents.bulletins < 2 || child.profil.complet < 6) return 'TIEDE';
  return 'CHAUD';
}
```

Calculé à la volée à chaque GET. Pas de cache · ça change rarement, et le
cache invalidation cause plus de bugs que la perf ne sauve.

## 5. Moteur de compatibilité métiers/parcours

**MVP · rule-based, pas de ML.**

Inputs · OCEAN scores (5 dims), optionnel RIASEC (6 dims), bulletins
(moyennes extraites par matière).

Matrice éditoriale en YAML (versionné dans le repo, relu par
psychométriciens) :

```yaml
metiers:
  architecte_ux:
    nom: "Architecte UX"
    secteur: "Design & Tech"
    growth: "+18%"
    weights_ocean: { O: 0.30, C: 0.20, E: 0.15, A: 0.20, N: -0.10 }
    weights_riasec: { A: 0.40, I: 0.25, S: 0.20 }
    bulletins_required:
      maths: 12      # moyenne min
      info: 13
    confidence_threshold: 0.65
  # ... ~80-120 métiers
```

Le moteur :
1. Calcule un score brut [0..1] = sum(weights * scaled_scores).
2. Si `source='estime'` (TIÈDE) · renvoie nom + secteur, **pas de %**.
3. Si `source='confirme'` (CHAUD) · multiplie par un coef d'ajustement
   bulletins (bonus si moyennes au-dessus du seuil), renvoie nom + score
   en %, secteur, growth.

Documenter la matrice publiquement (transparence vs "boîte noire").

**V2** · entraîner sur les vrais résultats Parcoursup des familles passées.
Pas pour le MVP.

## 6. RGPD · ce qui est non-négociable

1. **Hébergement EU bout en bout.** DB, storage, app, logs, email. Audit
   trail de tous les sous-traitants.
2. **Consentement parental explicite et tracé** avant tout traitement,
   surtout les tests sensibles (TDAH/Autisme/Anxiété). Stocké dans
   `consents` avec preuve (ip, ua, version CGU).
3. **Wording médical clair** · ces tests sont **indicatifs, pas un
   diagnostic**. À afficher AVANT le test, à ré-afficher dans les
   résultats. Faire valider par un juriste santé.
4. **Minimisation** · ne stocker que ce qui sert au produit. Pas d'IP
   permanente, pas de tracking publicitaire.
5. **Conservation** · 3 ans après dernier login, puis suppression
   effective (pas soft-delete). Bulletin = 1 an après réception (utile
   pour le rapport, pas au-delà).
6. **Droit d'accès, rectification, oubli, portabilité** · endpoints
   dédiés, ticket SLA 30 jours max.
7. **Chiffrement au repos** · DB (Supabase par défaut), storage (AES-256
   server-side). Chiffrement en transit (TLS).
8. **Accès scopé** · RLS PostgreSQL + signed URLs courte durée (15 min)
   pour les bulletins. Aucun fichier servi en public.
9. **Audit log** · toute lecture/modification donnée mineur écrite dans
   `audit_logs`. Conservé 1 an.
10. **DPO** · désigné (interne ou externe). DPIA (analyse d'impact) faite
    avant le lancement.
11. **DPA** signé avec chaque sous-traitant (Supabase, Scaleway, Vercel,
    Resend, etc.).

**Faire valider par un avocat RGPD AVANT le premier upload réel.** Une
amende CNIL sur données de mineurs coûte plus que le développement.

## 7. Plan de migration (5 phases)

### Phase 1 · Foundation (2-3 semaines)
- Next.js 14 app skeleton + routing
- Supabase EU instance, schema initial (Prisma ou Drizzle)
- Auth magic link (NextAuth + Resend)
- Politique RLS de base
- CI/CD (Vercel preview deploys par PR)
- **Livrable** · un user peut se créer un compte et créer un enfant. Rien
  d'autre. Vérifié end-to-end.

### Phase 2 · Parcours parent (2-3 semaines)
- Page profil édit (6 étapes formulaire)
- Page test OCEAN-X (porter le contenu UI existant, persist côté API)
- Page upload bulletins (drag-drop, scan virus async)
- Dashboard branche sur `GET /api/children/:id` (le shape `child` du Pont)
- **Livrable** · un parent peut compléter profil + test + upload bulletins.
  Le dashboard reflète l'état réel. Aucune donnée mockée.

### Phase 3 · Gating + rapport (2-3 semaines)
- `deriveStage` côté serveur
- `GET /api/children/:id/rapport` · CHAUD génère le rapport (template
  React → HTML → PDF via Playwright), apercu/verrouillé renvoient juste
  l'état + le lien sample Léa
- Sample report Léa stocké comme fixture publique (asset statique)
- Moteur de compatibilité v1 (rule-based, matrice YAML)
- **Livrable** · le rapport CHAUD est réel et téléchargeable PDF. Les
  états FROID/TIÈDE matchent exactement le Pont.

### Phase 4 · Ops & coaching (2 semaines)
- Page coach (planifier, voir notes, rejoindre visio)
- Intégration calendrier (Cal.com self-hosted ou Google Calendar API)
- Monitoring Sentry, logs structurés Logtail/Axiom EU
- Backup DB quotidien Supabase + restore drill testé
- Page admin minimale (support · consulter un dossier enfant en lecture)
- **Livrable** · ops production-ready. Un incident est détectable et
  réparable.

### Phase 5 · Sécurité + audit légal (2-3 semaines)
- Pen-test léger (Yes We Hack ou agence FR)
- Cabinet d'avocat RGPD valide CGU, politique confidentialité, DPA
- DPO setup (interne ou externe)
- DPIA finalisée
- Page transparence (politique cookies, données traitées, sous-traitants)
- **Livrable** · feu vert légal pour accueillir des familles réelles.

**Total** · 11-14 semaines · 1 dev full-time. **6-9 semaines · 2 devs.**

## 8. Ce qui devient obsolète

Quand le vrai produit tourne, ces éléments du proto sont retirés :

- Les ~40 scripts `_patch_*.py` (le proto reste comme **maquette de
  référence** versionnée, jamais déployée).
- L'état `localStorage` (remplacé par sessions + DB).
- Le dossier `louise/` dupliqué (remplacé par rows `children`).
- Le bundler Pretext et les patches d'injection de chaînes.

Le proto garde une valeur · c'est la **source de vérité du design** que le
vrai produit doit reproduire. Tant que l'équipe design itère sur le proto,
les devs ont une cible visuelle stable.

## 9. Risques majeurs et mitigations

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| RGPD mal cadré, amende CNIL | M | TRÈS HAUT | Avocat valide AVANT premier upload réel. Phase 5 bloquante. |
| Choix de stack trop figé | M | MOYEN | Garder des couches modulaires (API/UI séparées). Pas de lock-in vendor. |
| Scoring matrix biaisé | H | MOYEN | Matrice publique, relue par psychométriciens, A/B testée. |
| Photo de bulletin illisible | H | FAIBLE | OCR best-effort + saisie manuelle de la moyenne en fallback. |
| Mineur uploade sans consentement parent | M | HAUT | Compte ado lié à family\_id, upload bloqué si consents manquant. |
| Sous-traitant ferme (Supabase) | F | HAUT | Schema DB portable (Postgres standard). Backups DB exports nightly hors plateforme. |

## 10. Décisions ouvertes (pour Charles)

1. **Staffing** · build solo, recrutement 1 dev fullstack, ou agence FR ?
   - Solo · 11-14 semaines · risque burnout, pas de bus factor.
   - 1 hire · 6-9 semaines · coût ~25-35k€ sur la période + onboarding.
   - Agence · 8-10 semaines · 60-90k€, mais livre.

2. **Date butoir** · première vraie famille en bêta privée à quelle date ?
   Conditionne phase 5 (légal). Recommandation · pas avant 3 mois.

3. **Sample report** · un seul exemple (Léa) ou rotation de 3-4 profils
   différents (Léa Terminale L, Hugo 2nde STI2D, Sofia post-bac
   réorientation) ? Plus d'exemples = meilleure conversion mais plus
   d'éditorial à produire.

4. **Coach side** · ouvre-t-on l'app aux coachs externes dès le MVP, ou
   Charles est coach unique en phase 1 ? Plus simple si solo coach
   d'abord, multi-coach en V2.

5. **Tests psychométriques en V1** · OCEAN-X + RIASEC suffisent, ou il
   faut tous les 11-12 dès le départ ? Recommandation MVP · OCEAN-X seul
   (le test fondateur), RIASEC en option, les sensibles (TDAH/Autisme)
   seulement en V2 avec encadrement médical clair.

6. **Migration des familles existantes du proto** · personne n'a de
   compte réel sur le proto (mode démo), donc pas de migration de
   données. Si Charles a fait passer des tests OCEAN-X "à la main" à des
   familles, prévoir un import CSV.

## Annexe · Mapping Pont → Backend

Le Pont a déjà figé le contrat. Le backend doit servir exactement ce qui suit :

| Composant Pont (localStorage) | Endpoint backend |
|---|---|
| `_pxGetChild()` lit `localStorage.proxxie.child` | `GET /api/children/:id` |
| `_pxSyncToLegacy(child)` mirror sur `proxxie.docs.*`, `proxxie.tests.big5.*`, etc. | Disparait · les helpers (`_proxxieGetOnboardingState`, `_proxxieGetDocs`) sont remplacés par des hooks `useChild(id)` qui lisent l'API |
| `?etat=froid\|tiede\|chaud` (démo) | `?demo=froid\|tiede\|chaud` admin-only en non-prod, pour QA |
| Rapport sample Léa (PR #87) | Fixture statique servie en `verrouille`/`apercu` |
| Garde · `%` seulement si `source='confirme'` | Garde côté serveur dans le moteur de compatibilité (jamais renvoyer un % avec `source!='confirme'`) |

Le code front migre par composant, en remplaçant les helpers localStorage
par des hooks `useChild()` / `useTests()` / `useDocuments()`. Le shape ne
change pas, donc les JSX existants continuent de marcher.

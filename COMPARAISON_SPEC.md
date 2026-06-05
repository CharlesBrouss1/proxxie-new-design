# Comparaison parent ↔ ado · spec design

> Catégorie « Comparaison » : un parent répond aux tests à la place de son ado,
> envoie un code à l'ado, l'ado passe les vrais tests, et la comparaison s'affiche.
> Proxxie capte le lead parent pour le recontacter.

Décisions cadrées (2026-06-05) :
- Mécanique « répondre à la place de l'enfant » : **existe déjà**, role-scoped, pour tous les tests.
- Transport des données entre appareils : **mini-backend KV (Supabase EU)**, cf. BACKEND_SPEC.md.
- Capture du lead parent : **soft, après le résultat** (pas de gate).

---

## 1. Ce qui existe déjà (à réutiliser, pas à reconstruire)

| Brique | Fichier / clé | État |
|---|---|---|
| Rôle parent/ado | `proxxie.role`, `useProxxieRole`, `?role=` | OK |
| Réponse « à la place de » | run de n'importe quel test sous `role=parent` | OK, role-scoped |
| Statut double sur les cartes | `proxxie.tests.{id}.{role}`, `_patch_tests_dual_status.py` | OK |
| Surface de comparaison | `comparaison.html` (radar OCEAN-X, deltas, prompts) | OK mais Big Five only |
| Mint + partage de code | `_proxxieGetLinkCode`, `_patch_invite_screen.py` | OK mais cosmétique |

## 2. Les 3 manques à combler

### 2.1 Résultats structurés pour tous les tests
Aujourd'hui seul Big Five écrit des scores (`proxxie.tests.big5.{role}.results`).
Les autres tests écrivent seulement `"done"`.

**À faire :** chaque test écrit `proxxie.tests.{id}.{role}.results` (objet de scores
propre à son barème) en plus du flag `"done"`. Sans ça, la comparaison ne peut
jamais dépasser OCEAN-X. C'est la fondation de la feature.

### 2.2 Transport cross-device : enregistrement « paire » en KV
Le code `PXC-XXXX` devient une vraie ligne serveur (Supabase EU).

```
pair {
  code           : "PXC-4K7Q"        // charset sans ambiguïté, pas de O/0/I/1
  parent_results : { big5: {...}, riasec: {...}, ... }
  parent_email   : null              // rempli plus tard, soft opt-in
  parent_consent : null              // booléen + timestamp
  tests          : ["big5","riasec"] // tests comparables choisis
  child_results  : null              // rempli quand l'ado finit
  child_consent  : null              // l'ado accepte de partager ses vrais scores
  created_at     : ts
  child_done_at  : null
}
```

- Lien envoyé à l'ado : `proxxie.co/comparaison?code=PXC-4K7Q&role=enfant`
- Le proto statique peut continuer à fonctionner en démo via localStorage ;
  le code bascule vers le KV sans changer l'UX.

### 2.3 Lead tracking (soft, après résultat)
- Le parent voit la comparaison **gratuitement**.
- Puis CTA doux : « Recevez un email quand {prénom} a répondu, plus un récap
  pour en discuter ensemble. » → email + consentement explicite, optionnels.
- Quand l'ado finit (`child_done_at` set) **et** consentement parent donné :
  email auto au parent + CTA coach soft.
- Signal lead interne = ampleur de l'écart devine/réel (cf. §4), stocké
  côté serveur, **jamais montré comme une note**.

## 3. Parcours

```
PARENT                                    ADO
  │ passe des tests sous role=parent
  │ (= ses réponses « à la place de »)
  │ choisit « Comparer avec mon ado »
  │ → mint PXC-4K7Q, crée la paire KV
  │ partage le code/lien ───────────────▶ ouvre le lien (role=enfant)
                                          │ passe les VRAIS tests
                                          │ écran consentement :
                                          │ « Partager mes vrais résultats
                                          │   avec mon parent ? » (off par défaut)
                                          │ POST child_results → KV
  ◀───────────────────────────────────── child_done_at set
  │ ouvre Comparaison (code ou auto)
  │ voit deviné vs réel, zones de surprise
  │ CTA soft : email + récap coaching
  │ → parent_email + consent → KV
  │
  │ (plus tard) email auto + CTA coach
```

## 4. Surface « Comparaison » (généralisée depuis comparaison.html)

- Réutilise tokens marque, header, breakpoints 900/720/640 existants.
- **Re-légender** : bleu `#1320CE` = « Ce que vous avez deviné », orange
  `#FD6936` = « Le vrai profil de {prénom} ».
- Rendu par type de test :
  - Big5 → radar (existe).
  - RIASEC → hexagone / barres.
  - Valeurs et tests dimensionnels → deltas en barres.
- **Reframe « surprise score »** → « Vos zones de surprise » / « 3 découvertes ».
  Orienté conversation, pas notation. Le parent n'a pas « raté » un test sur son enfant.
- Prompts de conversation par écart fort (déjà dans comparaison.html).

## 5. Garde-fous éthiques (non négociables, visibles dans l'UI)

- La catégorie Comparaison **ne liste que** les tests dimensionnels non cliniques :
  OCEAN-X, RIASEC, Valeurs, Besoins, Drivers, Grit, etc.
- **Jamais comparables / jamais « devinables »** : TDAH, Autisme, Anxiété, DYS,
  HPI, Schémas de Young, PHQ9. Hard block, ils n'apparaissent pas dans la catégorie.
- L'ado a un moment de consentement explicite avant tout partage de ses vrais
  résultats (protège la posture et le RGPD).

## 6. RGPD (cf. BACKEND_SPEC.md)

- KV hébergé EU (Supabase EU).
- Minimisation : scores + email + consentements + timestamps. Rien d'autre.
- Consentement ado tracé. Consentement parent tracé. Tests cliniques exclus du flux.

## 7. Ordre de construction

1. Résultats structurés par rôle pour tous les tests (§2.1) · fondation.
2. Backend KV paire + mint/lecture du code (§2.2).
3. Généraliser la surface Comparaison au-delà d'OCEAN-X (§4).
4. Écran consentement ado + POST child_results (§3).
5. Capture lead soft + email auto parent (§2.3).
6. Garde-fous cliniques dans le filtrage de la catégorie (§5).

# TODOS — issus de /plan-ceo-review · profil-eleve.html

Mode de revue : **SELECTIVE EXPANSION** (baseline tenue + cherry-pick).

## Fait cette session
- [x] **3A** Faille XSS (noms de fichiers + récap injectés via innerHTML) → échappement `esc()`.
- [x] **2A** Secours Calendly : lien direct `calendly.com/proxxie` si le widget ne charge pas (timeout + onerror).
- [x] **4A** Garde anti double-clic sur « Continuer » (navLock 300 ms).
- [x] **4B** Vérification taille fichier (10 Mo) à l'upload.
- [x] **E1** Wizard branché au modèle existant : écrit `proxxie_firstName`, `proxxie_grade`,
      `proxxie.role`, `proxxie.justSignedUp`, `proxxie.onboarding.profile`,
      `proxxie.onboarding.data` (JSON), `proxxie.rdv.booked` (sur event Calendly) ;
      bouton final → `dashboard.html?role=`.
- [x] **E2** Événements analytics (`view_profil_exemple`, `wizard_open`, `wizard_step_done`,
      `wizard_completed`, `cta…`, `doc_added`, `test_reco_toggle`, `test_detail`,
      `calendly_booked`) via `window.dataLayer` (branchable GA/Plausible).
- [x] **E4** Cartes de tests reliées aux vraies pages (`test-riasec.html`, …).
- [x] **E5** Cadrage d'attentes dans le bandeau (« démarre simple, s'enrichit test après test »).

## Différé (NON dans le scope de cette session)
- [ ] **Section 6 — Tests** : aucun test automatisé. Prévoir un smoke (rend + wizard avance +
      profil écrit). Effort S. Raison du report : proto statique, faible risque immédiat.
- [ ] **7A — Poids des polices** : 3 familles × nombreux poids. Sous-ensembler / réduire les
      graisses chargées. Effort S.
- [ ] **10A — Divergence dashboard (dette n°1)** — ✅ **TRANCHÉ (2026-06-02) : Option A —
      « vitrine en amont du tunnel ».**
      Rôles figés : `profil-eleve.html` = page EXEMPLE/marketing AVANT inscription ;
      `dashboard.html` = PRODUIT connecté APRÈS inscription. Pas de fusion, pas de
      remplacement de l'onglet profil React.
      Tunnel cible : `index.html` (atterrir) → `profil-eleve.html` (exemple) →
      « Démarrer » (crée le profil) → `dashboard.html?role=`.
      - Aval (Démarrer → dashboard) : ✅ fait (E1).
      - **Amont (landing → exemple) : RESTE À FAIRE.** `profil-eleve.html` n'est lié par
        aucune page. `index.html` étant un bundle React compilé (1,9 Mo), le CTA
        « Voir un exemple de profil » doit être injecté via un **patch script**
        (`_patch_*.py`, conventions du repo : marqueur + regex), pas à la main.
        Effort S–M. Candidat de greffe : à côté du CTA principal de la landing.
- [ ] **dataLayer → vrai outil** : brancher `track()` à l'outil analytics réel (GA4/Plausible).
- [ ] **Backend** : la collecte du wizard reste locale (localStorage). Brancher au backend
      réel le moment venu (cf. `BACKEND_SPEC.md`).

## Delta vers le dream state (12 mois)
Funnel unique : atterrir → exemple → **Démarrer crée vraiment le compte/profil** (✅ E1, côté
client) → tests parent puis ado → profil vivant → coaching payant. Progrès : la jonction
vitrine → onboarding → dashboard existe désormais côté client ; manquent le backend et la
consolidation avec le dashboard réel (10A).

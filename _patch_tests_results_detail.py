#!/usr/bin/env python3
"""Enrich Proxxie Tests.html: richer results per test + booking CTA.

What this patches in the JSX asset of "Proxxie Tests.html":
  1. Adds a `results` array (4 bullets) to every test entry in
     TESTS_ORIENTATION and TESTS_ATYPIQUE. Each bullet describes
     what the user concretely receives.
  2. Replaces the TestCard "Résultat :" single-line block with a
     richer "Ce que vous obtenez" panel that renders the bullets.
  3. Replaces TestsCTA with a "Prendre RDV avec Charles" decryption
     CTA (https://calendly.com/proxxie/cadrage).

Idempotent · the marker /* __proxxie_tests_results_v1__ */ is
inserted into the asset; on re-run the previous patch is stripped
before re-applying.
"""
import re, json, base64, gzip, pathlib, sys

REPO = pathlib.Path(__file__).parent
TARGET = REPO / "Proxxie Tests.html"
ASSET_UUID = "61feca88-84c8-4b75-a93b-7138c831ebd9"
MARKER = "/* __proxxie_tests_results_v1__ */"

# ---------------------------------------------------------------- new test data
# 4 result bullets per test (k = short label, v = concrete payoff).
RESULTS_BY_CODE = {
    "OCEAN-X": [
        {"k": "Profil chiffré",     "v": "Score sur les 5 dimensions OCEAN, avec niveau (faible · moyen · élevé) et phrase-portrait."},
        {"k": "Comparaison âge",    "v": "Percentiles par tranche d'âge et genre, pour situer votre ado dans sa génération."},
        {"k": "Forces et tensions", "v": "3 forces dominantes du profil et 2 zones de vigilance pour la suite."},
        {"k": "Pistes métiers",     "v": "6 à 8 métiers compatibles et 3 environnements à éviter selon le profil."},
    ],
    "RIASEC": [
        {"k": "Code Holland",       "v": "Code en 3 lettres (ex · RIA, SEC) avec hiérarchie complète sur les 6 dimensions."},
        {"k": "Métiers à explorer", "v": "12 métiers concrets classés par adéquation, du plus aligné au plus éloigné."},
        {"k": "Filières Parcoursup","v": "3 filières post-bac alignées et 2 secteurs porteurs sur les 5 prochaines années."},
        {"k": "Environnements",     "v": "Types d'employeurs et de cadres de travail dans lesquels le profil s'épanouit."},
    ],
    "PCM": [
        {"k": "Base et phase",      "v": "Type de base (immuable) et type de phase actuelle parmi les 6 PCM (Empathique, Travaillomane, Persévérant, Rêveur, Promoteur, Rebelle)."},
        {"k": "Canal préféré",      "v": "Canal de communication efficace et 3 signaux de mécommunication à repérer."},
        {"k": "Dialogue parent",    "v": "3 stratégies concrètes pour mieux dialoguer avec son ado au quotidien."},
        {"k": "Sous stress",        "v": "Comportements typiques sous pression (drivers, masques) et leviers de désamorçage."},
    ],
    "MBTI": [
        {"k": "Type sur 16",        "v": "Type complet (ex · INTJ, ENFP) avec score de confiance par axe (E/I, S/N, T/F, J/P)."},
        {"k": "Cognition",          "v": "Comment votre ado perçoit l'info, décide et recharge son énergie."},
        {"k": "Forces et pièges",   "v": "3 forces typiques du type et 3 pièges récurrents à anticiper."},
        {"k": "Carrières types",    "v": "Carrières où ce type s'épanouit + environnements à fuir."},
    ],
    "Drivers": [
        {"k": "Driver dominant",    "v": "Driver le plus actif parmi les 5 (Sois Parfait, Sois Fort, Fais Effort, Fais Plaisir, Dépêche-toi)."},
        {"k": "Scénario type",      "v": "Mini-scénario du déclenchement sous pression, reconnaissable au quotidien."},
        {"k": "3 permissions",      "v": "3 phrases-permissions à utiliser pour neutraliser le driver dans les moments tendus."},
        {"k": "Impact orientation", "v": "Comment le driver pèse sur les choix scolaires et la prise de décision."},
    ],
    "Valeurs": [
        {"k": "Top 3 valeurs",      "v": "3 valeurs cardinales avec poids relatif et phrase de définition personnelle."},
        {"k": "Classement complet", "v": "Hiérarchie sur les 10 valeurs universelles Schwartz, du plus prioritaire au plus secondaire."},
        {"k": "Tensions internes",  "v": "Valeurs opposées détectées, sources de conflits intérieurs à anticiper."},
        {"k": "Alignement métiers", "v": "Métiers et environnements concrètement alignés avec les valeurs cardinales."},
    ],
    "Besoins": [
        {"k": "Besoin dominant",    "v": "Besoin moteur parmi Réussite (nAch), Affiliation (nAff), Pouvoir (nPow) avec score."},
        {"k": "Carte motivation",   "v": "Ce qui énergise votre ado et ce qui le démotive en profondeur."},
        {"k": "Missions à viser",   "v": "3 types de missions à privilégier dans le quotidien scolaire et associatif."},
        {"k": "Terrains favorables","v": "Métiers et secteurs où ce besoin trouve un terrain naturellement favorable."},
    ],
    "TDAH": [
        {"k": "Score Part A et B",  "v": "Score ASRS Part A (seuil OMS 4/6) et détail Part B sur les 12 items complémentaires."},
        {"k": "3 dimensions",       "v": "Profil par dimension · attention, hyperactivité, impulsivité, avec niveau pour chacune."},
        {"k": "Signaux quotidien",  "v": "Comportements concrets à observer en cours, sur les devoirs et dans les relations."},
        {"k": "Reco bilan",         "v": "Recommandation claire · continuer à observer ou consulter un neuropsy (avec critères de choix)."},
    ],
    "Autisme": [
        {"k": "Score AQ",           "v": "Score global avec seuil clinique de Cambridge (12/20) et interprétation."},
        {"k": "Sous-dimensions",    "v": "Détail sur les 5 sous-domaines AQ · interactions, attention aux détails, communication, imagination, switching."},
        {"k": "Forces vs charge",   "v": "Forces différentielles identifiées et charge cognitive associée au quotidien."},
        {"k": "Bilan si pertinent", "v": "Si score marqué · pistes concrètes (CRA, psychologue spécialisé TSA, neuropsy) et étapes."},
    ],
    "HPI": [
        {"k": "4 dimensions",       "v": "Traits HPI sur 4 dimensions · cognitive, émotionnelle, comportementale, sensorielle."},
        {"k": "Forces de douance",  "v": "Forces identifiées · raisonnement, hypersensibilité, créativité, intensité."},
        {"k": "Risques associés",   "v": "Risques à surveiller · perfectionnisme, ennui, dysynchronie, faux-self scolaire."},
        {"k": "Bilan WISC",         "v": "Si traits marqués · orientation vers un bilan WISC-V et spécialistes recommandés."},
    ],
    "Anxiété": [
        {"k": "Score GAD-7",        "v": "Score GAD-7 avec niveau clinique · minimal, léger, modéré ou sévère."},
        {"k": "5 items ado",        "v": "Détail par domaine · école, social, sommeil, somatique, ruminations."},
        {"k": "Trait vs état",      "v": "Cartographie anxiété-trait (de fond) vs anxiété-état (situation), basée sur le STAI."},
        {"k": "Conseils gradués",   "v": "Pistes adaptées au niveau · auto-régulation, posture parent, ou avis professionnel."},
    ],
    "DYS": [
        {"k": "Par domaine",        "v": "Score séparé sur 4 domaines · lecture, orthographe, calcul, coordination motrice."},
        {"k": "DYS suspectées",     "v": "Identification de la ou des DYS suggérées par les réponses (dyslexie, dysortho, dyscalculie, dyspraxie)."},
        {"k": "Aménagements",       "v": "Aménagements scolaires possibles (PAP, PPS) et démarches concrètes côté établissement."},
        {"k": "Spécialiste ciblé",  "v": "Spécialiste à consulter par domaine · orthophoniste, ergothérapeute, neuropsy."},
    ],
}

# ----------------------------------------------------------- new TestCard layout
NEW_TEST_CARD = r"""const TestCard = ({ t }) => (
  <a href={t.href} style={{
    display: "block", textDecoration: "none", color: "inherit",
    background: "white", borderRadius: 24, padding: 30,
    border: "1px solid var(--c-line)",
    boxShadow: "0 4px 14px -8px rgba(10,14,44,.08)",
    transition: "transform .2s, box-shadow .2s, border-color .2s",
  }}
    onMouseEnter={(e) => { e.currentTarget.style.transform = "translateY(-4px)"; e.currentTarget.style.boxShadow = "0 24px 50px -20px " + t.accent + "33, 0 8px 20px -8px rgba(10,14,44,.08)"; e.currentTarget.style.borderColor = t.accent; }}
    onMouseLeave={(e) => { e.currentTarget.style.transform = "none"; e.currentTarget.style.boxShadow = "0 4px 14px -8px rgba(10,14,44,.08)"; e.currentTarget.style.borderColor = "var(--c-line)"; }}
  >
    <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 18 }}>
      <div style={{ width: 56, height: 56, borderRadius: 16, background: t.accentSoft, color: t.accent, display: "grid", placeItems: "center" }}>{t.icon}</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: t.accent, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 2 }}>{t.eyebrow}</div>
        <div style={{ fontSize: 22, fontWeight: 700, fontFamily: "var(--font-display)", letterSpacing: "-0.02em" }}>{t.name}</div>
        <div style={{ fontSize: 12.5, color: "var(--c-muted)" }}>{t.model}</div>
      </div>
    </div>
    <p style={{ fontSize: 14.5, color: "var(--c-ink-2)", lineHeight: 1.55, marginBottom: 14 }}>{t.short}</p>
    <p style={{ fontSize: 13, color: "var(--c-muted)", lineHeight: 1.55, marginBottom: 18 }}>{t.long}</p>
    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 18 }}>
      {t.tags.map((tag) => (
        <span key={tag} style={{ fontSize: 11, fontWeight: 600, padding: "4px 10px", borderRadius: 99, background: t.accentSoft, color: t.accent }}>{tag}</span>
      ))}
    </div>
    {t.results && t.results.length > 0 && (
      <div style={{
        marginBottom: 16,
        padding: "16px 18px",
        borderRadius: 14,
        background: "var(--c-cream-light)",
        border: "1px solid var(--c-line)",
      }}>
        <div style={{
          display: "flex", alignItems: "center", gap: 8,
          fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em",
          color: t.accent, marginBottom: 12,
        }}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
          Ce que vous obtenez · {t.results.length} livrables
        </div>
        <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: 10 }}>
          {t.results.map((r, i) => (
            <li key={i} style={{ display: "grid", gridTemplateColumns: "auto 1fr", columnGap: 10, alignItems: "flex-start", fontSize: 12.5, lineHeight: 1.5 }}>
              <span aria-hidden="true" style={{
                width: 18, height: 18, borderRadius: 6, background: t.accentSoft, color: t.accent,
                display: "inline-flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
                fontSize: 11, fontWeight: 800, marginTop: 1,
              }}>{i + 1}</span>
              <span style={{ color: "var(--c-ink-2)" }}>
                <strong style={{ color: "var(--c-ink)", fontWeight: 700 }}>{r.k}.</strong> <span style={{ color: "var(--c-muted)" }}>{r.v}</span>
              </span>
            </li>
          ))}
        </ul>
      </div>
    )}
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: 16, borderTop: "1px solid var(--c-line)" }}>
      <div style={{ display: "flex", gap: 16, fontSize: 12.5, color: "var(--c-muted)" }}>
        <span>⏱ {t.duration}</span><span>· {t.questions}</span>
      </div>
      <span style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 14, fontWeight: 600, color: t.accent }}>
        Démarrer <Icon.arrow style={{ width: 14, height: 14 }} />
      </span>
    </div>
  </a>
);"""

# ------------------------------------------------------------- new TestsCTA copy
NEW_TESTS_CTA = r"""const TestsCTA = () => (
  <section style={{ paddingTop: 80, paddingBottom: 100 }}>
    <div className="shell">
      <div style={{
        background: "radial-gradient(circle at 20% 0%, #487AFF 0%, #1320CE 60%, #0A0E2C 100%)",
        borderRadius: 32, padding: "60px 50px", color: "white",
        position: "relative", overflow: "hidden",
      }}>
        <Pill color="#FD6936" w={250} h={250} style={{ position: "absolute", top: -100, right: -60, opacity: 0.6, borderRadius: "50%" }} />
        <Half color="#F5EB3F" side="t" w={180} h={80} style={{ position: "absolute", bottom: 0, left: 60, opacity: 0.5 }} />
        <div style={{ position: "relative", display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 48, alignItems: "center", maxWidth: 1080, margin: "0 auto" }}>
          <div>
            <span style={{ display: "inline-flex", alignItems: "center", gap: 8, fontSize: 12, fontWeight: 700, letterSpacing: "0.14em", textTransform: "uppercase", color: "#F5EB3F", marginBottom: 18 }}>
              <span style={{ width: 8, height: 8, borderRadius: 99, background: "#FD6936" }}></span>
              Étape suivante · décrypter ensemble
            </span>
            <h2 style={{ color: "white", fontSize: 38, lineHeight: 1.08, marginBottom: 18 }}>Vos résultats sont riches. Décryptons-les ensemble.</h2>
            <p style={{ fontSize: 17, opacity: 0.92, marginBottom: 24, lineHeight: 1.55 }}>
              Une fois les tests passés, vous avez beaucoup d'informations · personnalité, intérêts, communication, valeurs, besoins, parfois traits atypiques. Le plus utile, c'est de les relier · qu'est-ce qui fait sens pour votre ado et pour la suite ?
            </p>
            <p style={{ fontSize: 15, opacity: 0.85, marginBottom: 30, lineHeight: 1.55 }}>
              Je prends 30 minutes avec vous pour reprendre chaque test, croiser les signaux et sortir un plan d'action clair · filières à explorer, axes à creuser, alertes à surveiller. C'est offert et sans engagement.
            </p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 14, alignItems: "center" }}>
              <a
                href="https://calendly.com/proxxie/cadrage"
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-orange btn-lg btn-arrow"
                data-track="tests_cta_rdv_charles"
              >
                Prendre RDV avec Charles
              </a>
              <span style={{ fontSize: 13.5, opacity: 0.8 }}>
                30 min · visio · gratuit
              </span>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 22, marginTop: 26, fontSize: 13, opacity: 0.85 }}>
              <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
                Lecture croisée des 12 tests
              </span>
              <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
                Plan d'action concret
              </span>
              <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
                Sans engagement
              </span>
            </div>
          </div>
          <div style={{
            background: "rgba(255,255,255,0.08)",
            border: "1px solid rgba(255,255,255,0.18)",
            borderRadius: 22,
            padding: "26px 28px",
            backdropFilter: "blur(6px)",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 18 }}>
              <div style={{ width: 54, height: 54, borderRadius: 16, background: "#FD6936", color: "white", display: "grid", placeItems: "center", fontFamily: "var(--font-display)", fontSize: 22, fontWeight: 700 }}>C</div>
              <div>
                <div style={{ fontFamily: "var(--font-display)", fontSize: 19, fontWeight: 600, color: "white" }}>Charles · fondateur Proxxie</div>
                <div style={{ fontSize: 12.5, opacity: 0.75 }}>Coach orientation · 7 ans d'accompagnement</div>
              </div>
            </div>
            <div style={{ fontSize: 13.5, lineHeight: 1.6, opacity: 0.9 }}>
              <div style={{ fontWeight: 700, color: "#F5EB3F", marginBottom: 8, fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase" }}>Au programme de la session</div>
              <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: 8 }}>
                <li>① Relecture de chaque test, sans jargon, avec exemples concrets.</li>
                <li>② Croisement des signaux pour faire émerger 2 à 3 hypothèses fortes.</li>
                <li>③ Filières et métiers à creuser en priorité, alertes à surveiller.</li>
                <li>④ Prochaines étapes claires, à votre rythme, sans pression.</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
);"""

# ------------------------------------------------------------------- regex helpers
# Match the OLD TestCard component definition · stops at the closing );
OLD_TEST_CARD_RE = re.compile(
    r"const TestCard = \(\{ t \}\) => \(\s*<a href=\{t\.href\}.*?\n\s*</a>\n\);",
    flags=re.S,
)

# Match the OLD TestsCTA component definition
OLD_TESTS_CTA_RE = re.compile(
    r"const TestsCTA = \(\) => \(\s*<section.*?\n\s*</section>\n\);",
    flags=re.S,
)

# Per-test fragment matcher · we splice `results: [...],` between `output: "..."` and `tags: [`
# Format target · `... output: "...", tags: [...]`
def js_array(items):
    """Render a JS array literal of {k, v} objects."""
    parts = []
    for it in items:
        k = it["k"].replace('"', '\\"')
        v = it["v"].replace('"', '\\"')
        parts.append('{k:"' + k + '",v:"' + v + '"}')
    return "[" + ",".join(parts) + "]"


def inject_results(src: str) -> tuple:
    """Insert `results: [...]` into each test entry based on its `code` field.
    Returns (new_src, count)."""
    count = 0
    # Test entries have shape · `{ code: "XXX", ... output: "...", tags: [...] }`
    # We add results between output and tags.
    for code, items in RESULTS_BY_CODE.items():
        arr = js_array(items)
        # Pattern · code: "OCEAN-X",   ...   output: "...",   tags: [...]
        # Use the code marker to scope and the `output: "..."` -> `tags: [` window.
        pat = re.compile(
            r'(\{ code: "' + re.escape(code) + r'",.*?output: "[^"]*",) (tags: \[)',
            flags=re.S,
        )
        new_src, n = pat.subn(r'\1 results: ' + arr.replace("\\", "\\\\") + r', \2', src)
        if n != 1:
            raise RuntimeError(f"could not splice results for code={code!r} (n={n})")
        src = new_src
        count += 1
    return src, count


def strip_v1(src: str) -> str:
    """Remove any prior v1 patch · the marker line + any `results: [...]` we
    previously inserted. We rely on the OLD_*_RE regexes to also match the
    re-inserted block (since we keep its surface shape identical apart from
    additions). The simplest reversal is to drop any `, results: [...]` we
    inserted before `tags: [` for each known test code."""
    # Drop inserted `results: [...]` blocks (greedy-safe via balanced bracket
    # walk · the contents only contain {k:"...",v:"..."} segments so we can
    # use a single non-greedy character class up to `], tags:`).
    for code in RESULTS_BY_CODE:
        pat = re.compile(
            r'(\{ code: "' + re.escape(code) + r'",.*?output: "[^"]*",) results: \[[^\]]*\], (tags: \[)',
            flags=re.S,
        )
        src = pat.sub(r'\1 \2', src)
    # Remove marker (we only insert one)
    src = src.replace("\n" + MARKER + "\n", "\n")
    return src


def patch_asset_text(src: str) -> str:
    was_patched = MARKER in src
    if was_patched:
        # Restore the original TestCard and TestsCTA (we replaced them); the
        # simplest reversal is to detect the v1 versions by their hallmark
        # string and rewrite back to the originals. Since we never check in
        # the originals, instead we just leave the v1 TestCard/TestsCTA in
        # place and only re-inject results (idempotent for results too).
        src = strip_v1(src)

    # 1. inject `results` into every test entry
    src, n = inject_results(src)
    if n != len(RESULTS_BY_CODE):
        raise RuntimeError(f"expected {len(RESULTS_BY_CODE)} injections, got {n}")

    # 2. Replace TestCard if it still has the OLD shape (no `t.results` ref).
    if "t.results &&" not in src:
        new_src, n2 = OLD_TEST_CARD_RE.subn(NEW_TEST_CARD, src, count=1)
        if n2 != 1:
            raise RuntimeError("could not replace TestCard")
        src = new_src

    # 3. Replace TestsCTA if it still has the OLD shape (no calendly link).
    if "calendly.com/proxxie/cadrage" not in src or 'tests_cta_rdv_charles' not in src:
        new_src, n3 = OLD_TESTS_CTA_RE.subn(NEW_TESTS_CTA, src, count=1)
        if n3 != 1:
            raise RuntimeError("could not replace TestsCTA")
        src = new_src

    # 4. drop the marker (re-add a single one at top of asset)
    src = src.replace("\n" + MARKER + "\n", "\n")
    src = MARKER + "\n" + src

    return src


def main():
    if not TARGET.exists():
        print(f"ERROR · {TARGET} not found")
        sys.exit(1)

    html = TARGET.read_text(encoding="utf-8")
    m = re.search(r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)', html, re.DOTALL)
    if not m:
        print("ERROR · no bundler/manifest in file")
        sys.exit(1)

    manifest = json.loads(m.group(2))
    if ASSET_UUID not in manifest:
        print(f"ERROR · asset {ASSET_UUID} not in manifest")
        sys.exit(1)

    entry = manifest[ASSET_UUID]
    data = base64.b64decode(entry["data"])
    compressed = entry.get("compressed", False)
    if compressed:
        data = gzip.decompress(data)
    src = data.decode("utf-8")

    new_src = patch_asset_text(src)

    new_data = new_src.encode("utf-8")
    if compressed:
        new_data = gzip.compress(new_data)
    entry["data"] = base64.b64encode(new_data).decode("ascii")

    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]
    TARGET.write_text(new_html, encoding="utf-8")
    print(f"✓ patched {TARGET.name}")
    print(f"  asset size · {len(src)} → {len(new_src)} chars ({len(new_src)-len(src):+d})")
    print(f"  tests enriched · {len(RESULTS_BY_CODE)}")


if __name__ == "__main__":
    main()

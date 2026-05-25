#!/usr/bin/env python3
"""SaveResultsCallout : injecte un bloc « Sauvegarde tes résultats » sur la page
Results de tous les tests bundlés.

Pourquoi :
- Actuellement, les réponses ne vivent qu'en localStorage. Si le navigateur est
  vidé ou si l'utilisateur change d'appareil, tout est perdu.
- Le moment Results est le pic d'engagement (l'utilisateur vient de découvrir
  son profil), pile le bon moment pour proposer la création de compte.

Comportement :
- Le callout est rendu juste avant <Footer /> dans le TestApp.
- Il ne s'affiche QUE si l'utilisateur n'est pas déjà connecté
  (_proxxieIsConnected() retourne false).
- Pitch : lecture croisée des 16 tests, mode parent, accès cross-device.
- CTAs : « Créer mon compte gratuit » → connexion.html?signup=1
         « J'ai déjà un compte » → connexion.html

Architecture :
- 1 composant SaveResultsCallout injecté dans l'asset 61feca88 (où vit TestApp).
- Cible : tous les fichiers Proxxie Test *.html + leurs twins lowercase.
- Idempotent · sentinelles BEGIN/END, strip-and-readd.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
ASSET_UUID_PREFIX = "61feca88"

# Fichiers cibles · tous les tests existants + leurs twins lowercase
TARGETS = [
    # Existants en main
    "Proxxie Test.html",                    # OCEAN-X
    "Proxxie Test RIASEC.html",
    "Proxxie Test PCM.html",
    "Proxxie Test MBTI.html",
    "Proxxie Test HPI.html",
    "Proxxie Test TDAH.html",
    "Proxxie Test DYS.html",
    "Proxxie Test Autisme.html",
    "Proxxie Test Anxiete.html",
    "Proxxie Test Besoins.html",
    "Proxxie Test Drivers.html",
    "Proxxie Test Valeurs.html",
    # Nouveaux (construits par _patch_build_phq9.py / _grit.py / _caas.py)
    "Proxxie Test PHQ9.html",
    "Proxxie Test Grit.html",
    "Proxxie Test CAAS.html",
    # Twins lowercase (cf. convention _patch_test_pages_phase1.py)
    "test-riasec.html",
    "test-pcm.html",
    "test-mbti.html",
    "test-hpi.html",
    "test-tdah.html",
    "test-dys.html",
    "test-autisme.html",
    "test-anxiete.html",
    "test-besoins.html",
    "test-drivers.html",
    "test-valeurs.html",
    "test-phq9.html",
    "test-grit.html",
    "test-caas.html",
]

# Sentinelles JS-context (module top level) · plain block comments OK
BEGIN_DEF = "/* PROXXIE_SAVE_CALLOUT_DEF_BEGIN */"
END_DEF   = "/* PROXXIE_SAVE_CALLOUT_DEF_END */"
# Pas de sentinelles JSX : babel-standalone in-browser rend `{/* */}`,
# `{null /* */}` etc. comme texte visible. On détecte la présence du render
# par recherche de `<SaveResultsCallout />` littéral (cf. patch_src).

# ---- Le composant React (texte JSX) ----
# Injecté juste avant `const TestApp = () => {`
COMPONENT_JSX = BEGIN_DEF + r'''
const SaveResultsCallout = () => {
  if (typeof _proxxieIsConnected === "function" && _proxxieIsConnected()) return null;
  return (
    <section style={{ paddingTop: 0, paddingBottom: 80 }}>
      <div className="shell" style={{ maxWidth: 820 }}>
        <div style={{
          background: "linear-gradient(160deg, #1320CE, #0A0E2C)",
          color: "white",
          borderRadius: 24,
          padding: "36px 32px",
          textAlign: "center",
          position: "relative",
          overflow: "hidden",
          boxShadow: "0 24px 60px -20px rgba(19,32,206,.45)",
        }}>
          <div style={{
            position: "absolute", top: -40, right: -40, width: 180, height: 180,
            background: "radial-gradient(circle, rgba(245,235,63,.35), transparent 70%)",
            pointerEvents: "none",
          }} />
          <div style={{ fontSize: 11, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.14em", opacity: 0.88, marginBottom: 10, position: "relative" }}>
            ⚡ Avant de partir
          </div>
          <h2 style={{ color: "white", fontSize: 30, lineHeight: 1.25, marginBottom: 14, position: "relative" }}>
            Sauvegarde tes résultats <span style={{ background: "linear-gradient(180deg, transparent 60%, #F5EB3F 60%)", color: "#0A0E2C", paddingInline: 6 }}>avant de partir</span>.
          </h2>
          <p style={{ fontSize: 16, opacity: 0.92, lineHeight: 1.55, maxWidth: 580, margin: "0 auto 24px", position: "relative" }}>
            Tes réponses sont actuellement stockées dans ce navigateur. Si tu vides ton cache ou changes d'appareil, elles disparaissent. Avec un compte gratuit, tu gardes tout et tu peux passer les 15 autres tests sans rien perdre.
          </p>
          <ul style={{ listStyle: "none", padding: 0, maxWidth: 480, margin: "0 auto 28px", display: "grid", gap: 12, textAlign: "left", position: "relative" }}>
            {[
              ["Lecture croisée des 16 tests", "un rapport unique qui combine personnalité, intérêts, motivations, screenings"],
              ["Mode parent activé", "prédis les réponses de ton ado, compare avec son vécu réel"],
              ["Accès partout, à vie", "tes résultats te suivent sur ordi, tablette, mobile"],
            ].map((row, i) => (
              <li key={i} style={{ display: "flex", alignItems: "flex-start", gap: 12, fontSize: 14.5, opacity: 0.96, lineHeight: 1.5 }}>
                <span style={{
                  flexShrink: 0, width: 24, height: 24, borderRadius: 7,
                  background: "rgba(245,235,63,.28)", color: "#F5EB3F",
                  display: "grid", placeItems: "center", fontSize: 13, fontWeight: 800, marginTop: 1,
                }}>✓</span>
                <span><strong style={{ color: "white" }}>{row[0]}</strong> · <span style={{ opacity: 0.85 }}>{row[1]}</span></span>
              </li>
            ))}
          </ul>
          <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap", position: "relative" }}>
            <a href="connexion.html?signup=1" style={{
              background: "#FD6936", color: "white", padding: "14px 26px", borderRadius: 99,
              fontWeight: 700, fontSize: 15, textDecoration: "none",
              boxShadow: "0 14px 32px -10px rgba(253,105,54,.7)",
              display: "inline-flex", alignItems: "center", gap: 8,
            }}>
              Créer mon compte gratuit
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M13 5l7 7-7 7"/></svg>
            </a>
            <a href="connexion.html" style={{
              background: "transparent", color: "white",
              border: "1.5px solid rgba(255,255,255,.35)",
              padding: "14px 26px", borderRadius: 99, fontWeight: 600, fontSize: 15, textDecoration: "none",
              display: "inline-flex", alignItems: "center",
            }}>
              J'ai déjà un compte
            </a>
          </div>
          <div style={{ marginTop: 18, position: "relative" }}>
            <span style={{ fontSize: 12.5, opacity: 0.65, fontFamily: "var(--font-num, ui-monospace)" }}>
              Gratuit · 30 secondes · aucune carte bancaire demandée
            </span>
          </div>
        </div>
      </div>
    </section>
  );
};
''' + END_DEF + "\n\nconst TestApp = () => {"

# Ancre pour la définition du composant (avant TestApp)
ANCHOR_DEF = "const TestApp = () => {"

# Ancre + remplacement pour le render (juste avant <Footer /> dans TestApp).
# Important : on est dans un slot JSX child, donc les sentinelles doivent
# utiliser la syntaxe `{/* ... */}` (sinon le texte des commentaires est rendu).
ANCHOR_REN_OLD = "      <Footer />\n    </>\n  );\n};"
ANCHOR_REN_NEW = (
    "      {mode === \"results\" && results && <SaveResultsCallout />}\n"
    "      <Footer />\n    </>\n  );\n};"
)
# Marqueur de présence (idempotence) : si cette ligne exacte existe déjà,
# le render est déjà patché, on saute la ré-insertion.
RENDER_PRESENCE_MARKER = '{mode === "results" && results && <SaveResultsCallout />}'


def strip_between(src: str, begin: str, end: str) -> str:
    pat = re.compile(r'\s*' + re.escape(begin) + r'.*?' + re.escape(end), re.DOTALL)
    return pat.sub('', src)


def cleanup_orphan_empty_jsx_blocks(src: str) -> str:
    """Supprime les `{}` orphelins dans le slot JSX render (entre le block
    `{mode === "results" ...}` et `<Footer />`), héritage de cleanups partiels
    de versions précédentes. Sûr : un `{}` au seul JSX child est de toute
    façon erroné, donc on l'enlève systématiquement dans cette zone.
    """
    # On vise les lignes du TestApp render uniquement (entre </>) où on a inséré
    # avant <Footer />. Pattern : `      {}\n` (6 spaces + braces only).
    return re.sub(r'\n[ \t]+\{\}\s*(?=\n[ \t]+(?:<Footer|\{(?:null|mode)))', '\n', src)


def patch_src(src: str) -> tuple[str, list[str]]:
    changes = []
    # 1. Idempotence DEF : strip BEGIN..END entre sentinelles (JS context, OK)
    src = strip_between(src, BEGIN_DEF, END_DEF)

    # 2. Idempotence RENDER : cleanup de TOUTES les variantes de sentinelles
    # historiques (chacune était rendue comme texte par babel-standalone)
    # avant de re-supprimer la ligne du render lui-même.
    src = strip_between(src, "{null /* PROXXIE_SAVE_CALLOUT_REN_BEGIN */}", "{null /* PROXXIE_SAVE_CALLOUT_REN_END */}")
    src = strip_between(src, "{/* PROXXIE_SAVE_CALLOUT_REN_BEGIN */}", "{/* PROXXIE_SAVE_CALLOUT_REN_END */}")
    src = strip_between(src, "/* PROXXIE_SAVE_CALLOUT_REN_BEGIN */", "/* PROXXIE_SAVE_CALLOUT_REN_END */")
    # Strip aussi la ligne RENDER_PRESENCE_MARKER si elle existe déjà
    src = re.sub(r'\n[ \t]+' + re.escape(RENDER_PRESENCE_MARKER) + r'[^\n]*', '', src)
    # Nettoie d'éventuels `{}` orphelins
    src = cleanup_orphan_empty_jsx_blocks(src)

    # 3. Injection définition (avant TestApp)
    if ANCHOR_DEF not in src:
        return src, ["WARN ANCHOR_DEF introuvable"]
    src = src.replace(ANCHOR_DEF, COMPONENT_JSX, 1)
    changes.append("+ composant SaveResultsCallout")

    # 4. Injection render (avant <Footer />)
    if ANCHOR_REN_OLD not in src:
        return src, changes + ["WARN ANCHOR_REN_OLD introuvable"]
    src = src.replace(ANCHOR_REN_OLD, ANCHOR_REN_NEW, 1)
    changes.append("+ render <SaveResultsCallout/> avant <Footer/>")
    return src, changes


def patch_one(target: pathlib.Path) -> str:
    if not target.exists():
        return f"{target.name}: file not found (skip)"
    html = target.read_text(encoding="utf-8")
    m = re.search(r'(<script type="__bundler/manifest">)(.*?)(</script>)', html, re.DOTALL)
    if not m:
        return f"{target.name}: pas de manifest"
    manifest = json.loads(m.group(2))
    uuid = next((k for k in manifest if k.startswith(ASSET_UUID_PREFIX)), None)
    if uuid is None:
        return f"{target.name}: asset {ASSET_UUID_PREFIX} introuvable"
    entry = manifest[uuid]
    raw = base64.b64decode(entry['data'])
    comp = entry.get('compressed', False)
    src = gzip.decompress(raw).decode('utf-8') if comp else raw.decode('utf-8')

    new_src, changes = patch_src(src)
    if new_src == src:
        return f"{target.name}: aucun changement"
    nd = new_src.encode('utf-8')
    if comp:
        nd = gzip.compress(nd)
    entry['data'] = base64.b64encode(nd).decode('ascii')
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]
    target.write_text(new_html, encoding='utf-8')
    return f"{target.name}: [{', '.join(changes)}] (asset {uuid[:8]}, {len(src)} → {len(new_src)})"


if __name__ == "__main__":
    for fn in TARGETS:
        print(patch_one(REPO / fn))

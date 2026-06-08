#!/usr/bin/env python3
"""Réordonne et allège l'écran de résultats sur tous les tests câblés (v2).

Design-review · l'utilisateur a rejeté la v1 (« enchaînement de CTA à la fin,
complètement illisible »). Nouvelle direction, de haut en bas :

1. Tout en haut, deux CTA LIGHT côte à côte : « Sauvegarder mes résultats » +
   « Comparer les résultats ». Le gros bloc « Compare avec quelqu'un »
   (ApiShareLinkPanel peer) disparaît : il devient un CTA light qui ouvre le
   formulaire dans une modale (CompareReveal). Le bouton sauvegarde passe en
   outline light. Les deux tiennent sur une seule ligne (ResultsTopActions).

2. Le résultat (<Results>) juste en dessous (le payoff).

3. Le panneau narratif proéminent (« Le X, c'est une porte d'entrée », bleu
   foncé) attirait l'œil sans permettre d'agir : on le repeint en clair (fond
   dégradé crème, texte sombre) et on garde dedans les deux CTA de navigation
   « Voir tous les tests » + « Repasser le test » (ex-« Refaire »). Le copy
   narratif est conservé.

4. Les tests sans panneau proéminent (faint/none) reçoivent une carte de
   navigation claire équivalente (ResultsNavCard) à la place de leur lien de
   retake terne (ou en fin de branche s'ils n'en avaient pas).

5. Le rdv (AIAnalysisPanel · « Réserver 30 min avec Charles » orange) reste le
   seul CTA primaire orange, inchangé.

Transform en place sur le bundle gzip+base64, idempotent (skip si
ResultsTopActions déjà présent). Cliniques (anxiete, phq9) exclus.

Usage :
  python3 _patch_results_layout.py                  # tous les tests câblés
  python3 _patch_results_layout.py test-mbti.html   # un seul fichier
"""
import re
import json
import base64
import gzip
import pathlib
import sys

REPO = pathlib.Path(__file__).parent
ASSET_UUID_PREFIX = "61feca88"
CLINICAL = ("anxiete", "phq9")
MARKER = "ResultsTopActions"

# Gradient sombre partagé du panneau proéminent (identique sur les 6 tests).
GRAD = (
    'background: "radial-gradient(circle at 20% 0%, #487AFF 0%, '
    '#1320CE 60%, #0A0E2C 100%)",\n'
    '          borderRadius: 28, padding: "50px 40px", color: "white",'
)
GRAD_LIGHT = (
    'background: "linear-gradient(135deg, #F6F8FF 0%, #FFFFFF 100%)", '
    'border: "1px solid var(--c-line)",\n'
    '          borderRadius: 28, padding: "50px 40px", color: "var(--c-ink)",'
)

PILL_OLD = (
    '<Pill color="#FD6936" w={220} h={220} style={{ position: "absolute", '
    'top: -90, right: -50, opacity: 0.55, borderRadius: "50%" }} />'
)
PILL_NEW = (
    '<Pill color="#FD6936" w={220} h={220} style={{ position: "absolute", '
    'top: -90, right: -50, opacity: 0.1, borderRadius: "50%" }} />'
)

H2_OLD = '<h2 style={{ color: "white", fontSize: 30, marginBottom: 16 }}>'
H2_NEW = '<h2 style={{ color: "var(--c-ink)", fontSize: 30, marginBottom: 16 }}>'

P_OLD = '<p style={{ fontSize: 16, opacity: 0.92, marginBottom: 26 }}>'
P_NEW = '<p style={{ fontSize: 16, color: "var(--c-muted)", marginBottom: 26 }}>'

# Bouton retake du panneau proéminent (translucide blanc → outline light).
PROM_BTN_OLD = (
    '<button onClick={onRestart} style={{ background: "rgba(255,255,255,.15)", '
    'border: "1px solid rgba(255,255,255,.3)", color: "white", '
    'padding: "12px 22px", borderRadius: 99, fontSize: 14, fontWeight: 600, '
    'cursor: "pointer" }}>Refaire le test</button>'
)
PROM_BTN_NEW = (
    '<button onClick={onRestart} type="button" style={{ background: "white", '
    'border: "1.5px solid var(--c-line)", color: "var(--c-ink)", '
    'padding: "12px 22px", borderRadius: 99, fontSize: 14, fontWeight: 600, '
    'cursor: "pointer" }}>Repasser le test</button>'
)

# Bouton-déclencheur de sauvegarde (rempli accent → outline light, bare).
SAVE_TRIGGER_OLD = (
    '      {/* Compact trigger button rendered above the results */}\n'
    '      <section style={{ paddingTop: 24, paddingBottom: 0 }}>\n'
    '        <div className="shell" style={{ maxWidth: 820, display: "flex", '
    'justifyContent: "center" }}>\n'
    '          <button onClick={openModal} style={{\n'
    '            background: accent, color: "white", border: "none",\n'
    '            padding: "13px 26px", borderRadius: 99,\n'
    '            fontSize: 14, fontWeight: 600, cursor: "pointer",\n'
    '            display: "inline-flex", alignItems: "center", gap: 10,\n'
    '            boxShadow: "0 4px 14px -4px " + accent + "55",\n'
    '          }}>\n'
    '            <span style={{ fontSize: 18 }}>\U0001F4E5</span> '
    'Sauvegarder mes résultats\n'
    '          </button>\n'
    '        </div>\n'
    '      </section>'
)
SAVE_TRIGGER_NEW = (
    '      <button onClick={openModal} style={{\n'
    '            background: "white", color: accent, border: "1.5px solid " '
    '+ accent + "55",\n'
    '            padding: "13px 22px", borderRadius: 99,\n'
    '            fontSize: 14, fontWeight: 600, cursor: "pointer",\n'
    '            display: "inline-flex", alignItems: "center", gap: 9,\n'
    '            boxShadow: "none",\n'
    '          }}>\n'
    '            <span style={{ fontSize: 17 }}>\U0001F4E5</span> '
    'Sauvegarder mes résultats\n'
    '          </button>'
)

# Lien de retake terne (faint, 7 tests) · bloc isolé centré, dans <Results>.
FAINT_OLD = (
    '        <div style={{ textAlign: "center", marginTop: 30 }}>\n'
    '          <button onClick={onRestart} style={{ background: "transparent", '
    'border: "none", color: "var(--c-muted)", fontSize: 14, cursor: "pointer", '
    'textDecoration: "underline" }}>Refaire le test</button>\n'
    '        </div>'
)
FAINT_NEW = '        <ResultsNavCard onRestart={onRestart} />'

# Composants injectés juste avant TestApp.
COMPONENTS_JS = r"""
/* __proxxie_results_v2__ · CTA light + carte de navigation claire */
const CompareReveal = ({ answers, accent = "#487AFF" }) => {
  const [open, setOpen] = React.useState(false);
  const close = () => { setOpen(false); try { document.body.style.overflow = ""; } catch (e) {} };
  const openIt = () => { setOpen(true); try { document.body.style.overflow = "hidden"; } catch (e) {} };
  React.useEffect(() => {
    if (!open) return;
    const onKey = (e) => { if (e.key === "Escape") close(); };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);
  return (
    <>
      <button onClick={openIt} type="button" style={{ background: "white", color: accent, border: "1.5px solid " + accent + "55", padding: "13px 22px", borderRadius: 99, fontSize: 14, fontWeight: 600, cursor: "pointer", display: "inline-flex", alignItems: "center", gap: 9 }}>
        <span style={{ fontSize: 17 }}>🔗</span> Comparer les résultats
      </button>
      {open && (
        <div onClick={(e) => { if (e.target === e.currentTarget) close(); }} style={{ position: "fixed", inset: 0, zIndex: 110, background: "rgba(10,14,44,0.55)", backdropFilter: "blur(6px)", display: "grid", placeItems: "center", padding: 20, overflowY: "auto" }}>
          <div style={{ width: "100%", maxWidth: 640, position: "relative", maxHeight: "calc(100vh - 40px)", overflowY: "auto" }}>
            <button onClick={close} aria-label="Fermer" type="button" style={{ position: "absolute", top: 18, right: 14, zIndex: 2, background: "var(--c-cream-light)", border: "1px solid var(--c-line)", cursor: "pointer", width: 32, height: 32, borderRadius: 16, fontSize: 14, color: "var(--c-ink)", display: "grid", placeItems: "center", padding: 0 }}>✕</button>
            <ApiShareLinkPanel answers={answers} accent={accent} mode="peer" />
          </div>
        </div>
      )}
    </>
  );
};

const ResultsTopActions = ({ accent = "#487AFF", answers, testCode, testName, summary, showCompare }) => (
  <section style={{ paddingTop: 26, paddingBottom: 0 }}>
    <div className="shell" style={{ maxWidth: 820 }}>
      <div style={{ display: "flex", gap: 12, justifyContent: "center", alignItems: "center", flexWrap: "wrap" }}>
        <EmailResultsActions testCode={testCode} testName={testName} accent={accent} summary={summary} answers={answers} />
        {showCompare && answers && <CompareReveal answers={answers} accent={accent} />}
      </div>
    </div>
  </section>
);

const ResultsNavCard = ({ onRestart }) => (
  <section style={{ paddingTop: 8, paddingBottom: 0 }}>
    <div className="shell" style={{ maxWidth: 820 }}>
      <div style={{ background: "linear-gradient(135deg, #F6F8FF 0%, #FFFFFF 100%)", border: "1px solid var(--c-line)", borderRadius: 24, padding: "34px 32px", textAlign: "center" }}>
        <h2 style={{ fontSize: 22, marginBottom: 8 }}>Et maintenant ?</h2>
        <p style={{ fontSize: 14.5, color: "var(--c-muted)", lineHeight: 1.55, marginBottom: 22, maxWidth: 460, marginLeft: "auto", marginRight: "auto" }}>Ce test est une porte d'entrée. Croisez-le avec les autres pour un portrait complet, ou repassez-le quand vous voulez.</p>
        <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
          <a href="Proxxie Tests.html" className="btn btn-orange btn-lg btn-arrow">Voir tous les tests</a>
          <button onClick={onRestart} type="button" style={{ background: "white", border: "1.5px solid var(--c-line)", color: "var(--c-ink)", padding: "12px 22px", borderRadius: 99, fontSize: 14, fontWeight: 600, cursor: "pointer" }}>Repasser le test</button>
        </div>
      </div>
    </div>
  </section>
);
"""

_OPENER = '{mode === "results" && results && (\n        <>\n'
_BRANCH_CLOSE = "\n        </>\n      )}"

# L3 · bloc peer ApiShareLinkPanel (accent variable) · supprimé (→ CompareReveal).
_PEER_PAT = re.compile(
    r'          \{!isTeenBridge && !isParentReturn && persona !== "predict" '
    r'&& answers && \(<section style=\{\{ paddingTop: 40, paddingBottom: 0 \}\}>'
    r'<div className="shell" style=\{\{ maxWidth: 820 \}\}>'
    r'<ApiShareLinkPanel answers=\{answers\} accent="#[0-9A-Fa-f]{3,8}" '
    r'mode="peer" /></div></section>\)\}\n'
)

# L4 · <EmailResultsActions .../> · remplacé par <ResultsTopActions .../>.
_SAVE_LINE_PAT = re.compile(
    r'          <EmailResultsActions (?P<attrs>testCode="[^"]*" testName="[^"]*" '
    r'accent="#[0-9A-Fa-f]{3,8}" summary=\{buildEmailSummary\(results\)\} '
    r'answers=\{answers\}) />\n'
)

_SHOW_COMPARE = (
    'showCompare={!isTeenBridge && !isParentReturn && persona !== "predict"}'
)


def _patch_src(src: str) -> str:
    if _OPENER not in src:
        raise ValueError("branche results introuvable")
    if "const TestApp = () => {" not in src:
        raise ValueError("anchor TestApp introuvable")
    if not _SAVE_LINE_PAT.search(src):
        raise ValueError("ligne EmailResultsActions introuvable")

    # A · bouton sauvegarde → outline light bare.
    if SAVE_TRIGGER_OLD not in src:
        raise ValueError("trigger sauvegarde introuvable")
    src = src.replace(SAVE_TRIGGER_OLD, SAVE_TRIGGER_NEW, 1)

    # B · injecte les composants juste avant TestApp.
    src = src.replace(
        "const TestApp = () => {",
        COMPONENTS_JS + "\nconst TestApp = () => {",
        1,
    )

    # C · supprime le gros bloc peer (L3).
    src = _PEER_PAT.sub("", src, count=1)

    # D · EmailResultsActions (L4) → ResultsTopActions (CTA light côte à côte).
    def _repl(m: "re.Match[str]") -> str:
        return (
            "          <ResultsTopActions " + m.group("attrs")
            + " " + _SHOW_COMPARE + " />\n"
        )

    src = _SAVE_LINE_PAT.sub(_repl, src, count=1)

    # E · panneau proéminent : repeint en clair + retake renommé/restylé.
    prominent = GRAD in src
    if prominent:
        src = src.replace(GRAD, GRAD_LIGHT, 1)
        src = src.replace(PILL_OLD, PILL_NEW, 1)
        src = src.replace(H2_OLD, H2_NEW, 1)
        src = src.replace(P_OLD, P_NEW, 1)
        if PROM_BTN_OLD not in src:
            raise ValueError("bouton proéminent introuvable malgré gradient")
        src = src.replace(PROM_BTN_OLD, PROM_BTN_NEW, 1)
    else:
        # F · faint → ResultsNavCard ; none → injection en fin de branche.
        if FAINT_OLD in src:
            src = src.replace(FAINT_OLD, FAINT_NEW, 1)
        else:
            oi = src.index(_OPENER)
            ci = src.index(_BRANCH_CLOSE, oi)
            insert = "\n          <ResultsNavCard onRestart={restart} />"
            src = src[:ci] + insert + src[ci:]

    return src


def patch_file(path: pathlib.Path) -> str:
    html = path.read_text(encoding="utf-8")
    m = re.search(
        r'(<script type="__bundler/manifest">)(.*?)(</script>)', html, re.DOTALL
    )
    if not m:
        return f"{path.name}: pas de manifest"
    manifest = json.loads(m.group(2))
    uuid = next((k for k in manifest if k.startswith(ASSET_UUID_PREFIX)), None)
    if uuid is None:
        return f"{path.name}: asset introuvable"
    entry = manifest[uuid]
    raw = base64.b64decode(entry["data"])
    comp = entry.get("compressed", False)
    src = gzip.decompress(raw).decode("utf-8") if comp else raw.decode("utf-8")

    if "ApiShareLinkPanel" not in src:
        return f"{path.name}: non câblé, sauté"
    if MARKER in src:
        return f"{path.name}: déjà v2, sauté"

    try:
        new_src = _patch_src(src)
    except ValueError as e:
        return f"{path.name}: ÉCHEC ({e})"
    nd = new_src.encode("utf-8")
    if comp:
        nd = gzip.compress(nd)
    entry["data"] = base64.b64encode(nd).decode("ascii")
    new_manifest = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[: m.start(2)] + new_manifest + html[m.end(2):]
    path.write_text(new_html, encoding="utf-8")
    shape = "proéminent" if GRAD in src else (
        "faint" if FAINT_OLD in src else "none"
    )
    return f"{path.name}: v2 [{shape}] ({len(src)} → {len(new_src)})"


def _is_clinical(name: str) -> bool:
    low = name.lower()
    return any(c in low for c in CLINICAL)


def main() -> None:
    if len(sys.argv) > 1:
        targets = [REPO / a for a in sys.argv[1:]]
    else:
        targets = sorted(REPO.glob("test-*.html")) + sorted(
            REPO.glob("Proxxie Test *.html")
        )
        targets = [p for p in targets if not _is_clinical(p.name)]
    for p in targets:
        if not p.exists():
            print(f"  {p.name}: absent")
            continue
        print(" ", patch_file(p))


if __name__ == "__main__":
    main()

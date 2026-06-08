#!/usr/bin/env python3
"""Réordonne et harmonise l'écran de résultats sur tous les tests câblés.

Trois problèmes corrigés (design-consultation, écran de résultats) :

1. Hiérarchie · l'encadré « Compare avec quelqu'un » (ApiShareLinkPanel) et le
   CTA « Sauvegarder mes résultats » trônaient AU-DESSUS du résultat, même
   couleur, sans hiérarchie. On remonte <Results> en premier (le payoff), on
   passe la sauvegarde en secondaire (outline), l'invitation à comparer
   redescend sous le résultat.

2. Repasser le test · l'option était absente sur 2 tests (dweck, via),
   discrète sur 8 (lien souligné terne), proéminente sur 6. On injecte une
   barre d'actions partagée identique en bas de CHAQUE test : « Voir tous les
   tests » (primaire) + « Repasser le test » (secondaire).

3. Cohérence · on retire les CTA de retake hétérogènes existants (ligne de
   boutons du panneau gradient proéminent · lien terne) pour que la barre
   partagée soit la seule source d'action. Le copy narratif des panneaux
   proéminents (« Le X, c'est une porte d'entrée… ») est conservé.

Transform en place sur le bundle gzip+base64, idempotent (skip si
ResultsActionsBar déjà présent). Cliniques (anxiete, phq9) exclus : cadrage
perception préservé, ils gardent leur retake existant.

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

# Barre d'actions partagée · primaire « Voir tous les tests » + secondaire
# « Repasser le test » (appelle onRestart = restart, qui efface le storage,
# remet mode "test" et scrolle en haut). Accent du test passé en prop.
RESULTS_BAR_JS = r"""
/* __proxxie_results_bar_v1__ · barre d'actions de fin de résultats, partagée */
const ResultsActionsBar = ({ accent = "#487AFF", onRestart }) => (
  <section style={{ paddingTop: 6, paddingBottom: 90 }}>
    <div className="shell" style={{ maxWidth: 820 }}>
      <div style={{ display: "flex", gap: 14, justifyContent: "center", alignItems: "center", flexWrap: "wrap", paddingTop: 34, borderTop: "1px solid var(--c-line)" }}>
        <a href="Proxxie Tests.html" className="btn btn-orange btn-lg btn-arrow">Voir tous les tests</a>
        <button onClick={onRestart} type="button" style={{ background: "white", border: "1.5px solid " + accent + "55", color: accent, padding: "13px 24px", borderRadius: 99, fontSize: 14, fontWeight: 600, cursor: "pointer" }}>Repasser le test</button>
      </div>
    </div>
  </section>
);
"""

# Style secondaire (outline) du bouton « Sauvegarder mes résultats ».
_SAVE_PAT = re.compile(
    r'onClick=\{openModal\} style=\{\{[^}]*?boxShadow: "0 4px 14px -4px " \+ accent \+ "55",',
    re.S,
)
_SAVE_NEW = (
    'onClick={openModal} style={{\n'
    '            background: "white", color: accent, border: "1.5px solid " + accent + "55",\n'
    '            padding: "13px 26px", borderRadius: 99,\n'
    '            fontSize: 14, fontWeight: 600, cursor: "pointer",\n'
    '            display: "inline-flex", alignItems: "center", gap: 10,\n'
    '            boxShadow: "none",'
)

# Ligne de boutons du panneau gradient proéminent (6 tests) · on la retire,
# le copy narratif au-dessus reste.
_PROMINENT_PAT = re.compile(
    r'\s*<div style=\{\{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" \}\}>'
    r'\s*<a href="Proxxie Tests\.html"[^>]*>Voir tous les tests</a>'
    r'\s*<button onClick=\{onRestart\}[^>]*>Refaire le test</button>'
    r'\s*</div>',
    re.S,
)

# Lien de retake terne (8 tests) · bloc isolé centré.
_FAINT_PAT = re.compile(
    r'\s*<div style=\{\{ textAlign: "center", marginTop: 30 \}\}>'
    r'\s*<button onClick=\{onRestart\}[^>]*>Refaire le test</button>'
    r'\s*</div>',
    re.S,
)

_OPENER = '{mode === "results" && results && (\n        <>\n'
_RESULTS_TAG = "<Results results={results} onRestart={restart} />"
_BRANCH_CLOSE = "\n        </>\n      )}"


def _patch_src(src: str) -> str:
    if _OPENER not in src:
        raise ValueError("branche results introuvable")
    if _RESULTS_TAG not in src:
        raise ValueError("tag Results introuvable")
    if "const TestApp = () => {" not in src:
        raise ValueError("anchor TestApp introuvable")

    accent_m = re.search(
        r'<EmailResultsActions[^>]*accent="(#[0-9A-Fa-f]{3,8})"', src
    )
    accent = accent_m.group(1) if accent_m else "#487AFF"

    # A · sauvegarde → secondaire (outline). Non bloquant si absent.
    if _SAVE_PAT.search(src):
        src = _SAVE_PAT.sub(_SAVE_NEW, src, count=1)

    # E · retire la ligne de boutons du panneau proéminent (si présente).
    src = _PROMINENT_PAT.sub("", src, count=1)
    # F · retire le lien de retake terne (si présent).
    src = _FAINT_PAT.sub("", src, count=1)

    # B · réordonne : <Results> en premier enfant de la branche results.
    src = re.sub(r"\n\s*" + re.escape(_RESULTS_TAG), "", src, count=1)
    src = src.replace(_OPENER, _OPENER + "          " + _RESULTS_TAG + "\n", 1)

    # C · définit ResultsActionsBar juste avant TestApp.
    src = src.replace(
        "const TestApp = () => {",
        RESULTS_BAR_JS + "\nconst TestApp = () => {",
        1,
    )

    # D · rend la barre comme dernier enfant de la branche results.
    oi = src.index(_OPENER)
    ci = src.index(_BRANCH_CLOSE, oi)
    insert = (
        '\n          <ResultsActionsBar accent="' + accent
        + '" onRestart={restart} />'
    )
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
    if "ResultsActionsBar" in src:
        return f"{path.name}: déjà harmonisé, sauté"

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
    return f"{path.name}: harmonisé ({len(src)} → {len(new_src)})"


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

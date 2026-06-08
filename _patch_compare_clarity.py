"""Clarify the comparison flow on Future-Proof results/hub.

Three user-reported gaps:
  1. "Je n'ai pas trouvé de code PXC nulle part." The share flow only ever
     produces a LINK, never a bare code, yet the hub asks for a code. Fix:
     the hub input now accepts a pasted LINK (we extract ?code=), and an
     explainer tells the user where the link/code comes from.
  2. On a comparison results page, nothing separates the COMPARISON block
     from the user's OWN results. Fix: add a "Comparaison" section band
     above ComparePanel and a "Tes résultats" band before the personal
     results.
  3. No CTA between comparison and results. Fix: insert a "Réserver 30 min
     avec Charles" CTA (existing calendly.com/proxxie/entretien) between
     the comparison and the personal results, shown only in self_compare.

Idempotent: skips a file that already carries CLARITY_MARKER.
In-place on the gzip+base64 bundle, matching _patch_compare_interpretive.py.
Future-Proof only for now; generalise to other tests after sign-off.
"""
from __future__ import annotations

import base64
import gzip
import json
import pathlib
import re

ASSET_UUID_PREFIX = "61feca88"
CLARITY_MARKER = "__proxxie_compare_clarity_v1__"
ACCENT = "#C2410C"
BOOK_URL = "https://calendly.com/proxxie/entretien"

TARGETS = ("test-futureproof.html", "Proxxie Test FuturProof.html")

# --- Edit 1: hub resolver accepts a pasted link (extract ?code=) -------------
OLD_RESOLVE = (
    '  const code = (codeRaw || "").trim().toUpperCase();\n'
    '  if (!code) return Promise.reject(new Error("Colle un code PXC."));'
)
NEW_RESOLVE = (
    '  const _m = (codeRaw || "").trim().match(/code=([^&\\s]+)/i);\n'
    '  const code = (_m ? decodeURIComponent(_m[1]) : (codeRaw || "")).trim().toUpperCase();\n'
    '  if (!code) return Promise.reject(new Error("Colle le lien ou le code qu\'on t\'a envoyé."));'
)

# --- Edit 2: hub explainer (where does the link/code come from?) -------------
OLD_SUBTITLE = (
    "Fournis deux coordonnées qui portent sur le même test. On affiche les deux profils côte à côte.\n"
    "          </p>"
)
EXPLAINER = (
    'Fournis deux coordonnées qui portent sur le même test. On affiche les deux profils côte à côte.\n'
    '          </p>\n'
    '          <div style={{ marginTop: 18, padding: "14px 18px", borderRadius: 14, background: "rgba(253,105,54,.07)", '
    'border: "1px solid #FCE0CC", fontSize: 13.5, color: "var(--c-ink-2)", lineHeight: 1.6, maxWidth: 480, '
    'margin: "18px auto 0", textAlign: "left" }}>\n'
    '            <strong style={{ color: "var(--c-ink)" }}>Où trouver le lien ou le code ?</strong> Il est créé par la '
    'personne avec qui tu compares : elle passe le test, puis partage le lien généré à la fin. Colle ce lien (ou le code '
    '<span style={{ fontFamily: "var(--font-mono, monospace)", letterSpacing: "0.04em" }}>PXC-XXXX</span> qu\'il contient) '
    'dans la case 1.\n'
    '          </div>'
)

# --- Edit 3: reword slot 1 hint ---------------------------------------------
OLD_SLOT1 = '{slotCard("1", "L\'autre personne", "Colle le code PXC qu\'on t\'a envoyé.",'
NEW_SLOT1 = '{slotCard("1", "L\'autre personne", "Colle le lien (ou le code) qu\'on t\'a envoyé.",'

# --- Edit 4: section band + Charles CTA around the comparison panel ----------
OLD_COMPARE_RE = re.compile(
    r'\{effectivePersona === "self_compare" && PARENT_PREDICT && PARENT_PREDICT\.a && '
    r'\(<section.*?</section>\)\}',
    re.DOTALL,
)


def _new_compare_block(original: str) -> str:
    band = (
        '{/* ' + CLARITY_MARKER + ' */}\n'
        '          {effectivePersona === "self_compare" && PARENT_PREDICT && (\n'
        '            <section style={{ paddingTop: 44, paddingBottom: 0 }}>\n'
        '              <div className="shell" style={{ maxWidth: 820, textAlign: "center" }}>\n'
        '                <span className="eyebrow"><span className="dot"></span>Comparaison</span>\n'
        '                <h2 style={{ marginTop: 12, fontSize: 28, color: "var(--c-ink)" }}>'
        '{PARENT_PREDICT.mode === "predict" ? "Sa prédiction face à tes réponses" : "Vous deux, côte à côte"}</h2>\n'
        '                <p style={{ fontSize: 15, color: "var(--c-ink-2)", lineHeight: 1.6, maxWidth: 540, '
        'margin: "10px auto 0" }}>Voici d\'abord la comparaison. Tes résultats détaillés à toi suivent juste en dessous.</p>\n'
        '              </div>\n'
        '            </section>\n'
        '          )}\n'
        '          '
    )
    cta = (
        '\n'
        '          {effectivePersona === "self_compare" && PARENT_PREDICT && PARENT_PREDICT.a && (\n'
        '            <section style={{ paddingTop: 36, paddingBottom: 8 }}>\n'
        '              <div className="shell" style={{ maxWidth: 820 }}>\n'
        '                <div style={{ background: "linear-gradient(135deg, #FFF7ED, #FFEAD9)", border: "1px solid #FED7AA", '
        'borderRadius: 20, padding: "30px 32px", display: "flex", gap: 24, alignItems: "center", flexWrap: "wrap" }}>\n'
        '                  <div style={{ flex: 1, minWidth: 240 }}>\n'
        '                    <h3 style={{ fontSize: 21, marginBottom: 8, color: "var(--c-ink)" }}>'
        'Envie d\'aller plus loin que les chiffres ?</h3>\n'
        '                    <p style={{ fontSize: 14.5, color: "var(--c-ink-2)", lineHeight: 1.6, margin: 0 }}>'
        'Décryptez ces écarts ensemble. 30 min avec Charles pour transformer cette comparaison en pistes concrètes, '
        'le premier cadrage est offert.</p>\n'
        '                  </div>\n'
        '                  <a href="' + BOOK_URL + '" target="_blank" rel="noopener noreferrer" '
        'className="btn btn-orange btn-lg btn-arrow" style={{ background: "' + ACCENT + '", textDecoration: "none", '
        'whiteSpace: "nowrap" }}>Réserver 30 min avec Charles</a>\n'
        '                </div>\n'
        '              </div>\n'
        '            </section>\n'
        '          )}'
    )
    return band + original + cta


# --- Edit 5: "Tes résultats" band before the personal results toolbar --------
OLD_TOPACTIONS_RE = re.compile(r'\n(\s*)<ResultsTopActions testCode=')


def _new_topactions(m: re.Match) -> str:
    indent = m.group(1)
    band = (
        '\n' + indent + '{effectivePersona === "self_compare" && (\n'
        + indent + '  <section style={{ paddingTop: 48, paddingBottom: 0 }}>\n'
        + indent + '    <div className="shell" style={{ maxWidth: 820, textAlign: "center" }}>\n'
        + indent + '      <span className="eyebrow"><span className="dot"></span>Tes résultats</span>\n'
        + indent + '      <h2 style={{ marginTop: 12, fontSize: 28, color: "var(--c-ink)" }}>Ton profil en détail</h2>\n'
        + indent + '      <p style={{ fontSize: 15, color: "var(--c-ink-2)", lineHeight: 1.6, maxWidth: 540, '
        'margin: "10px auto 0" }}>Indépendamment de la comparaison, voici ce que ton test révèle sur toi.</p>\n'
        + indent + '    </div>\n'
        + indent + '  </section>\n'
        + indent + ')}\n'
        + indent + '<ResultsTopActions testCode='
    )
    return band


def _patch_src(src: str) -> str:
    if CLARITY_MARKER in src:
        return src
    if OLD_RESOLVE not in src:
        raise RuntimeError("resolve anchor not found")
    if OLD_SUBTITLE not in src:
        raise RuntimeError("subtitle anchor not found")
    if OLD_SLOT1 not in src:
        raise RuntimeError("slot1 anchor not found")
    if not OLD_COMPARE_RE.search(src):
        raise RuntimeError("compare-panel anchor not found")
    if not OLD_TOPACTIONS_RE.search(src):
        raise RuntimeError("ResultsTopActions anchor not found")

    src = src.replace(OLD_RESOLVE, NEW_RESOLVE, 1)
    src = src.replace(OLD_SUBTITLE, EXPLAINER, 1)
    src = src.replace(OLD_SLOT1, NEW_SLOT1, 1)
    src = OLD_COMPARE_RE.sub(lambda m: _new_compare_block(m.group(0)), src, count=1)
    src = OLD_TOPACTIONS_RE.sub(_new_topactions, src, count=1)
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
    comp = bool(entry.get("compressed"))
    src = gzip.decompress(raw).decode("utf-8") if comp else raw.decode("utf-8")

    if CLARITY_MARKER in src:
        return f"{path.name}: deja clarifie (skip)"

    new_src = _patch_src(src)
    if new_src == src:
        return f"{path.name}: aucun changement"

    nd = new_src.encode("utf-8")
    if comp:
        nd = gzip.compress(nd)
    entry["data"] = base64.b64encode(nd).decode("ascii")
    new_manifest = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[: m.start(2)] + new_manifest + html[m.end(2):]
    path.write_text(new_html, encoding="utf-8")
    return f"{path.name}: PATCHED"


def main() -> None:
    root = pathlib.Path(".")
    for name in TARGETS:
        p = root / name
        if not p.exists():
            print(f"{name}: absent")
            continue
        print(patch_file(p))


if __name__ == "__main__":
    main()

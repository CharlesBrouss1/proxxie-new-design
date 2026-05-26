#!/usr/bin/env python3
"""Ouvre 6 tests qui étaient gated par requiresAuth: true.

Demandé par Charles : PCM, MBTI, Drivers, Valeurs, Besoins, DYS doivent être
accessibles sans création de compte. Le CTA affichera « Démarrer » au lieu
de « Inscription requise », et le href pointera vers le test direct.

Les autres tests (OCEAN-X, RIASEC, TDAH, Autisme, Anxiété, HPI) restent
gated par inscription.

Cible : Proxxie Tests.html + tests.html (legacy)
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
ASSET_UUID_PREFIX = "61feca88"

TARGETS = [
    "Proxxie Tests.html",
    "tests.html",
]

# Codes des 6 tests à ouvrir
OPEN_CODES = ["PCM", "MBTI", "Drivers", "Valeurs", "Besoins", "DYS"]


def patch_src(src: str) -> tuple[str, list[str]]:
    changes = []
    for code in OPEN_CODES:
        # Cible le motif exact « code: "X", requiresAuth: true, » (avec espaces variables)
        # On accepte des espaces multiples entre code et requiresAuth.
        pattern = re.compile(rf'(code:\s*"{re.escape(code)}",\s*)requiresAuth:\s*true(\s*,)')
        new_src, n = pattern.subn(rf'\1requiresAuth: false\2', src)
        if n > 0:
            src = new_src
            changes.append(f"{code} ouvert ({n}x)")
    return src, changes


def patch_one(target: pathlib.Path) -> str:
    if not target.exists():
        return f"{target.name}: file not found"
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
    if not changes:
        return f"{target.name}: aucun changement (déjà ouvert ou codes absents)"
    nd = new_src.encode('utf-8')
    if comp:
        nd = gzip.compress(nd)
    entry['data'] = base64.b64encode(nd).decode('ascii')
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]
    target.write_text(new_html, encoding='utf-8')
    return f"{target.name}: {', '.join(changes)}"


if __name__ == "__main__":
    for fn in TARGETS:
        print(patch_one(REPO / fn))

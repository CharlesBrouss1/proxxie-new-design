#!/usr/bin/env python3
"""Met à jour le compteur de tests dans la navigation (onglet Ressources)
de TOUTES les pages bundlées.

Le NAV_RESOURCES est dupliqué dans chaque bundle (chaque page a sa propre
copie du JS de nav). Le patch _patch_add_4_tests.py n'a touché que
Proxxie Tests.html. Les autres pages affichent encore "12 tests".

Stratégie : scanner tous les assets JavaScript de chaque manifest bundlé,
faire les remplacements de strings, ré-encoder.

Idempotent : les nouvelles strings ne re-match pas les anciennes.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent

# Remplacements à appliquer dans tous les assets JS de toutes les pages
# (ordre : du plus spécifique au plus générique pour éviter les sur-remplacements)
REPLACEMENTS = [
    # NAV_RESOURCES · description complète des 12 tests
    (
        '"12 tests : OCEAN, RIASEC, PCM, MBTI, Drivers, Valeurs, Besoins, TDAH, Autisme, HPI, Anxiété, DYS."',
        '"16 tests : OCEAN, RIASEC, Raisonnement, Grit, CAAS, PCM, MBTI, Drivers, Valeurs, Besoins, TDAH, Autisme, HPI, Anxiété, Dépression, DYS."',
    ),
    # NAV_RESOURCES · badge "12 tests · gratuit"
    (
        'badge: "12 tests · gratuit"',
        'badge: "16 tests · gratuit"',
    ),
    # Variantes potentielles si le compteur apparaît ailleurs
    (
        '"12 tests psychométriques"',
        '"16 tests psychométriques"',
    ),
    (
        '12 tests · 100% gratuits · sans inscription',
        '16 tests · 100% gratuits · sans inscription',
    ),
]


def patch_asset_src(src: str) -> tuple[str, list[str]]:
    """Applique les remplacements. Retourne (new_src, list de changements)."""
    changes = []
    new_src = src
    for old, new in REPLACEMENTS:
        if old in new_src:
            new_src = new_src.replace(old, new)
            changes.append(old[:50] + "...")
    return new_src, changes


def patch_one(target: pathlib.Path) -> str:
    if not target.exists():
        return f"{target.name}: file not found"
    html = target.read_text(encoding="utf-8")
    m = re.search(r'(<script type="__bundler/manifest">)(.*?)(</script>)', html, re.DOTALL)
    if not m:
        return f"{target.name}: pas de manifest"
    manifest = json.loads(m.group(2))
    total_changes = []
    modified_assets = 0
    for uuid, entry in manifest.items():
        if 'javascript' not in entry.get('mime', ''):
            continue
        raw = base64.b64decode(entry['data'])
        comp = entry.get('compressed', False)
        try:
            src = gzip.decompress(raw).decode('utf-8') if comp else raw.decode('utf-8')
        except Exception:
            continue
        new_src, changes = patch_asset_src(src)
        if new_src == src:
            continue
        nd = new_src.encode('utf-8')
        if comp:
            nd = gzip.compress(nd)
        entry['data'] = base64.b64encode(nd).decode('ascii')
        total_changes.extend(changes)
        modified_assets += 1
    if not total_changes:
        return f"{target.name}: aucun changement (déjà à jour ou strings absentes)"
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]
    target.write_text(new_html, encoding='utf-8')
    return f"{target.name}: patched {modified_assets} asset(s), {len(total_changes)} remplacement(s)"


if __name__ == "__main__":
    # Toutes les pages bundlées (Proxxie *.html + twins lowercase)
    targets = sorted(p.name for p in REPO.glob("*.html") if not p.name.startswith("_"))
    for fn in targets:
        print(patch_one(REPO / fn))

#!/usr/bin/env python3
"""Retire le blocage « 2 tests gratuits avant inscription » (inverse de _patch_quota_2_tests.py).

Demande de Charles (2026-06-15) : enlever le mur d'inscription à 2 tests pour le moment.
Les tests restent tous ouverts (requiresAuth reste false), mais :
  1. On supprime le helper _proxxieCheckQuota / _proxxieCount... (sentinelles BEGIN/END).
  2. On retire le rendu <ProxxieQuotaBanner />.
  3. On nettoie le onClick quota sur la carte de test (garde seulement la logique `bientot`).
  4. On corrige le chip du hero pour ne plus promettre une limite de 2 tests.

Réversible : pour restaurer le mur, relancer
    python3 _patch_quota_2_tests.py && python3 _fix_access_copy.py

Idempotent · écrit un .bak horodaté la première fois.
"""
import re, json, base64, gzip, pathlib, datetime

REPO = pathlib.Path(__file__).parent
ASSET_UUID_PREFIX = "61feca88"
TARGETS = ["Proxxie Tests.html", "tests.html"]

BEGIN_HELPER = "/* PROXXIE_QUOTA_HELPER_BEGIN */"
END_HELPER   = "/* PROXXIE_QUOTA_HELPER_END */"

# onClick quota injecté par _patch_quota_2_tests.py (variante "bientot")
TESTCARD_QUOTA_HREF_BIENTOT = (
    '<a href={t.bientot ? "#" : t.href} onClick={(e) => { if (t.bientot) '
    '{ e.preventDefault(); return; } _proxxieCheckQuota(e, t.href); }} style={{'
)
# version nettoyée : garde la gestion `bientot`, retire le quota
TESTCARD_CLEAN_HREF_BIENTOT = (
    '<a href={t.bientot ? "#" : t.href} '
    'onClick={t.bientot ? (e) => e.preventDefault() : undefined} style={{'
)

# variante simple (legacy tests.html)
TESTCARD_QUOTA_HREF_SIMPLE = '<a href={t.href} onClick={(e) => _proxxieCheckQuota(e, t.href)} style={{'
TESTCARD_CLEAN_HREF_SIMPLE = '<a href={t.href} style={{'

# Chip du hero : ne plus annoncer la limite « 2 gratuits sans compte »
CHIP_OLD = "2 gratuits sans compte · inscription gratuite pour la suite"
CHIP_NEW = "tous gratuits, sans compte"


def strip_between(src: str, begin: str, end: str) -> str:
    pat = re.compile(r'\s*' + re.escape(begin) + r'.*?' + re.escape(end), re.DOTALL)
    return pat.sub('', src)


def patch_src(src: str) -> tuple[str, list[str]]:
    changes = []

    if BEGIN_HELPER in src:
        src = strip_between(src, BEGIN_HELPER, END_HELPER)
        changes.append("- helper _proxxieCheckQuota + ProxxieQuotaBanner")

    # retire le rendu du banner
    new = re.sub(r'\n\s*<ProxxieQuotaBanner\s*/>\s*', '\n', src)
    if new != src:
        src = new
        changes.append("- rendu <ProxxieQuotaBanner />")

    # nettoie le onClick quota sur la carte
    if TESTCARD_QUOTA_HREF_BIENTOT in src:
        src = src.replace(TESTCARD_QUOTA_HREF_BIENTOT, TESTCARD_CLEAN_HREF_BIENTOT, 1)
        changes.append("TestCard onClick quota retiré (variante bientot)")
    elif TESTCARD_QUOTA_HREF_SIMPLE in src:
        src = src.replace(TESTCARD_QUOTA_HREF_SIMPLE, TESTCARD_CLEAN_HREF_SIMPLE, 1)
        changes.append("TestCard onClick quota retiré")

    # corrige le chip du hero
    if CHIP_OLD in src:
        src = src.replace(CHIP_OLD, CHIP_NEW, 1)
        changes.append("chip hero corrigé (plus de limite annoncée)")

    return src, changes


def patch_one(target: pathlib.Path) -> str:
    if not target.exists():
        return f"{target.name}: introuvable (skip)"
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
    if new_src == src or not changes:
        return f"{target.name}: aucun changement (déjà retiré ?)"

    bak = target.with_suffix(target.suffix + f".bak-quota-{datetime.date.today():%Y%m%d}")
    if not bak.exists():
        bak.write_text(html, encoding="utf-8")

    nd = new_src.encode('utf-8')
    if comp:
        nd = gzip.compress(nd)
    entry['data'] = base64.b64encode(nd).decode('ascii')
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]
    target.write_text(new_html, encoding='utf-8')
    return f"{target.name}: [{', '.join(changes)}] (bak: {bak.name})"


if __name__ == "__main__":
    for fn in TARGETS:
        print(patch_one(REPO / fn))

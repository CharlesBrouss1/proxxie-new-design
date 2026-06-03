#!/usr/bin/env python3
"""Align the access-policy copy with what the code actually enforces.

Reality: every test has requiresAuth=false (all 16 openly accessible). The only
gate is PROXXIE_FREE_TESTS=2 — an anonymous user completes 2 tests, then a free
signup is needed to continue and to save results. Data stays local.

Old copy was wrong and inconsistent:
- Catalogue: "3 en accès libre, les autres demandent une inscription gratuite"
  (+ "Dix-sept tests" contradicting the chip's "16").
- Dashboard: "OCEAN-X et RIASEC en accès libre, les autres après le 1er RDV".

Edits the relevant manifest asset per file, asserting each target appears
exactly once before replacing, then re-encodes preserving compression.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
CAT = "61feca88-84c8-4b75-a93b-7138c831ebd9"
DASH_PREFIX = "5a278f70"

CHIP_OLD = "16 tests · 3 en accès libre · inscription gratuite pour les autres"
CHIP_NEW = "16 tests · 2 gratuits sans compte · inscription gratuite pour la suite"

INTRO_NEW = ("Seize tests répartis en 2 catégories : 10 tests d'orientation "
             "(personnalité, intérêts, raisonnement, persévérance, adaptabilité) ; "
             "6 screenings santé mentale et apprentissage (TDAH, autisme, HPI, anxiété, "
             "dépression, DYS). Les 16 tests sont en accès libre : passez-en 2 sans compte, "
             "puis créez un compte gratuit pour passer les autres et retrouver vos résultats. "
             "Vos données restent stockées en local.")

INTRO_OLD_CANON = ("Dix-sept tests répartis en 2 catégories : 10 tests d'orientation "
                   "(personnalité, intérêts, raisonnement, persévérance, adaptabilité) ; "
                   "6 screenings santé mentale et apprentissage (TDAH, autisme, HPI, anxiété, "
                   "dépression, DYS). Trois tests en accès libre (Raisonnement, Adaptabilité "
                   "Carrière, HPI). Les autres demandent une inscription gratuite. Tous les "
                   "tests restent gratuits et vos données sont stockées en local.")

INTRO_OLD_STALE = ("Douze tests répartis en 2 catégories : 7 tests psychométriques pour cerner "
                   "personnalité, intérêts et motivations ; 5 screenings pour identifier "
                   "d'éventuels traits TDAH, autisme, HPI, anxiété ou troubles DYS. Le test HPI "
                   "est en accès libre. Les autres demandent une inscription gratuite. Vos "
                   "données restent stockées en local.")

DASH_OLD = ("<strong>OCEAN-X et RIASEC</strong> sont en accès libre. Les autres tests se "
            "débloquent après le premier RDV de cadrage avec Charles.")
DASH_NEW = ("<strong>Tes 16 tests</strong> sont en accès libre, sans RDV préalable. "
            "Tes résultats sont sauvegardés sur ton compte.")

# file -> (asset uid-or-prefix, [(old, new), ...])
JOBS = {
    "Proxxie Tests.html":     (CAT, [(CHIP_OLD, CHIP_NEW), (INTRO_OLD_CANON, INTRO_NEW)]),
    "tests.html":             (CAT, [(CHIP_OLD, CHIP_NEW), (INTRO_OLD_STALE, INTRO_NEW)]),
    "Proxxie Dashboard.html": (DASH_PREFIX, [(DASH_OLD, DASH_NEW)]),
    "dashboard.html":         (DASH_PREFIX, [(DASH_OLD, DASH_NEW)]),
}

def resolve(manifest, key):
    if key in manifest:
        return key
    for k in manifest:
        if k.startswith(key):
            return k
    raise SystemExit(f"asset {key} not found")

for fname, (key, repls) in JOBS.items():
    path = REPO / fname
    html = path.read_text(encoding="utf-8")
    m = re.search(r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)', html, re.DOTALL)
    if not m:
        raise SystemExit(f"{fname}: manifest not found")
    manifest = json.loads(m.group(2))
    uid = resolve(manifest, key)
    entry = manifest[uid]
    data = base64.b64decode(entry["data"])
    if entry.get("compressed", False):
        data = gzip.decompress(data)
    txt = data.decode("utf-8")

    for old, new in repls:
        n = txt.count(old)
        if n != 1:
            raise SystemExit(f"{fname}: target count {n} != 1 for: {old[:60]!r}")
        txt = txt.replace(old, new, 1)

    # sanity: no stale phrases left, new ones present
    for bad in ("demandent une inscription", "se débloquent après le premier RDV", "3 en accès libre"):
        if bad in txt:
            raise SystemExit(f"{fname}: stale phrase still present: {bad!r}")

    out = txt.encode("utf-8")
    if entry.get("compressed", False):
        out = gzip.compress(out)
    entry["data"] = base64.b64encode(out).decode("ascii")
    new_manifest = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    path.write_text(html[:m.start(2)] + new_manifest + html[m.end(2):], encoding="utf-8")
    print(f"OK {fname}: {len(repls)} replacement(s) in asset {uid[:8]}")

print("done")

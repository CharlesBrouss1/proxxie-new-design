#!/usr/bin/env python3
"""Câble un test existant (pont statique → pont API pair symétrique) en place.

Les 11 tests restants (anxiete, autisme, besoins, drivers, dys, hpi, mbti,
pcm, riasec, tdah, valeurs) ont déjà le pont statique #predict= + leur propre
ComparePanel dans leur format. Ce script applique le même transform que les
6 tests déjà câblés (brief/caas/dweck/grit/via/futureproof) :

  patch_persona_intro(prefix) + wire_bridge(block, test_id, page_filename)

Transform en place sur le bundle gzip+base64 du HTML déjà construit. Garde
d'idempotence : un fichier déjà câblé (ApiShareLinkPanel présent) est sauté.

Usage:
  python3 _patch_wire_remaining.py            # câble les 11 d'un coup
  python3 _patch_wire_remaining.py valeurs    # câble un seul test
"""
import re
import json
import base64
import gzip
import pathlib
import sys
import _bridge_common

REPO = pathlib.Path(__file__).parent
ASSET_UUID_PREFIX = "61feca88"

# test_id (minuscule, = __PROXXIE_TEST_ID__) -> nom PascalCase du fichier.
# NB · "Proxxie Test Anxiete.html" est la SOURCE clonée par les 6 patchers
# _patch_build_*.py : on ne la câble PAS en place (sinon patch_persona_intro
# casserait la ré-exécution des 6). De plus anxiete + phq9 sont cliniques
# (item suicide, 3114) -> on les garde en cadre perception, pas de comparaison
# pair grand public. Ils ne sont donc pas dans cette liste.
TESTS = {
    "autisme": "Autisme",
    "besoins": "Besoins",
    "drivers": "Drivers",
    "dys": "DYS",
    "hpi": "HPI",
    "mbti": "MBTI",
    "pcm": "PCM",
    "riasec": "RIASEC",
    "tdah": "TDAH",
    "valeurs": "Valeurs",
}


def wire_file(path: pathlib.Path, test_id: str, page_filename: str) -> str:
    if not path.exists():
        return f"{path.name}: absent"
    html = path.read_text(encoding="utf-8")
    m = re.search(r'(<script type="__bundler/manifest">)(.*?)(</script>)', html, re.DOTALL)
    if not m:
        return f"{path.name}: pas de manifest"
    manifest = json.loads(m.group(2))
    uuid = next((k for k in manifest if k.startswith(ASSET_UUID_PREFIX)), None)
    if uuid is None:
        return f"{path.name}: asset {ASSET_UUID_PREFIX} introuvable"
    entry = manifest[uuid]
    raw = base64.b64decode(entry["data"])
    comp = entry.get("compressed", False)
    src = gzip.decompress(raw).decode("utf-8") if comp else raw.decode("utf-8")

    if "ApiShareLinkPanel" in src:
        return f"{path.name}: déjà câblé, sauté"

    boundary = re.search(r"(/\*\s*Test Proxxie [^/]*\*/\s*\n)?const QUESTIONS\s*=", src)
    if not boundary:
        return f"{path.name}: boundary introuvable"

    prefix = src[: boundary.start()]
    block = src[boundary.start():]
    new_src = _bridge_common.patch_persona_intro(prefix) + _bridge_common.wire_bridge(
        block, test_id, page_filename
    )

    nd = new_src.encode("utf-8")
    if comp:
        nd = gzip.compress(nd)
    entry["data"] = base64.b64encode(nd).decode("ascii")
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[: m.start(2)] + new_manifest_json + html[m.end(2):]
    path.write_text(new_html, encoding="utf-8")
    return f"{path.name}: câblé ({len(src)} → {len(new_src)})"


def wire_test(test_id: str) -> None:
    pascal = TESTS[test_id]
    page = "Proxxie%20Test%20" + pascal + ".html"
    print(f"=== {test_id} ===")
    print(" ", wire_file(REPO / f"Proxxie Test {pascal}.html", test_id, page))
    print(" ", wire_file(REPO / f"test-{test_id}.html", test_id, page))


if __name__ == "__main__":
    targets = sys.argv[1:] if len(sys.argv) > 1 else list(TESTS.keys())
    for t in targets:
        if t not in TESTS:
            print(f"!! test inconnu: {t} (connus: {', '.join(TESTS)})")
            continue
        wire_test(t)

#!/usr/bin/env python3
"""Remplace l'intégralité du composant `QuickExample` dans le bundle React
de Proxxie Home.html / index.html par la version enrichie stockée dans
`_qe_new.jsx` (rapport d'orientation complet, 12 sections, narratif coach
+ voix de Léa, arbitrages explicites).

L'asset visé est UUID 3cf76be5-... (mêmes assets dans les deux fichiers).
Le composant est délimité par :
  - début :  "\nconst QuickExample = "
  - fin :    le prochain "\nconst " / "\nfunction " / "\nexport " de niveau 0.

Re-runnable. Idempotent (compare avant d'écrire).
"""
from __future__ import annotations

import re, json, base64, gzip, pathlib, sys

REPO = pathlib.Path(__file__).parent
NEW_COMPONENT_PATH = REPO / "_qe_new.jsx"
ASSET_UUID = "3cf76be5-cba3-403c-b219-8836e7b32e4d"
TARGET_FILES = ["Proxxie Home.html", "index.html"]


def find_component_span(text: str) -> tuple[int, int] | None:
    """Returns (start, end) byte offsets of the QuickExample component, or None."""
    m = re.search(r"\nconst QuickExample = ", text)
    if not m:
        return None
    start = m.start() + 1  # skip the leading newline
    # End = next top-level definition. Search after the opening brace's body.
    m2 = re.search(r"\n(const|function|export)\s", text[start + 20:])
    if not m2:
        end = len(text)
    else:
        end = start + 20 + m2.start() + 1  # include trailing newline before next decl
    return start, end


def patch_asset_text(text: str, new_component: str) -> tuple[str, bool]:
    span = find_component_span(text)
    if not span:
        return text, False
    start, end = span
    current = text[start:end].rstrip("\n") + "\n"
    new = new_component.rstrip("\n") + "\n"
    if current == new:
        return text, False
    return text[:start] + new + text[end:], True


def patch_file(path: pathlib.Path, new_component: str) -> bool:
    html = path.read_text(encoding="utf-8")
    m = re.search(
        r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)',
        html,
        re.DOTALL,
    )
    if not m:
        print(f"  no manifest in {path.name}")
        return False

    manifest = json.loads(m.group(2))
    if ASSET_UUID not in manifest:
        print(f"  asset {ASSET_UUID} missing in {path.name}")
        return False

    entry = manifest[ASSET_UUID]
    data = base64.b64decode(entry["data"])
    compressed = entry.get("compressed", False)
    if compressed:
        data = gzip.decompress(data)
    text = data.decode("utf-8")

    new_text, changed = patch_asset_text(text, new_component)
    if not changed:
        print(f"  asset {ASSET_UUID} in {path.name}: already up to date")
        return False

    # Re-encode
    new_data = new_text.encode("utf-8")
    if compressed:
        new_data = gzip.compress(new_data)
    entry["data"] = base64.b64encode(new_data).decode("ascii")

    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[: m.start(2)] + new_manifest_json + html[m.end(2):]
    path.write_text(new_html, encoding="utf-8")
    delta = len(new_text) - len(text)
    print(
        f"  ✓ {path.name}: QuickExample rewritten "
        f"(asset {len(text)} → {len(new_text)} bytes, Δ {delta:+d})"
    )
    return True


def main() -> int:
    if not NEW_COMPONENT_PATH.exists():
        print(f"Missing source: {NEW_COMPONENT_PATH}")
        return 1
    new_component = NEW_COMPONENT_PATH.read_text(encoding="utf-8")
    any_changed = False
    for fn in TARGET_FILES:
        p = REPO / fn
        if not p.exists():
            print(f"skip (missing): {fn}")
            continue
        print(f"Processing: {fn}")
        if patch_file(p, new_component):
            any_changed = True
    return 0 if any_changed or True else 1


if __name__ == "__main__":
    sys.exit(main())

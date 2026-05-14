#!/usr/bin/env python3
"""Patch bundled HTML files in this repo to redirect the
'Le guide de l'orientation' menu link to ./guide-orientation.html.

Re-runnable. Idempotent. Only modifies the manifest entries that
contain the literal `inscription-newsletter` URL.
"""
import re, json, base64, gzip, sys, pathlib, shutil

REPO = pathlib.Path(__file__).parent

# Each patch: (search-needle, list-of-replacements-to-try)
# A file's asset is rewritten if ANY of the needles is found.
PATCHES = [
    {
        "needle": "https://www.proxxie.co/inscription-newsletter",
        "replacements": [
            ("https://www.proxxie.co/inscription-newsletter", "./guide-orientation.html"),
        ],
        # extra regex pass: flip external:true → false on the patched item
        "regex": (
            r'(n: "Le guide de l\'orientation",\s*d: "[^"]*",\s*href: "\./guide-orientation\.html",\s*external:\s*)true',
            r'\1false',
        ),
    },
    {
        "needle": "Parler à Charles",
        "replacements": [
            ("Parler à Charles", "Rdv avec Charles"),
        ],
        "regex": None,
    },
]

def patch_file(path: pathlib.Path) -> bool:
    """Returns True if file was modified."""
    html = path.read_text(encoding="utf-8")

    m = re.search(r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)', html, re.DOTALL)
    if not m:
        print(f"  no manifest in {path.name}")
        return False

    manifest = json.loads(m.group(2))
    changed = False
    for uuid, entry in manifest.items():
        data = base64.b64decode(entry["data"])
        compressed = entry.get("compressed", False)
        if compressed:
            try:
                data = gzip.decompress(data)
            except Exception:
                continue

        # Check if any patch applies
        applicable = [p for p in PATCHES if p["needle"].encode() in data]
        if not applicable:
            continue

        text = data.decode("utf-8")
        for p in applicable:
            for old, new in p["replacements"]:
                text = text.replace(old, new)
            if p["regex"]:
                text = re.sub(p["regex"][0], p["regex"][1], text)

        new_data = text.encode("utf-8")
        if compressed:
            new_data = gzip.compress(new_data)
        entry["data"] = base64.b64encode(new_data).decode("ascii")
        changed = True
        names = ", ".join(p["needle"][:30] for p in applicable)
        print(f"  patched asset {uuid} [{names}] in {path.name}")

    if not changed:
        return False

    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]
    path.write_text(new_html, encoding="utf-8")
    return True

if __name__ == "__main__":
    files = ["Proxxie Home.html", "index.html"]
    for fn in files:
        p = REPO / fn
        if not p.exists():
            print(f"skip (missing): {fn}")
            continue
        print(f"Processing: {fn}")
        if patch_file(p):
            print(f"  ✓ modified {fn}")
        else:
            print(f"  - no change to {fn} (already patched or URL not found)")

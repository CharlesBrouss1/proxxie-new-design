#!/usr/bin/env python3
"""Patch bundled HTML files in this repo to redirect the
'Le guide de l'orientation' menu link to ./guide-orientation.html.

Re-runnable. Idempotent. Only modifies the manifest entries that
contain the literal `inscription-newsletter` URL.
"""
import re, json, base64, gzip, sys, pathlib, shutil

REPO = pathlib.Path(__file__).parent
OLD_URL = "https://www.proxxie.co/inscription-newsletter"
NEW_URL = "./guide-orientation.html"

def patch_file(path: pathlib.Path) -> bool:
    """Returns True if file was modified."""
    html = path.read_text(encoding="utf-8")

    # locate manifest <script> tag and split exactly to preserve bytes
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
        if OLD_URL.encode() not in data:
            continue
        # Patch: replace URL. Also flip `external: true` → `external: false`
        # for the resource entry so the React UI doesn't render an "external" indicator.
        text = data.decode("utf-8")
        new_text = text.replace(OLD_URL, NEW_URL)
        # Find the RESOURCES entry that we just touched and flip its external flag.
        # Pattern matches the n: "Le guide..." block specifically.
        new_text = re.sub(
            r'(n: "Le guide de l\'orientation",\s*d: "[^"]*",\s*href: "\./guide-orientation\.html",\s*external:\s*)true',
            r'\1false',
            new_text,
        )
        new_data = new_text.encode("utf-8")
        if compressed:
            new_data = gzip.compress(new_data)
        entry["data"] = base64.b64encode(new_data).decode("ascii")
        changed = True
        print(f"  patched asset {uuid} in {path.name}")

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

#!/usr/bin/env python3
"""Phase 2 · nav restructure de 5 onglets à 4.

Avant (5 onglets) ·
  Tableau de bord · Documents · Rapport · Coach · Ressources

Après (4 onglets) ·
  Tableau de bord · Parcours · Documents · Ressources

  - Rapport supprimé du nav (sera fusionné dans Documents en Phase 2.B)
  - Coach supprimé du nav (sera absorbé dans Parcours en Phase 3)
  - Parcours ajouté · pointe vers Proxxie Parcours.html (créé en Phase 3 ;
    en attendant, click → 404, accepté pour cette étape intermédiaire)

Deux endroits à patcher·
  1. ShellHeader (asset partagé ~5KB) dans documents.html, rapport.html,
     coach.html, ressources.html · contient un tableau `tabs` JSX
  2. DashHeader (asset dashboard 113KB) dans dashboard.html · contient
     5 <a> en dur

Idempotent · MARKER présent → strip + readd.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
MARKER = "/* __proxxie_nav_4_tabs_v1__ */"

# Files containing ShellHeader (shared asset)
SHELL_FILES = [
    "Proxxie Documents.html", "documents.html",
    "Proxxie Rapport.html",   "rapport.html",
    "Proxxie Coach.html",     "coach.html",
    "Proxxie Ressources.html", "ressources.html",
]
# Dashboard has its own DashHeader inline
DASH_FILES = ["Proxxie Dashboard.html", "dashboard.html"]


# ShellHeader · the old 5-tabs array
SHELL_OLD = """  const tabs = [
    { id: "dashboard", l: "Tableau de bord", h: "Proxxie Dashboard.html" },
    { id: "documents", l: "Documents", h: "Proxxie Documents.html" },
    { id: "rapport", l: "Rapport", h: "Proxxie Rapport.html" },
    { id: "coach", l: "Coach", h: "Proxxie Coach.html" },
    { id: "ressources", l: "Ressources", h: "Proxxie Ressources.html" },
  ];"""

SHELL_NEW = """  /* __proxxie_nav_4_tabs_v1__ */
  const tabs = [
    { id: "dashboard", l: "Tableau de bord", h: "Proxxie Dashboard.html" },
    { id: "parcours", l: "Parcours", h: "Proxxie Parcours.html" },
    { id: "documents", l: "Documents", h: "Proxxie Documents.html" },
    { id: "ressources", l: "Ressources", h: "Proxxie Ressources.html" },
  ];"""

# DashHeader · the old 5 hard-coded links
DASH_OLD = '''          <a href="Proxxie Dashboard.html" style={{ color: "var(--c-ink)", borderBottom: "2px solid #FD6936", paddingBottom: 4 }}>Tableau de bord</a>
          <a href="Proxxie Documents.html" className="muted">Documents</a>
          <a href="Proxxie Rapport.html" className="muted">Rapport</a>
          <a href="Proxxie Coach.html" className="muted">Coach</a>
          <a href="Proxxie Ressources.html" className="muted">Ressources</a>'''

DASH_NEW = '''          {/* __proxxie_nav_4_tabs_v1__ */}
          <a href="Proxxie Dashboard.html" style={{ color: "var(--c-ink)", borderBottom: "2px solid #FD6936", paddingBottom: 4 }}>Tableau de bord</a>
          <a href="Proxxie Parcours.html" className="muted">Parcours</a>
          <a href="Proxxie Documents.html" className="muted">Documents</a>
          <a href="Proxxie Ressources.html" className="muted">Ressources</a>'''


def patch_asset_text(src: str, kind: str) -> tuple:
    """Returns (new_src, was_patched)."""
    was_patched = MARKER in src
    if kind == "shell":
        old, new = SHELL_OLD, SHELL_NEW
    else:
        old, new = DASH_OLD, DASH_NEW

    if was_patched:
        # Strip · revert new → old
        if new in src:
            src = src.replace(new, old, 1)
        else:
            # already in stripped state somehow
            pass
    if old not in src:
        raise SystemExit(f"anchor not found in {kind} asset")
    new_src = src.replace(old, new, 1)
    return new_src, was_patched


def find_target_asset(manifest, kind: str):
    """For shell, find the asset containing ShellHeader. For dash, find DashHeader."""
    needle = "const ShellHeader" if kind == "shell" else "const DashHeader"
    for uuid, entry in manifest.items():
        data = base64.b64decode(entry["data"])
        if entry.get("compressed"):
            try: data = gzip.decompress(data)
            except: continue
        try: src = data.decode("utf-8")
        except: continue
        if needle in src:
            return uuid, src, entry.get("compressed", False)
    return None, None, False


def patch_one(target: pathlib.Path, kind: str) -> str:
    if not target.exists():
        return "SKIP missing"
    html = target.read_text(encoding="utf-8")
    m = re.search(r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)', html, re.DOTALL)
    if not m: return "no manifest"
    manifest = json.loads(m.group(2))

    uuid, src, was_compressed = find_target_asset(manifest, kind)
    if not uuid:
        return f"SKIP no {kind} asset found"

    try:
        new_src, was_patched = patch_asset_text(src, kind)
    except SystemExit as e:
        return f"ERROR · {e}"

    nd = new_src.encode("utf-8")
    if was_compressed: nd = gzip.compress(nd)
    manifest[uuid]["data"] = base64.b64encode(nd).decode("ascii")
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]
    target.write_text(new_html, encoding="utf-8")
    verb = "re-patched" if was_patched else "patched"
    return f"{verb} ({kind}, asset {uuid[:8]} {len(new_src)} chars)"


if __name__ == "__main__":
    print("== ShellHeader (4 fichiers connectés) ==")
    for fn in SHELL_FILES:
        print(f"  {fn}: {patch_one(REPO / fn, 'shell')}")
    print("\n== DashHeader (Dashboard) ==")
    for fn in DASH_FILES:
        print(f"  {fn}: {patch_one(REPO / fn, 'dash')}")

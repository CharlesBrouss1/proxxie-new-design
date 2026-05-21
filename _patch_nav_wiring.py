#!/usr/bin/env python3
"""Fluidity wiring · connect built-but-unreachable features.

Two fixes in the bundle headers (DashHeader in the dashboard asset,
ShellHeader in the shared asset used by Documents/Rapport/Coach/Ressources)·

  1. Nav "Ressources" repointed from the old thin bundle
     (Proxxie Ressources.html) to the new rich content hub
     (Proxxie Ressources Hub.html) created in #40.

  2. The user pill (top-right) becomes clickable → Proxxie Compte.html
     (the account page from #41, currently unreachable from the UI).
     Done by adding an onClick + cursor:pointer to the pill's opening
     div, so no fragile close-tag matching is needed.

Idempotent · re-applying is a no-op (anchors are already-transformed).
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent

SHELL_FILES = [
    "Proxxie Documents.html", "documents.html",
    "Proxxie Rapport.html",   "rapport.html",
    "Proxxie Coach.html",     "coach.html",
    "Proxxie Ressources.html", "ressources.html",
]
DASH_FILES = ["Proxxie Dashboard.html", "dashboard.html"]

# Shared pill opening div (identical in ShellHeader + DashHeader)
PILL_OLD = '<div style={{ display: "flex", alignItems: "center", gap: 10, padding: "6px 14px 6px 6px", background: "white", borderRadius: 999, border: "1px solid var(--c-line)" }}>'
PILL_NEW = '<div onClick={() => { try { window.location.href = "Proxxie Compte.html"; } catch (e) {} }} title="Mon compte" style={{ display: "flex", alignItems: "center", gap: 10, padding: "6px 14px 6px 6px", background: "white", borderRadius: 999, border: "1px solid var(--c-line)", cursor: "pointer" }}>'

# Ressources repoints
SHELL_RES_OLD = '{ id: "ressources", l: "Ressources", h: "Proxxie Ressources.html" }'
SHELL_RES_NEW = '{ id: "ressources", l: "Ressources", h: "Proxxie Ressources Hub.html" }'
DASH_RES_OLD = '<a href="Proxxie Ressources.html" className="muted">Ressources</a>'
DASH_RES_NEW = '<a href="Proxxie Ressources Hub.html" className="muted">Ressources</a>'


def find_asset(manifest, needle):
    for uuid, entry in manifest.items():
        data = base64.b64decode(entry["data"])
        if entry.get("compressed"):
            try: data = gzip.decompress(data)
            except Exception: continue
        try: src = data.decode("utf-8")
        except UnicodeDecodeError: continue
        if needle in src:
            return uuid, src, entry.get("compressed", False)
    return None, None, False


def patch_one(target, kind):
    if not target.exists(): return "SKIP missing"
    html = target.read_text(encoding="utf-8")
    m = re.search(r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)', html, re.DOTALL)
    if not m: return "no manifest"
    manifest = json.loads(m.group(2))
    needle = "const ShellHeader" if kind == "shell" else "const DashHeader"
    uuid, src, comp = find_asset(manifest, needle)
    if not uuid: return f"SKIP no {kind} asset"

    changes = []
    # 1. Pill → Compte
    if PILL_OLD in src:
        src = src.replace(PILL_OLD, PILL_NEW, 1)
        changes.append("pill→compte")
    elif PILL_NEW in src:
        changes.append("pill(already)")
    # 2. Ressources repoint
    if kind == "shell":
        if SHELL_RES_OLD in src:
            src = src.replace(SHELL_RES_OLD, SHELL_RES_NEW, 1); changes.append("res→hub")
        elif SHELL_RES_NEW in src:
            changes.append("res(already)")
    else:
        if DASH_RES_OLD in src:
            src = src.replace(DASH_RES_OLD, DASH_RES_NEW, 1); changes.append("res→hub")
        elif DASH_RES_NEW in src:
            changes.append("res(already)")

    if not any(c.endswith("compte") or c.endswith("hub") for c in changes):
        return f"noop ({', '.join(changes) or 'no anchors'})"

    nd = src.encode("utf-8")
    if comp: nd = gzip.compress(nd)
    manifest[uuid]["data"] = base64.b64encode(nd).decode("ascii")
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]
    target.write_text(new_html, encoding="utf-8")
    return f"patched [{', '.join(changes)}] (asset {uuid[:8]})"


if __name__ == "__main__":
    print("== ShellHeader bundles ==")
    for fn in SHELL_FILES:
        print(f"  {fn}: {patch_one(REPO / fn, 'shell')}")
    print("\n== DashHeader bundles ==")
    for fn in DASH_FILES:
        print(f"  {fn}: {patch_one(REPO / fn, 'dash')}")

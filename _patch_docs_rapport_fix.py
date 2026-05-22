#!/usr/bin/env python3
"""Documents · corrige le bandeau rapport au-dessus du header + CTA du héros.

Bug : un script du template (__proxxie_rapport_fusion_v1__) construit un bandeau
« le rapport d'orientation en un coup d'œil » et l'insère AVANT #root
(root.parentNode.insertBefore(section, root)). Comme le ShellHeader est rendu
dans #root, le bandeau s'affiche au-dessus du header.

Correctif (demande utilisateur) :
  · on retire ce bandeau (le script rapport-fusion) du template Documents,
  · on remplace le bouton héros « + Ajouter un document » par le CTA
    « Voir le rapport complet → » (on peut déjà ajouter des documents juste en
    dessous par glisser-déposer).

Idempotent · no-op si le script est déjà retiré / le CTA déjà repointé.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
FILES = ["Proxxie Documents.html", "documents.html"]

FUSION_MARKER = "/* __proxxie_rapport_fusion_v1__ */"

ACTIONS_OLD = (
    'actions={<button\n'
    '          className="btn btn-orange btn-arrow"\n'
    '          data-click-key={t.audit ? "docs-upload" : undefined}\n'
    '          onClick={() => { if (window.__proxxieOpenUpload) { window.__proxxieOpenUpload(); } else { openDrawer("docs-upload"); } }}\n'
    '        >+ Ajouter un document</button>}'
)
ACTIONS_NEW = 'actions={<a href="Proxxie Rapport.html" className="btn btn-orange btn-arrow" style={{ textDecoration: "none" }}>Voir le rapport complet →</a>}'


def fix_template(html: str, changes: list) -> str:
    m = re.search(r'(<script type="__bundler/template">)(.*?)(</script>)', html, re.DOTALL)
    if not m:
        return html
    tpl = json.loads(m.group(2))
    if FUSION_MARKER not in tpl:
        return html
    mi = tpl.find(FUSION_MARKER)
    sstart = tpl.rfind("<script>", 0, mi)
    send = tpl.find("</script>", mi)
    if sstart == -1 or send == -1:
        return html
    send += len("</script>")
    # strip trailing newline left behind
    tail = tpl[send:]
    if tail.startswith("\n"):
        tail = tail[1:]
    tpl = tpl[:sstart] + tail
    new_json = json.dumps(tpl, ensure_ascii=False).replace("</", "<\\/")
    changes.append("banner-removed")
    return html[:m.start(2)] + new_json + html[m.end(2):]


def fix_asset(html: str, changes: list) -> str:
    m = re.search(r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)', html, re.DOTALL)
    if not m:
        return html
    manifest = json.loads(m.group(2))
    target_uuid = None
    for uuid, e in manifest.items():
        data = base64.b64decode(e["data"])
        comp = e.get("compressed", False)
        if comp:
            try: data = gzip.decompress(data)
            except Exception: continue
        try: src = data.decode("utf-8")
        except UnicodeDecodeError: continue
        if "render(<DocsApp />)" not in src:
            continue
        if "Voir le rapport complet →" in src and ACTIONS_OLD not in src:
            changes.append("cta(already)")
            return html
        if ACTIONS_OLD not in src:
            changes.append("cta(anchor missing)")
            return html
        src = src.replace(ACTIONS_OLD, ACTIONS_NEW, 1)
        changes.append("cta→rapport")
        nd = src.encode("utf-8")
        if comp:
            nd = gzip.compress(nd)
        manifest[uuid]["data"] = base64.b64encode(nd).decode("ascii")
        target_uuid = uuid
        break
    if not target_uuid:
        return html
    new_manifest = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    return html[:m.start(2)] + new_manifest + html[m.end(2):]


def patch_one(target: pathlib.Path) -> str:
    if not target.exists():
        return "SKIP missing"
    html = target.read_text(encoding="utf-8")
    changes = []
    html = fix_template(html, changes)
    html = fix_asset(html, changes)
    if not changes:
        return "noop"
    target.write_text(html, encoding="utf-8")
    return "patched [" + ", ".join(changes) + "]"


if __name__ == "__main__":
    for fn in FILES:
        print("  " + fn + ": " + patch_one(REPO / fn))

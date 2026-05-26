#!/usr/bin/env python3
"""Simplification de EmailResultsActions sur tous les tests.

Changements demandés par Charles :
- Garder UNIQUEMENT le bouton « M'envoyer le rapport par email »
- Retirer le bouton « 🖨 Imprimer / PDF »
- Retirer le bouton « 🔗 Copier le lien »
- Changer le label « Classe de l'ado » en « Classe »
- Ajuster la phrase d'intro qui mentionnait « l'imprimer »

Architecture : remplacements de strings exactes dans l'asset 61feca88 de chaque
bundle. Idempotent (les nouvelles strings ne matchent pas les anciennes).
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
ASSET_UUID_PREFIX = "61feca88"

# Bloc à supprimer : bouton PDF (variante avec type="button" · panneau principal)
OLD_PDF_BUTTON = '''                  <button type="button" onClick={() => window.print()} style={{
                    background: "white", color: accent, border: "1.5px solid " + accent,
                    padding: "11px 18px", borderRadius: 99, fontSize: 14, fontWeight: 600, cursor: "pointer",
                  }}>
                    🖨 Imprimer / PDF
                  </button>
'''

# Bloc à supprimer : bouton PDF (variante sans type="button" · dans modal)
OLD_PDF_BUTTON_MODAL = '''                  <button onClick={() => window.print()} style={{
                    background: "white", color: accent, border: "1.5px solid " + accent,
                    padding: "11px 18px", borderRadius: 99, fontSize: 14, fontWeight: 600, cursor: "pointer",
                  }}>
                    🖨 Imprimer / PDF
                  </button>
'''

# Bloc à supprimer : bouton Copier le lien (variante avec type="button")
OLD_COPY_BUTTON = '''                  <button type="button" onClick={copyUrl} style={{
                    background: "var(--c-cream-light)", color: "var(--c-ink)", border: "1px solid var(--c-line)",
                    padding: "11px 18px", borderRadius: 99, fontSize: 14, fontWeight: 600, cursor: "pointer",
                  }}>
                    {copied ? "✓ Lien copié" : "🔗 Copier le lien"}
                  </button>
'''

# Bloc à supprimer : bouton Copier le lien (variante sans type="button" · dans modal)
OLD_COPY_BUTTON_MODAL = '''                  <button onClick={copyUrl} style={{
                    background: "var(--c-cream-light)", color: "var(--c-ink)", border: "1px solid var(--c-line)",
                    padding: "11px 18px", borderRadius: 99, fontSize: 14, fontWeight: 600, cursor: "pointer",
                  }}>
                    {copied ? "✓ Lien copié" : "🔗 Copier le lien"}
                  </button>
'''

REPLACEMENTS = [
    # Retire le bouton PDF (panneau principal · type="button")
    (OLD_PDF_BUTTON, ""),
    # Retire le bouton PDF (modale · sans type="button")
    (OLD_PDF_BUTTON_MODAL, ""),
    # Retire le bouton Copy link (panneau principal)
    (OLD_COPY_BUTTON, ""),
    # Retire le bouton Copy link (modale)
    (OLD_COPY_BUTTON_MODAL, ""),
    # Simplifie le label du champ classe
    ("<label style={labelStyle}>Classe de l'ado</label>", "<label style={labelStyle}>Classe</label>"),
    # Ajuste la phrase d'intro (retire la mention « l'imprimer »)
    (
        "Recevez votre rapport par email pour le retrouver plus tard, l'imprimer, ou le partager avec un professionnel.",
        "Recevez votre rapport par email pour le retrouver plus tard ou le partager avec un professionnel.",
    ),
]

TARGETS = sorted(p.name for p in REPO.glob("*.html") if not p.name.startswith("_"))


def patch_src(src: str) -> tuple[str, list[str]]:
    changes = []
    for old, new in REPLACEMENTS:
        if old in src:
            src = src.replace(old, new)
            changes.append(old[:40].replace("\n", "·") + "...")
    return src, changes


def patch_one(target: pathlib.Path) -> str:
    if not target.exists():
        return f"{target.name}: file not found"
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
    if not changes:
        return f"{target.name}: aucun changement"
    nd = new_src.encode('utf-8')
    if comp:
        nd = gzip.compress(nd)
    entry['data'] = base64.b64encode(nd).decode('ascii')
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]
    target.write_text(new_html, encoding='utf-8')
    return f"{target.name}: {len(changes)} chgt(s) [{', '.join(changes)}]"


if __name__ == "__main__":
    for fn in TARGETS:
        print(patch_one(REPO / fn))

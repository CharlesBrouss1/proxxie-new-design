#!/usr/bin/env python3
"""Déclutter · alléger le haut du dashboard, qu'un seul élément domine.

Le haut empilait trois blocs concurrents :
  · ReengagementBanner (bandeau « c'est la période · bulletins ? »),
  · NextBestAction (« Votre prochaine étape » · l'action unique du moment, F1),
  · OnboardingChecklist (« N actions pour démarrer » · la liste complète).

NextBestAction et OnboardingChecklist guident le même démarrage (doublon), et
le rappel doc du ReengagementBanner est déjà couvert par l'étape document du
héros, son état régime, et le panel de complétude plus bas. On garde le héros
action-unique comme élément dominant + le fil « depuis ta dernière visite »,
et on retire les deux autres rendus du haut de page.

On supprime simplement les rendus <OnboardingChecklist .../> et
<ReengagementBanner /> de l'arbre du composant Dashboard. Les définitions des
composants restent intactes (zéro référence cassée). Idempotent : no-op si un
rendu est déjà absent.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
FILES = ["Proxxie Dashboard.html", "dashboard.html"]

RENDERS_TO_REMOVE = [
    "      <OnboardingChecklist onOpenProfile={() => setProfileOpen(true)} onOpenInvite={() => setInviteOpen(true)} />\n",
    "      <ReengagementBanner />\n",
]


def find_dash_asset(manifest):
    for uuid, entry in manifest.items():
        data = base64.b64decode(entry["data"])
        comp = entry.get("compressed", False)
        if comp:
            try: data = gzip.decompress(data)
            except Exception: continue
        try: src = data.decode("utf-8")
        except UnicodeDecodeError: continue
        if 'render(<Dashboard />)' in src:
            return uuid, src, comp
    return None, None, False


def patch_one(target: pathlib.Path) -> str:
    if not target.exists():
        return "SKIP missing"
    html = target.read_text(encoding="utf-8")
    m = re.search(r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)', html, re.DOTALL)
    if not m:
        return "no manifest"
    manifest = json.loads(m.group(2))
    uuid, src, comp = find_dash_asset(manifest)
    if not uuid:
        return "SKIP no dashboard asset"

    removed = []
    for r in RENDERS_TO_REMOVE:
        if r in src:
            src = src.replace(r, "", 1)
            removed.append(r.strip().split()[0].lstrip("<"))
    if not removed:
        return "noop (already removed)"

    nd = src.encode("utf-8")
    if comp:
        nd = gzip.compress(nd)
    manifest[uuid]["data"] = base64.b64encode(nd).decode("ascii")
    new_manifest = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest + html[m.end(2):]
    target.write_text(new_html, encoding="utf-8")
    return "removed [" + ", ".join(removed) + "] (asset " + uuid[:8] + ")"


if __name__ == "__main__":
    for fn in FILES:
        print("  " + fn + ": " + patch_one(REPO / fn))

#!/usr/bin/env python3
"""Déclutter · retirer la checklist d'onboarding redondante du dashboard.

Le haut du dashboard avait DEUX blocs de mise en route empilés :
  · NextBestAction (« Votre prochaine étape » · l'action unique du moment, F1),
  · OnboardingChecklist (« N actions pour démarrer » · la liste complète).

Les deux guident le même démarrage (profil → doc → test → invitation), donc ils
font doublon et surchargent la page. On garde le héros action-unique (plus
clair, une seule action + progression) et on retire la checklist.

On supprime simplement le rendu <OnboardingChecklist .../> de l'arbre du
composant Dashboard. La définition du composant et les autres usages restent
intacts (zéro risque de référence cassée · NextBestAction couvre les mêmes
étapes). Idempotent : no-op si le rendu est déjà absent.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
FILES = ["Proxxie Dashboard.html", "dashboard.html"]

RENDER_OLD = "      <OnboardingChecklist onOpenProfile={() => setProfileOpen(true)} onOpenInvite={() => setInviteOpen(true)} />\n"


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

    if RENDER_OLD not in src:
        return "noop (already removed)"
    src = src.replace(RENDER_OLD, "", 1)

    nd = src.encode("utf-8")
    if comp:
        nd = gzip.compress(nd)
    manifest[uuid]["data"] = base64.b64encode(nd).decode("ascii")
    new_manifest = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest + html[m.end(2):]
    target.write_text(new_html, encoding="utf-8")
    return "removed OnboardingChecklist render (asset " + uuid[:8] + ")"


if __name__ == "__main__":
    for fn in FILES:
        print("  " + fn + ": " + patch_one(REPO / fn))

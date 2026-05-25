#!/usr/bin/env python3
"""Wire le CTA « Connexion » des pages publiques du proto vers la vraie app
prod (Next.js sur Vercel). Le proto reste maquette pour le marketing/landing,
mais l'authentification réelle se fait dans proxxie-app.

Avant · `<a href="Proxxie Connexion.html">Connexion</a>` ouvre une page
        de démo locale du proto.
Après · même lien, mais redirige vers `https://proxxie-app-seven.vercel.app/login`
        où le user reçoit son magic link et atterrit sur son vrai tableau de bord.

Le funnel `<OnboardingFlow>` (CTA « Commencer le parcours gratuit ») n'est
PAS touché · il collecte email + téléphone et restera lead-gen côté proto
tant qu'on n'a pas branché sa dernière étape sur l'API prod (chantier
suivant).

Le lien Calendly (« 30 min avec Charles ») n'est pas touché non plus.

Idempotent · cherche l'ancien href ; si plus présent (déjà patché), no-op.
Sécurité · ne modifie QUE les assets contenant la chaîne exacte. Pas de
risque de toucher des hrefs sans rapport.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
PROD_LOGIN_URL = "https://proxxie-app-seven.vercel.app/login"

OLD_HREF = 'href="Proxxie Connexion.html"'
NEW_HREF = f'href="{PROD_LOGIN_URL}"'
# Variantes possibles (avec target/rel, ou orthographe alternative)
EXTRA_OLDS = [
    "href='Proxxie Connexion.html'",
    'href="./Proxxie Connexion.html"',
    'href="connexion.html"',  # lowercase variant
]
EXTRA_NEWS = [
    f"href='{PROD_LOGIN_URL}'",
    f'href="{PROD_LOGIN_URL}"',
    f'href="{PROD_LOGIN_URL}"',
]


def patch_asset(src: str) -> tuple[str, int]:
    """Renvoie (nouveau_source, nombre_remplacements)."""
    n = src.count(OLD_HREF)
    if n:
        src = src.replace(OLD_HREF, NEW_HREF)
    for old, new in zip(EXTRA_OLDS, EXTRA_NEWS):
        cnt = src.count(old)
        if cnt:
            src = src.replace(old, new)
            n += cnt
    return src, n


def _raw_html_patch(html: str) -> tuple[str, int]:
    """Patch direct sur le HTML statique (pages sans bundle Pretext)."""
    n = 0
    for old, new in zip([OLD_HREF] + EXTRA_OLDS, [NEW_HREF] + EXTRA_NEWS):
        cnt = html.count(old)
        if cnt:
            html = html.replace(old, new)
            n += cnt
    return html, n


def patch_one(target: pathlib.Path) -> str:
    if not target.exists():
        return "SKIP missing"
    html = target.read_text(encoding="utf-8")
    m = re.search(r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)', html, re.DOTALL)
    if not m:
        # Page statique HTML sans bundle Pretext · patch direct.
        new_html, count = _raw_html_patch(html)
        if count == 0:
            return "no manifest, no Connexion href"
        target.write_text(new_html, encoding="utf-8")
        return f"raw-patched · {count} replacement(s)"
    manifest = json.loads(m.group(2))

    total = 0
    changed_assets = []
    for uuid, entry in manifest.items():
        data = base64.b64decode(entry["data"])
        comp = entry.get("compressed", False)
        if comp:
            try:
                data = gzip.decompress(data)
            except OSError:
                continue
        try:
            src = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        new_src, count = patch_asset(src)
        if count == 0:
            continue
        nd = new_src.encode("utf-8")
        if comp:
            nd = gzip.compress(nd)
        entry["data"] = base64.b64encode(nd).decode("ascii")
        total += count
        changed_assets.append(f"{uuid[:8]}(+{count})")

    if total == 0:
        return "no Connexion href found (already patched?)"

    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]
    target.write_text(new_html, encoding="utf-8")
    return f"patched · {total} replacement(s) · assets " + ", ".join(changed_assets)


def main():
    # Toutes les pages publiques top-level (skip louise/ et tests psy
    # internes qui ne contiennent pas de nav publique).
    targets = sorted(REPO.glob("*.html"))
    for t in targets:
        # Skip les pages de tests internes (Proxxie Test *.html) sauf si
        # elles ont une nav publique. Pour l'instant on les patche aussi ·
        # c'est inoffensif (si pas de href Connexion → no-op).
        try:
            print(f"{t.name}: {patch_one(t)}")
        except SystemExit as e:
            print(f"{t.name}: ERROR · {e}")


if __name__ == "__main__":
    main()

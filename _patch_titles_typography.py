#!/usr/bin/env python3
"""Polish · normaliser la typographie des <title> (onglets navigateur).

La règle de style interdit les tirets cadratins (—) dans le texte visible. Les
titres d'onglet violaient ça, et un linter en a transformé certains en « , »
bancal (« Réflexion guidée , Proxxie »). On normalise UNIQUEMENT le contenu des
balises <title> (surface la plus visible, et exactement ce qui a été signalé) :

  " — "  → " · "      |      " , "  → " · "      |      "—" isolé → "·"

On reste scoped aux <title> (y compris la forme échappée <\\/title> dans les
templates du bundler) pour ne PAS toucher au JS/CSS/données où un remplacement
aveugle casserait des choses. Idempotent (aucun — ni « , » résiduel dans les
titres après passage).
"""
import re, pathlib

REPO = pathlib.Path(__file__).parent

# Tous les .html du repo (standalone + bundles).
FILES = sorted([p.name for p in REPO.glob("*.html")])

TITLE_RE = re.compile(r"(<title>)(.*?)(<\\?/title>)", re.DOTALL)


def fix_title_text(t: str) -> str:
    t = t.replace(" — ", " · ")
    t = t.replace(" , ", " · ")
    # tiret cadratin restant (collé ou non), on remplace par un point médian espacé
    t = t.replace(" —", " ·").replace("— ", "· ").replace("—", " · ")
    # nettoie d'éventuels espaces doubles introduits
    t = re.sub(r"\s{2,}", " ", t).strip()
    return t


def patch_one(target: pathlib.Path) -> str:
    if not target.exists():
        return "SKIP missing"
    html = target.read_text(encoding="utf-8")
    n = [0]

    def repl(m):
        before = m.group(2)
        after = fix_title_text(before)
        if after != before:
            n[0] += 1
        return m.group(1) + after + m.group(3)

    new_html = TITLE_RE.sub(repl, html)
    if n[0] == 0:
        return "noop"
    target.write_text(new_html, encoding="utf-8")
    return f"fixed {n[0]} title(s)"


if __name__ == "__main__":
    for fn in FILES:
        res = patch_one(REPO / fn)
        if res != "noop":
            print(f"  {fn}: {res}")

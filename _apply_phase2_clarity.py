#!/usr/bin/env python3
"""Phase 2 clarity: inject result-screen direction/framing into the 11 bundled-only
tests (no _patch_build_*.py BLOCK). Each hunk is (anchor, insertion): the anchor is
a unique existing substring of the decoded 61feca88 asset; insertion is appended
right after it. Idempotent: a hunk whose insertion is already present is skipped.

Two families:
  - profile (no good/bad): Besoins, Drivers, Valeurs, MBTI, PCM, RIASEC
  - clinical/screening (direction): Anxiete, TDAH, Autisme, DYS, HPI

Read-only on .py; writes the HTML files in place.
"""
import re, json, base64, gzip, sys, pathlib

ASSET_PREFIX = "61feca88"

# Profile-family framing line, inserted after the hero subtitle <p>.
def _frame(text: str) -> str:
    return (
        '\n          <p style={{ fontSize: 13.5, color: "var(--c-muted)", '
        'margin: "10px auto 0", maxWidth: 620, fontStyle: "italic" }}>\n'
        '            ' + text + '\n          </p>'
    )

# Clinical-family direction line, inserted after the score figure.
def _dir(text: str) -> str:
    return (
        '\n          <div style={{ fontSize: 13, opacity: 0.85, marginBottom: 14 }}>'
        + text + '</div>'
    )

TESTS = {
    # ---- profile family ----
    "besoins": (["Proxxie Test Besoins.html", "test-besoins.html"], [(
        "            {dom.short} · Voici votre carburant principal selon McClelland.\n          </p>",
        _frame("Ce test n'a ni bon ni mauvais score. Les % montrent l'intensité relative de vos 3 besoins, pas une note de valeur."),
    )]),
    "drivers": (["Proxxie Test Drivers.html", "test-drivers.html"], [(
        "            {dom.short} · Voici ce qui pilote inconsciemment vos comportements, surtout sous stress.\n          </p>",
        _frame("Ce test n'a ni bon ni mauvais score. Les % montrent le poids de chaque driver, pas une note de valeur."),
    )]),
    "valeurs": (["Proxxie Test Valeurs.html", "test-valeurs.html"], [(
        "            Voici les 3 valeurs qui orientent le plus fortement vos décisions, suivies du classement complet sur les 10 valeurs Schwartz.\n          </p>",
        _frame("Ce test n'a ni bon ni mauvais score. Le classement montre ce qui compte le plus pour vous, pas une note de valeur."),
    )]),
    "mbti": (["Proxxie Test MBTI.html", "test-mbti.html"], [(
        '>{td.d}</p>',
        _frame("Ce test n'a ni bon ni mauvais type. Les % montrent vers quel pôle vous penchez sur chaque axe, pas une note de valeur."),
    )]),
    "pcm": (["Proxxie Test PCM.html", "test-pcm.html"], [(
        "            Votre type de base (le plus profond) et votre type de phase actuel (ce qui vous porte aujourd'hui).\n          </p>",
        _frame("Ce test n'a ni bon ni mauvais type. Les % montrent votre affinité avec chaque profil, pas une note de valeur."),
    )]),
    "riasec": (["Proxxie Test RIASEC.html", "test-riasec.html"], [(
        "            Vos 3 types dominants forment votre code RIASEC personnel.\n          </p>",
        _frame("Ce test n'a ni bon ni mauvais score. Les % montrent l'affinité de vos intérêts, pas une note de valeur."),
    )]),
    # ---- clinical / screening family ----
    "anxiete": (["Proxxie Test Anxiete.html", "test-anxiete.html"], [(
        "<strong>{gadLevel.charAt(0).toUpperCase() + gadLevel.slice(1)}</strong> · seuils : ≤4 minimal · 5-9 léger · 10-14 modéré · ≥15 sévère\n          </div>",
        _dir("Plus le score est élevé, plus les signaux d'anxiété sont présents. Ce n'est pas une note de valeur, juste un repère clinique."),
    )]),
    "tdah": (["Proxxie Test TDAH.html", "test-tdah.html"], [(
        ">{partAShaded} / {partATotal}</div>",
        _dir("Plus le score est élevé, plus les indicateurs sont présents. Ce n'est pas une note de valeur, juste un signal."),
    )]),
    "autisme": (["Proxxie Test Autisme.html", "test-autisme.html"], [(
        ">Seuil de référence : {threshold}/{total}</div>",
        _dir("Plus le score est élevé, plus les traits AQ sont présents. Ce n'est pas une note de valeur, juste un signal à vérifier."),
    )]),
    "hpi": (["Proxxie Test HPI.html", "test-hpi.html"], [(
        ">{totalTraits} / {totalQ}</div>",
        _dir("Plus de traits identifiés = plus d'indices de douance, à confirmer par un bilan. Ce n'est pas une note de valeur."),
    )]),
    "dys": (["Proxxie Test DYS.html", "test-dys.html"], [(
        '<h2 style={{ fontSize: 22, marginBottom: 22 }}>Score par domaine</h2>',
        '\n          <p style={{ fontSize: 13, color: "var(--c-muted)", lineHeight: 1.55, marginBottom: 18 }}>'
        "Plus de traits marqués dans un domaine = plus de signaux à explorer, pas une note de valeur. Un seul domaine marqué peut justifier un bilan.</p>",
    )]),
}


def decode_asset(html: str):
    m = re.search(r'<script type="__bundler/manifest">(.*?)</script>', html, re.DOTALL)
    man = json.loads(m.group(1))
    uuid = next(k for k in man if k.startswith(ASSET_PREFIX))
    e = man[uuid]
    raw = base64.b64decode(e["data"])
    src = gzip.decompress(raw).decode("utf-8") if e.get("compressed") else raw.decode("utf-8")
    return man, uuid, e, src, m


def reencode(html: str, man, uuid, entry, new_src, mmatch):
    if entry.get("compressed"):
        entry["data"] = base64.b64encode(gzip.compress(new_src.encode("utf-8"))).decode("ascii")
    else:
        entry["data"] = base64.b64encode(new_src.encode("utf-8")).decode("ascii")
    new_manifest = json.dumps(man, ensure_ascii=False)
    return html[:mmatch.start(1)] + new_manifest + html[mmatch.end(1):]


def main() -> None:
    only = sys.argv[1:]
    for test, (files, hunks) in TESTS.items():
        if only and test not in only:
            continue
        print(f"=== {test}: {len(hunks)} hunk(s) ===")
        for fname in files:
            html = open(fname, encoding="utf-8").read()
            man, uuid, entry, src, mmatch = decode_asset(html)
            applied = skipped = failed = 0
            for anchor, insertion in hunks:
                if insertion in src:
                    skipped += 1
                elif src.count(anchor) == 1:
                    src = src.replace(anchor, anchor + insertion, 1)
                    applied += 1
                else:
                    failed += 1
                    print(f"  !! {fname}: anchor count={src.count(anchor)} (expected 1); not applied")
            new_html = reencode(html, man, uuid, entry, src, mmatch)
            pathlib.Path(fname).write_text(new_html, encoding="utf-8")
            print(f"  {fname}: applied={applied} skipped={skipped} failed={failed}")


if __name__ == "__main__":
    main()

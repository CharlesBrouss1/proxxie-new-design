#!/usr/bin/env python3
"""Ajoute la carte BRIEF (fonctions exécutives) dans TESTS_ORIENTATION
sur Proxxie Tests.html et tests.html.

Inséré juste après Besoins, dernier élément de TESTS_ORIENTATION.
Compteurs mis à jour (16 → 17 tests).

Idempotent · sentinelles BEGIN/END.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
ASSET_UUID_PREFIX = "61feca88"

TARGETS = ["Proxxie Tests.html", "tests.html"]

BEGIN = "/* PROXXIE_ADD_BRIEF_BEGIN */"
END   = "/* PROXXIE_ADD_BRIEF_END */"

# Nouvelle entrée BRIEF · insérée après le dernier élément de TESTS_ORIENTATION
NEW_BRIEF = BEGIN + r"""
  { code: "BRIEF", name: "Test Fonctions exécutives", model: "BDEFS-CA (Barkley)", accent: "#0EA5E9", accentSoft: "rgba(14,165,233,0.12)", href: "./Proxxie Test BRIEF.html", duration: "6 min", questions: "20 questions", eyebrow: "Fonctions exécutives",
    short: "Mesure 4 muscles cognitifs : organiser, gérer le temps, réguler les émotions, retenir l'info.",
    long: "Inspiré du BDEFS-CA de Russell Barkley (Penn State, 2012). 40 ans de recherche sur les fonctions exécutives chez l'enfant et l'ado. Prédicteur d'autonomie scolaire et professionnelle, parfois mieux que le QI.",
    output: "Profil 4 axes + chantier prioritaire", results: [{k:"Profil 4 axes",v:"Score sur Organisation, Gestion du temps, Régulation émotion, Mémoire de travail."},{k:"Chantier prioritaire",v:"Dimension la plus en difficulté · 3 exercices concrets à faire sur 30 jours."},{k:"Lien orientation",v:"Implications pour études longues vs courtes, formats avec/sans encadrement."},{k:"Comorbidité TDAH",v:"Si score haut, recommandation de croiser avec ASRS pour évaluer un TDAH éventuel."}], tags: ["Cognition", "Barkley"],
    icon: (<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a10 10 0 1 0 10 10"/><path d="M12 6v6l4 2"/></svg>) },
""" + END

# Anchor · juste après l'entrée Besoins (dernier de TESTS_ORIENTATION)
# Pattern unique : icon de Besoins + `, },` puis `\n];` ou suite
ANCHOR_BESOINS_CLOSE = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-6 8-12a8 8 0 1 0-16 0c0 6 8 12 8 12z"/><circle cx="12" cy="10" r="3"/></svg>) },'

# Compteurs à mettre à jour (avec et sans BRIEF déjà compté)
COUNT_REPLACEMENTS = [
    # 16 → 17 dans le badge
    ('badge: "16 tests · gratuit"', 'badge: "17 tests · gratuit"'),
    # Pill hero
    (' 16 tests · 100% gratuits', ' 17 tests · 100% gratuits'),
    # Subtitle hero
    ('Seize tests répartis en 2 catégories', 'Dix-sept tests répartis en 2 catégories'),
    # NAV_RESOURCES description
    ('"16 tests : OCEAN, RIASEC, Raisonnement, Grit, CAAS, PCM, MBTI, Drivers, Valeurs, Besoins, TDAH, Autisme, HPI, Anxiété, Dépression, DYS."',
     '"17 tests : OCEAN, RIASEC, Raisonnement, Grit, CAAS, BRIEF, PCM, MBTI, Drivers, Valeurs, Besoins, TDAH, Autisme, HPI, Anxiété, Dépression, DYS."'),
    # Cat 1 title
    ('title="10 tests pour comprendre qui est votre ado"', 'title="11 tests pour comprendre qui est votre ado"'),
    # Lecture croisée
    ('Lecture croisée des 16 tests', 'Lecture croisée des 17 tests'),
]


def strip_between(src: str, begin: str, end: str) -> str:
    pat = re.compile(r'\s*' + re.escape(begin) + r'.*?' + re.escape(end), re.DOTALL)
    return pat.sub('', src)


def patch_src(src: str) -> tuple[str, list[str]]:
    changes = []
    src = strip_between(src, BEGIN, END)
    if ANCHOR_BESOINS_CLOSE not in src:
        return src, ["WARN ancre Besoins introuvable"]
    src = src.replace(ANCHOR_BESOINS_CLOSE, ANCHOR_BESOINS_CLOSE + "\n" + NEW_BRIEF, 1)
    changes.append("+ entrée BRIEF (fonctions exécutives)")
    for old, new in COUNT_REPLACEMENTS:
        if old in src:
            src = src.replace(old, new)
            changes.append(f"count: {old[:40]}...")
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
    if not changes or new_src == src:
        return f"{target.name}: aucun changement"
    nd = new_src.encode('utf-8')
    if comp:
        nd = gzip.compress(nd)
    entry['data'] = base64.b64encode(nd).decode('ascii')
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]
    target.write_text(new_html, encoding='utf-8')
    return f"{target.name}: [{', '.join(changes)}]"


if __name__ == "__main__":
    for fn in TARGETS:
        print(patch_one(REPO / fn))

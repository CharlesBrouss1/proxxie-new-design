#!/usr/bin/env python3
"""Ajoute les cartes VIA Strengths + Mindset Dweck dans TESTS_ORIENTATION
de Proxxie Tests.html, bump compteur 17 → 19 tests.

Position : juste après FuturProof (en haut du catalogue · psychologie positive
en avant pour casser l'idée que les tests Proxxie sont juste cliniques).
Idempotent : détection par présence des codes.
"""
import re
import json
import base64
import gzip
import pathlib

REPO = pathlib.Path(__file__).parent
TARGETS = ["Proxxie Tests.html", "tests.html"]
ASSET_UUID_PREFIX = "61feca88"

VIA_CARD = (
    '{ code: "VIA", name: "Forces de caractère", '
    'model: "VIA Strengths (Peterson & Seligman)", '
    'accent: "#7C3AED", accentSoft: "rgba(124,58,237,0.12)", '
    'href: "./Proxxie Test VIA.html", duration: "6 min", '
    'questions: "24 questions", eyebrow: "Psychologie positive",\n'
    '    short: "Identifie tes 5 forces signatures parmi 24 forces de caractère universelles. Ce sur quoi t\'appuyer dans ton parcours.",\n'
    '    long: "VIA Inventory of Strengths (Peterson & Seligman, 2004). Validé sur 10M+ d\'utilisateurs depuis 20 ans. Cadre de référence en psychologie positive. 24 forces × 6 vertus universelles. Version courte adaptée ados.",\n'
    '    output: "Top 5 forces signatures + 5 zones d\'éveil + 6 vertus", '
    'results: [{k:"5 forces signatures",v:"Top 5 sur 24 · ce qui te rend toi, à valoriser dans ton orientation."},'
    '{k:"5 forces à éveiller",v:"Bottom 5 · pas des défauts, des forces qui dorment. UNE à pratiquer 30 jours."},'
    '{k:"6 vertus",v:"Sagesse, courage, humanité, justice, tempérance, transcendance · ta vertu dominante."},'
    '{k:"Lien orientation",v:"Tes forces signatures pointent vers des métiers et des contextes où tu seras le plus naturel."}], '
    'tags: ["Forces", "Seligman", "Positif"],\n'
    '    icon: (<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01z"/></svg>) }'
)

DWECK_CARD = (
    '{ code: "Dweck", name: "Mindset growth ou fixed", '
    'model: "Dweck Mindset Scale (Stanford)", '
    'accent: "#0EA5E9", accentSoft: "rgba(14,165,233,0.12)", '
    'href: "./Proxxie Test Dweck.html", duration: "4 min", '
    'questions: "16 questions", eyebrow: "Mindset éducation",\n'
    '    short: "Tu crois que l\'intelligence se travaille, ou qu\'on naît avec ? Cette croyance change tes prises de risque, tes apprentissages, ta réaction à l\'échec.",\n'
    '    long: "Carol Dweck (Stanford), « Mindset » (2006). 4M+ livres vendus, concept devenu central en éducation US. 16 items sur 4 dimensions : intelligence, talent, effort, échec. Pas un instrument clinique · outil éducatif puissant et actionable.",\n'
    '    output: "% growth mindset + 4 dimensions + 3 actions", '
    'results: [{k:"% growth mindset",v:"De 0 (fixed marqué) à 100 (growth solide), sur 4 dimensions équipondérées."},'
    '{k:"4 dimensions",v:"Intelligence, talent, effort, échec · où tu penches growth, où tu restes fixed."},'
    '{k:"3 actions concrètes",v:"Ciblées sur ta dimension la plus fixe · à pratiquer 30 jours pour basculer."},'
    '{k:"Lien orientation",v:"Le growth mindset prédit la persévérance face aux études difficiles (prépa, médecine, ingénierie)."}], '
    'tags: ["Mindset", "Dweck", "Stanford"],\n'
    '    icon: (<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M9 12l2 2 4-4"/><circle cx="12" cy="12" r="10"/></svg>) }'
)

VIA_MARKER = 'code: "VIA"'
DWECK_MARKER = 'code: "Dweck"'


def patch_src(src: str) -> tuple[str, list[str]]:
    changes: list[str] = []

    # Find anchor : after FuturProof entry. We insert just after its closing }.
    # Strategy : find the FuturProof entry, walk to its closing brace, insert
    # the new cards right after.
    m = re.search(r'\{\s*code:\s*"FuturProof"', src)
    if m:
        # walk balanced braces from m.start
        depth = 0
        end = m.start()
        for j, c in enumerate(src[m.start():], start=m.start()):
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    end = j + 1
                    break
        insert_at = end
        # The string after end is `,\n  ` typically. We insert ",\n  CARD"
        to_insert = ""
        if VIA_MARKER not in src:
            to_insert += ",\n  " + VIA_CARD
            changes.append("+ carte VIA Strengths")
        if DWECK_MARKER not in src:
            to_insert += ",\n  " + DWECK_CARD
            changes.append("+ carte Mindset Dweck")
        if to_insert:
            src = src[:insert_at] + to_insert + src[insert_at:]
    else:
        # Fallback : insert at start of TESTS_ORIENTATION array
        m2 = re.search(r"const TESTS_ORIENTATION\s*=\s*\[\s*", src)
        if not m2:
            return src, ["WARN ni FuturProof ni TESTS_ORIENTATION trouvés"]
        to_insert = ""
        if VIA_MARKER not in src:
            to_insert += VIA_CARD + ",\n  "
            changes.append("+ carte VIA Strengths (fallback head)")
        if DWECK_MARKER not in src:
            to_insert += DWECK_CARD + ",\n  "
            changes.append("+ carte Mindset Dweck (fallback head)")
        if to_insert:
            src = src[:m2.end()] + to_insert + src[m2.end():]

    # Bump counters : 17 tests → 19 tests
    n = len(re.findall(r"\b17\s+tests\b", src))
    if n > 0:
        src = re.sub(r"\b17\s+tests\b", "19 tests", src)
        changes.append(f"compteur 17 → 19 tests ({n}x)")

    if not changes:
        changes.append("rien à faire (déjà présent)")
    return src, changes


def patch_one(target: pathlib.Path) -> str:
    if not target.exists():
        return f"{target.name}: file not found"
    html = target.read_text(encoding="utf-8")
    m = re.search(
        r'(<script type="__bundler/manifest">)(.*?)(</script>)', html, re.DOTALL
    )
    if not m:
        return f"{target.name}: pas de manifest"
    manifest = json.loads(m.group(2))
    uuid = next((k for k in manifest if k.startswith(ASSET_UUID_PREFIX)), None)
    if uuid is None:
        return f"{target.name}: asset {ASSET_UUID_PREFIX} introuvable"
    entry = manifest[uuid]
    raw = base64.b64decode(entry["data"])
    comp = entry.get("compressed", False)
    src = gzip.decompress(raw).decode("utf-8") if comp else raw.decode("utf-8")
    new_src, changes = patch_src(src)
    if new_src == src:
        return f"{target.name}: {', '.join(changes)}"
    nd = new_src.encode("utf-8")
    if comp:
        nd = gzip.compress(nd)
    entry["data"] = base64.b64encode(nd).decode("ascii")
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[: m.start(2)] + new_manifest_json + html[m.end(2) :]
    target.write_text(new_html, encoding="utf-8")
    return f"{target.name}: [{', '.join(changes)}] (src {len(src)} → {len(new_src)})"


if __name__ == "__main__":
    for fn in TARGETS:
        print(patch_one(REPO / fn))

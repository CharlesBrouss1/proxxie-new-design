#!/usr/bin/env python3
"""Ajoute la carte Future-Proof 2035 en première position de TESTS_ORIENTATION
dans Proxxie Tests.html, et bump le compteur de tests (16 → 17 où mentionné).

Pourquoi en première position : c'est le test signature Proxxie, le hook
marketing (« auras-tu un métier en 2035 ? »). Il doit être visible en premier.

Idempotent : détection par présence de `code: "FuturProof"` avant insertion.
"""
import re
import json
import base64
import gzip
import pathlib

REPO = pathlib.Path(__file__).parent
TARGETS = ["Proxxie Tests.html", "tests.html"]
ASSET_UUID_PREFIX = "61feca88"

FUTUREPROOF_CARD = (
    '{ code: "FuturProof", name: "Score Future-Proof 2035", '
    'model: "WEF + OECD + McKinsey 2024-25", '
    'accent: "#C2410C", accentSoft: "rgba(194,65,12,0.12)", '
    'href: "./Proxxie Test FuturProof.html", duration: "5 min", '
    'questions: "30 questions", eyebrow: "Métier 2035 · signature Proxxie",\n'
    '    short: "Auras-tu un métier que l\'IA ne fera pas à ta place en 2035 ? Mesure 3 piliers : ce qui reste humain, ce que l\'IA peut augmenter chez toi, ta capacité à pivoter.",\n'
    '    long: "Test signature Proxxie, construit sur 3 frameworks crédibles : WEF Future of Jobs 2025, OECD Skills Outlook 2023, McKinsey GenAI & Future of Work 2024. Pas un instrument psychométrique validé : un outil de positionnement orienté coaching avec 5 familles de métiers résilients.",\n'
    '    output: "Score IA-résilience 0-100 + 3 piliers + 3 familles de métiers", '
    'results: [{k:"Score Future-Proof",v:"0-100 sur 3 piliers équipondérés (humain, augmentation IA, adaptation)."},'
    '{k:"3 familles de métiers",v:"Le top 3 des familles où ce profil a un avantage durable face à l\'IA."},'
    '{k:"3 forces",v:"Les compétences que tu coches le plus fort, à valoriser dans ton parcours."},'
    '{k:"3 leviers à 6 mois",v:"Les compétences les plus fragiles, avec une piste d\'action concrète."}], '
    'tags: ["IA", "Signature Proxxie", "Métier 2035"],\n'
    '    icon: (<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>) }'
)

MARKER = 'code: "FuturProof"'


def patch_src(src: str) -> tuple[str, list[str]]:
    changes: list[str] = []
    if MARKER in src:
        return src, ["déjà présent (skip)"]

    # Find the start of TESTS_ORIENTATION = [
    m = re.search(r"const TESTS_ORIENTATION\s*=\s*\[\s*", src)
    if not m:
        return src, ["WARN TESTS_ORIENTATION introuvable"]

    insert_at = m.end()
    # Insert as first card, comma-separator after
    src = src[:insert_at] + FUTUREPROOF_CARD + ",\n  " + src[insert_at:]
    changes.append("+ carte Future-Proof en 1ère position de TESTS_ORIENTATION")

    # Bump counters visible : "16 tests" → "17 tests" (string match safe)
    # On ne touche que les occurrences EXACTES qui parlent du compteur
    # (pas les noms internes).
    n_bumps = 0
    new_src = re.sub(r'\b16\s+tests\b', '17 tests', src)
    n_bumps = len(re.findall(r'\b16\s+tests\b', src))
    if n_bumps > 0:
        src = new_src
        changes.append(f"compteur 16 → 17 tests ({n_bumps}x)")

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

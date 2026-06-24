#!/usr/bin/env python3
"""Aligne le test CAAS sur le proto famille dans toutes les versions du repo :
items reformulés à la 1re personne (« je »), échelle de capacité → échelle
d'accord, hint/introLead cohérents.

Couvre deux banques d'items :
  - banque standard 24 items (pages dédiées Test CAAS / test-caas, via générateur)
  - banque étendue 48 items (Proxxie Lab.html + proto local lab)

Re-runnable, idempotent. Traite plaintext ET assets compressés (manifest
gzip+base64), comme _patch_bundle.py.

Usage :
  DRY=1 python3 _patch_caas_reword.py   # rapport sans écriture
  python3 _patch_caas_reword.py         # applique (avec .bak)
"""
import re, json, base64, gzip, os, pathlib

REPO = pathlib.Path(__file__).parent
DRY = os.environ.get("DRY") == "1"
EXTRA_DIRS = [REPO, REPO.parent / "proxxie-lab-proto"]
CAAS_MARKER = "ressemblera mon"  # couvre l'ancien "futur" et le nouveau "avenir"

# Banque standard (24) — pages dédiées + générateur. Mock hero inclus.
STD_24 = [
    ("Penser à ce à quoi ressemblera mon futur.", "Je pense souvent à ce à quoi ressemblera mon avenir."),
    ("Réaliser que les choix d'aujourd'hui construisent mon avenir.", "Je réalise que mes choix d'aujourd'hui construisent mon avenir."),
    ("Me préparer pour le futur.", "Je me prépare pour le futur."),
    ("Prendre conscience des choix éducatifs et professionnels à faire.", "J'ai conscience des choix d'études et de métier que j'aurai à faire."),
    ("Planifier comment atteindre mes objectifs.", "Je planifie comment atteindre mes objectifs."),
    ("Me soucier de ma future carrière.", "Je me soucie de ma future carrière."),
    ("Être responsable de mes propres choix.", "Je me sens responsable de mes propres choix."),
    ("Compter sur moi-même.", "Je compte sur moi-même."),
    ("Décider par moi-même.", "Je décide par moi-même."),
    ("Tenir mes engagements.", "Je tiens mes engagements."),
    ("Faire ce qui est juste pour moi.", "Je fais ce qui est juste pour moi."),
    ("Faire les choses moi-même.", "Je fais les choses par moi-même."),
    ("Explorer ce qui m'entoure.", "J'explore ce qui m'entoure."),
    ("Chercher des opportunités de progression personnelle.", "Je cherche des occasions de progresser."),
    ("Explorer les différentes façons de faire les choses.", "J'explore différentes façons de faire les choses."),
    ("Approfondir les questions qui me semblent importantes.", "J'approfondis les questions qui me semblent importantes."),
    ("Devenir curieux(se) de nouvelles opportunités.", "Je suis curieux(se) des nouvelles opportunités."),
    ("Étudier les différents rôles que je pourrais jouer.", "J'explore les différents rôles que je pourrais jouer."),
    ("Accomplir des tâches efficacement.", "J'accomplis mes tâches efficacement."),
    ("Prendre soin de bien faire les choses.", "Je prends soin de bien faire les choses."),
    ("Apprendre de nouvelles compétences.", "J'apprends de nouvelles compétences."),
    ("Travailler à la hauteur de mes capacités.", "Je travaille à la hauteur de mes capacités."),
    ("Surmonter les obstacles.", "Je surmonte les obstacles."),
    ("Résoudre des problèmes.", "Je résous les problèmes que je rencontre."),
]

# Banque étendue (48) — Lab.html + lab-proto. Les items partagés avec STD_24
# mappent vers la même cible (cohérence garantie).
LAB_48 = [
    # CN · Anticiper
    ("Penser à ce à quoi ressemblera mon futur.", "Je pense souvent à ce à quoi ressemblera mon avenir."),
    ("Réaliser que les choix d'aujourd'hui construisent mon avenir.", "Je réalise que mes choix d'aujourd'hui construisent mon avenir."),
    ("Me préparer pour le futur.", "Je me prépare pour le futur."),
    ("Prendre conscience des choix d'études et de métier à faire.", "J'ai conscience des choix d'études et de métier que j'aurai à faire."),
    ("Planifier comment atteindre mes objectifs.", "Je planifie comment atteindre mes objectifs."),
    ("Me soucier de ma future carrière.", "Je me soucie de ma future carrière."),
    ("Anticiper les étapes de mon parcours.", "J'anticipe les étapes de mon parcours."),
    ("Imaginer où je veux être dans quelques années.", "J'imagine où je veux être dans quelques années."),
    ("Réfléchir aujourd'hui à mon orientation de demain.", "Je réfléchis dès aujourd'hui à mon orientation de demain."),
    ("Garder mes objectifs de carrière en tête.", "Je garde mes objectifs de carrière en tête."),
    ("Préparer les transitions avant qu'elles n'arrivent.", "Je prépare les transitions avant qu'elles n'arrivent."),
    ("Me fixer un cap pour les années à venir.", "Je me fixe un cap pour les années à venir."),
    # CT · Décider
    ("Être responsable de mes propres choix.", "Je me sens responsable de mes propres choix."),
    ("Compter sur moi-même.", "Je compte sur moi-même."),
    ("Décider par moi-même.", "Je décide par moi-même."),
    ("Tenir mes engagements.", "Je tiens mes engagements."),
    ("Faire ce qui est juste pour moi.", "Je fais ce qui est juste pour moi."),
    ("Faire les choses par moi-même.", "Je fais les choses par moi-même."),
    ("Assumer les conséquences de mes décisions.", "J'assume les conséquences de mes décisions."),
    ("Rester maître de mon parcours.", "Je reste maître de mon parcours."),
    ("Agir selon mes propres convictions.", "J'agis selon mes propres convictions."),
    ("Me discipliner pour avancer.", "Je me discipline pour avancer."),
    ("Prendre mes responsabilités sans me défausser.", "Je prends mes responsabilités sans me défausser."),
    ("Décider ce qui est bon pour moi sans me laisser dicter.", "Je décide ce qui est bon pour moi sans me laisser dicter."),
    # CU · Explorer
    ("Explorer ce qui m'entoure.", "J'explore ce qui m'entoure."),
    ("Chercher des occasions de progresser.", "Je cherche des occasions de progresser."),
    ("Explorer différentes façons de faire les choses.", "J'explore différentes façons de faire les choses."),
    ("Approfondir les questions qui me semblent importantes.", "J'approfondis les questions qui me semblent importantes."),
    ("Rester curieux(se) des nouvelles occasions.", "Je reste curieux(se) des nouvelles occasions."),
    ("Étudier les différents rôles que je pourrais jouer.", "J'explore les différents rôles que je pourrais jouer."),
    ("M'informer sur des métiers que je connais mal.", "Je m'informe sur des métiers que je connais mal."),
    ("Tester de nouvelles expériences pour mieux me connaître.", "Je teste de nouvelles expériences pour mieux me connaître."),
    ("Observer comment d'autres réussissent leur parcours.", "J'observe comment d'autres réussissent leur parcours."),
    ("Poser des questions sur ce qui m'intrigue.", "Je pose des questions sur ce qui m'intrigue."),
    ("Sortir de ma zone de confort pour apprendre.", "Je sors de ma zone de confort pour apprendre."),
    ("Explorer des chemins auxquels je n'avais pas pensé.", "J'explore des chemins auxquels je n'avais pas pensé."),
    # CF · Oser
    ("Accomplir des tâches efficacement.", "J'accomplis mes tâches efficacement."),
    ("Prendre soin de bien faire les choses.", "Je prends soin de bien faire les choses."),
    ("Apprendre de nouvelles compétences.", "J'apprends de nouvelles compétences."),
    ("Travailler à la hauteur de mes capacités.", "Je travaille à la hauteur de mes capacités."),
    ("Surmonter les obstacles.", "Je surmonte les obstacles."),
    ("Résoudre des problèmes.", "Je résous les problèmes que je rencontre."),
    ("Mener à bien une tâche difficile.", "Je mène à bien une tâche difficile."),
    ("Faire face à l'imprévu sans me décourager.", "Je fais face à l'imprévu sans me décourager."),
    ("Tenir bon malgré les difficultés.", "Je tiens bon malgré les difficultés."),
    ("Compter sur mes compétences pour réussir.", "Je compte sur mes compétences pour réussir."),
    ("Atteindre les buts que je me fixe.", "J'atteins les buts que je me fixe."),
    ("Rebondir après un échec.", "Je rebondis après un échec."),
]

# Union dédupliquée (old → new). Les doublons mappent à l'identique.
ITEMS = {}
for old, new in STD_24 + LAB_48:
    ITEMS[old] = new
# Trier par longueur décroissante d'old pour éviter qu'un old plus court
# (sous-chaîne) ne s'applique avant un plus long.
ITEMS_ORDERED = sorted(ITEMS.items(), key=lambda kv: -len(kv[0]))

# Échelle capacité → accord (libellés individuels, CAAS-uniques).
SCALE = [
    ("Pas du tout fort", "Pas du tout"),
    ("Un peu fort", "Plutôt non"),
    ("Moyennement fort", "Neutre"),
    ("Très fort", "Plutôt oui"),
    ("Extrêmement fort", "Tout à fait"),
    ("pas du tout fort", "pas du tout"),
    ("extrêmement fort", "tout à fait"),
]
# "Moyennement" seul (mock hero) : ne convertir QUE s'il est encadré par les
# libellés déjà convertis — évite les 10 "Moyennement" en prose ailleurs.
SCALE_CONTEXT = [
    ('"Plutôt non", "Moyennement", "Plutôt oui"', '"Plutôt non", "Neutre", "Plutôt oui"'),
    ('"Plutôt non","Moyennement","Plutôt oui"', '"Plutôt non","Neutre","Plutôt oui"'),
]
# Framing capacité spécifique Lab/lab-proto (hint + introLead).
FRAMING = [
    ('["Peu développé","Très développé"]', '["Pas du tout","Tout à fait"]'),
    ('["Peu développé", "Très développé"]', '["Pas du tout", "Tout à fait"]'),
    (" Réponds selon ce que tu sens développé en toi.", " Réponds spontanément."),
]


def transform(text):
    n_items = 0
    for old, new in ITEMS_ORDERED:
        c = text.count(old)
        if c:
            text = text.replace(old, new)
            n_items += c
    n_scale = 0
    if CAAS_MARKER in text:
        for old, new in SCALE + SCALE_CONTEXT + FRAMING:
            c = text.count(old)
            if c:
                text = text.replace(old, new)
                n_scale += c
    return text, n_items, n_scale


def process_file(path):
    raw = path.read_text(encoding="utf-8")
    html = raw
    total_items = total_scale = 0
    asset_hits = 0

    m = re.search(r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)', html, re.DOTALL)
    if m:
        try:
            manifest = json.loads(m.group(2))
        except Exception:
            manifest = None
        if manifest is not None:
            changed = False
            for uuid, entry in manifest.items():
                if not isinstance(entry, dict) or "data" not in entry:
                    continue
                data = base64.b64decode(entry["data"])
                compressed = entry.get("compressed", False)
                if compressed:
                    try:
                        data = gzip.decompress(data)
                    except Exception:
                        continue
                try:
                    text = data.decode("utf-8")
                except Exception:
                    continue
                if CAAS_MARKER not in text and not any(o in text for o in ITEMS):
                    continue
                new_text, ni, ns = transform(text)
                if ni or ns:
                    total_items += ni
                    total_scale += ns
                    asset_hits += 1
                    if not DRY:
                        nd = new_text.encode("utf-8")
                        if compressed:
                            nd = gzip.compress(nd)
                        entry["data"] = base64.b64encode(nd).decode("ascii")
                        changed = True
            if changed and not DRY:
                new_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
                html = html[:m.start(2)] + new_json + html[m.end(2):]

    new_html, ni, ns = transform(html)
    if ni or ns:
        total_items += ni
        total_scale += ns
        html = new_html

    if (total_items or total_scale) and not DRY and html != raw:
        bak = path.with_suffix(path.suffix + ".bak-caasreword")
        if not bak.exists():
            bak.write_text(raw, encoding="utf-8")
        path.write_text(html, encoding="utf-8")

    return total_items, total_scale, asset_hits


def main():
    targets = []
    for d in EXTRA_DIRS:
        if d.exists():
            targets += sorted(d.glob("*.html"))
    gen = REPO / "_patch_build_caas.py"
    if gen.exists():
        targets.append(gen)

    print(f"{'DRY-RUN' if DRY else 'APPLY'} · {len(targets)} fichiers\n")
    touched = 0
    for p in targets:
        if ".bak" in p.name:
            continue
        try:
            ti, ts, ah = process_file(p)
        except Exception as e:
            print(f"  ! erreur {p.name}: {e}")
            continue
        if ti or ts:
            touched += 1
            loc = p.parent.name + "/" + p.name
            print(f"  {loc:52s} items={ti:3d} échelle={ts:3d}" + (f"  [asset]" if ah else ""))
    print(f"\n{touched} fichier(s) {'à modifier' if DRY else 'modifié(s)'}.")


if __name__ == "__main__":
    main()

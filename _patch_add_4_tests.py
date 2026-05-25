#!/usr/bin/env python3
"""Ajout des 4 nouveaux tests recommandés par la synthèse Proxxie 2026-05-25.

Tests ajoutés (3 en Orientation, 1 en Profils atypiques) :
  · Raisonnement (ICAR)            · GMA · #1 prédicteur emploi (Schmidt & Hunter)
  · Grit (Duckworth)               · persévérance · best-seller mondial
  · CAAS (Savickas)                · adaptabilité carrière · futur IA
  · PHQ-9 (Kroenke 2001)           · dépression · miroir manquant du GAD-7

Modifications :
  · Insère 3 entrées dans TESTS_ORIENTATION (avant le ];)
  · Insère 1 entrée dans TESTS_ATYPIQUE (juste après Anxiété, son pair clinique)
  · Met à jour TestCard pour gérer le flag bientot=true (4 nouveaux tests · pages à venir)
  · Met à jour le tableau ComparisonTable (4 nouvelles lignes)
  · Met à jour les compteurs : 12 tests → 16, 7 tests → 10, 5 screenings → 6,
    Douze → Seize, Les sept tests → Les seize tests, lecture croisée des 12 → 16.
  · Met à jour NAV_RESOURCES (badge "12 tests" + description).

Idempotent · sentinelles BEGIN/END pour les blocs JSX, replace simple pour les
chaînes (les nouvelles valeurs ne re-déclenchent pas le replace).
"""
import re, json, base64, gzip, pathlib, sys

REPO = pathlib.Path(__file__).parent
TARGETS = ["Proxxie Tests.html"]
ASSET_UUID_PREFIX = "61feca88"  # asset JS qui contient les arrays TESTS_*

BEGIN_O = "/* PROXXIE_ADD_4_TESTS_ORIENTATION_BEGIN */"
END_O   = "/* PROXXIE_ADD_4_TESTS_ORIENTATION_END */"
BEGIN_A = "/* PROXXIE_ADD_4_TESTS_ATYPIQUE_BEGIN */"
END_A   = "/* PROXXIE_ADD_4_TESTS_ATYPIQUE_END */"
BEGIN_T = "/* PROXXIE_ADD_4_TESTS_TABLE_BEGIN */"
END_T   = "/* PROXXIE_ADD_4_TESTS_TABLE_END */"
BEGIN_C = "/* PROXXIE_ADD_4_TESTS_CARD_BEGIN */"
END_C   = "/* PROXXIE_ADD_4_TESTS_CARD_END */"

# ---------- 3 nouvelles entrées TESTS_ORIENTATION ----------

NEW_ORIENTATION = BEGIN_O + r"""
  { code: "Raisonnement", name: "Test Raisonnement", model: "ICAR-Sample (cognition)", accent: "#1E88E5", accentSoft: "rgba(30,136,229,0.12)", href: "#bientot", bientot: true, duration: "12 min", questions: "12 questions", eyebrow: "Raisonnement cognitif",
    short: "Cartographie ses zones de confort cognitif. Pas un test de QI : un outil de découverte.",
    long: "ICAR (International Cognitive Ability Resource, Condon & Revelle 2014) est un test open-source validé. Le raisonnement général est, selon 30 ans de recherche (Schmidt & Hunter 1998), le meilleur prédicteur de performance professionnelle, toutes professions confondues.",
    output: "Profil cognitif (verbal · numérique · figural)", results: [{k:"Profil 3 axes",v:"Score sur 3 dimensions du raisonnement · verbal, numérique, figural (matrices)."},{k:"Zones fortes",v:"Identification des modalités où l'ado est le plus à l'aise et celles à muscler."},{k:"Adéquation filières",v:"Filières post-bac qui s'appuient sur les forces cognitives détectées."},{k:"Préparation tests",v:"Conseils ciblés si concours ou tests d'admission (Sciences Po, prépa, écoles ingé)."}], tags: ["Raisonnement", "ICAR"],
    icon: (<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><path d="M14 14h7v7"/><path d="M17 14v7M14 17h7"/></svg>) },
  { code: "Grit", name: "Test Grit", model: "Grit-S (Duckworth)", accent: "#6B46C1", accentSoft: "rgba(107,70,193,0.12)", href: "#bientot", bientot: true, duration: "5 min", questions: "8 questions", eyebrow: "Persévérance",
    short: "Mesure la 'grit' : passion + persévérance pour les objectifs long terme.",
    long: "L'échelle Grit-S d'Angela Duckworth (Penn, 2009). Utilisée par West Point, Stanford et Yale pour identifier qui termine ses études et qui décroche. Best-seller mondial (livre Grit, 2016).",
    output: "Score Grit + percentile par âge", results: [{k:"Score global",v:"Score Grit sur 5, avec percentile par tranche d'âge et genre."},{k:"Passion vs persévérance",v:"Décomposition entre constance des intérêts (passion) et effort soutenu (persévérance)."},{k:"Pistes concrètes",v:"3 leviers pour développer la grit au quotidien (sport, projet long, mentor)."},{k:"Alerte décrochage",v:"Si score bas + filière exigeante, signal d'alerte sur le risque de décrochage."}], tags: ["Persévérance", "Grit"],
    icon: (<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2v6M12 16v6M4.93 4.93l4.24 4.24M14.83 14.83l4.24 4.24M2 12h6M16 12h6M4.93 19.07l4.24-4.24M14.83 9.17l4.24-4.24"/></svg>) },
  { code: "CAAS", name: "Test Adaptabilité Carrière", model: "CAAS (Savickas)", accent: "#00897B", accentSoft: "rgba(0,137,123,0.12)", href: "#bientot", bientot: true, duration: "7 min", questions: "24 questions", eyebrow: "Adaptabilité au futur",
    short: "Mesure les 4 muscles de l'adaptation carrière dans un monde qui change vite.",
    long: "Career Adapt-Abilities Scale (Savickas & Porfeli, 2012). Validé dans 18 pays. 4 dimensions : Concern (anticiper), Control (décider), Curiosity (explorer), Confidence (oser). Compétence-clé à l'ère de l'IA.",
    output: "Profil sur 4 dimensions CAAS", results: [{k:"4 dimensions",v:"Score sur Concern, Control, Curiosity, Confidence avec niveau (faible · moyen · fort)."},{k:"Dimension à muscler",v:"La dimension la plus faible, avec 3 exercices concrets pour la renforcer en 30 jours."},{k:"Profil archétype",v:"Archétype d'adaptabilité (Explorateur, Stratège, Audacieux, Anticipateur)."},{k:"Métiers d'avenir",v:"5 familles de métiers résilients à l'automatisation, alignées avec le profil."}], tags: ["Adaptabilité", "Futur du travail"],
    icon: (<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 1 1-9-9c2.5 0 4.8 1 6.5 2.6"/><path d="M21 3v6h-6"/></svg>) },
""" + END_O

ANCHOR_O = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-6 8-12a8 8 0 1 0-16 0c0 6 8 12 8 12z"/><circle cx="12" cy="10" r="3"/></svg>) },\n];'

# ---------- 1 nouvelle entrée TESTS_ATYPIQUE (après Anxiété, son pair clinique) ----------

NEW_ATYPIQUE = BEGIN_A + r"""
  { code: "Dépression", name: "Test Dépression", model: "PHQ-9 (Kroenke)", accent: "#5C6BC0", accentSoft: "rgba(92,107,192,0.12)", href: "./Proxxie Test PHQ9.html", duration: "3 min", questions: "9 questions", eyebrow: "Traits dépressifs",
    short: "Screening PHQ-9, outil clinique de référence pour la dépression chez l'ado.",
    long: "Patient Health Questionnaire (Kroenke, Spitzer & Williams, 2001). Utilisé en médecine générale dans le monde entier. Complète le GAD-7 (anxiété) qui n'évalue qu'une moitié du couple anxiété-dépression. Anxiété + dépression sont co-occurrentes dans 50-60% des cas.",
    output: "Score PHQ-9 + niveau de sévérité", results: [{k:"Score PHQ-9",v:"Score sur 27 avec niveau clinique · minimal, léger, modéré, modérément sévère, sévère."},{k:"Anxiété + dépression",v:"Lecture croisée GAD-7 / PHQ-9 si les deux tests sont passés. Comorbidité fréquente à l'ado."},{k:"Alerte sécurité",v:"Si signaux d'idées noires (item 9), affichage immédiat du 3114 (numéro national prévention suicide)."},{k:"Pistes graduées",v:"Pistes par niveau · auto-régulation, posture parent, ou consultation pédopsy."}], tags: ["Dépression", "Screening", "PHQ-9"],
    icon: (<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d="M3 12a9 9 0 1 0 18 0 9 9 0 0 0-18 0z"/><path d="M8 9h.01M16 9h.01M16 16c-1-1-2-1.5-4-1.5s-3 .5-4 1.5"/></svg>) },
""" + END_A

# Anchor : juste après l'entrée Anxiété (avant DYS) dans TESTS_ATYPIQUE
# On termine l'ancre au \n qui suit la fermeture d'Anxiété, et on insère
# entre. La ligne DYS suivante reste intacte.
ANCHOR_A = '<path d="M3 12a9 9 0 1 0 18 0 9 9 0 0 0-18 0z"/><path d="M8 9h.01M16 9h.01M8 16c1-1 2-1.5 4-1.5s3 .5 4 1.5"/></svg>) },\n'

# ---------- 4 nouvelles lignes ComparisonTable ----------

NEW_TABLE = BEGIN_T + r"""
            { q: "Comment raisonne-t-il sur des problèmes nouveaux ?",   m: "Raisonnement", t: "12 min", r: "Profil cognitif 3 axes",    c: "#1E88E5" },
            { q: "Va-t-il tenir sur la durée ou décrocher ?",             m: "Grit",         t: "5 min",  r: "Score Grit + percentile",   c: "#6B46C1" },
            { q: "Saura-t-il s'adapter aux métiers de demain ?",          m: "CAAS",         t: "7 min",  r: "4 dimensions adaptabilité", c: "#00897B" },
            { q: "Présente-t-il des signes de dépression ?",              m: "Dépression",   t: "3 min",  r: "Score PHQ-9 + niveau",      c: "#5C6BC0" },
""" + END_T

# Anchor : juste après la ligne DYS (dernière du tableau)
ANCHOR_T = "{ q: \"A-t-il un trouble DYS (lecture, calcul...) ?\",     m: \"DYS\",    t: \"6 min\",  r: \"Domaines DYS marqués\",     c: \"#FD6936\" },\n"

# ---------- Modification TestCard pour gérer flag bientot ----------
# On modifie 2 endroits :
# 1. <a href={t.href}> devient <a href={t.bientot ? "#" : t.href} onClick={t.bientot ? (e) => e.preventDefault() : undefined}>
# 2. "Démarrer" devient {t.bientot ? "Bientôt disponible" : "Démarrer"}
# 3. Ajout d'un badge "BIENTÔT" en haut de la card si t.bientot

CARD_HREF_OLD = '  <a href={t.href} style={{'
CARD_HREF_NEW = '  <a href={t.bientot ? "#" : t.href} onClick={t.bientot ? (e) => e.preventDefault() : undefined} style={{'

CARD_BIENTOT_BADGE_OLD = '<div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 18 }}>\n      <div style={{ width: 56, height: 56,'
CARD_BIENTOT_BADGE_NEW = ('<div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 18, position: "relative" }}>\n'
    '      ' + BEGIN_C + '\n'
    '      {t.bientot && (\n'
    '        <span style={{ position: "absolute", top: -14, right: -14, background: "#F5EB3F", color: "#0A0E2C", fontSize: 9.5, fontWeight: 800, padding: "4px 9px", borderRadius: 99, letterSpacing: "0.08em", textTransform: "uppercase" }}>\n'
    '          Bientôt\n'
    '        </span>\n'
    '      )}\n'
    '      ' + END_C + '\n'
    '      <div style={{ width: 56, height: 56,')

CARD_CTA_OLD = '        Démarrer <Icon.arrow style={{ width: 14, height: 14 }} />\n'
CARD_CTA_NEW = '        {t.bientot ? "Bientôt disponible" : "Démarrer"} <Icon.arrow style={{ width: 14, height: 14 }} />\n'

# Une 4e variante : la couleur du CTA passe en muted si bientot
# Pas critique, on garde l'accent — visuellement c'est plus lisible.

# ---------- Substitutions de compteurs (idempotent : nouvelles valeurs ne re-matchent pas) ----------

COUNT_REPLACEMENTS = [
    # NAV_RESOURCES
    ('"12 tests : OCEAN, RIASEC, PCM, MBTI, Drivers, Valeurs, Besoins, TDAH, Autisme, HPI, Anxiété, DYS."',
     '"16 tests : OCEAN, RIASEC, Raisonnement, Grit, CAAS, PCM, MBTI, Drivers, Valeurs, Besoins, TDAH, Autisme, HPI, Anxiété, Dépression, DYS."'),
    ('badge: "12 tests · gratuit"', 'badge: "16 tests · gratuit"'),
    # Hero pill
    (' 12 tests · 100% gratuits · sans inscription',
     ' 16 tests · 100% gratuits · sans inscription'),
    # Sous-titre hero
    ('Douze tests répartis en 2 catégories : 7 tests psychométriques pour cerner personnalité, intérêts et motivations ; 5 screenings pour identifier d\'éventuels traits TDAH, autisme, HPI, anxiété ou troubles DYS.',
     'Seize tests répartis en 2 catégories : 10 tests d\'orientation (personnalité, intérêts, raisonnement, persévérance, adaptabilité) ; 6 screenings santé mentale et apprentissage (TDAH, autisme, HPI, anxiété, dépression, DYS).'),
    # Catégorie 1
    ('title="7 tests pour comprendre qui est votre ado"',
     'title="10 tests pour comprendre qui est votre ado"'),
    # Catégorie 2
    ('title="5 screenings pour les neuro-atypies et l\'anxiété"',
     'title="6 screenings pour neuro-atypies, anxiété et dépression"'),
    # ComparisonTable intro
    ('Les sept tests sont complémentaires.', 'Les seize tests sont complémentaires.'),
    # Rapport mention
    ('Lecture croisée des 12 tests', 'Lecture croisée des 16 tests'),
    # Comment commentaire Master en haut
    ('listant les 7 tests d\'orientation', 'listant les 10 tests d\'orientation'),
    # Phrase "combinés, ils dessinent un portrait" + count
    ('combine ces 12 tests', 'combine ces 16 tests'),
    ('Le rapport Proxxie combine ces 12 tests',
     'Le rapport Proxxie combine ces 16 tests'),
]

# ---------- Plomberie ----------

def strip_between(src: str, begin: str, end: str) -> str:
    """Remove begin..end inclusive (idempotent re-application)."""
    pat = re.compile(re.escape(begin) + r'.*?' + re.escape(end), re.DOTALL)
    return pat.sub('', src)

def insert_after(src: str, anchor: str, payload: str, label: str) -> str:
    if anchor not in src:
        raise RuntimeError(f"anchor introuvable pour {label}: {anchor[:80]!r}")
    return src.replace(anchor, anchor + payload, 1)

def patch_src(src: str) -> tuple[str, list[str]]:
    changes = []
    # 1. Strip prior runs (idempotence)
    for b, e in [(BEGIN_O, END_O), (BEGIN_A, END_A), (BEGIN_T, END_T), (BEGIN_C, END_C)]:
        src = strip_between(src, b, e)

    # 2. Insert 3 new orientation tests
    src = insert_after(src, ANCHOR_O.replace('];', ''), '\n' + NEW_ORIENTATION, "TESTS_ORIENTATION")
    changes.append("+3 orientation (Raisonnement, Grit, CAAS)")

    # 3. Insert 1 new atypique test (between Anxiété and DYS)
    src = insert_after(src, ANCHOR_A, NEW_ATYPIQUE + '\n', "TESTS_ATYPIQUE")
    changes.append("+1 atypique (PHQ-9 Dépression)")

    # 4. Insert 4 new table rows
    src = insert_after(src, ANCHOR_T, NEW_TABLE, "ComparisonTable")
    changes.append("+4 lignes tableau")

    # 5. Modify TestCard (3 surgical edits)
    if CARD_HREF_OLD in src:
        src = src.replace(CARD_HREF_OLD, CARD_HREF_NEW, 1)
        changes.append("TestCard href")
    if CARD_BIENTOT_BADGE_OLD in src:
        src = src.replace(CARD_BIENTOT_BADGE_OLD, CARD_BIENTOT_BADGE_NEW, 1)
        changes.append("TestCard badge bientôt")
    if CARD_CTA_OLD in src:
        src = src.replace(CARD_CTA_OLD, CARD_CTA_NEW, 1)
        changes.append("TestCard CTA")

    # 6. Compteurs
    for old, new in COUNT_REPLACEMENTS:
        if old in src:
            src = src.replace(old, new)
            changes.append(f"count: {old[:40]}...")
        elif new in src:
            pass  # already applied
        else:
            changes.append(f"WARN count manquant: {old[:60]!r}")
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
    if new_src == src:
        return f"{target.name}: aucun changement (déjà à jour ?)"

    nd = new_src.encode('utf-8')
    if comp:
        nd = gzip.compress(nd)
    entry['data'] = base64.b64encode(nd).decode('ascii')
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]
    target.write_text(new_html, encoding='utf-8')
    return f"{target.name}: patched [{', '.join(changes)}] (asset {uuid[:8]}, src {len(src)} → {len(new_src)})"

if __name__ == "__main__":
    for fn in TARGETS:
        print(patch_one(REPO / fn))

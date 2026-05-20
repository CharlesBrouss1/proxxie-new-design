#!/usr/bin/env python3
"""Inject a runtime "tu/vous" swapper into Proxxie dashboard/rapport/documents pages.

These pages bundle a React app via Pretext. Rather than modify the React JSX
inline (50+ string changes spread across multiple manifest assets), we add a
small <script> at the end of the template body. It:

  1. Reads role from ?role=parent|enfant or localStorage.
  2. When role=enfant, walks DOM text nodes and substitutes a curated list
     of phrases from formal (vous) to informal (tu).
  3. Sets up a MutationObserver so substitutions also apply to React's
     subsequent renders (drawers, modals, etc.).

Idempotent: skipped if marker is present.
"""
import re, json, pathlib, sys

REPO = pathlib.Path(__file__).parent
TARGETS = [
    "dashboard.html", "Proxxie Dashboard.html",
    "rapport.html", "Proxxie Rapport.html",
    "documents.html", "Proxxie Documents.html",
]
MARKER = "__proxxie_role_runtime_v1__"

# Substitutions, longest first. Plain string replacement (no regex).
# Order matters: longer phrases catch context before shorter ones strike.
SUBS = [
    # Specific full sentences (longest)
    ["Une fois inscrit·e et après votre RDV avec Charles, vous retrouverez les vraies données de votre ado.",
     "Une fois inscrit·e et après ton RDV avec Charles, tu retrouveras tes vraies données."],
    ["Aucune obligation. Si vous ne parrainez personne, votre parcours Proxxie reste entier. Les 3 séances sont un bonus, pas un prérequis.",
     "Aucune obligation. Si tu ne parraines personne, ton parcours Proxxie reste entier. Les 3 séances sont un bonus, pas un prérequis."],
    ["Aucun partage n'est automatique. Vous gardez le contrôle complet, et pouvez révoquer un lien en 1 clic.",
     "Aucun partage n'est automatique. Tu gardes le contrôle complet, et peux révoquer un lien en 1 clic."],
    ["Charles (votre coach) ne peut consulter que les documents que vous avez explicitement partagés. Par défaut, elle ne voit que le rapport généré.",
     "Charles (ton coach) ne peut consulter que les documents que tu as explicitement partagés. Par défaut, elle ne voit que le rapport généré."],
    ["Charles a préparé cette session à partir de votre rapport et de l'historique. Elle arrivera avec des questions précises.",
     "Charles a préparé cette session à partir de ton rapport et de l'historique. Elle arrivera avec des questions précises."],
    ["Chaque ami qui rejoint Proxxie via votre code débloque une séance coach de 30 min ciblée sur un sujet précis.",
     "Chaque ami qui rejoint Proxxie via ton code débloque une séance coach de 30 min ciblée sur un sujet précis."],
    ["Cette étape a été complétée. Aucune action requise — mais vous pouvez la revoir ou l'exporter en PDF.",
     "Cette étape a été complétée. Aucune action requise, mais tu peux la revoir ou l'exporter en PDF."],
    ["En répondant à 4 questions, vous accédez à l'accompagnement le plus adapté à votre situation, aux besoins et au rythme de votre famille.",
     "En répondant à 4 questions, tu accèdes à l'accompagnement le plus adapté à ta situation, à tes besoins et à ton rythme."],
    ["Hébergement français (OVH Roubaix), chiffrement de bout en bout. Vous pouvez supprimer un document à tout moment — la suppression est définitive sous 24 h.",
     "Hébergement français (OVH Roubaix), chiffrement de bout en bout. Tu peux supprimer un document à tout moment, la suppression est définitive sous 24 h."],
    ["Hébergement français. Chiffrement de bout en bout. Aucun document partagé avec un tiers sans votre accord explicite.",
     "Hébergement français. Chiffrement de bout en bout. Aucun document partagé avec un tiers sans ton accord explicite."],
    ["Le rapport est privé par défaut. Chaque partage est nominatif, expirable, et vous voyez qui a lu quoi.",
     "Le rapport est privé par défaut. Chaque partage est nominatif, expirable, et tu vois qui a lu quoi."],
    ["Les données affichées (rapport, documents, métiers, vœux Parcoursup…) sont là à titre indicatif pour vous montrer ce que Proxxie produit.",
     "Les données affichées (rapport, documents, métiers, vœux Parcoursup…) sont là à titre indicatif pour te montrer ce que Proxxie produit."],
    ["Notes de Charles disponibles ci-dessous (section Agir). Vous pouvez aussi réécouter l'enregistrement (chiffré, à votre disposition uniquement).",
     "Notes de Charles disponibles ci-dessous (section Agir). Tu peux aussi réécouter l'enregistrement (chiffré, à ta disposition uniquement)."],
    ["PDF, JPG, PNG · 20 Mo max · vos fichiers sont chiffrés à la réception et ne sont jamais partagés avec un tiers.",
     "PDF, JPG, PNG · 20 Mo max · tes fichiers sont chiffrés à la réception et ne sont jamais partagés avec un tiers."],
    ["Proxxie conserve toutes les versions du rapport. Vous pouvez voir l'évolution des recommandations à mesure que le dossier se complète.",
     "Proxxie conserve toutes les versions du rapport. Tu peux voir l'évolution des recommandations à mesure que le dossier se complète."],
    ["Profil de votre ado croisé aux tendances du marché du travail",
     "Ton profil croisé aux tendances du marché du travail"],
    ["Un rapport actionnable qui croise bulletins, contexte, et — si vous le faites — le test OCEAN-X. Métiers compatibles, secteurs porteurs, et formations Parcoursup adaptées au profil de votre ado.",
     "Un rapport actionnable qui croise bulletins, contexte, et, si tu le fais, le test OCEAN-X. Métiers compatibles, secteurs porteurs, et formations Parcoursup adaptées à ton profil."],
    ["Vous générez un lien sécurisé, nominatif, qui expire dans 30 jours.",
     "Tu génères un lien sécurisé, nominatif, qui expire dans 30 jours."],
    ["Préparation recommandée de votre côté : 5 min pour noter 2-3 points à aborder.",
     "Préparation recommandée de ton côté · 5 min pour noter 2-3 points à aborder."],
    ["Il vous reçoit ensemble ou séparément selon votre préférence — il reste disponible par WhatsApp entre les séances.",
     "Il te reçoit selon ta préférence, il reste disponible par WhatsApp entre les séances."],
    ["pour finaliser. Charles vous accompagne sur la lettre de motivation au prochain RDV.",
     "pour finaliser. Charles t'accompagne sur la lettre de motivation au prochain RDV."],
    [", vous retrouverez ici les vraies données de votre ado.",
     ", tu retrouveras ici tes vraies données."],
    [". Vous pouvez consulter l'intégralité du rapport en ligne — toutes les sections sont navigables.",
     ". Tu peux consulter l'intégralité du rapport en ligne, toutes les sections sont navigables."],
    ["Une fois inscrit·e et après votre RDV avec Charles", "Une fois inscrit·e et après ton RDV avec Charles"],

    # Questions
    ["À quel rythme préférez-vous avancer ?", "À quel rythme préfères-tu avancer ?"],
    ["Êtes-vous en pleine phase Parcoursup ?", "Es-tu en pleine phase Parcoursup ?"],
    ["Quel est votre besoin principal ?", "Quel est ton besoin principal ?"],
    ["Avec qui voulez-vous partager le rapport ?", "Avec qui veux-tu partager le rapport ?"],
    ["Sur quoi voulez-vous travailler avec Charles ?", "Sur quoi veux-tu travailler avec Charles ?"],
    ["En quelle classe est votre ado ?", "En quelle classe es-tu ?"],

    # Mid-length phrases
    ["Trouvons l'accompagnement parfait pour votre ado.", "Trouvons l'accompagnement parfait pour toi."],
    ["L'avenir de votre ado se prépare aujourd'hui.", "Ton avenir se prépare aujourd'hui."],
    ["Notre recommandation pour vous", "Notre recommandation pour toi"],
    ["Modèle à adapter à votre situation", "Modèle à adapter à ta situation"],
    ["Glissez vos fichiers ou parcourez votre ordi", "Glisse tes fichiers ou parcours ton ordi"],
    ["Vous pouvez aussi choisir d'envoyer la", "Tu peux aussi choisir d'envoyer la"],
    ["Compléter la description de Arthur", "Compléter ma description"],
    ["Compléter la description d'Arthur", "Compléter ma description"],

    # Short, specific
    ["Vous pouvez aussi partager", "Tu peux aussi partager"],
    ["Vos données restent privées", "Tes données restent privées"],
    ["🔒 Vos données restent privées", "🔒 Tes données restent privées"],
    ["Votre RDV de 30 min est confirmé pour", "Ton RDV de 30 min est confirmé pour"],
    ["Votre code de parrainage", "Ton code de parrainage"],
    ["Glissez vos fichiers ici", "Glisse tes fichiers ici"],
    ["Vous avez encore", "Tu as encore"],
    ["Réservez 30 min avec Charles", "Réserve 30 min avec Charles"],
    ["débloquez des séances bonus", "débloque des séances bonus"],
    ["30 min · avec votre coach", "30 min · avec ton coach"],
    ["Classe de l'ado", "Ta classe"],
    ["Espace parent", "Espace ado"],
    ["Email parent", "Ton email"],
    ["Tableau de bord parent", "Tableau de bord"],

    # Word-pair fallbacks (lowercase/uppercase variants)
    ["Cliquez sur un trait", "Clique sur un trait"],
    ["Cliquez au centre", "Clique au centre"],
    ["Réservez", "Réserve"],
    ["Cliquez", "Clique"],
    ["Glissez", "Glisse"],
    ["votre ado", "toi"],
    ["Votre ado", "Toi"],
    ["votre coach", "ton coach"],
    ["votre RDV", "ton RDV"],
    ["Votre RDV", "Ton RDV"],
    ["votre rapport", "ton rapport"],
    ["votre côté", "ton côté"],
    ["votre famille", "ta famille"],
    ["votre profil", "ton profil"],
    ["votre parcours", "ton parcours"],
    ["votre situation", "ta situation"],
    ["votre besoin", "ton besoin"],
    ["votre préférence", "ta préférence"],
    ["votre code", "ton code"],
    ["Votre code", "Ton code"],
    ["votre disposition", "ta disposition"],
    ["votre accord", "ton accord"],
    ["votre ordi", "ton ordi"],
    ["vos données", "tes données"],
    ["Vos données", "Tes données"],
    ["vos fichiers", "tes fichiers"],
    ["Vos fichiers", "Tes fichiers"],
    ["vos vœux", "tes vœux"],
    ["vos bulletins", "tes bulletins"],
    ["Vos bulletins", "Tes bulletins"],

    # Generic "Vous + verb" patterns (after specific ones above)
    ["Vous pouvez", "Tu peux"],
    ["vous pouvez", "tu peux"],
    ["Vous avez", "Tu as"],
    ["vous avez", "tu as"],
    ["Vous gardez", "Tu gardes"],
    ["vous gardez", "tu gardes"],
    ["Vous voyez", "Tu vois"],
    ["vous voyez", "tu vois"],
    ["Vous générez", "Tu génères"],
    ["Vous vous", "Tu te"],
    ["pour vous", "pour toi"],
    ["chez vous", "chez toi"],
]


def render_runtime_script():
    subs_json = json.dumps(SUBS, ensure_ascii=False)
    return f"""<script>
/* {MARKER} */
(function() {{
  function getRole() {{
    try {{
      var u = new URLSearchParams(window.location.search).get("role");
      if (u === "parent" || u === "enfant") return u;
      var s = localStorage.getItem("proxxie.role");
      if (s === "parent" || s === "enfant") return s;
    }} catch(e) {{}}
    return "parent";
  }}
  var SUBS = {subs_json};
  SUBS.sort(function(a, b) {{ return b[0].length - a[0].length; }});
  function applyToText(t) {{
    var orig = t;
    for (var i = 0; i < SUBS.length; i++) {{
      if (t.indexOf(SUBS[i][0]) >= 0) t = t.split(SUBS[i][0]).join(SUBS[i][1]);
    }}
    return t === orig ? null : t;
  }}
  function walk(node) {{
    if (!node) return;
    if (node.nodeType === 3) {{
      var nt = applyToText(node.nodeValue);
      if (nt !== null) node.nodeValue = nt;
    }} else if (node.nodeType === 1) {{
      if (node.tagName === "SCRIPT" || node.tagName === "STYLE" || node.tagName === "TEXTAREA" || node.tagName === "INPUT") return;
      var c = node.childNodes;
      for (var i = 0; i < c.length; i++) walk(c[i]);
    }}
  }}
  function init() {{
    var role = getRole();
    if (role !== "enfant") return;
    try {{ localStorage.setItem("proxxie.role", "enfant"); }} catch(e) {{}}
    if (document.body) walk(document.body);
    var obs = new MutationObserver(function(muts) {{
      for (var i = 0; i < muts.length; i++) {{
        var m = muts[i];
        if (m.type === "childList") {{
          for (var j = 0; j < m.addedNodes.length; j++) walk(m.addedNodes[j]);
        }} else if (m.type === "characterData") {{
          walk(m.target);
        }}
      }}
    }});
    obs.observe(document.body, {{ childList: true, characterData: true, subtree: true }});
  }}
  if (document.readyState === "loading") {{
    document.addEventListener("DOMContentLoaded", init);
  }} else {{
    init();
  }}
}})();
</script>"""


def encode_template(tpl_str: str) -> str:
    raw = json.dumps(tpl_str, ensure_ascii=False)
    return raw.replace("</script>", r"<\/script>")


def extract_template(html: str):
    start_m = re.search(r'<script[^>]*type="__bundler/template"[^>]*>', html)
    if not start_m: return None
    last_close = html.rfind("</script>")
    if last_close <= start_m.end(): return None
    raw = html[start_m.end():last_close]
    return start_m.end(), last_close, json.loads(raw.strip())


def patch_one(target: pathlib.Path) -> str:
    if not target.exists():
        return "SKIP missing"
    html = target.read_text(encoding="utf-8")
    ext = extract_template(html)
    if ext is None:
        return "SKIP no template"
    s, e, tpl = ext

    if MARKER in tpl:
        return "noop already patched"

    runtime = render_runtime_script()
    # Inject just before </body>
    if "</body>" not in tpl:
        return "SKIP no </body>"
    new_tpl = tpl.replace("</body>", runtime + "\n</body>", 1)
    new_raw = encode_template(new_tpl)
    new_html = html[:s] + new_raw + html[e:]
    target.write_text(new_html, encoding="utf-8")
    return f"+ patched (tpl {len(tpl)} -> {len(new_tpl)} chars)"


if __name__ == "__main__":
    for fn in TARGETS:
        p = REPO / fn
        print(f"{fn}: {patch_one(p)}")

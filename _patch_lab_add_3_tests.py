#!/usr/bin/env python3
"""Ajoute FuturProof, VIA Strengths et Mindset Dweck au Proxxie Lab.

Proxxie Lab.html n'utilise PAS le bundler · c'est un HTML/JS inline avec une
architecture psychométrique complète. 3 structures à patcher :

1. `FACETS` (carte intérieure du Lab) : mapper chaque test à son groupe
   - perso (Personnalité) : + via, dweck
   - carr (Carrière) : + futureproof
2. `GMETA` (libellés courts du nœud sur la carte) : 3 nouvelles entrées
3. `TESTS` (définition complète : items, dims, portraits, about) : 3 entrées
   complètes, items réduits pour ne pas exploser le poids du fichier.

Idempotent : détection par présence des clés (`futureproof:`, `via:`, `dweck:`).
"""
import re
import pathlib

REPO = pathlib.Path(__file__).parent
TARGET = REPO / "Proxxie Lab.html"

# === 1. FACETS : ajouter les codes aux groupes ===

FACETS_UPDATES = [
    # (group_key, tests_to_add)
    ("perso", ["via", "dweck"]),
    ("carr", ["futureproof"]),
]

# === 2. GMETA : libellés courts pour la carte ===

GMETA_NEW = '''futureproof:{name:"Future-Proof",tag:"Auras-tu un métier que l'IA ne fera pas en 2035 ?",dims:3},
    via:    {name:"Forces VIA",  tag:"Tes 5 forces de caractère parmi 24, à valoriser.",dims:6},
    dweck:  {name:"Mindset",     tag:"Croissance ou figé : ta croyance sur l'effort et l'échec.",dims:4}'''

# === 3. TESTS : définitions complètes ===

# FuturProof : 12 items, 3 dims (HUM, AUG, ADA)
FUTUREPROOF_TEST = '''    futureproof:{
      id:"futureproof", code:"FUTUREPROOF", short:"Future-Proof", kind:"self",
      name:"Ton score Future-Proof 2035",
      tagline:"Auras-tu un métier que l'IA ne fera pas à ta place ?",
      meta:["Métier 2035","3 piliers","~5 min"],
      minutes:"~5 min",
      introTitle:"Auras-tu un métier en 2035 ?",
      introLead:"Test signature Proxxie, construit sur les rapports WEF Future of Jobs 2025, OECD Skills 2023 et McKinsey GenAI 2024. Mesure 3 piliers : ce qui reste humain, ce que l'IA peut augmenter chez toi, ta capacité à pivoter quand tout change.",
      freeCount:6,
      scale:["Pas du tout moi","Un peu","Moyennement","Beaucoup","Tout à fait moi"],
      hint:["Pas du tout moi","Tout à fait moi"],
      order:["HUM","AUG","ADA"],
      dims:{
        HUM:{name:"Capacités humaines", sub:"créativité, empathie, éthique, leadership"},
        AUG:{name:"Augmentation par l'IA", sub:"prompter, douter, penser systémique, apprendre"},
        ADA:{name:"Adaptation post-IA", sub:"pivoter, identité fluide, réseau, entreprendre"}
      },
      items:[
        {id:"FP_HUM1",dim:"HUM",key:+1,t:"J'aime trouver une approche qu'on n'a pas encore essayée pour résoudre un problème."},
        {id:"FP_HUM2",dim:"HUM",key:+1,t:"Je remarque quand quelqu'un autour de moi ne va pas, même s'il ne dit rien."},
        {id:"FP_HUM3",dim:"HUM",key:+1,t:"Avant une décision importante, je pense à qui peut être impacté."},
        {id:"FP_HUM4",dim:"HUM",key:+1,t:"Quand un groupe est tendu, je sais comment apaiser la situation."},
        {id:"FP_AUG1",dim:"AUG",key:+1,t:"Quand je pose une question à une IA, je sais reformuler si la réponse ne convient pas."},
        {id:"FP_AUG2",dim:"AUG",key:+1,t:"Je sais repérer quand une réponse d'IA est fausse, inventée, ou trop générique."},
        {id:"FP_AUG3",dim:"AUG",key:+1,t:"J'arrive à voir comment plusieurs éléments d'un problème sont reliés entre eux."},
        {id:"FP_AUG4",dim:"AUG",key:+1,t:"J'apprends régulièrement des choses sans qu'on me le demande (vidéos, livres, projets)."},
        {id:"FP_ADA1",dim:"ADA",key:+1,t:"Si mon plan ne marche pas, je trouve assez vite un plan B sans paniquer."},
        {id:"FP_ADA2",dim:"ADA",key:+1,t:"Je suis à l'aise avec l'idée que je n'exercerai pas le même métier toute ma vie."},
        {id:"FP_ADA3",dim:"ADA",key:+1,t:"J'arrive à demander de l'aide à des gens que je connais peu."},
        {id:"FP_ADA4",dim:"ADA",key:+1,t:"Quand je vois quelque chose qui ne marche pas, j'ai envie de proposer une solution plutôt que de me plaindre."}
      ],
      portrait:{
        HUM:{hi:"Tu as un socle humain très solide : créativité, empathie, éthique, leadership. Ce sont précisément les compétences que l'IA ne saura pas répliquer. Continue à pratiquer ces forces en contexte réel, c'est ton vrai avantage.",
            mid:"Tu mobilises tes capacités humaines quand le contexte s'y prête, sans en avoir fait ton centre. Une marge claire pour aller plus loin.",
            lo:"Tu t'appuies peu sur ce qui distingue l'humain de la machine. Le risque, c'est de te retrouver dans des rôles substituables. À cultiver d'urgence : créativité, relation, jugement."},
        AUG:{hi:"Tu sais collaborer avec l'IA plutôt que la subir : tu prompts, tu vérifies, tu vois les liens. C'est exactement le profil que les rapports 2025 décrivent comme « augmenté ».",
            mid:"Tu utilises les outils IA quand il le faut, sans en avoir fait un atout central. Travailler la pensée systémique et l'esprit critique te ferait gagner beaucoup.",
            lo:"L'IA t'impressionne plus qu'elle ne t'augmente. C'est le pilier le plus facile à muscler en quelques mois avec de la curiosité régulière et un peu de pratique."},
        ADA:{hi:"Tu pivotes facilement, tu sais collaborer avec des inconnus, tu agis plutôt que tu te plains. Profil rare et précieux dans un monde qui change vite.",
            mid:"Tu sais t'adapter quand tu y es poussé, mais tu préfères la stabilité. Choisir un petit projet à toi (asso, blog, événement) renforcerait ce muscle.",
            lo:"L'incertitude t'angoisse, et tu cherches plutôt à éviter le changement. C'est le pilier qui prédit le plus la résilience aux bascules d'industrie : à pratiquer en sécurité."}
      },
      about:"Test signature Proxxie inspiré du WEF Future of Jobs 2025, de l'OECD Skills Outlook 2023 et du rapport McKinsey GenAI 2024. Ce n'est pas un instrument psychométrique validé : c'est un outil de positionnement qui te dit où tu en es aujourd'hui sur 3 piliers que les rapports identifient comme clés pour 2030+. Ces compétences se développent toutes."
    }'''

# VIA Strengths : 18 items (3 par vertu × 6 vertus)
VIA_TEST = '''    via:{
      id:"via", code:"VIA", short:"Forces VIA", kind:"self",
      name:"Tes forces de caractère",
      tagline:"Tes 5 forces signatures parmi 24 forces universelles.",
      meta:["Psycho positive","6 vertus","~6 min"],
      minutes:"~6 min",
      introTitle:"Qu'est-ce qui te rend toi ?",
      introLead:"Le VIA Inventory of Strengths (Peterson & Seligman, 2004) identifie 24 forces de caractère universelles, organisées en 6 vertus. Validé sur 10M+ d'utilisateurs. Version courte : on identifie ta vertu dominante et tes axes à éveiller.",
      freeCount:9,
      scale:["Pas du tout moi","Un peu","Moyennement","Beaucoup","Tout à fait moi"],
      hint:["Pas du tout moi","Tout à fait moi"],
      order:["SAG","COU","HUM_V","JUS","TEM","TRA"],
      dims:{
        SAG:{name:"Sagesse", sub:"connaître, apprendre, comprendre, juger"},
        COU:{name:"Courage", sub:"tenir, oser, être vrai quand c'est dur"},
        HUM_V:{name:"Humanité", sub:"aimer, prendre soin, comprendre l'autre"},
        JUS:{name:"Justice", sub:"vivre avec les autres, contribuer, mener"},
        TEM:{name:"Tempérance", sub:"se modérer, se connaître, durer"},
        TRA:{name:"Transcendance", sub:"se relier à plus grand que soi, espérer"}
      },
      items:[
        {id:"VI_SAG1",dim:"SAG",key:+1,t:"J'aime trouver de nouvelles façons de faire les choses."},
        {id:"VI_SAG2",dim:"SAG",key:+1,t:"Je m'intéresse à des sujets très différents les uns des autres."},
        {id:"VI_SAG3",dim:"SAG",key:+1,t:"Apprendre une nouvelle compétence me donne de l'énergie, même sans note."},
        {id:"VI_COU1",dim:"COU",key:+1,t:"Quand je crois à quelque chose, je le défends même si la majorité pense le contraire."},
        {id:"VI_COU2",dim:"COU",key:+1,t:"Je termine ce que je commence, même quand c'est plus dur que prévu."},
        {id:"VI_COU3",dim:"COU",key:+1,t:"Je préfère dire ce que je pense plutôt que ce que les gens veulent entendre."},
        {id:"VI_HUM1",dim:"HUM_V",key:+1,t:"J'ai au moins une personne avec qui je peux être totalement moi-même."},
        {id:"VI_HUM2",dim:"HUM_V",key:+1,t:"Faire quelque chose pour quelqu'un sans rien attendre en retour me rend heureux(se)."},
        {id:"VI_HUM3",dim:"HUM_V",key:+1,t:"Je devine assez vite ce qui se joue émotionnellement dans un groupe."},
        {id:"VI_JUS1",dim:"JUS",key:+1,t:"Je trouve naturellement ma place dans un groupe et je tire les autres vers le haut."},
        {id:"VI_JUS2",dim:"JUS",key:+1,t:"Je suis incapable de profiter d'une situation si je sais que quelqu'un est lésé."},
        {id:"VI_JUS3",dim:"JUS",key:+1,t:"Quand un projet a besoin de quelqu'un qui prend en main, je peux le faire."},
        {id:"VI_TEM1",dim:"TEM",key:+1,t:"Je n'aime pas garder rancune longtemps, ça me fatigue."},
        {id:"VI_TEM2",dim:"TEM",key:+1,t:"Je connais mes points faibles et je peux les reconnaître sans drame."},
        {id:"VI_TEM3",dim:"TEM",key:+1,t:"Quand je suis énervé(e), j'arrive à attendre avant de réagir ou répondre."},
        {id:"VI_TRA1",dim:"TRA",key:+1,t:"Une musique, un paysage, une œuvre d'art peuvent m'arrêter net."},
        {id:"VI_TRA2",dim:"TRA",key:+1,t:"Je remarque souvent les petites choses qui me font du bien dans la journée."},
        {id:"VI_TRA3",dim:"TRA",key:+1,t:"Quand les choses vont mal, je crois généralement qu'elles vont s'améliorer."}
      ],
      portrait:{
        SAG:{hi:"La sagesse est ta vertu cardinale : tu cherches à comprendre, tu apprends pour le plaisir, tu vois clair là où d'autres s'emmêlent. Métiers qui te conviennent : chercheur, journaliste, analyste, enseignant, conseil.",
            mid:"Tu utilises la sagesse comme un outil, pas comme une identité. Ça te sert quand le sujet t'intéresse.",
            lo:"L'analyse et la connaissance abstraite ne sont pas ton terrain favori. Tu préfères agir, ressentir, créer."},
        COU:{hi:"Le courage est ton signe : tu oses, tu tiens, tu dis ce que tu penses. Profil précieux dans les rôles où il faut décider sous pression et porter une vision.",
            mid:"Tu trouves le courage quand l'enjeu est clair pour toi. C'est un muscle activable mais pas central.",
            lo:"Tu évites les confrontations et les engagements risqués. Aller pas à pas dans des situations un peu inconfortables peut faire grandir ce muscle progressivement."},
        HUM_V:{hi:"L'humanité te guide : tu aimes, tu écoutes, tu prends soin. Profil naturel pour les métiers de relation : santé, éducation, coaching, RH, médiation.",
            mid:"Tu te connectes aux autres quand tu en as l'énergie, sans en avoir fait ton centre.",
            lo:"Les relations te demandent plus d'effort qu'à d'autres. Ce n'est pas un défaut, c'est juste un terrain où tu fonctionnes différemment."},
        JUS:{hi:"La justice t'anime : équité, collaboration, leadership pour le bien commun. Profil engagé, idéal pour management, politique, ONG, droit.",
            mid:"Tu agis pour le collectif quand tu sens un sens, sans en faire un combat permanent.",
            lo:"Les enjeux collectifs te touchent moins que les enjeux personnels. Pas un défaut, juste un focus différent."},
        TEM:{hi:"La tempérance est ta force : tu te modères, tu te connais, tu durés. Profil rare et précieux, surtout à 16-25 ans où tout pousse à l'excès.",
            mid:"Tu sais te modérer quand il le faut, mais tu peux aussi t'enflammer.",
            lo:"L'impulsivité te guide souvent. Apprendre à attendre 24h avant les décisions importantes est un petit changement à gros impact."},
        TRA:{hi:"La transcendance est ta vertu : sens du beau, gratitude, espoir, humour, recherche de sens. Profil qui apporte de la couleur partout où tu passes.",
            mid:"Tu te connectes à plus grand que toi par moments, surtout dans la nature, l'art, l'amitié.",
            lo:"Tu es ancré(e) dans le concret, peu attiré(e) par les questions de sens. Ça peut suffire, ou ça peut être une dimension à explorer plus tard."}
      },
      about:"Le VIA Inventory of Strengths (Peterson & Seligman, 2004) est un cadre de référence en psychologie positive, validé sur 10M+ d'utilisateurs. La version officielle comporte 96 à 240 items. Cette version courte (1 item par force, 3 par vertu) sert au positionnement et au coaching, pas à l'évaluation clinique. Pour une version longue gratuite, voir viacharacter.org."
    }'''

# Dweck Mindset : 16 items (4 par dim × 4 dims, 8 reverse)
DWECK_TEST = '''    dweck:{
      id:"dweck", code:"DWECK", short:"Mindset", kind:"self",
      name:"Ton mindset growth ou fixed",
      tagline:"Ta croyance sur l'effort, le talent, et l'échec.",
      meta:["Mindset","4 dimensions","~4 min"],
      minutes:"~4 min",
      introTitle:"L'intelligence se travaille, ou c'est inné ?",
      introLead:"Le concept de growth vs fixed mindset, développé par Carol Dweck (Stanford, 2006), change tout : prises de risque, apprentissages, réaction à l'échec. Ce repérage te dit où tu en es sur 4 dimensions.",
      freeCount:8,
      scale:["Pas du tout d'accord","Plutôt pas d'accord","Mitigé","Plutôt d'accord","Tout à fait d'accord"],
      hint:["Pas d'accord","Tout à fait"],
      order:["INT","ABI","EFF","FAI"],
      dims:{
        INT:{name:"Intelligence", sub:"le QI se développe-t-il ?"},
        ABI:{name:"Talent", sub:"on naît doué, ou on le devient ?"},
        EFF:{name:"Effort", sub:"forcer = pas doué, ou condition du progrès ?"},
        FAI:{name:"Échec", sub:"verdict sur soi, ou info utile ?"}
      },
      items:[
        {id:"DW_INT1",dim:"INT",key:-1,t:"Ton intelligence est quelque chose que tu ne peux pas vraiment changer."},
        {id:"DW_INT2",dim:"INT",key:-1,t:"Tu peux apprendre des choses, mais ton niveau d'intelligence reste à peu près le même."},
        {id:"DW_INT3",dim:"INT",key:+1,t:"Tu peux développer ton intelligence en t'entraînant et en apprenant régulièrement."},
        {id:"DW_INT4",dim:"INT",key:+1,t:"Plus tu fais d'efforts, plus tu deviens vraiment intelligent(e), pas juste plus expérimenté(e)."},
        {id:"DW_ABI1",dim:"ABI",key:-1,t:"On a un talent pour certaines choses et pas d'autres, c'est ainsi."},
        {id:"DW_ABI2",dim:"ABI",key:-1,t:"Quand quelqu'un est doué dans un domaine, c'est qu'il est né comme ça."},
        {id:"DW_ABI3",dim:"ABI",key:+1,t:"Avec assez de travail, presque tout le monde peut devenir bon dans presque n'importe quoi."},
        {id:"DW_ABI4",dim:"ABI",key:+1,t:"Les meilleurs dans un domaine sont surtout ceux qui ont le plus pratiqué."},
        {id:"DW_EFF1",dim:"EFF",key:-1,t:"Si tu dois fournir beaucoup d'efforts pour quelque chose, c'est que tu n'es pas fait(e) pour."},
        {id:"DW_EFF2",dim:"EFF",key:-1,t:"Avoir du talent, c'est faire les choses facilement, sans avoir à se forcer."},
        {id:"DW_EFF3",dim:"EFF",key:+1,t:"L'effort, c'est ce qui transforme un talent en vraie compétence."},
        {id:"DW_EFF4",dim:"EFF",key:+1,t:"Galérer sur quelque chose est en général un signe que tu es en train d'apprendre."},
        {id:"DW_FAI1",dim:"FAI",key:-1,t:"Échouer publiquement à quelque chose en dit beaucoup sur ton niveau réel."},
        {id:"DW_FAI2",dim:"FAI",key:-1,t:"Quand je rate quelque chose d'important, je préfère arrêter d'essayer plutôt que continuer."},
        {id:"DW_FAI3",dim:"FAI",key:+1,t:"Un échec est une info utile, pas une preuve que tu n'es pas capable."},
        {id:"DW_FAI4",dim:"FAI",key:+1,t:"Quand je rate quelque chose, je veux comprendre ce qui s'est passé pour mieux faire la fois suivante."}
      ],
      portrait:{
        INT:{hi:"Tu crois fermement que l'intelligence se développe. Cette croyance te protège : tu prends des défis, tu persévères, tu ne te résignes pas. C'est la base d'un parcours qui peut aller loin.",
            mid:"Tu hésites entre les deux selon les domaines. C'est normal et c'est le moment de basculer franchement vers growth, surtout avant Parcoursup.",
            lo:"Tu crois que l'intelligence est largement figée. Conséquence : tu évites les domaines où tu pourrais échouer, et tu te résignes vite. À retravailler en priorité, ça change littéralement le parcours."},
        ABI:{hi:"Tu sais que le talent se construit avec la pratique. Tu ne te limites pas à ce que tu sais déjà faire, ce qui ouvre énormément de portes.",
            mid:"Tu crois au talent inné pour certaines choses, à la pratique pour d'autres. Le risque c'est de t'auto-éliminer trop vite sur ce que tu crois ne pas être « ton truc ».",
            lo:"Tu crois fortement au talent inné. Tu finis par te dire « pas pour moi » dès qu'un domaine te résiste un peu. Beaucoup de portes que tu fermes pourraient s'ouvrir."},
        EFF:{hi:"L'effort, pour toi, c'est ce qui transforme le potentiel en compétence. Cette croyance est ton plus grand atout : elle te fait apparaître quand d'autres lâchent.",
            mid:"Tu valorises l'effort quand il porte ses fruits, mais tu doutes quand ça résiste trop. Apprendre à voir la friction comme un signal d'apprentissage te ferait beaucoup gagner.",
            lo:"Tu interprètes l'effort comme un signe que tu n'es pas fait(e) pour le sujet. Cette croyance te coûte cher : tu lâches juste avant le déclic. À déplacer en priorité."},
        FAI:{hi:"L'échec, pour toi, est une info utile, pas un verdict. Tu prends des risques, tu apprends vite de tes ratés. C'est une force rare à ton âge.",
            mid:"Tu prends mieux les petits échecs que les gros. C'est normal. Cultiver la pratique de « j'ai appris quoi de ce raté » t'ancrera plus solidement en growth.",
            lo:"L'échec te paralyse et tu l'évites en évitant aussi les défis. Cette dimension est centrale dans les filières exigeantes (prépa, médecine, ingé) où l'échec ponctuel fait partie du parcours."}
      },
      about:"Le concept de growth vs fixed mindset vient des travaux de Carol Dweck (Stanford, 2006). Ce n'est pas un instrument clinique mais un cadre éducatif puissant et bien documenté. Une étude Stanford sur 12 000 ados a montré qu'enseigner le growth mindset améliore durablement les notes. Le mindset se change · pratique régulière du « pas encore » au lieu du « jamais »."
    }'''


# --- Idempotent patch helpers ---

def patch_facets(html: str) -> tuple[str, list[str]]:
    changes = []
    for group, codes_to_add in FACETS_UPDATES:
        # find tests: [...] in the matching group block
        # Pattern : `group:{...tests:[...]}` - find the group_key followed by tests array
        pat = re.compile(
            r'(' + re.escape(group) + r':\s*\{[^}]*?tests:\s*\[)([^\]]*)\]',
            re.DOTALL,
        )
        m = pat.search(html)
        if not m:
            changes.append(f"WARN facet {group} introuvable")
            continue
        prefix = m.group(1)
        body = m.group(2)
        # Insert each code if not already present
        new_body = body
        added = []
        for code in codes_to_add:
            quoted = '"' + code + '"'
            if quoted not in new_body:
                # append with comma
                if new_body.rstrip().endswith(","):
                    new_body = new_body.rstrip() + quoted
                else:
                    new_body = new_body.rstrip() + "," + quoted
                added.append(code)
        if added:
            html = html[: m.start()] + prefix + new_body + "]" + html[m.end() :]
            changes.append(f"FACETS.{group} += {added}")
    return html, changes


def patch_gmeta(html: str) -> tuple[str, list[str]]:
    if "futureproof:{" in html and "via:" in html.split("GMETA")[1] and "dweck:" in html.split("GMETA")[1]:
        return html, ["GMETA: déjà présent"]
    # Find GMETA closing brace
    m = re.search(r'var GMETA\s*=\s*\{', html)
    if not m:
        return html, ["WARN GMETA introuvable"]
    start = m.end() - 1
    depth = 0
    end = start
    for j, c in enumerate(html[start:], start=start):
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                end = j
                break
    # Insert before closing brace, prepend comma to previous entry
    insertion = ",\n    " + GMETA_NEW + "\n  "
    # Strip current trailing whitespace before }
    new_html = html[:end].rstrip() + insertion + html[end:]
    return new_html, ["+ GMETA : futureproof, via, dweck"]


def patch_tests(html: str) -> tuple[str, list[str]]:
    if "futureproof:{" in html and re.search(r'\n\s{4}via:\{', html) and re.search(r'\n\s{4}dweck:\{', html):
        return html, ["TESTS: déjà présent"]
    # Find TESTS closing brace
    m = re.search(r'var TESTS\s*=\s*\{', html)
    if not m:
        return html, ["WARN TESTS introuvable"]
    start = m.end() - 1
    depth = 0
    end = start
    for j, c in enumerate(html[start:], start=start):
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                end = j
                break
    # Build insertion : prepend comma to previous entry (last test before closing brace)
    insertion = ",\n\n" + FUTUREPROOF_TEST + ",\n\n" + VIA_TEST + ",\n\n" + DWECK_TEST + "\n\n  "
    new_html = html[:end].rstrip() + insertion + html[end:]
    return new_html, ["+ TESTS : futureproof, via, dweck"]


def patch_one(target: pathlib.Path) -> str:
    if not target.exists():
        return f"{target.name}: file not found"
    html = target.read_text(encoding="utf-8")
    all_changes: list[str] = []
    html, c1 = patch_facets(html)
    all_changes.extend(c1)
    html, c2 = patch_gmeta(html)
    all_changes.extend(c2)
    html, c3 = patch_tests(html)
    all_changes.extend(c3)
    target.write_text(html, encoding="utf-8")
    return f"{target.name}: [{', '.join(all_changes)}]"


if __name__ == "__main__":
    print(patch_one(TARGET))

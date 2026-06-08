#!/usr/bin/env python3
"""Construit Proxxie Test Grit.html depuis Proxxie Test Anxiete.html.

Pattern identique à _patch_build_phq9.py · clone + swap JSX test-spécifique.

Source psychométrique : Grit-S (Duckworth & Quinn 2009), 8 items, Likert 1-5.
4 items inversés (CI), 4 items directs (PE). Score = moyenne sur 5.
Pas un screening clinique, pas de disclaimer médical.
"""
import re, json, base64, gzip, pathlib, shutil
import _bridge_common

REPO = pathlib.Path(__file__).parent
SOURCE = REPO / "Proxxie Test Anxiete.html"
TARGET = REPO / "Proxxie Test Grit.html"
TARGET_LOWER = REPO / "test-grit.html"
ASSET_UUID_PREFIX = "61feca88"

GRIT_BLOCK = r'''/* Test Proxxie Grit, persévérance et passion long terme (Duckworth & Quinn 2009)
   Pas un outil clinique. Mesure de psychologie positive. */

const QUESTIONS = [
  // 4 items INVERSÉS (Consistency of Interest) · score inversé 6-raw
  { type: "CI", q: "De nouvelles idées et de nouveaux projets me détournent parfois de ceux sur lesquels je travaille déjà.", reverse: true },
  { type: "CI", q: "J'ai eu du mal à rester concentré(e) sur des projets qui prenaient plus de quelques mois à finir.", reverse: true },
  { type: "CI", q: "Mes centres d'intérêt changent d'une année à l'autre.", reverse: true },
  { type: "CI", q: "Je suis devenu(e) obsédé(e) par une idée ou un projet pendant un temps, mais j'ai ensuite perdu l'intérêt.", reverse: true },
  // 4 items DIRECTS (Perseverance of Effort) · score direct
  { type: "PE", q: "Je suis travailleur(se).", reverse: false },
  { type: "PE", q: "Je finis tout ce que je commence.", reverse: false },
  { type: "PE", q: "Je suis assidu(e). Je ne lâche jamais l'affaire.", reverse: false },
  { type: "PE", q: "Je suis très investi(e) dans ce que j'entreprends.", reverse: false },
];

const TYPE_META = {
  CI: { l: "Constance des intérêts", c: "#6B46C1", short: "Tenir un cap sur le long terme" },
  PE: { l: "Persévérance de l'effort", c: "#4C1D95", short: "Fournir un effort soutenu" },
};
const STORAGE_KEY = "proxxie-grit-answers";

const getTypeMeta = (q) => ({ label: TYPE_META[q.type].l, color: TYPE_META[q.type].c });

const computeResults = (answers) => {
  let ciSum = 0, ciCount = 0, peSum = 0, peCount = 0;
  QUESTIONS.forEach((q, idx) => {
    if (answers[idx] == null) return;
    const score = q.reverse ? (6 - answers[idx]) : answers[idx];
    if (q.type === "CI") { ciSum += score; ciCount++; }
    else { peSum += score; peCount++; }
  });
  const ciAvg = ciCount > 0 ? ciSum / ciCount : 0;
  const peAvg = peCount > 0 ? peSum / peCount : 0;
  const total = (ciSum + peSum) / Math.max(1, ciCount + peCount);
  const totalRounded = Math.round(total * 100) / 100;
  let level = "faible";
  if (total >= 4.5) level = "très fort";
  else if (total >= 4.0) level = "fort";
  else if (total >= 3.5) level = "moyen-haut";
  else if (total >= 2.5) level = "moyen-bas";
  const profile = peAvg > ciAvg + 0.4 ? "Persévérant" : ciAvg > peAvg + 0.4 ? "Constant" : "Équilibré";
  const dropoutFlag = total < 2.5;
  return { total: totalRounded, level, ciAvg: Math.round(ciAvg*100)/100, peAvg: Math.round(peAvg*100)/100, profile, dropoutFlag };
};

const DisclaimerBanner = () => (
  <div style={{
    background: "#F4EFFE", borderLeft: "4px solid #6B46C1",
    padding: "14px 20px", marginBottom: 30, borderRadius: 8,
    fontSize: 13.5, color: "#0A0E2C", lineHeight: 1.55,
  }}>
    <strong>ℹ️ La grit se travaille.</strong> L'échelle Grit-S (Duckworth, 2009) mesure la persévérance et la constance des intérêts. Un score faible aujourd'hui n'est pas une fatalité, c'est une compétence qui se développe avec un sport régulier, un projet long, ou un mentor.
  </div>
);

const TestHero = ({ onStart }) => (
  <section style={{ paddingTop: 70, paddingBottom: 80, position: "relative", overflow: "hidden" }}>
    <Pill color="rgba(245,235,63,.5)" w={260} h={130} style={{ position: "absolute", top: 110, right: -60, borderRadius: 999 }} />
    <Half color="rgba(107,70,193,.18)" side="t" w={300} h={120} style={{ position: "absolute", bottom: -10, left: -40 }} />
    <div className="shell" style={{ position: "relative", display: "grid", gridTemplateColumns: "1.1fr 1fr", gap: 60, alignItems: "center" }}>
      <div>
        <span className="chip" style={{ background: "rgba(107,70,193,.15)", color: "#6B46C1" }}>
          <Icon.spark style={{ width: 14, height: 14 }} /> Persévérance · Duckworth
        </span>
        <h1 style={{ marginTop: 22, marginBottom: 22 }}>
          Test <span style={{ background: "linear-gradient(180deg, transparent 60%, #F5EB3F 60%)", paddingInline: 4 }}>Grit</span> · sprint ou marathon ?
        </h1>
        <p style={{ fontSize: 18, color: "var(--c-ink-2)", maxWidth: 520, marginBottom: 28 }}>
          L'échelle <strong>Grit-S</strong> mesure ce qui distingue ceux qui terminent ce qu'ils commencent. Utilisée par West Point, Stanford et Yale pour identifier qui décroche et qui tient. 8 questions, 5 minutes.
        </p>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 22 }}>
          <button className="btn btn-orange btn-lg btn-arrow" onClick={onStart}>Démarrer le test</button>
          <a href="#methode" className="btn btn-ghost btn-lg"><Icon.play /> Comment ça marche</a>
        </div>
        <div style={{ display: "flex", gap: 22, fontSize: 13, color: "var(--c-muted)", flexWrap: "wrap" }}>
          <span><Icon.shield style={{ width: 13, height: 13, verticalAlign: "-2px", marginRight: 4 }} /> Données privées · stockées en local</span>
          <span>⏱ 5 min · 8 questions</span>
          <span>📋 Grit-S (Duckworth 2009)</span>
        </div>
      </div>
      <div style={{ position: "relative" }}>
        <div style={{ background: "white", borderRadius: 24, padding: 28, boxShadow: "var(--shadow-md)", border: "1px solid var(--c-line)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 18 }}>
            <span style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--c-muted)" }}>Question 5 / 8</span>
            <span style={{ fontSize: 12, color: "#6B46C1", fontWeight: 600 }}>● Persévérance</span>
          </div>
          <div style={{ height: 4, background: "var(--c-cream)", borderRadius: 2, marginBottom: 24, overflow: "hidden" }}>
            <div style={{ width: "62%", height: "100%", background: "#6B46C1" }} />
          </div>
          <h3 style={{ fontSize: 19, lineHeight: 1.35, fontWeight: 600, marginBottom: 22, fontFamily: "var(--font-display)", letterSpacing: "-0.02em" }}>
            "Je finis tout ce que je commence."
          </h3>
          <div style={{ display: "flex", gap: 8, justifyContent: "space-between" }}>
            {["Pas du tout moi", "Un peu", "Moyennement", "Beaucoup", "Tout à fait"].map((label, n) => (
              <div key={n} style={{
                flex: 1, padding: "10px 4px", borderRadius: 10, textAlign: "center",
                background: n === 3 ? "linear-gradient(160deg, #6B46C1, #4C1D95)" : "var(--c-cream)",
                color: n === 3 ? "white" : "var(--c-ink)",
                fontWeight: 600, fontSize: 9.5,
                border: n === 3 ? "none" : "1px solid var(--c-line)",
              }}>{label}</div>
            ))}
          </div>
        </div>
        <div style={{ position: "absolute", bottom: -18, right: -18, background: "#0A0E2C", color: "white", padding: "12px 16px", borderRadius: 14, fontSize: 12, display: "flex", alignItems: "center", gap: 10, boxShadow: "var(--shadow-md)" }}>
          <Icon.brain style={{ color: "#F5EB3F" }} /> West Point · Stanford · Yale
        </div>
      </div>
    </div>
  </section>
);

const HowItWorks = () => (
  <section id="methode" style={{ paddingTop: 100, paddingBottom: 100, background: "white" }}>
    <div className="shell">
      <div style={{ textAlign: "center", maxWidth: 720, margin: "0 auto 50px" }}>
        <span className="eyebrow"><span className="dot"></span>Comment c'est calculé</span>
        <h2 style={{ marginTop: 14 }}>Grit-S, 8 items, 2 facteurs.</h2>
        <p style={{ fontSize: 17, color: "var(--c-ink-2)", marginTop: 16 }}>
          L'échelle d'Angela Duckworth mesure 2 facteurs distincts. La <strong>constance des intérêts</strong>, capacité à maintenir un cap sur des années. La <strong>persévérance de l'effort</strong>, capacité à tenir face aux obstacles. Score moyen sur 5.
        </p>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, maxWidth: 920, margin: "0 auto" }}>
        {[
          { n: "1", t: "8 questions", d: "4 sur la constance des intérêts, 4 sur la persévérance de l'effort. 5 minutes." },
          { n: "2", t: "Score sur 5", d: "Moyenne des 8 items. Top 10% : ≥ 4.5. Faible : < 2.5. Comparable par âge." },
          { n: "3", t: "Profil + pistes", d: "Profil dominant (Persévérant / Constant / Équilibré) et 3 leviers concrets pour la développer." },
        ].map((s) => (
          <div key={s.n} style={{ background: "var(--c-cream-light)", padding: 22, borderRadius: 16, border: "1px solid var(--c-line)" }}>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: "linear-gradient(135deg, #6B46C1, #4C1D95)", color: "white", display: "grid", placeItems: "center", fontWeight: 700, fontFamily: "var(--font-num)", marginBottom: 14 }}>{s.n}</div>
            <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 6 }}>{s.t}</div>
            <p style={{ fontSize: 13.5, color: "var(--c-muted)", lineHeight: 1.55 }}>{s.d}</p>
          </div>
        ))}
      </div>
    </div>
  </section>
);

const LEVEL_COPY = {
  "très fort": {
    color: "#6B46C1",
    body: "Grit exceptionnelle, top 10% (Duckworth, échantillon US). Atout structurel pour les parcours longs : médecine, prépa, thèse, entrepreneuriat. Vigilance : la grit forte rime parfois avec rigidité et burnout. Cultiver aussi la flexibilité.",
    advice: ["Filières longues envisageables sans crainte de la durée", "Garder un mentor pour aider à pivoter si un projet n'a plus de sens", "Veiller au burnout, signaux corps/esprit"],
  },
  "fort": {
    color: "#7C3AED",
    body: "Grit solide. L'ado tient sur la durée, finit ce qu'il commence. Bon prédicteur de réussite dans les filières longues. Combiner avec une orientation alignée (test RIASEC) pour maximiser l'impact.",
    advice: ["Médecine, ingé, doctorat envisageables", "Possible cumul études + projet personnel", "Croiser avec RIASEC pour vérifier l'alignement intérêts/effort"],
  },
  "moyen-haut": {
    color: "#A78BFA",
    body: "Grit moyenne haute, dépend du sujet. L'ado tient quand le sujet l'intéresse vraiment, moins sur les corvées. Le levier : trouver des sujets qui font écho à ses valeurs (test Valeurs) pour transformer l'effort en passion.",
    advice: ["Vérifier l'alignement filière/intérêts AVANT de s'engager", "Parcours avec feedback fréquent (alternance, projets)", "Identifier les sujets-passions pour mobiliser l'énergie"],
  },
  "moyen-bas": {
    color: "#FD6936",
    body: "Grit modeste. L'ado a tendance à pivoter quand l'effort devient ingrat. Pas un défaut, c'est un trait modifiable. À 17 ans, ça signale : éviter les filières longues sans feedback (médecine, prépa), privilégier les formats courts et appliqués.",
    advice: ["BTS, BUT, écoles courtes avec stages dès la 1re année", "Construire la grit par petites victoires (sport, projet semestriel)", "Éviter prépa et médecine sauf passion authentique"],
  },
  "faible": {
    color: "#C62828",
    body: "Signal d'alerte : risque de décrochage si filière exigeante. À ce niveau, engager l'ado dans une filière longue sans accompagnement = risque élevé. Pas une fatalité (la grit se travaille), mais à ne pas ignorer pour Parcoursup. Privilégier des parcours courts, concrets, avec feedback immédiat.",
    advice: ["Parcours courts avec rythme alternance ou pratique", "Coach/tuteur dès la 1re année post-bac", "Travailler la grit en parallèle : sport régulier, projet semestriel, journal de bord"],
  },
};

/* RICH_RESULTS · contenu psychométrique étayé par niveau */
const RICH_RESULTS = {
  "très fort": {
    headline: "Grit exceptionnelle, le profil rare des marathoniens",
    decoding: [
      "Un score ≥ 4.5/5 place votre ado dans les 10% les plus persévérants (Duckworth, échantillon US). Ce niveau a été observé chez les cadets de West Point qui terminent la formation, les enfants prodiges qui maintiennent leur engagement après l'adolescence, et les entrepreneurs qui survivent aux 5 premières années. C'est un trait structurel, pas une humeur passagère.",
      "Important : grit ≠ rigidité. Une grit exceptionnelle accompagnée de flexibilité (capacité à pivoter quand un projet n'a plus de sens) est un atout massif. Mais grit forte + faible flexibilité = risque de s'enfermer dans un projet qui ne fonctionne plus, ou de burnout. Le travail à cet âge : ajouter la flexibilité, pas la persévérance.",
    ],
    forces: [
      { t: "Résistance à la frustration", d: "Capacité à continuer face aux obstacles que d'autres trouveraient décourageants." },
      { t: "Visions long terme", d: "Capable de viser un objectif à 5+ ans et de structurer son présent autour." },
      { t: "Recovery rapide après échec", d: "Échec interprété comme info, pas comme jugement personnel." },
      { t: "Engagement profond", d: "Quand un projet est choisi, il est mené à terme, sans demi-mesure." },
      { t: "Modèle pour les pairs", d: "Effet d'entraînement sur les camarades, leadership par l'exemple." },
    ],
    vigilances: [
      { t: "Rigidité face au pivot", d: "Difficulté à abandonner un projet même quand il faudrait." },
      { t: "Burnout silencieux", d: "Tendance à pousser au-delà du signal corporel de fatigue." },
      { t: "Auto-exigence excessive", d: "Standards très élevés appliqués à soi, parfois aux autres." },
      { t: "Isolement par engagement", d: "Le projet prend toute la place, le lien social s'érode." },
      { t: "Dépendance au feedback de réussite", d: "Vulnérabilité aux périodes sans victoire visible." },
    ],
    portraits: [
      { n: "Le médaillé olympique en devenir", d: "Sport quotidien, sommeil discipliné, objectif aux JO 2032. La grit est consciente et assumée." },
      { n: "L'entrepreneur ado", d: "Side-project lancé à 14 ans, monétisé à 16, présenté à des concours. Vision claire de son indépendance." },
      { n: "L'académique élite", d: "Vise prépa puis ENS. Travaille 4h/jour hors cours. Sait pourquoi, accepte le prix." },
    ],
    pistes_parent: [
      { t: "Protéger les pauses", d: "À ce niveau, c'est vous qui devez imposer le repos. L'ado ne le fera pas seul." },
      { t: "Valoriser le repos sans le déguiser en récompense", d: "« Tu mérites de te reposer parce que tu es humain », pas « parce que tu as bien travaillé »." },
      { t: "Ouvrir d'autres options", d: "Présenter régulièrement des alternatives, sans pression, pour entretenir la flexibilité." },
      { t: "Surveiller l'isolement", d: "Garantir des moments sociaux non-projet (repas famille, sorties, amis hors équipe)." },
      { t: "Anticiper le moment du pivot", d: "Préparer émotionnellement la possibilité d'arrêter un projet majeur, à 18-22 ans souvent." },
    ],
    pistes_ado: [
      { t: "Apprendre à dire stop", d: "La grit s'use. Faire 1 jour de break complet par semaine. Sans culpabilité." },
      { t: "Identifier 1 alternative crédible", d: "Si ton plan A échouait, que ferais-tu ? Avoir une réponse réduit l'angoisse." },
      { t: "Cultiver 1 hobby sans objectif", d: "Une activité juste pour le plaisir, pas pour exceller. Antidote au burnout." },
      { t: "Mentor (vrai)", d: "Identifier un adulte qui te dira « ralentis » sans crainte de te perdre comme client / élève." },
      { t: "Mesurer la fatigue, pas que la productivité", d: "Journal : énergie /10 chaque soir. Repère les patterns avant l'effondrement." },
    ],
    impact_orientation: [
      "Avec cette grit, presque toutes les filières exigeantes sont jouables : médecine, prépa, doctorat, sport haut niveau, entrepreneuriat. Le filtre n'est pas la capacité à tenir, c'est la justesse du choix. À ce niveau, le risque est de choisir une filière prestigieuse mais inalignée avec ses intérêts (RIASEC) ou ses valeurs (Schwartz), et d'y rester par grit alors qu'il faudrait pivoter. Croiser absolument avec RIASEC et Valeurs avant de s'engager.",
    ],
    ressources: [
      { type: "Livre", title: "Grit, the power of passion and perseverance", author: "Angela Duckworth", desc: "Le livre source. Lire en VO si possible, sinon traduction française." },
      { type: "Podcast", title: "How I Built This", host: "Guy Raz, NPR", desc: "Récits d'entrepreneurs qui ont tenu sur 10+ ans. Inspiration et leçons concrètes." },
      { type: "Site", title: "Character Lab", url: "https://characterlab.org", desc: "Labo de Duckworth à Penn. Outils gratuits pour développer caractère + grit chez les ados." },
    ],
  },
  "fort": {
    headline: "Grit solide, le profil des parcours longs réussis",
    decoding: [
      "Un score entre 4.0 et 4.5/5 est un excellent niveau. Plus haut que la moyenne des étudiants américains de Penn (3.8) selon Duckworth. À ce niveau, l'ado finit ce qu'il commence dans 80%+ des cas, supporte des frustrations qui décourageraient d'autres, et a déjà un historique de projets menés à terme (sport sur plusieurs années, instrument, projets école).",
      "Ce niveau est compatible avec la grande majorité des filières exigeantes : prépa, médecine, école d'ingé, droit, sciences-po. Le travail à cet âge : aligner cette grit avec les intérêts réels (test RIASEC) plutôt que la dépenser sur des objectifs imposés. Une grit forte sur un sujet désaligné = beau parcours formellement, mais fatigue identitaire à 25-30 ans.",
    ],
    forces: [
      { t: "Achève les projets", d: "Ratio « projets commencés / projets terminés » très favorable." },
      { t: "Tolérance frustration", d: "Capable de redoubler, de reprendre un cours qu'il ne comprend pas." },
      { t: "Discipline acquise", d: "A déjà construit des routines (sport, devoirs, hobby) qui tiennent dans la durée." },
      { t: "Curiosité maintenue", d: "Ne se désinvestit pas une fois la nouveauté passée." },
      { t: "Capacité à attendre", d: "Comprend que les vrais résultats prennent du temps, accepte de ne pas voir d'effet immédiat." },
    ],
    vigilances: [
      { t: "Grit mal orientée", d: "Risque de pousser sur un projet hérité (filière parent, sport familial) sans alignement personnel." },
      { t: "Confusion grit/perfectionnisme", d: "Vigilance sur l'origine de la persévérance : passion ou peur de l'échec ?" },
      { t: "Sous-investissement social", d: "Tendance à prioriser projet sur relations, à reconsidérer." },
      { t: "Insuffisance de feedback", d: "Tient sans qu'on lui dise que c'est bien, ce qui peut masquer un épuisement." },
      { t: "Difficulté à changer de cap", d: "Peut s'enferrer dans un choix au lieu de pivoter à temps." },
    ],
    portraits: [
      { n: "Le futur médecin", d: "Sait depuis le collège, accepte 10 ans d'études, prépare sereinement la PASS." },
      { n: "Le sportif compétiteur amateur", d: "Pratique sérieuse 4-5x/semaine, vise compétitions régionales sans rêver pro." },
      { n: "L'élève régulier de prépa", d: "Pas le 1er de classe, mais celui qui tient les 2 ans, finit dans le top tiers, intègre une école." },
    ],
    pistes_parent: [
      { t: "Vérifier l'alignement avant Parcoursup", d: "Croiser ce score Grit avec un test RIASEC. Si désalignement, en parler." },
      { t: "Valoriser l'effort + l'autonomie", d: "« Tu as fait ce qu'il fallait » plus que « tu es brillant »." },
      { t: "Préserver les week-ends de récupération", d: "1 jour off par semaine, vraiment off, est une routine de pro." },
      { t: "Pas surinvestir", d: "Votre fierté ne doit pas devenir sa pression. Garder un ton informel." },
      { t: "Anticiper les périodes creuses", d: "Toute filière a ses moments de doute. Avoir une routine de soutien prête (resto en duo, ciné, marche)." },
    ],
    pistes_ado: [
      { t: "Choisir un objectif aligné", d: "Avant la prochaine grosse échéance, vérifier que tu vises quelque chose qui te ressemble vraiment." },
      { t: "1 mentor", d: "Adulte qui exerce le métier vers lequel tu vas. 30 min/trimestre suffit." },
      { t: "Sport régulier", d: "Pas pour la perf, pour la régulation. 3x/semaine 30 min." },
      { t: "Apprendre à demander de l'aide", d: "Capacité distincte de la grit, à muscler en parallèle." },
      { t: "Garder 1 hobby non scolaire", d: "Avoir 1 truc qui te définit en dehors des études." },
    ],
    impact_orientation: [
      "Avec cette grit, médecine, prépa, ingé, droit sont accessibles. Le facteur limitant n'est pas la persévérance mais la pertinence du choix. Investir 2-3 stages d'observation avant Parcoursup pour valider que la filière correspond. Si vous hésitez entre 2 filières, choisir celle qui correspond le mieux aux résultats RIASEC + Valeurs, pas celle qui est la plus prestigieuse. La grit fera tenir, mais elle ne corrigera pas un mauvais alignement de fond.",
    ],
    ressources: [
      { type: "Livre", title: "Mindset, the new psychology of success", author: "Carol Dweck", desc: "Complément naturel à la grit, growth mindset = grit + flexibilité." },
      { type: "Podcast", title: "Hidden Brain, NPR", host: "Shankar Vedantam", desc: "Épisodes réguliers sur persévérance, succès long terme, biais d'orientation." },
      { type: "Site", title: "Character Lab", url: "https://characterlab.org", desc: "Outils gratuits Duckworth pour parents et enseignants." },
    ],
  },
  "moyen-haut": {
    headline: "Grit moyenne-haute, dépend du sujet et du contexte",
    decoding: [
      "Un score entre 3.5 et 4.0/5 est au-dessus de la moyenne. L'ado tient quand le sujet l'intéresse vraiment, abandonne plus facilement les corvées ou les sujets imposés. C'est un profil très courant, pas un défaut. L'enjeu : trouver le ou les sujets où l'engagement est naturel, et orienter sa vie là où la grit s'active spontanément.",
      "À ce niveau, le pire choix est une filière imposée par défaut (par exemple « ingénieur parce que c'est sûr »). Le meilleur choix est une filière en résonance avec un intérêt déjà manifesté (test RIASEC, Valeurs). La grit suivra naturellement quand le sujet fait sens. À l'inverse, sans alignement, le risque de décrochage en L1/L2 est réel.",
    ],
    forces: [
      { t: "Engagement profond sur ce qui compte", d: "Quand un sujet l'intéresse, l'ado y consacre une énergie remarquable." },
      { t: "Capacité de discernement", d: "Sait reconnaître ce qui mérite son effort ou pas." },
      { t: "Lisibilité émotionnelle", d: "Ses ressentis sont des indicateurs fiables d'alignement." },
      { t: "Énergie pour les projets choisis", d: "Capable de blitz sur 2-3 mois sur un projet qui le passionne." },
      { t: "Apprentissage rapide quand motivé", d: "La motivation intrinsèque débloque rapidement les compétences." },
    ],
    vigilances: [
      { t: "Lâche les sujets ingrats", d: "Les apprentissages de base obligatoires (maths, langues) peuvent décrocher." },
      { t: "Désengagement face à la routine", d: "Les premiers mois passionnants, puis baisse si pas de nouveauté." },
      { t: "Procrastination ciblée", d: "Sait procrastiner stratégiquement sur ce qui ne le passionne pas." },
      { t: "Dépendance au sens immédiat", d: "Difficulté à investir un effort dont le sens n'est pas clair tout de suite." },
      { t: "Risque de zapping", d: "Tendance à enchaîner les projets sans les terminer si le suivant a l'air plus excitant." },
    ],
    portraits: [
      { n: "Le passionné mono-sujet", d: "Excellent dans 1 domaine (info, art, sport), médiocre dans les autres. Bulletin déséquilibré." },
      { n: "Le chercheur d'alignement", d: "Cherche sa voie depuis la 3e. A testé 4 hobbies. Veut un métier qui ait du sens." },
      { n: "Le serial-starter", d: "Lance beaucoup, finit peu. Énergie réelle mais dispersée. Besoin d'aide pour cadrer." },
    ],
    pistes_parent: [
      { t: "Investir dans le test RIASEC", d: "Pour ce profil, l'alignement intérêts/filière est crucial. Faire passer le RIASEC avant Parcoursup." },
      { t: "Ne pas pousser une filière prestigieuse par défaut", d: "Sciences Po sans intérêt politique = abandon en L2. Médecine sans empathie = burnout interne." },
      { t: "Valoriser les passions atypiques", d: "Manga, gaming, foot : si l'engagement est là, c'est un sujet d'orientation viable." },
      { t: "Aider à cadrer les projets", d: "Si serial-starter : proposer un cahier où il note ce qu'il commence, mensuel." },
      { t: "Préférer formats avec feedback rapide", d: "BTS, BUT, alternance : visibilité concrète de la progression." },
    ],
    pistes_ado: [
      { t: "Vérifier ton alignement avant Parcoursup", d: "Test RIASEC + Valeurs. Si ta filière n°1 ne ressort pas, repenser." },
      { t: "Choisir des formats stimulants", d: "Stages, projets concrets, alternance plutôt que cours magistraux abstraits." },
      { t: "Identifier ton ressort principal", d: "Quel est le truc qui t'a fait travailler 4h sans voir le temps ? Note-le." },
      { t: "Bornes pour les corvées", d: "Pour les sujets ingrats : 25 min focus puis 5 pause (Pomodoro), pas plus." },
      { t: "1 projet long avec un pair", d: "Trouver 1 ami pour démarrer un projet à 2, accountability réciproque." },
    ],
    impact_orientation: [
      "Pour ce profil, le pire choix est une filière généraliste sans intérêt fort (économie « parce que ça ouvre des portes », ingénierie « parce que c'est solide »). Le meilleur choix est une filière en résonance avec un intérêt déjà manifesté, même si elle paraît atypique. Privilégier les formats avec feedback fréquent : BTS, BUT, alternance, écoles avec stages dès la 1re année. Si prépa ou L1 généraliste, choisir un campus avec encadrement humain (petite promo, tutorat) pour compenser le risque de désengagement.",
    ],
    ressources: [
      { type: "Livre", title: "Réveiller le tigre, libérer le potentiel des élèves", author: "Anne-Marie Gaignard", desc: "Pour parents qui veulent aider sans pousser. Posture coach plutôt que prof." },
      { type: "Podcast", title: "Génération Z, France Inter", host: "Marie Misset", desc: "Témoignages d'ados qui ont trouvé leur voie en sortant des cases." },
      { type: "Site", title: "JobIRL", url: "https://www.jobirl.com", desc: "Réseau gratuit pour échanger avec des pros, identifier ce qui résonne vraiment." },
    ],
  },
  "moyen-bas": {
    headline: "Grit modeste, attention aux choix d'orientation engageants",
    decoding: [
      "Un score entre 2.5 et 3.5/5 est modeste. L'ado a tendance à pivoter quand l'effort devient ingrat. Ce n'est pas un défaut, c'est un trait modifiable. Mais à 17 ans, ça signale concrètement : éviter les filières où la persévérance silencieuse sur des matières peu motivantes est la clé du succès (prépa, médecine, droit). Privilégier les formats courts, concrets, avec feedback rapide.",
      "À ce niveau, la grit se développe avec : des petites victoires régulières (sport semestriel, projet associatif), un mentor qui croit en l'ado, et un contexte où l'effort est rendu visible. Important : la grit modeste est très souvent corrélée à un autre facteur (anxiété, dépression légère, désalignement profond intérêts/filière). Faire les autres tests (GAD-7, PHQ-9, RIASEC) pour comprendre la racine.",
    ],
    forces: [
      { t: "Lucidité sur ses limites", d: "Capacité à reconnaître quand c'est trop, à demander de l'aide." },
      { t: "Flexibilité", d: "Capable de pivoter sans culpabilité, ce qui peut être un atout dans un monde mouvant." },
      { t: "Énergie sur les sujets passion", d: "Quand un sujet l'allume vraiment, l'engagement existe." },
      { t: "Capacité d'autocompassion", d: "Moins de dureté envers soi que les profils high-grit." },
      { t: "Sociabilité préservée", d: "Moins de risque d'isolement par sur-investissement projet." },
    ],
    vigilances: [
      { t: "Risque de décrochage", d: "Dans toute filière exigeante sans accompagnement adapté." },
      { t: "Stratégies d'évitement", d: "Procrastination sur les sujets durs, qui peuvent devenir des trous de compétence." },
      { t: "Sous-estime ses capacités", d: "« J'y arriverai pas » devient parfois prophétie auto-réalisatrice." },
      { t: "Dépendance au feedback externe", d: "Sans validation régulière, l'engagement chute." },
      { t: "Fenêtre fragile post-bac", d: "L1 est le moment classique de décrochage pour ce profil." },
    ],
    portraits: [
      { n: "Le créatif mal logé", d: "Talent réel en art/musique/écriture, frustré par filière généraliste, décroche en L1." },
      { n: "L'incompris de la prépa", d: "A intégré la prépa par fierté familiale, n'y trouve pas son sens, songe à arrêter dès le 1er trimestre." },
      { n: "L'anxieux invisible", d: "Capable de blocages massifs face à un examen. Grit basse est en partie un symptôme d'anxiété." },
    ],
    pistes_parent: [
      { t: "Ne pas dramatiser le score", d: "La grit basse n'est pas un défaut, c'est un signal d'orientation différent." },
      { t: "Cibler BTS / BUT / alternance", d: "Formats avec feedback rapide, cadre humain, débouchés clairs." },
      { t: "Faire les tests GAD-7 et PHQ-9", d: "Vérifier qu'il n'y a pas anxiété/dépression sous-jacente qui plombe le score." },
      { t: "Coach ou tuteur dès la 1re année post-bac", d: "Investissement modeste, impact massif. 1h/semaine avec un étudiant avancé." },
      { t: "Valoriser les petites victoires", d: "Reconnaître chaque chose finie, pas juste les grandes." },
    ],
    pistes_ado: [
      { t: "Choisir un format adapté", d: "BTS, BUT, école avec stages dès la 1re année. Évite prépa et médecine sauf passion vraie." },
      { t: "Vérifier l'anxiété", d: "Faire le test GAD-7. Une anxiété traitée peut faire remonter la grit de 1 point." },
      { t: "1 projet semestriel petit mais fini", d: "Apprendre à conclure quelque chose, même petit. Sport sur 6 mois, road trip, projet vidéo." },
      { t: "Mentor accessible", d: "Étudiant un peu plus avancé qui te coache. Souvent gratuit via assos étudiantes." },
      { t: "Pas d'orientation sous pression parentale", d: "Si tes parents poussent prépa et que tu n'es pas aligné, parle à un coach d'orientation tiers." },
    ],
    impact_orientation: [
      "À ce niveau, choisir une prépa ou une PASS sans passion authentique pour le sujet est statistiquement une erreur (risque de décrochage > 50%). Mieux : BTS, BUT, école post-bac avec stages dès la 1re année, alternance. Le feedback rapide, le cadre humain, le débouché concret compensent la grit modeste. Si Parcoursup approche et que les vœux sont mal alignés, demander une année de césure (cf. portail Parcoursup) ou une réorientation BTS/BUT, c'est 100% légitime.",
    ],
    ressources: [
      { type: "Livre", title: "Et si je m'écoutais ?", author: "Sophie Carquain", desc: "Pour ado qui doute. Aide à différencier vraies envies et attentes parentales." },
      { type: "Podcast", title: "Émotions, Louie Media", host: "Cyrielle Bedu", desc: "Épisodes sur procrastination, anxiété d'orientation, doute. Valide les émotions." },
      { type: "Site", title: "Onisep, par centres d'intérêt", url: "https://www.onisep.fr/decouvrir-les-metiers", desc: "Catalogue métiers filtrable par intérêt, format vidéo accessible." },
    ],
  },
  "faible": {
    headline: "Grit faible, signal d'orientation prioritaire à recalibrer",
    decoding: [
      "Un score sous 2.5/5 est un signal d'alerte sérieux à 17 ans. Il indique une difficulté structurelle à tenir des engagements long terme. Pas une fatalité (la grit se travaille à tout âge), mais à ne pas ignorer pour Parcoursup. À ce niveau, le risque de décrochage en L1 ou en prépa est élevé (> 60% selon les études françaises sur le décrochage). La priorité n'est pas tant le choix de filière que l'accompagnement.",
      "Important : grit faible est presque toujours un symptôme, pas une cause. Les causes les plus fréquentes : dépression non traitée (faire PHQ-9), anxiété chronique (faire GAD-7), TDAH non diagnostiqué (faire ASRS), trouble DYS non aménagé, ou désalignement profond entre intérêts et études actuelles. Traiter la cause fait remonter la grit naturellement. Sans cause traitable identifiée, c'est un travail patient sur 12-18 mois avec coach et structure quotidienne.",
    ],
    forces: [
      { t: "Honnêteté avec soi", d: "Avoir répondu honnêtement à ce test demande déjà du courage." },
      { t: "Conscience du problème", d: "Sait que la persévérance est un enjeu, premier pas vers le changement." },
      { t: "Capacité à demander de l'aide", d: "À ce niveau, les ados qui consultent ont un meilleur pronostic." },
      { t: "Flexibilité réelle", d: "Sait changer de cap, qualité dans certains contextes (start-up, métiers mouvants)." },
      { t: "Pas enfermé dans la fierté", d: "Moins de difficulté à abandonner un projet inadapté." },
    ],
    vigilances: [
      { t: "Risque décrochage post-bac très élevé", d: "L1 généraliste, prépa : statistiquement très défavorables sans aménagement." },
      { t: "Cause sous-jacente probable", d: "Anxiété, dépression, TDAH, DYS, trauma : faire les screenings." },
      { t: "Évitement chronique", d: "Procrastination sur tous les sujets exigeants, pas que les ingrats." },
      { t: "Estime de soi fragile", d: "Cumul d'abandons passés a souvent miné la confiance." },
      { t: "Pression parentale contre-productive", d: "« Sois plus persévérant ! » empire le problème, jamais ne le résout." },
    ],
    portraits: [
      { n: "L'ado en dépression masquée", d: "Grit faible est ici un symptôme. Score PHQ-9 sera positif. Traiter la dépression débloque tout le reste." },
      { n: "Le TDAH non diagnostiqué", d: "Capable d'hyperfocus sur ses passions, incapable de tenir 10 min de devoirs. Bilan neuropsy prioritaire." },
      { n: "Le perdu d'orientation", d: "Ne sait pas pourquoi il étudie. Pas en souffrance grave, mais sans moteur. Travail RIASEC + accompagnement urgents." },
    ],
    pistes_parent: [
      { t: "Faire les screenings de cause", d: "PHQ-9, GAD-7, ASRS (TDAH), DYS. Avant tout sujet orientation." },
      { t: "Consulter un coach d'orientation", d: "Pour ce profil, l'investissement humain est crucial. 5-10 séances minimum." },
      { t: "Choisir un parcours protecteur", d: "École avec promo restreinte, tutorat, alternance. Pas L1 anonyme à 800 étudiants." },
      { t: "Année de césure formalisée", d: "Si pas prêt à choisir, une année structurée (service civique, bénévolat, langue) vaut mieux qu'une orientation par défaut." },
      { t: "Surtout : pas d'injonction « secoue-toi »", d: "Cette posture aggrave systématiquement. Posture bienveillante, exigeante mais soutenante." },
    ],
    pistes_ado: [
      { t: "Faire les tests de cause", d: "PHQ-9 (dépression), GAD-7 (anxiété), TDAH-ASRS. La grit basse est souvent un symptôme." },
      { t: "Consulter coach orientation", d: "Pas un psy au sens clinique : un coach d'orientation neutre. 5-10 séances pour clarifier." },
      { t: "Pas d'orientation engageante cette année", d: "BTS, BUT, alternance : OK. Prépa, PASS : non, ou alors avec accompagnement musclé." },
      { t: "1 routine non négociable pendant 3 mois", d: "Choisir UNE chose à protéger : sport, sommeil, hobby. Construire la grit par 1 petite réussite répétée." },
      { t: "Demande aux adultes de t'aider à structurer", d: "Tu n'es pas censé(e) tenir tout seul à 17 ans. Parents, coach, mentor : équipe à mobiliser." },
    ],
    impact_orientation: [
      "À ce score, la priorité absolue n'est pas le choix de filière mais l'identification de la cause (dépression, anxiété, TDAH, DYS, désalignement profond). Une cause traitée fait remonter la grit. Sans cause traitable, un parcours protecteur (BTS, BUT, alternance) est statistiquement le meilleur choix. Année de césure formalisée parfaitement légitime. Surtout : éviter les filières prestige sans alignement réel (prépa, médecine, droit en L1 anonyme). Le risque de décrochage à 1 an est très élevé.",
    ],
    ressources: [
      { type: "Livre", title: "Mon ado se cherche, mon ado m'inquiète", author: "Nicole Prieur", desc: "Pour parents en situation difficile. Pose les bonnes questions sans dramatiser." },
      { type: "Podcast", title: "Génération Quoi", host: "Émilie Aubry, France Inter", desc: "Témoignages d'ados en difficulté, parcours de remontée." },
      { type: "Association", title: "Maison des Adolescents", url: "https://anmda.fr", desc: "Lieu d'écoute multidisciplinaire dans chaque département. Gratuit, sans rendez-vous." },
    ],
  },
};

const RichAnalysisSection = ({ rich, accent, accentSoft }) => {
  if (!rich) return null;
  const card = { background: "white", borderRadius: 18, padding: 22, border: "1px solid var(--c-line)" };
  const h3style = { fontSize: 16, marginBottom: 14, color: accent, textTransform: "uppercase", letterSpacing: "0.06em", fontWeight: 700 };
  return (
    <section style={{ paddingTop: 50, paddingBottom: 50, background: "var(--c-cream-light)" }}>
      <div className="shell" style={{ maxWidth: 920 }}>
        <div style={{ textAlign: "center", marginBottom: 36 }}>
          <span className="eyebrow"><span className="dot"></span>Analyse approfondie</span>
          <h2 style={{ marginTop: 10, fontSize: 28 }}>{rich.headline}</h2>
        </div>
        <div style={{ ...card, marginBottom: 18 }}>
          <h3 style={h3style}>Décodage du score</h3>
          {rich.decoding.map((p, i) => (<p key={i} style={{ fontSize: 15, lineHeight: 1.65, color: "var(--c-ink-2)", marginBottom: i < rich.decoding.length - 1 ? 12 : 0 }}>{p}</p>))}
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18, marginBottom: 18 }}>
          <div style={card}>
            <h3 style={h3style}>Forces typiques · 5</h3>
            <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: 10 }}>
              {rich.forces.map((f, i) => (<li key={i} style={{ fontSize: 13.5, lineHeight: 1.55 }}><strong style={{ color: "var(--c-ink)" }}>{f.t}.</strong> <span style={{ color: "var(--c-muted)" }}>{f.d}</span></li>))}
            </ul>
          </div>
          <div style={card}>
            <h3 style={{ ...h3style, color: "#C62828" }}>Points de vigilance · 5</h3>
            <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: 10 }}>
              {rich.vigilances.map((v, i) => (<li key={i} style={{ fontSize: 13.5, lineHeight: 1.55 }}><strong style={{ color: "var(--c-ink)" }}>{v.t}.</strong> <span style={{ color: "var(--c-muted)" }}>{v.d}</span></li>))}
            </ul>
          </div>
        </div>
        <div style={{ ...card, marginBottom: 18 }}>
          <h3 style={h3style}>3 profils typiques à ce niveau</h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14 }}>
            {rich.portraits.map((p, i) => (<div key={i} style={{ background: accentSoft, borderRadius: 12, padding: 14 }}><div style={{ fontSize: 13, fontWeight: 700, color: accent, marginBottom: 6 }}>{p.n}</div><p style={{ fontSize: 13, lineHeight: 1.5, color: "var(--c-ink-2)", margin: 0 }}>{p.d}</p></div>))}
          </div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18, marginBottom: 18 }}>
          <div style={card}>
            <h3 style={h3style}>Côté parent · 5 actions</h3>
            <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: 10 }}>
              {rich.pistes_parent.map((p, i) => (<li key={i} style={{ fontSize: 13.5, lineHeight: 1.55 }}><strong style={{ color: "var(--c-ink)" }}>{p.t}.</strong> <span style={{ color: "var(--c-muted)" }}>{p.d}</span></li>))}
            </ul>
          </div>
          <div style={card}>
            <h3 style={h3style}>Côté ado · 5 actions</h3>
            <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: 10 }}>
              {rich.pistes_ado.map((p, i) => (<li key={i} style={{ fontSize: 13.5, lineHeight: 1.55 }}><strong style={{ color: "var(--c-ink)" }}>{p.t}.</strong> <span style={{ color: "var(--c-muted)" }}>{p.d}</span></li>))}
            </ul>
          </div>
        </div>
        <div style={{ ...card, marginBottom: 18 }}>
          <h3 style={h3style}>Impact sur l'orientation</h3>
          {rich.impact_orientation.map((p, i) => (<p key={i} style={{ fontSize: 15, lineHeight: 1.65, color: "var(--c-ink-2)", marginBottom: i < rich.impact_orientation.length - 1 ? 12 : 0 }}>{p}</p>))}
        </div>
        <div style={card}>
          <h3 style={h3style}>Ressources à explorer · 3</h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14 }}>
            {rich.ressources.map((r, i) => (<div key={i} style={{ background: accentSoft, borderRadius: 12, padding: 14 }}><div style={{ fontSize: 10.5, fontWeight: 800, color: accent, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 6 }}>{r.type}</div><div style={{ fontSize: 14, fontWeight: 700, color: "var(--c-ink)", marginBottom: 4 }}>{r.title}</div>{r.author && <div style={{ fontSize: 12, color: "var(--c-muted)", marginBottom: 6 }}>{r.author}</div>}{r.host && <div style={{ fontSize: 12, color: "var(--c-muted)", marginBottom: 6 }}>{r.host}</div>}<p style={{ fontSize: 12.5, lineHeight: 1.5, color: "var(--c-ink-2)", margin: "0 0 8px" }}>{r.desc}</p>{r.url && <a href={r.url} target="_blank" rel="noopener noreferrer" style={{ fontSize: 12, fontWeight: 600, color: accent, textDecoration: "none" }}>Ouvrir →</a>}</div>))}
          </div>
        </div>
      </div>
    </section>
  );
};

const Results = ({ results, onRestart }) => {
  const { total, level, profile, ciAvg, peAvg, dropoutFlag } = results;
  const copy = LEVEL_COPY[level];
  return (
    <section style={{ paddingTop: 60, paddingBottom: 100 }}>
      <div className="shell" style={{ maxWidth: 820 }}>
        <DisclaimerBanner />
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <span className="chip" style={{ background: "rgba(34,160,107,.15)", color: "#22A06B" }}>
            <Icon.check /> Test terminé · 8 réponses analysées
          </span>
          <h1 style={{ marginTop: 18, fontSize: 36 }}>
            Grit <span style={{ background: "linear-gradient(180deg, transparent 60%, " + copy.color + "55 60%)", paddingInline: 8 }}>{level}</span>
          </h1>
        </div>

        <div style={{
          background: "linear-gradient(160deg, " + copy.color + ", #2D1B69)",
          color: "white", borderRadius: 24, padding: "32px 28px", marginBottom: 24, textAlign: "center",
        }}>
          <div style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", opacity: 0.85, marginBottom: 8 }}>Score Grit</div>
          <div style={{ fontFamily: "var(--font-display)", fontSize: 80, fontWeight: 700, lineHeight: 1, marginBottom: 12 }}>{total} / 5</div>
          <div style={{ maxWidth: 360, margin: "0 auto 10px" }}>
            <div style={{ height: 6, borderRadius: 3, background: "linear-gradient(90deg,#C62828,#FD6936,#FFC107,#22A06B)" }} />
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, opacity: 0.92, marginTop: 5 }}>
              <span>1 · lâche vite</span><span>5 · très persévérant</span>
            </div>
          </div>
          <div style={{ fontSize: 14, opacity: 0.95, marginBottom: 12 }}>Ici, <strong>plus le score est haut, mieux c'est</strong> : grit <strong>{level}</strong>.</div>
          <div style={{ fontSize: 13, opacity: 0.88, marginBottom: 16 }}>
            <strong>Profil : {profile}</strong> · constance des intérêts {ciAvg}/5 · persévérance dans l'effort {peAvg}/5
          </div>
          <p style={{ fontSize: 15, maxWidth: 540, margin: "0 auto", lineHeight: 1.55 }}>{copy.body}</p>
        </div>

        <div style={{ background: "#0A0E2C", color: "white", borderRadius: 20, padding: "32px 28px", marginBottom: 24 }}>
          <h2 style={{ color: "white", fontSize: 22, marginBottom: 14 }}>🎯 Pistes concrètes</h2>
          <ul style={{ paddingLeft: 22, marginBottom: 18, opacity: 0.92, lineHeight: 1.8, fontSize: 14.5 }}>
            {copy.advice.map((a, i) => <li key={i}>{a}</li>)}
          </ul>
          <a href="https://calendly.com/proxxie/entretien" target="_blank" rel="noopener noreferrer" className="btn btn-orange">
            30 min avec Charles pour ajuster la stratégie d'orientation
          </a>
        </div>

        <div style={{ background: "var(--c-cream-light)", borderRadius: 20, padding: 24, border: "1px solid var(--c-line)" }}>
          <h3 style={{ fontSize: 16, marginBottom: 10 }}>📍 La grit ne suffit pas seule</h3>
          <p style={{ fontSize: 13.5, color: "var(--c-muted)", lineHeight: 1.55, marginBottom: 14 }}>
            Compléter avec OCEAN-X (personnalité), RIASEC (intérêts), Valeurs (Schwartz) pour cerner ce sur quoi la grit doit s'appliquer.
          </p>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <a href="Proxxie Test.html" style={{ background: "white", padding: "10px 14px", borderRadius: 99, fontSize: 13, fontWeight: 600, color: "#1320CE", border: "1px solid var(--c-line)", textDecoration: "none" }}>OCEAN-X</a>
            <a href="Proxxie Test RIASEC.html" style={{ background: "white", padding: "10px 14px", borderRadius: 99, fontSize: 13, fontWeight: 600, color: "#FD6936", border: "1px solid var(--c-line)", textDecoration: "none" }}>RIASEC</a>
            <a href="Proxxie Test Valeurs.html" style={{ background: "white", padding: "10px 14px", borderRadius: 99, fontSize: 13, fontWeight: 600, color: "#F5EB3F", border: "1px solid var(--c-line)", textDecoration: "none" }}>Valeurs</a>
            <a href="Proxxie Test Besoins.html" style={{ background: "white", padding: "10px 14px", borderRadius: 99, fontSize: 13, fontWeight: 600, color: "#FD6936", border: "1px solid var(--c-line)", textDecoration: "none" }}>Besoins</a>
          </div>
        </div>

        <div style={{ textAlign: "center", marginTop: 30 }}>
          <button onClick={onRestart} style={{ background: "transparent", border: "none", color: "var(--c-muted)", fontSize: 14, cursor: "pointer", textDecoration: "underline" }}>Refaire le test</button>
        </div>
      </div>
    </section>
  );
};

const ComparePanel = ({ peerLabel, selfLabel, parentAnswers, teenAnswers }) => {
  const pR = computeResults(parentAnswers);
  const tR = computeResults(teenAnswers);
  const gap = Math.abs(pR.total - tR.total);
  return (
    <div style={{ marginBottom: 40 }}>
      <DisclaimerBanner />
      <div style={{ background: "linear-gradient(160deg, #6B46C1, #4C1D95)", color: "white", borderRadius: 24, padding: "32px 28px", marginBottom: 24, textAlign: "center" }}>
        <div style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", opacity: 0.85, marginBottom: 8 }}>Comparaison · Grit</div>
        <div style={{ display: "flex", justifyContent: "center", gap: 40, fontFamily: "var(--font-display)", fontSize: 56 }}>
          <div>
            <div style={{ fontSize: 11, opacity: 0.8, fontFamily: "inherit", marginBottom: 4 }}>{peerLabel || "L'autre"}</div>
            <div>{pR.total} / 5</div>
            <div style={{ fontSize: 13, opacity: 0.85, marginTop: 4 }}>{pR.level}</div>
          </div>
          <div style={{ opacity: 0.6, fontSize: 36 }}>→</div>
          <div>
            <div style={{ fontSize: 11, opacity: 0.8, fontFamily: "inherit", marginBottom: 4 }}>{selfLabel || "Toi"}</div>
            <div>{tR.total} / 5</div>
            <div style={{ fontSize: 13, opacity: 0.85, marginTop: 4 }}>{tR.level}</div>
          </div>
        </div>
        <p style={{ marginTop: 16, opacity: 0.92, fontSize: 15, maxWidth: 520, marginInline: "auto" }}>
          {gap >= 1.0
            ? "Écart significatif. Vos deux lectures de la persévérance diffèrent nettement. Conversation prioritaire pour calibrer."
            : gap >= 0.5
              ? "Écart modéré. À discuter ensemble."
              : "Profils alignés."}
        </p>
      </div>
    </div>
  );
};

const buildEmailSummary = (results) => {
  return "Test Grit (Duckworth Grit-S)\nScore Grit : " + results.total + "/5, " + results.level + "\nProfil : " + results.profile + "\nConstance intérêts : " + results.ciAvg + " · Persévérance effort : " + results.peAvg;
};

const TestApp = () => {
  const PARENT_PREDICT = React.useMemo(() => readPredictHash(), []);
  const RESULTS_HASH = React.useMemo(() => readResultsHash(), []);
  const [persona, setPersona] = React.useState(null);
  const [mode, setMode] = React.useState(RESULTS_HASH ? "results" : (PARENT_PREDICT ? "compare-intro" : "landing"));
  const [results, setResults] = React.useState(RESULTS_HASH ? computeResults(RESULTS_HASH.a) : null);
  const [answers, setAnswers] = React.useState(RESULTS_HASH ? RESULTS_HASH.a : null);
  const goPicker = () => { setMode("picker"); window.scrollTo({ top: 0, behavior: "smooth" }); };
  const pickPersona = (p) => {
    var testType = window.__proxxie_test_type || 'grit';
    var consentKey = 'proxxie_test_consent_' + testType;
    var hasConsent = false;
    try { hasConsent = !!window.localStorage.getItem(consentKey); } catch(e) {}
    if (window.trackEvent) window.trackEvent('test_initiated', { test_type: testType, persona: p });
    function startNow() {
      setPersona(p);
      setMode("test");
      window.scrollTo({ top: 0, behavior: "smooth" });
      if (window.trackEvent) window.trackEvent('test_started', { test_type: testType, persona: p });
      window.__proxxie_test_in_progress = { startedAt: Date.now(), questionIndex: 0, totalQuestions: 0, completionPct: 0, testType: testType, persona: p };
    }
    if (hasConsent) { startNow(); return; }
    if (window.trackEvent) window.trackEvent('test_consent_shown', { test_type: testType });
    var overlay = document.createElement('div');
    overlay.id = '__proxxie_test_consent';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.style.cssText = 'position:fixed;inset:0;z-index:99999;background:rgba(10,14,44,.55);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);display:grid;place-items:center;padding:24px';
    overlay.innerHTML = '<div style="background:#fff;border-radius:18px;padding:28px 32px;max-width:520px;font-family:Montserrat,system-ui,sans-serif;box-shadow:0 24px 60px -16px rgba(19,32,206,.28)"><div style="font-family:Mulish,Goldplay,system-ui,sans-serif;font-size:22px;font-weight:600;letter-spacing:-.02em;color:#0A0E2C;margin-bottom:10px">Avant de commencer ce test</div><p style="font-size:14px;line-height:1.55;color:#2A2F4F;margin:0 0 14px">Vos réponses sont confidentielles et stockées <strong>uniquement sur votre appareil</strong>. Elles ne sortent jamais sans votre action.</p><p style="font-size:14px;line-height:1.55;color:#2A2F4F;margin:0 0 18px">En continuant, vous acceptez que vos réponses soient analysées par notre algorithme pour générer un rapport. <strong>Elles ne servent jamais à entraîner un modèle d\'IA.</strong></p><div style="display:flex;gap:10px;justify-content:flex-end;flex-wrap:wrap"><button id="__proxxie_decline" style="background:transparent;border:1.5px solid rgba(10,14,44,.16);border-radius:99px;padding:10px 18px;font-size:13px;font-weight:600;color:#0A0E2C;cursor:pointer;font-family:inherit">Refuser</button><button id="__proxxie_accept" style="background:#FD6936;color:#fff;border:none;border-radius:99px;padding:10px 22px;font-size:14px;font-weight:600;cursor:pointer;font-family:inherit;box-shadow:0 8px 22px -6px rgba(253,105,54,.55)">Commencer le test →</button></div></div>';
    document.body.appendChild(overlay);
    document.getElementById('__proxxie_accept').onclick = function() {
      try { window.localStorage.setItem(consentKey, 'granted_' + Date.now()); } catch(e) {}
      if (window.trackEvent) window.trackEvent('test_consent_granted', { test_type: testType });
      overlay.remove();
      startNow();
    };
    document.getElementById('__proxxie_decline').onclick = function() {
      if (window.trackEvent) window.trackEvent('test_consent_declined', { test_type: testType });
      overlay.remove();
    };
  };
  const exitTest = () => { setMode(PARENT_PREDICT ? "compare-intro" : "landing"); setPersona(null); window.scrollTo({ top: 0, behavior: "smooth" }); };
  const onComplete = (ans) => {
    setAnswers(ans);
    setResults(computeResults(ans));
    setMode("results");
    window.scrollTo({ top: 0, behavior: "smooth" });
    if (window.trackEvent) {
      var inProgress = window.__proxxie_test_in_progress;
      var elapsed = inProgress && inProgress.startedAt ? (Date.now() - inProgress.startedAt) : null;
      window.trackEvent('test_completed', {
        test_type: window.__proxxie_test_type || 'grit',
        total_questions: (ans || []).length,
        time_total_ms: elapsed,
        persona: inProgress ? inProgress.persona : null
      });
    }
    window.__proxxie_test_in_progress = null;
  };
  const restart = () => { try { window.localStorage.removeItem(STORAGE_KEY); } catch (e) {} setResults(null); setAnswers(null); setMode("test"); window.scrollTo({ top: 0, behavior: "smooth" }); };
  const effectivePersona = PARENT_PREDICT ? "self_compare" : persona;
  const storageKeyEffective = effectivePersona === "predict" ? STORAGE_KEY + ":predict" : STORAGE_KEY;
  return (
    <>
      <ProxxieNav />
      {mode === "landing" && (<><TestHero onStart={goPicker} /><HowItWorks /></>)}
      {mode === "picker" && <PersonaIntro testName="Grit" accent="#6B46C1" comingFromPredict={null} onPick={pickPersona} />}
      {mode === "compare-intro" && <PersonaIntro testName="Grit" accent="#6B46C1" comingFromPredict={PARENT_PREDICT} onPick={pickPersona} />}
      {mode === "test" && (
        <>
          {persona === "predict" && (<div style={{ background: "#F5EB3F", color: "#0A0E2C", padding: "10px 16px", textAlign: "center", fontSize: 13, fontWeight: 600 }}>🎯 Mode prédiction · Répondez comme vous pensez que votre ado répondrait</div>)}
          <TestFlowEngine questions={QUESTIONS} storageKey={storageKeyEffective} getTypeMeta={getTypeMeta} onExit={exitTest} onComplete={onComplete} />
        </>
      )}
      {mode === "results" && results && (
        <>
          {effectivePersona === "self_compare" && PARENT_PREDICT && (<section style={{ paddingTop: 40, paddingBottom: 0 }}><div className="shell" style={{ maxWidth: 820 }}><ComparePanel peerLabel={PARENT_PREDICT.peerLabel} selfLabel={PARENT_PREDICT.selfLabel} parentAnswers={PARENT_PREDICT.a} teenAnswers={answers} /></div></section>)}
          {persona === "predict" && (<section style={{ paddingTop: 40, paddingBottom: 0 }}><div className="shell" style={{ maxWidth: 820 }}><ShareLinkPanel testCode="Grit" accent="#6B46C1" answers={answers} defaultName="" onSkip={() => {}} /></div></section>)}
          <EmailResultsActions testCode="Grit" testName="Grit (Duckworth)" accent="#6B46C1" summary={buildEmailSummary(results)} answers={answers} />
          <Results results={results} onRestart={restart} />
          <RichAnalysisSection rich={RICH_RESULTS[results.level]} accent="#6B46C1" accentSoft="rgba(107,70,193,0.12)" />
        </>
      )}
      <Footer />
    </>
  );
};

ReactDOM.createRoot(document.getElementById("root")).render(<TestApp />);
'''


def build_grit(source_path: pathlib.Path, target_path: pathlib.Path) -> str:
    if not source_path.exists():
        return f"SOURCE manquant : {source_path.name}"
    shutil.copy(source_path, target_path)
    html = target_path.read_text(encoding="utf-8")
    m = re.search(r'(<script type="__bundler/manifest">)(.*?)(</script>)', html, re.DOTALL)
    if not m:
        return f"{target_path.name}: pas de manifest"
    manifest = json.loads(m.group(2))
    uuid = next((k for k in manifest if k.startswith(ASSET_UUID_PREFIX)), None)
    if uuid is None:
        return f"{target_path.name}: asset {ASSET_UUID_PREFIX} introuvable"
    entry = manifest[uuid]
    raw = base64.b64decode(entry['data'])
    comp = entry.get('compressed', False)
    src = gzip.decompress(raw).decode('utf-8') if comp else raw.decode('utf-8')

    src = re.sub(r'const __PROXXIE_TEST_ID__\s*=\s*"[^"]*";', 'const __PROXXIE_TEST_ID__ = "grit";', src, count=1)
    boundary_match = re.search(r'(/\*\s*Test Proxxie Anxi[^/]*\*/\s*\n)?const QUESTIONS\s*=', src)
    if not boundary_match:
        return f"{target_path.name}: boundary introuvable"
    new_src = _bridge_common.patch_persona_intro(src[:boundary_match.start()]) + _bridge_common.wire_bridge(GRIT_BLOCK, "grit", "Proxxie%20Test%20Grit.html")

    nd = new_src.encode('utf-8')
    if comp:
        nd = gzip.compress(nd)
    entry['data'] = base64.b64encode(nd).decode('ascii')
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]

    new_html = re.sub(r'<title[^>]*>[^<]*</title>', '<title>Test Grit, Proxxie</title>', new_html, count=1)
    new_html = re.sub(r'<title[^>]*>[^<]*<\\/title>', '<title>Test Grit, Proxxie<\\/title>', new_html, count=1)

    target_path.write_text(new_html, encoding='utf-8')
    return f"{target_path.name}: built (asset {uuid[:8]}, src {len(src)} → {len(new_src)})"


if __name__ == "__main__":
    print(build_grit(SOURCE, TARGET))
    print(build_grit(SOURCE, TARGET_LOWER))

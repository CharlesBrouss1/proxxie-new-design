#!/usr/bin/env python3
"""Construit Proxxie Test PHQ9.html depuis Proxxie Test Anxiete.html.

Stratégie : on duplique le bundle Anxiete (toute l'infra React + nav + flow engine
+ persona picker + share link + email actions reste identique), puis on swap UNIQUEMENT
le contenu test-spécifique de l'asset 61feca88 (du `const QUESTIONS` jusqu'à la fin).

Touche aussi :
· const __PROXXIE_TEST_ID__ = "anxiete" → "phq9"
· STORAGE_KEY → proxxie-phq9-answers
· Couleur accent #487AFF (bleu anxiété) → #5C6BC0 (indigo dépression)
· Référence : GAD-7 Spitzer → PHQ-9 Kroenke 2001
· Item 9 (idées suicidaires) → alerte 3114 non-fermable

Idempotent · regenerate à chaque run (le fichier cible est entièrement réécrit
à partir du Anxiete source à jour).
"""
import re, json, base64, gzip, pathlib, shutil
import _bridge_common

REPO = pathlib.Path(__file__).parent
SOURCE = REPO / "Proxxie Test Anxiete.html"
TARGET = REPO / "Proxxie Test PHQ9.html"
TARGET_LOWER = REPO / "test-phq9.html"  # lowercase twin (cf. _patch_test_pages_phase1.py)
ASSET_UUID_PREFIX = "61feca88"

# ---- Le bloc PHQ-9 qui remplace tout de `const QUESTIONS` à la fin ----

PHQ9_BLOCK = r'''/* Test Proxxie Dépression, screening PHQ-9 (Kroenke, Spitzer & Williams 2001)
   ⚠️ Outil de SENSIBILISATION, PAS un diagnostic médical
   ⚠️ Item 9 (idées noires) déclenche l'affichage immédiat du 3114, numéro
      national de prévention du suicide, gratuit, anonyme, 24h/24, 7j/7. */

const QUESTIONS = [
  // PHQ-9 officiel · "Au cours des 2 dernières semaines, à quelle fréquence avez-vous
  // été gêné(e) par les problèmes suivants ?"
  // Échelle officielle 0-3 · ici on utilise 1-5 (cohérence app) puis on mappe.
  { type: "PHQ", q: "Peu d'intérêt ou de plaisir à faire les choses." },
  { type: "PHQ", q: "Me sentir triste, déprimé(e) ou désespéré(e)." },
  { type: "PHQ", q: "Difficultés à s'endormir, sommeil interrompu, ou dormir trop." },
  { type: "PHQ", q: "Me sentir fatigué(e) ou manquer d'énergie." },
  { type: "PHQ", q: "Manque d'appétit ou trop manger." },
  { type: "PHQ", q: "Avoir une mauvaise opinion de soi, sentir qu'on est un raté, ou qu'on a déçu sa famille ou soi-même." },
  { type: "PHQ", q: "Difficultés à se concentrer (lire, regarder la télé, étudier)." },
  { type: "PHQ", q: "Bouger ou parler si lentement que les autres l'ont remarqué. Ou au contraire, être si agité(e) qu'on a du mal à tenir en place." },
  { type: "PHQ_RISK", q: "Avoir pensé qu'il vaudrait mieux être mort(e) ou se faire du mal d'une manière ou d'une autre." },
];

const TYPE_META = {
  PHQ:      { l: "PHQ-9 · Dépression", c: "#5C6BC0", short: "9 items validés (Kroenke 2001)" },
  PHQ_RISK: { l: "PHQ-9 · Sécurité",   c: "#D32F2F", short: "Item critique, déclenche message d'aide" },
};
const STORAGE_KEY = "proxxie-phq9-answers";

const getTypeMeta = (q) => ({ label: TYPE_META[q.type].l, color: TYPE_META[q.type].c });

const computeResults = (answers) => {
  // Mapping échelle app (1-5) → échelle officielle PHQ-9 (0-3)
  // 1 (jamais) → 0 · 2 → 1 · 3 → 1 · 4 → 2 · 5 (presque tous les jours) → 3
  const phqMap = { 1: 0, 2: 1, 3: 1, 4: 2, 5: 3 };
  let phqScore = 0;
  let item9Raw = 0;
  QUESTIONS.forEach((q, idx) => {
    if (answers[idx] == null) return;
    phqScore += phqMap[answers[idx]];
    if (q.type === "PHQ_RISK") item9Raw = answers[idx];
  });
  // Seuils officiels Kroenke 2001 (score 0-27)
  let level = "minimal", levelLabel = "Symptômes minimaux";
  if (phqScore >= 20) { level = "severe"; levelLabel = "Sévère"; }
  else if (phqScore >= 15) { level = "moderate_severe"; levelLabel = "Modérément sévère"; }
  else if (phqScore >= 10) { level = "moderate"; levelLabel = "Modéré"; }
  else if (phqScore >= 5) { level = "mild"; levelLabel = "Léger"; }
  const consultFlag = phqScore >= 10;
  const safetyAlert = item9Raw >= 4; // 4 ou 5 sur l'échelle 1-5 = idées présentes plusieurs jours
  return { phqScore, level, levelLabel, consultFlag, safetyAlert, item9Raw };
};

const DisclaimerBanner = () => (
  <div style={{
    background: "#EEF1F9", borderLeft: "4px solid #5C6BC0",
    padding: "14px 20px", marginBottom: 30, borderRadius: 8,
    fontSize: 13.5, color: "#0A0E2C", lineHeight: 1.55,
  }}>
    <strong>⚠️ Ce test n'est pas un diagnostic médical.</strong> Il s'agit d'un outil de sensibilisation basé sur le <strong>PHQ-9</strong> (Kroenke, Spitzer & Williams, 2001), questionnaire validé internationalement pour la dépression. Si les résultats suggèrent un niveau modéré ou sévère, consultez un médecin généraliste, un psychologue ou un psychiatre.
  </div>
);

const SafetyAlert = () => (
  <div style={{
    background: "linear-gradient(160deg, #D32F2F, #8B1F1F)", color: "white",
    borderRadius: 18, padding: "26px 28px", marginBottom: 26,
    boxShadow: "0 18px 40px -14px rgba(211,47,47,.45)",
  }}>
    <div style={{ fontSize: 13, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.12em", opacity: 0.92, marginBottom: 10 }}>
      ❤️ Vous n'êtes pas seul(e)
    </div>
    <h2 style={{ color: "white", fontSize: 22, lineHeight: 1.35, marginBottom: 14 }}>
      Si vous, ou votre ado, avez des idées noires, parlez-en maintenant.
    </h2>
    <ul style={{ listStyle: "none", padding: 0, margin: "0 0 18px", display: "grid", gap: 12, fontSize: 14.5, lineHeight: 1.55 }}>
      <li style={{ background: "rgba(255,255,255,.12)", borderRadius: 12, padding: "12px 16px" }}>
        <strong style={{ fontSize: 18, letterSpacing: "0.04em" }}>3114</strong>, numéro national de prévention du suicide
        <div style={{ opacity: 0.88, fontSize: 13, marginTop: 2 }}>Gratuit, confidentiel, 24h/24, 7j/7. Un professionnel de santé répond.</div>
      </li>
      <li style={{ background: "rgba(255,255,255,.12)", borderRadius: 12, padding: "12px 16px" }}>
        <strong>Fil Santé Jeunes</strong> · 0 800 235 236
        <div style={{ opacity: 0.88, fontSize: 13, marginTop: 2 }}>Pour les 12-25 ans, anonyme, gratuit, 7j/7 de 9h à 23h.</div>
      </li>
      <li style={{ background: "rgba(255,255,255,.12)", borderRadius: 12, padding: "12px 16px" }}>
        <strong>Urgences</strong> · 15 ou 112
        <div style={{ opacity: 0.88, fontSize: 13, marginTop: 2 }}>Si danger immédiat ou crise aiguë.</div>
      </li>
    </ul>
    <p style={{ fontSize: 14, opacity: 0.95, lineHeight: 1.55, margin: 0 }}>
      Demander de l'aide est un acte de force, pas de faiblesse. Les idées suicidaires sont un symptôme qui se soigne, comme la fièvre.
    </p>
  </div>
);

const TestHero = ({ onStart }) => (
  <section style={{ paddingTop: 70, paddingBottom: 80, position: "relative", overflow: "hidden" }}>
    <Pill color="rgba(245,235,63,.5)" w={260} h={130} style={{ position: "absolute", top: 110, right: -60, borderRadius: 999 }} />
    <Half color="rgba(92,107,192,.18)" side="t" w={300} h={120} style={{ position: "absolute", bottom: -10, left: -40 }} />
    <div className="shell" style={{ position: "relative", display: "grid", gridTemplateColumns: "1.1fr 1fr", gap: 60, alignItems: "center" }}>
      <div>
        <span className="chip" style={{ background: "rgba(92,107,192,.15)", color: "#5C6BC0" }}>
          <Icon.spark style={{ width: 14, height: 14 }} /> Outil de sensibilisation · pas un diagnostic
        </span>
        <h1 style={{ marginTop: 22, marginBottom: 22 }}>
          Test <span style={{ background: "linear-gradient(180deg, transparent 60%, #F5EB3F 60%)", paddingInline: 4 }}>Dépression</span> · screening PHQ-9 pour votre ado.
        </h1>
        <p style={{ fontSize: 18, color: "var(--c-ink-2)", maxWidth: 520, marginBottom: 28 }}>
          Le <strong>PHQ-9</strong> est l'outil clinique de référence utilisé en médecine générale dans le monde entier. Il complète le GAD-7 (anxiété) sur le couple anxiété-dépression, fréquent à l'adolescence.
        </p>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 22 }}>
          <button className="btn btn-orange btn-lg btn-arrow" onClick={onStart}>Démarrer le test</button>
          <a href="#methode" className="btn btn-ghost btn-lg"><Icon.play /> Comment ça marche</a>
        </div>
        <div style={{ display: "flex", gap: 22, fontSize: 13, color: "var(--c-muted)", flexWrap: "wrap" }}>
          <span><Icon.shield style={{ width: 13, height: 13, verticalAlign: "-2px", marginRight: 4 }} /> Données privées · stockées en local</span>
          <span>⏱ 3 min · 9 questions</span>
          <span>📋 PHQ-9 (Kroenke 2001)</span>
        </div>
      </div>
      <div style={{ position: "relative" }}>
        <div style={{ background: "white", borderRadius: 24, padding: 28, boxShadow: "var(--shadow-md)", border: "1px solid var(--c-line)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 18 }}>
            <span style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--c-muted)" }}>Question 3 / 9</span>
            <span style={{ fontSize: 12, color: "#5C6BC0", fontWeight: 600 }}>● PHQ-9</span>
          </div>
          <div style={{ height: 4, background: "var(--c-cream)", borderRadius: 2, marginBottom: 24, overflow: "hidden" }}>
            <div style={{ width: "33%", height: "100%", background: "#5C6BC0" }} />
          </div>
          <h3 style={{ fontSize: 19, lineHeight: 1.35, fontWeight: 600, marginBottom: 22, fontFamily: "var(--font-display)", letterSpacing: "-0.02em" }}>
            "Me sentir fatigué(e) ou manquer d'énergie."
          </h3>
          <div style={{ display: "flex", gap: 8, justifyContent: "space-between" }}>
            {["Jamais", "Quelques jours", "Plus de la moitié", "Presque chaque jour", "Tous les jours"].map((label, n) => (
              <div key={n} style={{
                flex: 1, padding: "10px 4px", borderRadius: 10, textAlign: "center",
                background: n === 2 ? "linear-gradient(160deg, #5C6BC0, #3949AB)" : "var(--c-cream)",
                color: n === 2 ? "white" : "var(--c-ink)",
                fontWeight: 600, fontSize: 9.5,
                border: n === 2 ? "none" : "1px solid var(--c-line)",
              }}>{label}</div>
            ))}
          </div>
        </div>
        <div style={{ position: "absolute", bottom: -18, right: -18, background: "#0A0E2C", color: "white", padding: "12px 16px", borderRadius: 14, fontSize: 12, display: "flex", alignItems: "center", gap: 10, boxShadow: "var(--shadow-md)" }}>
          <Icon.brain style={{ color: "#F5EB3F" }} /> Standard clinique mondial
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
        <h2 style={{ marginTop: 14 }}>Le PHQ-9, outil clinique de référence.</h2>
        <p style={{ fontSize: 17, color: "var(--c-ink-2)", marginTop: 16 }}>
          Le PHQ-9 (Patient Health Questionnaire, 9 items) est utilisé dans le monde entier pour évaluer la dépression. 5 seuils officiels : minimal (0-4), léger (5-9), modéré (10-14), modérément sévère (15-19), sévère (20-27). Modéré ou plus = consultation recommandée.
        </p>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, maxWidth: 920, margin: "0 auto" }}>
        {[
          { n: "1", t: "9 questions", d: "Les 9 critères du DSM pour la dépression majeure. 3 min en moyenne." },
          { n: "2", t: "Seuils cliniques", d: "Score ≥ 10 = niveau modéré ou plus → consultation recommandée." },
          { n: "3", t: "Filet de sécurité", d: "L'item 9 (idées noires) déclenche un message d'aide avec le 3114, la première priorité." },
        ].map((s) => (
          <div key={s.n} style={{ background: "var(--c-cream-light)", padding: 22, borderRadius: 16, border: "1px solid var(--c-line)" }}>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: "linear-gradient(135deg, #5C6BC0, #3949AB)", color: "white", display: "grid", placeItems: "center", fontWeight: 700, fontFamily: "var(--font-num)", marginBottom: 14 }}>{s.n}</div>
            <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 6 }}>{s.t}</div>
            <p style={{ fontSize: 13.5, color: "var(--c-muted)", lineHeight: 1.55 }}>{s.d}</p>
          </div>
        ))}
      </div>
    </div>
  </section>
);

const LEVEL_COPY = {
  minimal: {
    color: "#22A06B",
    body: "L'ado ne présente pas de signaux dépressifs cliniques sur les 2 dernières semaines. Maintenir l'hygiène de vie (sommeil, activité physique, lien social) qui protège la santé mentale ado.",
    action: "Refaire ce test dans 3 mois si vous percevez un changement.",
  },
  mild: {
    color: "#487AFF",
    body: "Quelques signaux présents, mais pas au seuil clinique. À l'adolescence, les fluctuations émotionnelles sont normales. Si ces signes persistent plus de 3 semaines OU s'accompagnent d'isolement marqué, parler à un professionnel.",
    action: "Refaire le test dans 4 semaines. Garder le dialogue ouvert sans surinvestir.",
  },
  moderate: {
    color: "#FD6936",
    body: "Le score atteint le seuil clinique. Une consultation auprès du médecin traitant ou d'un psychologue est indiquée. La dépression modérée à l'adolescence répond bien à un suivi précoce, psychothérapie en première intention.",
    action: "Prendre rendez-vous chez le médecin traitant ou un psychologue cette semaine.",
  },
  moderate_severe: {
    color: "#E64A19",
    body: "Le score est élevé. Une évaluation par un pédopsychiatre ou un psychologue clinicien est fortement recommandée. À ce niveau, l'impact sur les études et la vie sociale est presque toujours significatif.",
    action: "Consultation pédopsy ou psychologue clinicien dans les 7 jours. Le médecin traitant peut orienter et faire un certificat pour Parcoursup si besoin.",
  },
  severe: {
    color: "#C62828",
    body: "Le score correspond à une dépression sévère. Une prise en charge urgente est nécessaire. Le médecin traitant, le CMP (Centre Médico-Psychologique) ou les urgences pédopsy sont les bonnes portes d'entrée.",
    action: "Consultation cette semaine, sans attendre. CMP gratuit dans tous les départements. Si urgence : Fil Santé Jeunes 0 800 235 236, gratuit, anonyme.",
  },
};

/* RICH_RESULTS : contenu psychométrique étayé par niveau, baké dans le bundle.
   Permet d'afficher une analyse fine directement sur la page de résultats,
   sans appel LLM en runtime. */
const RICH_RESULTS = {
  minimal: {
    headline: "Symptômes minimaux, le niveau attendu en bonne santé mentale",
    decoding: [
      "Un score sous 5 signifie que votre ado ne présente aucun signal dépressif cliniquement significatif sur les 14 derniers jours. C'est le niveau attendu chez un ado qui dort suffisamment, a des liens sociaux, et trouve du sens dans ses activités. Ne pas confondre avec « tout va bien à 100% » : un ado peut avoir un score minimal et traverser une période difficile, le PHQ-9 mesure surtout l'intensité et la durée des symptômes.",
      "À retenir : la santé mentale n'est pas un état figé. Refaire le test dans 3 mois si vous percevez un changement (baisse d'énergie persistante, isolement, perte d'intérêt). La période la plus à risque pour l'apparition d'un premier épisode dépressif chez l'ado se situe entre 14 et 17 ans, particulièrement chez les filles.",
    ],
    forces: [
      { t: "Régulation émotionnelle correcte", d: "Capacité à traverser les frustrations sans bascule durable." },
      { t: "Ancrage du quotidien", d: "Les routines (sommeil, repas, école) fonctionnent globalement." },
      { t: "Lien social préservé", d: "Au moins 1 à 2 personnes de confiance dans l'entourage proche." },
      { t: "Plaisir préservé", d: "Activités qui font encore plaisir, énergie pour s'y engager." },
      { t: "Vision du futur", d: "Capacité à se projeter à 3-6 mois sans angoisse paralysante." },
    ],
    vigilances: [
      { t: "Période de transition", d: "Déménagement, rupture amicale, séparation parentale peuvent rapidement faire monter le score." },
      { t: "Réseaux sociaux", d: "Au-delà de 3h/jour, corrélation avec hausse symptômes dépressifs (méta Twenge 2018)." },
      { t: "Sommeil", d: "Moins de 7h/nuit régulières est un précurseur classique." },
      { t: "Isolement progressif", d: "Désengagement des activités collectives, signal précoce." },
      { t: "Histoire familiale", d: "Antécédents dépressifs parentaux doublent le risque, à surveiller." },
    ],
    portraits: [
      { n: "L'équilibré", d: "Ado tranquille, alterne hauts et bas normaux. Sommeil régulier, ami(e)s stables, hobbies actifs." },
      { n: "Le combattant traversant", d: "Vient de surmonter une période difficile (échec scolaire, rupture). Score bas car les ressources internes ont fonctionné." },
      { n: "Le sereinement engagé", d: "Investi dans 2-3 projets (sport, art, école). Sens et structure protègent du mal-être." },
    ],
    pistes_parent: [
      { t: "Maintenir le rituel hebdo", d: "1 moment ado-parent prévisible chaque semaine (resto, sport, ciné) sans téléphone." },
      { t: "Observer sans surveiller", d: "Repérer les changements sur 2-3 semaines avant de questionner." },
      { t: "Valider les hauts ET les bas", d: "« C'est ok d'aller mal une journée », sans dramatiser ni minimiser." },
      { t: "Protéger le sommeil", d: "Téléphones hors chambre la nuit, règle non négociable jusqu'à 18 ans." },
      { t: "Ne pas projeter ses propres angoisses", d: "Si vous-même êtes anxieux pour son avenir, traitez votre anxiété en parallèle." },
    ],
    pistes_ado: [
      { t: "Bouger 3x/semaine", d: "30 min d'activité cardio fait baisser le risque dépressif autant qu'un antidépresseur léger." },
      { t: "1 confident hors famille", d: "Identifier 1 adulte de confiance (prof, oncle, coach) à qui parler si besoin." },
      { t: "Limiter scroll passif", d: "Plafond 90 min/jour Insta+TikTok+Snap combinés. Pas avant 9h, pas après 21h." },
      { t: "1 projet long terme", d: "Sport, instrument, association : avoir 1 truc qui se construit sur 6+ mois." },
      { t: "Journal de 3 lignes", d: "Le soir : 1 bonne chose, 1 difficulté, 1 chose pour demain. Effet anti-rumination prouvé." },
    ],
    impact_orientation: [
      "Avec un score minimal, l'orientation peut se construire sereinement. L'énergie psychique est disponible pour explorer (RIASEC), tester des stages, faire ses choix Parcoursup sans biais lié à l'humeur. C'est la fenêtre idéale pour les choix engageants : prépa, filières sélectives, projets ambitieux. Le risque inverse : surinvestir scolaire pour éviter d'autres sujets (relation, identité, autonomie). Veiller à un équilibre vie/études dans cette zone.",
    ],
    ressources: [
      { type: "Livre", title: "Sortir de la dépression et vaincre la déprime", author: "Jean Cottraux", desc: "Référence francophone TCC. Niveau accessible parents." },
      { type: "Podcast", title: "Les Adultes de Demain", host: "Stéphanie d'Esclaibes", desc: "Épisodes courts sur santé mentale ado, ton bienveillant." },
      { type: "Association", title: "Nightline France", url: "https://nightline.fr", desc: "Écoute par étudiants pour étudiants, gratuit, anonyme, soir+nuit." },
    ],
  },
  mild: {
    headline: "Symptômes légers, surveillance active sans alarme",
    decoding: [
      "Un score entre 5 et 9 indique des signaux dépressifs présents mais pas au seuil clinique. À l'adolescence, c'est extrêmement courant (jusqu'à 25% des 15-18 ans selon Santé Publique France 2023). La plupart du temps, ces fluctuations s'autorégulent en 2-4 semaines. La distinction-clé : durée et impact. Si ça dure plus de 3 semaines OU ça commence à toucher les notes, le sommeil, les amis, on bascule vers le modéré.",
      "Ce niveau n'est pas un diagnostic, c'est un signal de vigilance. Le faux pas le plus fréquent des parents : soit dramatiser (« va voir un psy ! ») et braquer l'ado, soit minimiser (« t'as juste besoin de bouger ») et passer à côté d'une vraie souffrance. La bonne posture : ouvrir la conversation sans presser, refaire le test dans 4 semaines, ajuster en fonction.",
    ],
    forces: [
      { t: "Conscience de soi", d: "Capacité à reconnaître son état, étape préalable au changement." },
      { t: "Demande implicite", d: "Avoir fait le test EST une demande d'aide, à valoriser." },
      { t: "Réserves fonctionnelles", d: "L'école, les amis, le quotidien tiennent encore globalement." },
      { t: "Marge d'action", d: "À ce niveau, les interventions non médicamenteuses suffisent souvent." },
      { t: "Pas de comorbidité grave", d: "Si pas d'idées noires (item 9 = 0), pas d'urgence." },
    ],
    vigilances: [
      { t: "Durée > 3 semaines", d: "Si les symptômes persistent au-delà, consulter sans attendre." },
      { t: "Impact scolaire net", d: "Chute de notes inexpliquée, absences répétées = consulter." },
      { t: "Isolement croissant", d: "Désengagement social progressif, signal d'aggravation." },
      { t: "Comorbidité anxiété", d: "Si le test GAD-7 est aussi positif, le risque de bascule modéré est plus élevé." },
      { t: "Pic du dimanche soir", d: "Anxiété/tristesse récurrente avant l'école = signal à explorer." },
    ],
    portraits: [
      { n: "Le surchargé silencieux", d: "Pression scolaire/parentale forte, dort mal, dit « ça va » par défaut. Souvent en Terminale ou hypokhâgne." },
      { n: "Le post-rupture", d: "Rupture amicale ou amoureuse récente. Score monte 4-8 semaines, redescend si entourage bienveillant." },
      { n: "L'identité en chantier", d: "Questionnements sur orientation sexuelle, genre, vocation. Anxiété + tristesse mêlées." },
    ],
    pistes_parent: [
      { t: "Ouvrir, ne pas interroger", d: "« J'ai l'impression que tu es ailleurs ces temps-ci, tu veux qu'on en parle ? » plutôt que « qu'est-ce qui se passe ? »." },
      { t: "Proposer le médecin traitant", d: "Pas le psy d'emblée, le MT comme première porte. Moins stigmatisant." },
      { t: "Réduire la pression scolaire 4 semaines", d: "Annoncer explicitement : « les notes ne sont pas la priorité ce mois-ci »." },
      { t: "Vérifier le sommeil", d: "Demander combien d'heures réelles, pas l'horaire de coucher. Viser 8h minimum." },
      { t: "Surveiller sans espionner", d: "Repas en famille 4x/semaine. Refus de manger ensemble = signal." },
    ],
    pistes_ado: [
      { t: "Refaire le test dans 30 jours", d: "Bookmarker la page, refaire le PHQ-9 dans 4 semaines pour mesurer l'évolution." },
      { t: "Parler à 1 personne cette semaine", d: "Ami, prof, infirmier scolaire, médecin. Verbaliser réduit déjà l'intensité." },
      { t: "Sport 3x cette semaine", d: "30 min suffisent. Marche rapide compte. Effet mesurable dès 7 jours." },
      { t: "Couper réseaux 2h/jour minimum", d: "Idéalement matin (réveil) et soir (avant dodo). Pour casser le cycle de comparaison." },
      { t: "Fil Santé Jeunes si seul", d: "0 800 235 236, gratuit, anonyme, 9h-23h. Pas pour les urgences uniquement." },
    ],
    impact_orientation: [
      "Un score léger n'empêche pas Parcoursup, mais demande de la prudence sur les choix les plus engageants. Éviter les filières où l'isolement est la norme la première année (prépa parisienne en internat, médecine sans groupe d'amis sur place) si le score ne redescend pas. Privilégier les formations avec encadrement (BUT, BTS avec promo restreinte, écoles post-bac avec parrainage) qui offrent un filet social naturel. Si le score persiste, le médecin traitant peut faire un certificat pour aménagement Parcoursup (priorité, choix géographique).",
    ],
    ressources: [
      { type: "Livre", title: "L'adolescence pour les nuls", author: "Michel Fize", desc: "Pour parents qui veulent comprendre sans jargon clinique." },
      { type: "Podcast", title: "Émotions", host: "Louie Media (Cyrielle Bedu)", desc: "Épisodes sur tristesse, perte, ado. Format intime, valide les émotions." },
      { type: "Association", title: "Fil Santé Jeunes", url: "https://www.filsantejeunes.com", desc: "0 800 235 236, 9h-23h. Chat anonyme, articles ados-friendly." },
    ],
  },
  moderate: {
    headline: "Dépression modérée, consultation recommandée cette semaine",
    decoding: [
      "Un score entre 10 et 14 atteint le seuil clinique du PHQ-9. C'est le moment où la médecine générale internationale recommande une évaluation par un professionnel. Important à comprendre : « modérée » ne veut pas dire « légère ». C'est le niveau qui touche concrètement les études, le sommeil, les relations, et qui, sans suivi, évolue vers le sévère dans 30 à 50% des cas en 6 mois. C'est aussi le niveau qui répond le mieux au traitement précoce, avec un excellent pronostic.",
      "À ce score, la psychothérapie (TCC en première intention selon les recommandations HAS 2014 mises à jour 2022) suffit dans 60-70% des cas, sans médicament. Le médecin traitant peut prescrire les premières séances (remboursées via Mon Soutien Psy : 12 séances/an, 50€/séance prise en charge à 60% par la Sécu, le reste par la mutuelle). Le piège classique : attendre que « ça passe » et laisser s'installer un épisode qui aurait pu être traité en 2-3 mois.",
    ],
    forces: [
      { t: "Score fiable", d: "Le PHQ-9 a une excellente fiabilité à ce niveau, ce n'est pas un faux positif." },
      { t: "Réversibilité élevée", d: "Avec un suivi adapté, retour à la baseline en 2-4 mois pour la majorité." },
      { t: "Demande implicite", d: "L'ado a accepté de faire le test, marque d'ouverture à parler." },
      { t: "Pas (encore) d'urgence", d: "Sauf item 9 positif, on a le temps d'organiser une prise en charge structurée." },
      { t: "Outils éprouvés", d: "TCC, activation comportementale : protocoles bien standardisés, formateurs nombreux." },
    ],
    vigilances: [
      { t: "Item 9 positif", d: "Si idées de se faire du mal présentes même 1 jour, appel 3114 immédiat." },
      { t: "Décrochage scolaire", d: "L'absentéisme silencieux est le signal d'aggravation le plus fiable." },
      { t: "Isolement total", d: "Plus aucun contact ami choisi = risque de bascule sévère." },
      { t: "Comorbidité anxiété", d: "Si GAD-7 aussi modéré, ne pas négliger, c'est le profil le plus chronicisant." },
      { t: "Auto-médication", d: "Cannabis, alcool, écrans excessifs sont des stratégies d'évitement qui aggravent." },
    ],
    portraits: [
      { n: "L'épuisé invisible", d: "Tient en façade au lycée, s'effondre à la maison. Notes correctes, mais plus aucun plaisir. Souvent en Première ou Terminale." },
      { n: "Le replié post-trauma", d: "Évènement récent (deuil, harcèlement, agression). Symptômes installés depuis 1-3 mois. Risque PTSD associé." },
      { n: "Le chronique négligé", d: "Symptômes présents depuis 6+ mois, mais jamais nommés. Parents en avaient fait « son caractère »." },
    ],
    pistes_parent: [
      { t: "RDV médecin traitant cette semaine", d: "Pas attendre la prochaine visite. Appel ou télémédecine si pas de créneau rapide." },
      { t: "Demander Mon Soutien Psy", d: "Le MT prescrit, l'ado accède à 12 séances/an chez psychologue conventionné. Sans avance de frais possible." },
      { t: "Aménagement scolaire", d: "Lettre du MT au lycée pour assouplir présence, devoirs. Préserver l'engagement scolaire sans pression." },
      { t: "Pas de menace, pas de chantage", d: "« Si tu n'y vas pas, je confisque ton tel » est l'erreur classique. Co-construire le rendez-vous." },
      { t: "Suivi parental aussi", d: "Voir un psy soi-même 1-2 séances pour apprendre la posture juste, ne pas porter seul." },
    ],
    pistes_ado: [
      { t: "Doctolib MT cette semaine", d: "20 min suffisent. Le MT n'est pas là pour juger, il oriente." },
      { t: "Pas attendre que ça passe", d: "À ce niveau, sans aide, 1 chance sur 2 que ça empire en 6 mois. Avec aide, retour normal en 2-4 mois." },
      { t: "1 routine non négociable", d: "Sommeil 22h30-7h, ou 1 sport 2x/semaine, ou 1 repas dehors avec ami. Choisir UN truc à protéger." },
      { t: "Limiter cannabis + alcool", d: "À ce niveau, ils aggravent toujours. Pas de substance, période non négociable." },
      { t: "3114 si idée noire même fugace", d: "Confidentiel, ne déclenche rien d'institutionnel. Juste un humain à l'écoute." },
    ],
    impact_orientation: [
      "Un score modéré non traité impacte Parcoursup directement : choix faits par défaut, sous-estimation de ses capacités, évitement des filières exigeantes par crainte plutôt que par envie réelle. Recommandation : décaler les choix engageants de 6 mois si possible (année de césure, BTS court, alternance) le temps que le traitement fasse effet. Un certificat médical permet de cocher l'aménagement Parcoursup (priorité géographique, prise en compte handicap psychique). Aussi : éviter de choisir une filière « parce qu'il faut bien faire quelque chose » dans cet état, le risque de réorientation est élevé.",
    ],
    ressources: [
      { type: "Livre", title: "La dépression chez l'adolescent", author: "Patrick Delaroche", desc: "Pédopsy reconnu. Pour parents qui veulent comprendre les enjeux développementaux." },
      { type: "Podcast", title: "Quoi de Meuf", host: "Nouvelles Écoutes", desc: "Épisodes sur santé mentale ado, regards féministes, ressources concrètes." },
      { type: "Association", title: "Mon Soutien Psy", url: "https://monsoutienpsy.sante.gouv.fr", desc: "Dispositif officiel : 12 séances/an chez psy conventionné, prescription MT." },
    ],
  },
  moderate_severe: {
    headline: "Dépression modérément sévère, intervention spécialisée urgente",
    decoding: [
      "Un score entre 15 et 19 indique un niveau dépressif qui altère significativement le fonctionnement quotidien. À ce stade, l'évaluation par un pédopsychiatre ou un psychologue clinicien spécialisé adolescents devient nécessaire, pas seulement utile. Les TCC restent efficaces mais peuvent nécessiter d'être combinées à un suivi médicamenteux selon le tableau clinique (notamment si le sommeil est très perturbé ou si l'épisode dure depuis 3+ mois). Le pronostic reste bon avec une prise en charge structurée, mais le retard de traitement est le facteur de chronicisation #1.",
      "Concrètement : l'ado à ce niveau a probablement déjà des conséquences scolaires (chute des notes, absentéisme), sociales (perte d'amis, rupture amoureuse, conflits famille), et physiques (sommeil dégradé, perte ou prise de poids, fatigue chronique). Il peut y avoir des idées noires intermittentes, même sans plan d'acte. La parole « je ne sers à rien » ou « tout serait plus simple si je n'étais pas là » doit toujours être prise au sérieux, jamais minimisée.",
    ],
    forces: [
      { t: "Cadre de soins clair", d: "À ce niveau, les recommandations (HAS, AAP) sont nettes : pédopsychiatrie ou psy clinicien." },
      { t: "Dispositifs publics actifs", d: "CMP, CMPP, hôpital de jour ado, MDA : maillage français existe, accès gratuit." },
      { t: "Réponse au traitement", d: "70-80% rémission à 6 mois avec TCC + suivi régulier, médicament si besoin." },
      { t: "Famille mobilisable", d: "Vous avez fait faire le test = votre rôle de filet de sécurité fonctionne." },
      { t: "Réseau d'urgence accessible", d: "3114, urgences pédopsy 15, Fil Santé Jeunes : ressources 24/7." },
    ],
    vigilances: [
      { t: "Risque suicidaire à explorer", d: "Demander explicitement à l'ado s'il pense à se faire du mal. Question non taboue, recommandée." },
      { t: "Auto-mutilation discrète", d: "Vérifier bras, cuisses. Cicatrices fines, brûlures de cigarette = consulter ce jour." },
      { t: "Abandon scolaire imminent", d: "Si déjà 2 semaines d'absence, alerter assistante sociale du lycée pour cadre soutien." },
      { t: "Substances psychoactives", d: "Cannabis quotidien, alcoolisations massives : facteur aggravant majeur." },
      { t: "Isolement total écran", d: "Si seule interaction = jeux vidéo en ligne, signal de désengagement." },
    ],
    portraits: [
      { n: "L'effondrement Terminale", d: "Performances chute brutalement après tenue de façade. Souvent autour des bulletins du 1er ou 2e trimestre." },
      { n: "Le post-harcèlement", d: "Harcèlement scolaire ou cyber sur 6+ mois. Repli, anxiété sociale massive, méfiance généralisée." },
      { n: "L'épisode majeur familial", d: "Divorce conflictuel, deuil, maladie parent. Pas de soutien adulte stable au quotidien." },
    ],
    pistes_parent: [
      { t: "Pédopsy ou psy clinicien sous 7 jours", d: "Si liste d'attente longue, demander au MT une consultation en urgence. CMP = gratuit." },
      { t: "Lettre au lycée formelle", d: "Médecin scolaire, CPE : demander un PAI (Projet d'Accueil Individualisé)." },
      { t: "Sécuriser le domicile", d: "Médicaments hors de portée, armes (si présentes) verrouillées, alcool fermé." },
      { t: "Ne pas rester seul(e) parent", d: "Voir un psy pour vous, ou groupe parents (UNAFAM, Espace Parents)." },
      { t: "Plan en cas d'aggravation", d: "Discuter avec l'ado, par écrit, quoi faire si crise (qui appeler, où aller)." },
    ],
    pistes_ado: [
      { t: "Tu peux dire non aux séances", d: "Mais teste 3 psy différents avant de conclure que ça ne marche pas. Le « match » thérapeute est crucial." },
      { t: "Le 3114 n'est pas que pour le pire", d: "Tu peux appeler pour parler, même sans projet d'acte. C'est fait pour ça." },
      { t: "Maintenir 1 activité hors maison", d: "Sport, asso, job d'été : 1 contexte non-école où tu existes autrement." },
      { t: "Cannabis quotidien = stop net", d: "À ce niveau, c'est un aggravateur connu. En parler au médecin sans honte." },
      { t: "Si idée d'acte, demander à un adulte de ne pas te laisser seul ce soir", d: "Pas une faiblesse, une stratégie qui marche. Présence humaine = protection." },
    ],
    impact_orientation: [
      "À ce score, reporter Parcoursup d'un an est souvent la meilleure décision. Une année de césure (formalisée via le portail Parcoursup) permet de soigner sans pression supplémentaire, puis de choisir en pleine capacité. Alternative : commencer une formation courte et concrète (BTS, BUT en alternance) qui apporte structure, revenu, et possibilité d'arrêt sans grand impact. Éviter les filières où la décompensation a un coût social fort (prépa, médecine, écoles d'art exigeantes). Le médecin peut faire un certificat pour reconnaissance handicap psychique transitoire à la MDPH, qui ouvre des droits Parcoursup spécifiques.",
    ],
    ressources: [
      { type: "Livre", title: "Mon ado, ma bataille", author: "Stéphanie Hahusseau", desc: "Psychiatre. Pour parents en première ligne d'une crise dépressive ado." },
      { type: "Podcast", title: "InPower par Louise Aubery", host: "Louise Aubery", desc: "Épisode dépression jeune adulte. Témoignages et stratégies de remontée." },
      { type: "Association", title: "Maison des Adolescents (MDA)", url: "https://anmda.fr", desc: "Lieu d'écoute multidisciplinaire dans chaque département. Gratuit, sans rdv, ado et famille." },
    ],
  },
  severe: {
    headline: "Dépression sévère, prise en charge cette semaine, urgence si besoin",
    decoding: [
      "Un score de 20 ou plus correspond à une dépression sévère. À ce stade, le risque d'idées suicidaires et de passage à l'acte est significativement élevé (jusqu'à 30% de tentatives dans l'année sans prise en charge selon Kennard 2009). La prise en charge doit être pédopsychiatrique, parfois hospitalière de jour, parfois avec traitement médicamenteux. Le bon réflexe : ne pas attendre un rendez-vous classique, passer par les urgences pédopsy ou le CMP en demande de consultation rapide.",
      "Important pour les parents : ce n'est ni votre faute, ni le caractère de votre ado. C'est une maladie qui se soigne, comme un diabète ou une fracture. Le traitement efficace existe et a un excellent pronostic à 6-12 mois (rémission complète pour la majorité), mais le délai d'accès au soin est le facteur pronostique #1. Chaque semaine sans suivi double quasi-mécaniquement le risque de chronicisation.",
    ],
    forces: [
      { t: "Cadre clair, ressources accessibles", d: "À ce niveau, le système de soin sait quoi faire. Pédopsy, CMP, hospitalisation jour." },
      { t: "Traitements efficaces", d: "TCC + ISRS combinés : 80% de rémission à 12 mois (étude TADS 2007)." },
      { t: "Réseau de soutien activable", d: "Vous, la famille élargie, le lycée, le médecin : tous peuvent s'organiser." },
      { t: "Acte de soin = acte d'amour", d: "Aller au rdv malgré la résistance de l'ado est la bonne décision long-terme." },
      { t: "Réversibilité quasi-totale", d: "Avec traitement, retour à une vie normale dans la grande majorité des cas." },
    ],
    vigilances: [
      { t: "Risque suicidaire élevé", d: "Item 9 ≥ 1 ou parole « je veux mourir » : passer aux urgences pédopsy ce jour." },
      { t: "Auto-mutilation active", d: "Coupures récentes visibles : consulter en urgence, ne pas attendre." },
      { t: "Pas de manger / ne dort plus", d: "Désorganisation physique majeure = hospitalisation jour à envisager." },
      { t: "Délire ou hallucinations", d: "Dépression sévère avec symptômes psychotiques = pédopsy en urgence." },
      { t: "Abandon total scolaire ET social", d: "Rester en chambre 7j/7 + plus aucune sortie : signal de gravité majeure." },
    ],
    portraits: [
      { n: "L'effondrement total", d: "Ne sort plus de la chambre. Mange mal. Dort mal. Pleure souvent. Souvent post-événement majeur." },
      { n: "Le silencieux à risque", d: "Pas démonstratif, mais score sévère au PHQ-9 et idées noires confirmées. Le profil le plus dangereux car invisible." },
      { n: "Le post-tentative", d: "A déjà fait une tentative ou avoue avoir tenté seul. Risque récidive très élevé les 6 mois suivants." },
    ],
    pistes_parent: [
      { t: "Pédopsy ou urgences ce jour", d: "Pas demain. CMP en demande urgente, ou urgences pédopsy d'un CHU. Médecin traitant peut faire un courrier." },
      { t: "Présence physique cette semaine", d: "Pas seul(e) à la maison plus de 2h. Reprogrammer agenda parents si besoin." },
      { t: "Sécuriser absolument", d: "Médicaments, armes, cordes, ceintures : tout hors d'accès. Sans dramatiser mais sans négocier." },
      { t: "Pas de jugement, pas de pression", d: "« On va traverser ça ensemble » plutôt que « secoue-toi ». L'effort moral est impossible à ce niveau." },
      { t: "Soutien parental indispensable", d: "Voir psy soi-même cette semaine, parler à 1 ami de confiance. La charge est immense, vous n'êtes pas obligé(e) de la porter seul(e)." },
    ],
    pistes_ado: [
      { t: "Tu n'es pas faible, tu es malade", d: "La dépression sévère est une maladie. Comme une grippe, sauf qu'elle touche le cerveau. Elle se soigne." },
      { t: "Tiens jusqu'au rdv", d: "Un jour à la fois. Si trop dur dans la nuit : 3114, gratuit, anonyme, immédiat." },
      { t: "Tu n'es pas seul(e)", d: "1 ado sur 8 traverse ce que tu traverses. La majorité s'en sort complètement avec aide." },
      { t: "Accepte 1 personne près de toi cette semaine", d: "Un parent, un ami, un proche : pas seul plus de quelques heures." },
      { t: "Si tu sens que ce soir ne passera pas, dis-le", d: "Aux parents, au 3114, à un ami. Demander = protéger ta vie. Pas de honte, jamais." },
    ],
    impact_orientation: [
      "À ce score, suspendre Parcoursup est légitime et recommandé. Aucune filière ne mérite que la santé soit sacrifiée. Année de césure formalisée, retour à la formation l'année suivante en pleine capacité. Si la scolarité actuelle est trop lourde, le médecin peut prescrire un aménagement (cours à domicile via CNED réglementé, hospitalisation jour avec scolarité intégrée, redoublement en lycée plus calme). La reconnaissance handicap psychique transitoire (MDPH) ouvre des droits durables sans stigmate pérenne. Priorité absolue : soin. L'orientation suit, jamais l'inverse.",
    ],
    ressources: [
      { type: "Livre", title: "L'enfer du dimanche soir, sortir de la dépression", author: "Christophe André", desc: "Psychiatre. Pour ado et parent en parallèle. Bienveillant, validant, concret." },
      { type: "Podcast", title: "Métamorphose, Anne Ghesquière", host: "Anne Ghesquière", desc: "Épisodes spécifiques dépression sévère, témoignages de rémission, espoir factuel." },
      { type: "Numéro vital", title: "3114, prévention du suicide", url: "https://3114.fr", desc: "Gratuit, anonyme, 24h/24. Pas que pour les urgences absolues. Pour parler maintenant." },
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
          {rich.decoding.map((p, i) => (
            <p key={i} style={{ fontSize: 15, lineHeight: 1.65, color: "var(--c-ink-2)", marginBottom: i < rich.decoding.length - 1 ? 12 : 0 }}>{p}</p>
          ))}
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18, marginBottom: 18 }}>
          <div style={card}>
            <h3 style={h3style}>Forces typiques · 5</h3>
            <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: 10 }}>
              {rich.forces.map((f, i) => (
                <li key={i} style={{ fontSize: 13.5, lineHeight: 1.55 }}>
                  <strong style={{ color: "var(--c-ink)" }}>{f.t}.</strong> <span style={{ color: "var(--c-muted)" }}>{f.d}</span>
                </li>
              ))}
            </ul>
          </div>
          <div style={card}>
            <h3 style={{ ...h3style, color: "#C62828" }}>Points de vigilance · 5</h3>
            <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: 10 }}>
              {rich.vigilances.map((v, i) => (
                <li key={i} style={{ fontSize: 13.5, lineHeight: 1.55 }}>
                  <strong style={{ color: "var(--c-ink)" }}>{v.t}.</strong> <span style={{ color: "var(--c-muted)" }}>{v.d}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
        <div style={{ ...card, marginBottom: 18 }}>
          <h3 style={h3style}>3 profils typiques à ce niveau</h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14 }}>
            {rich.portraits.map((p, i) => (
              <div key={i} style={{ background: accentSoft, borderRadius: 12, padding: 14 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: accent, marginBottom: 6 }}>{p.n}</div>
                <p style={{ fontSize: 13, lineHeight: 1.5, color: "var(--c-ink-2)", margin: 0 }}>{p.d}</p>
              </div>
            ))}
          </div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18, marginBottom: 18 }}>
          <div style={card}>
            <h3 style={h3style}>Côté parent · 5 actions</h3>
            <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: 10 }}>
              {rich.pistes_parent.map((p, i) => (
                <li key={i} style={{ fontSize: 13.5, lineHeight: 1.55 }}>
                  <strong style={{ color: "var(--c-ink)" }}>{p.t}.</strong> <span style={{ color: "var(--c-muted)" }}>{p.d}</span>
                </li>
              ))}
            </ul>
          </div>
          <div style={card}>
            <h3 style={h3style}>Côté ado · 5 actions</h3>
            <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: 10 }}>
              {rich.pistes_ado.map((p, i) => (
                <li key={i} style={{ fontSize: 13.5, lineHeight: 1.55 }}>
                  <strong style={{ color: "var(--c-ink)" }}>{p.t}.</strong> <span style={{ color: "var(--c-muted)" }}>{p.d}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
        <div style={{ ...card, marginBottom: 18 }}>
          <h3 style={h3style}>Impact sur l'orientation</h3>
          {rich.impact_orientation.map((p, i) => (
            <p key={i} style={{ fontSize: 15, lineHeight: 1.65, color: "var(--c-ink-2)", marginBottom: i < rich.impact_orientation.length - 1 ? 12 : 0 }}>{p}</p>
          ))}
        </div>
        <div style={card}>
          <h3 style={h3style}>Ressources à explorer · 3</h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14 }}>
            {rich.ressources.map((r, i) => (
              <div key={i} style={{ background: accentSoft, borderRadius: 12, padding: 14 }}>
                <div style={{ fontSize: 10.5, fontWeight: 800, color: accent, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 6 }}>{r.type}</div>
                <div style={{ fontSize: 14, fontWeight: 700, color: "var(--c-ink)", marginBottom: 4 }}>{r.title}</div>
                {r.author && <div style={{ fontSize: 12, color: "var(--c-muted)", marginBottom: 6 }}>{r.author}</div>}
                {r.host && <div style={{ fontSize: 12, color: "var(--c-muted)", marginBottom: 6 }}>{r.host}</div>}
                <p style={{ fontSize: 12.5, lineHeight: 1.5, color: "var(--c-ink-2)", margin: "0 0 8px" }}>{r.desc}</p>
                {r.url && <a href={r.url} target="_blank" rel="noopener noreferrer" style={{ fontSize: 12, fontWeight: 600, color: accent, textDecoration: "none" }}>Ouvrir →</a>}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

const Results = ({ results, onRestart }) => {
  const { phqScore, level, levelLabel, consultFlag, safetyAlert } = results;
  const copy = LEVEL_COPY[level];
  return (
    <section style={{ paddingTop: 60, paddingBottom: 100 }}>
      <div className="shell" style={{ maxWidth: 820 }}>
        {safetyAlert && <SafetyAlert />}
        <DisclaimerBanner />
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <span className="chip" style={{ background: "rgba(34,160,107,.15)", color: "#22A06B" }}>
            <Icon.check /> Test terminé · 9 réponses analysées
          </span>
          <h1 style={{ marginTop: 18, fontSize: 36 }}>
            Symptômes <span style={{ background: "linear-gradient(180deg, transparent 60%, " + copy.color + "55 60%)", paddingInline: 8 }}>{levelLabel.toLowerCase()}</span>
          </h1>
        </div>

        <div style={{
          background: consultFlag ? "linear-gradient(160deg, " + copy.color + ", #C62828)" : "linear-gradient(160deg, #5C6BC0, #B0B7E0)",
          color: "white", borderRadius: 24, padding: "32px 28px", marginBottom: 24, textAlign: "center",
        }}>
          <div style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", opacity: 0.85, marginBottom: 8 }}>Score PHQ-9</div>
          <div style={{ fontFamily: "var(--font-display)", fontSize: 80, fontWeight: 700, lineHeight: 1, marginBottom: 12 }}>{phqScore} / 27</div>
          <div style={{ maxWidth: 420, margin: "0 auto 10px" }}>
            <div style={{ position: "relative", height: 8, borderRadius: 4, background: "linear-gradient(90deg,#22A06B,#8BC34A,#FFC107,#FB8C00,#C62828)" }}>
              <div style={{ position: "absolute", top: "50%", left: `${Math.min(100, (phqScore/27)*100)}%`, width: 14, height: 14, borderRadius: "50%", background: "white", border: "2px solid #0A0E2C", transform: "translate(-50%,-50%)", boxShadow: "0 1px 4px rgba(0,0,0,.3)" }} />
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, opacity: 0.92, marginTop: 6 }}>
              <span>0 · aucun symptôme</span><span>27 · sévère</span>
            </div>
          </div>
          <div style={{ fontSize: 13.5, opacity: 0.95, marginBottom: 12 }}>
            Plus le score est bas, moins il y a de signaux dépressifs. Ici : <strong>{levelLabel.toLowerCase()}</strong>.
          </div>
          <div style={{ fontSize: 12.5, opacity: 0.82, marginBottom: 16 }}>
            Seuils : ≤4 minimal · 5-9 léger · 10-14 modéré · 15-19 modérément sévère · ≥20 sévère
          </div>
          <p style={{ fontSize: 15, maxWidth: 540, margin: "0 auto", lineHeight: 1.55 }}>{copy.body}</p>
        </div>

        <div style={{ background: "#0A0E2C", color: "white", borderRadius: 20, padding: "32px 28px", marginBottom: 24 }}>
          <h2 style={{ color: "white", fontSize: 22, marginBottom: 14 }}>🩺 Action recommandée</h2>
          <p style={{ fontSize: 15, opacity: 0.92, lineHeight: 1.6, marginBottom: 18 }}>{copy.action}</p>
          <ul style={{ paddingLeft: 22, marginBottom: 18, opacity: 0.92, lineHeight: 1.8, fontSize: 14.5 }}>
            <li><strong>Médecin traitant</strong>, premier interlocuteur, peut orienter et prescrire</li>
            <li><strong>Psychologue</strong>, TCC efficace en première intention sur l'épisode dépressif léger à modéré</li>
            <li><strong>Pédopsychiatre</strong>, indispensable pour la dépression modérément sévère à sévère</li>
            <li><strong>CMP / CMPP</strong>, consultations gratuites pour ado, délai variable selon département</li>
            <li><strong>Fil Santé Jeunes</strong>, 0800 235 236, gratuit, anonyme, 7j/7</li>
          </ul>
          <a href="https://calendly.com/proxxie/entretien" target="_blank" rel="noopener noreferrer" className="btn btn-orange">
            30 min avec Charles pour orienter la démarche
          </a>
        </div>

        <div style={{ background: "var(--c-cream-light)", borderRadius: 20, padding: 24, border: "1px solid var(--c-line)" }}>
          <h3 style={{ fontSize: 16, marginBottom: 10 }}>📍 La dépression à l'ado est rarement isolée</h3>
          <p style={{ fontSize: 13.5, color: "var(--c-muted)", lineHeight: 1.55, marginBottom: 14 }}>
            Souvent intriquée avec l'anxiété (GAD-7), un TDAH non détecté, ou la pression scolaire (Parcoursup). Les tests complémentaires aident à cartographier.
          </p>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <a href="Proxxie Test Anxiete.html" style={{ background: "white", padding: "10px 14px", borderRadius: 99, fontSize: 13, fontWeight: 600, color: "#487AFF", border: "1px solid var(--c-line)", textDecoration: "none" }}>Anxiété (GAD-7)</a>
            <a href="Proxxie Test TDAH.html" style={{ background: "white", padding: "10px 14px", borderRadius: 99, fontSize: 13, fontWeight: 600, color: "#FD6936", border: "1px solid var(--c-line)", textDecoration: "none" }}>TDAH</a>
            <a href="Proxxie Test.html" style={{ background: "white", padding: "10px 14px", borderRadius: 99, fontSize: 13, fontWeight: 600, color: "#1320CE", border: "1px solid var(--c-line)", textDecoration: "none" }}>OCEAN-X (personnalité)</a>
            <a href="Proxxie Test HPI.html" style={{ background: "white", padding: "10px 14px", borderRadius: 99, fontSize: 13, fontWeight: 600, color: "#22A06B", border: "1px solid var(--c-line)", textDecoration: "none" }}>HPI</a>
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
  const gap = Math.abs(pR.phqScore - tR.phqScore);
  return (
    <div style={{ marginBottom: 40 }}>
      {tR.safetyAlert && <SafetyAlert />}
      <DisclaimerBanner />
      <div style={{ background: "linear-gradient(160deg, #5C6BC0, #3949AB)", color: "white", borderRadius: 24, padding: "32px 28px", marginBottom: 24, textAlign: "center" }}>
        <div style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", opacity: 0.85, marginBottom: 8 }}>Comparaison · PHQ-9</div>
        <div style={{ display: "flex", justifyContent: "center", gap: 40, fontFamily: "var(--font-display)", fontSize: 56 }}>
          <div>
            <div style={{ fontSize: 11, opacity: 0.8, fontFamily: "inherit", marginBottom: 4 }}>{peerLabel || "L'autre"}</div>
            <div>{pR.phqScore} / 27</div>
            <div style={{ fontSize: 13, opacity: 0.85, marginTop: 4 }}>{pR.levelLabel}</div>
          </div>
          <div style={{ opacity: 0.6, fontSize: 36 }}>→</div>
          <div>
            <div style={{ fontSize: 11, opacity: 0.8, fontFamily: "inherit", marginBottom: 4 }}>{selfLabel || "Toi"}</div>
            <div>{tR.phqScore} / 27</div>
            <div style={{ fontSize: 13, opacity: 0.85, marginTop: 4 }}>{tR.levelLabel}</div>
          </div>
        </div>
        <p style={{ marginTop: 16, opacity: 0.92, fontSize: 15, maxWidth: 520, marginInline: "auto" }}>
          {gap >= 6
            ? "Écart significatif. Vos deux vécus de la dépression diffèrent nettement. Sujet de conversation important."
            : gap >= 3
              ? "Écart modéré. À discuter ensemble pour comprendre."
              : "Vécus alignés."}
        </p>
      </div>
    </div>
  );
};

const buildEmailSummary = (results) => {
  return "Test Dépression (PHQ-9 Kroenke 2001)\nScore PHQ-9 : " + results.phqScore + "/27, " + results.levelLabel + "\n" + (results.consultFlag ? "Consultation recommandée." : "Niveau sous le seuil clinique modéré.") + (results.safetyAlert ? "\n⚠️ Item 9 positif, 3114 affiché en haut du résultat." : "");
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
    var testType = window.__proxxie_test_type || 'phq9';
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
        test_type: window.__proxxie_test_type || 'phq9',
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
      {mode === "picker" && <PersonaIntro testName="Dépression" accent="#5C6BC0" comingFromPredict={null} onPick={pickPersona} />}
      {mode === "compare-intro" && <PersonaIntro testName="Dépression" accent="#5C6BC0" comingFromPredict={PARENT_PREDICT} onPick={pickPersona} />}
      {mode === "test" && (
        <>
          {persona === "predict" && (<div style={{ background: "#F5EB3F", color: "#0A0E2C", padding: "10px 16px", textAlign: "center", fontSize: 13, fontWeight: 600 }}>🎯 Mode prédiction · Répondez comme vous pensez que votre ado répondrait</div>)}
          <TestFlowEngine questions={QUESTIONS} storageKey={storageKeyEffective} getTypeMeta={getTypeMeta} onExit={exitTest} onComplete={onComplete} />
        </>
      )}
      {mode === "results" && results && (
        <>
          {effectivePersona === "self_compare" && PARENT_PREDICT && (<section style={{ paddingTop: 40, paddingBottom: 0 }}><div className="shell" style={{ maxWidth: 820 }}><ComparePanel peerLabel={PARENT_PREDICT.peerLabel} selfLabel={PARENT_PREDICT.selfLabel} parentAnswers={PARENT_PREDICT.a} teenAnswers={answers} /></div></section>)}
          {persona === "predict" && (<section style={{ paddingTop: 40, paddingBottom: 0 }}><div className="shell" style={{ maxWidth: 820 }}><ShareLinkPanel testCode="PHQ9" accent="#5C6BC0" answers={answers} defaultName="" onSkip={() => {}} /></div></section>)}
          <EmailResultsActions testCode="PHQ9" testName="Dépression (PHQ-9)" accent="#5C6BC0" summary={buildEmailSummary(results)} answers={answers} />
          <Results results={results} onRestart={restart} />
          <RichAnalysisSection rich={RICH_RESULTS[results.level]} accent="#5C6BC0" accentSoft="rgba(92,107,192,0.12)" />
        </>
      )}
      <Footer />
    </>
  );
};

ReactDOM.createRoot(document.getElementById("root")).render(<TestApp />);
'''


def build_phq9(source_path: pathlib.Path, target_path: pathlib.Path) -> str:
    if not source_path.exists():
        return f"SOURCE manquant : {source_path.name}"
    # 1. Copie complète Anxiete → PHQ9
    shutil.copy(source_path, target_path)
    html = target_path.read_text(encoding="utf-8")

    # 2. Localise l'asset 61feca88 du manifest et décode
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

    # 3. Remplace TEST_ID
    src = re.sub(
        r'const __PROXXIE_TEST_ID__\s*=\s*"[^"]*";',
        'const __PROXXIE_TEST_ID__ = "phq9";',
        src, count=1
    )

    # 4. Swap la section test-spécifique (de `const QUESTIONS` jusqu'à la fin)
    boundary_match = re.search(r'(/\*\s*Test Proxxie Anxi[^/]*\*/\s*\n)?const QUESTIONS\s*=', src)
    if not boundary_match:
        return f"{target_path.name}: boundary `const QUESTIONS` introuvable"
    new_src = _bridge_common.patch_persona_intro(src[:boundary_match.start()]) + PHQ9_BLOCK

    # 5. Re-encode
    nd = new_src.encode('utf-8')
    if comp:
        nd = gzip.compress(nd)
    entry['data'] = base64.b64encode(nd).decode('ascii')
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]

    # 6. Remplace les <title> à 2 endroits :
    #    a) le <title> statique dans le <head> (visible avant que JS s'exécute)
    #    b) le <title> à l'intérieur du template bundler (JSON-escaped, c'est lui
    #       qui prend le pas dès que le bundler unpack et remplace le document)
    new_html = re.sub(
        r'<title[^>]*>[^<]*</title>',
        '<title>Test Dépression PHQ-9, Proxxie</title>',
        new_html, count=1
    )
    # Dans le template JSON, le slash de fermeture est échappé : <\/title>
    new_html = re.sub(
        r'<title[^>]*>[^<]*<\\/title>',
        '<title>Test Dépression PHQ-9, Proxxie<\\/title>',
        new_html, count=1
    )

    target_path.write_text(new_html, encoding='utf-8')
    return f"{target_path.name}: built from {source_path.name} (asset {uuid[:8]}, src {len(src)} → {len(new_src)})"


if __name__ == "__main__":
    print(build_phq9(SOURCE, TARGET))
    print(build_phq9(SOURCE, TARGET_LOWER))

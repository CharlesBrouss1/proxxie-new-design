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
          <div style={{ fontFamily: "var(--font-display)", fontSize: 80, fontWeight: 700, lineHeight: 1, marginBottom: 8 }}>{phqScore} / 27</div>
          <div style={{ fontSize: 14, opacity: 0.92, marginBottom: 16 }}>
            <strong>{levelLabel}</strong> · seuils : ≤4 minimal · 5-9 léger · 10-14 modéré · 15-19 modérément sévère · ≥20 sévère
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

const ComparePanel = ({ parentName, parentAnswers, teenAnswers }) => {
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
            <div style={{ fontSize: 11, opacity: 0.8, fontFamily: "inherit", marginBottom: 4 }}>{parentName || "Parent"} pensait</div>
            <div>{pR.phqScore} / 27</div>
            <div style={{ fontSize: 13, opacity: 0.85, marginTop: 4 }}>{pR.levelLabel}</div>
          </div>
          <div style={{ opacity: 0.6, fontSize: 36 }}>→</div>
          <div>
            <div style={{ fontSize: 11, opacity: 0.8, fontFamily: "inherit", marginBottom: 4 }}>Réel</div>
            <div>{tR.phqScore} / 27</div>
            <div style={{ fontSize: 13, opacity: 0.85, marginTop: 4 }}>{tR.levelLabel}</div>
          </div>
        </div>
        <p style={{ marginTop: 16, opacity: 0.92, fontSize: 15, maxWidth: 520, marginInline: "auto" }}>
          {gap >= 6
            ? "Écart significatif. Votre ado ressent la dépression très différemment de ce que vous pensiez. Sujet de conversation prioritaire."
            : gap >= 3
              ? "Écart modéré. À discuter ensemble pour comprendre."
              : "Perception alignée avec son vécu."}
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
          {effectivePersona === "self_compare" && PARENT_PREDICT && (<section style={{ paddingTop: 40, paddingBottom: 0 }}><div className="shell" style={{ maxWidth: 820 }}><ComparePanel parentName={PARENT_PREDICT.n} parentAnswers={PARENT_PREDICT.a} teenAnswers={answers} /></div></section>)}
          {persona === "predict" && (<section style={{ paddingTop: 40, paddingBottom: 0 }}><div className="shell" style={{ maxWidth: 820 }}><ShareLinkPanel testCode="PHQ9" accent="#5C6BC0" answers={answers} defaultName="" onSkip={() => {}} /></div></section>)}
          <EmailResultsActions testCode="PHQ9" testName="Dépression (PHQ-9)" accent="#5C6BC0" summary={buildEmailSummary(results)} answers={answers} />
          <Results results={results} onRestart={restart} />
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
    new_src = src[:boundary_match.start()] + PHQ9_BLOCK

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

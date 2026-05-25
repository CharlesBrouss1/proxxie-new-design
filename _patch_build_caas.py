#!/usr/bin/env python3
"""Construit Proxxie Test CAAS.html depuis Proxxie Test Anxiete.html.

Pattern identique à _patch_build_phq9.py / _patch_build_grit.py.

Source psychométrique : Career Adapt-Abilities Scale (Savickas & Porfeli, 2012).
24 items, 4 sous-échelles de 6 items chacune (Concern, Control, Curiosity, Confidence).
Likert 1-5 (pas du tout fort → extrêmement fort). Validé dans 18 pays.

Pas un screening clinique, pas de disclaimer médical.
"""
import re, json, base64, gzip, pathlib, shutil

REPO = pathlib.Path(__file__).parent
SOURCE = REPO / "Proxxie Test Anxiete.html"
TARGET = REPO / "Proxxie Test CAAS.html"
TARGET_LOWER = REPO / "test-caas.html"
ASSET_UUID_PREFIX = "61feca88"

CAAS_BLOCK = r'''/* Test Proxxie CAAS, adaptabilité carrière (Savickas & Porfeli 2012)
   Échelle de psychologie du travail, validée dans 18 pays.
   4 sous-échelles : Concern, Control, Curiosity, Confidence. */

const QUESTIONS = [
  // CONCERN (6 items) · Préoccupation pour le futur
  { type: "CONCERN", q: "Penser à ce à quoi ressemblera mon futur." },
  { type: "CONCERN", q: "Réaliser que les choix d'aujourd'hui construisent mon avenir." },
  { type: "CONCERN", q: "Me préparer pour le futur." },
  { type: "CONCERN", q: "Prendre conscience des choix éducatifs et professionnels à faire." },
  { type: "CONCERN", q: "Planifier comment atteindre mes objectifs." },
  { type: "CONCERN", q: "Me soucier de ma future carrière." },
  // CONTROL (6 items) · Capacité de décision
  { type: "CONTROL", q: "Être responsable de mes propres choix." },
  { type: "CONTROL", q: "Compter sur moi-même." },
  { type: "CONTROL", q: "Décider par moi-même." },
  { type: "CONTROL", q: "Tenir mes engagements." },
  { type: "CONTROL", q: "Faire ce qui est juste pour moi." },
  { type: "CONTROL", q: "Faire les choses moi-même." },
  // CURIOSITY (6 items) · Exploration
  { type: "CURIOSITY", q: "Explorer ce qui m'entoure." },
  { type: "CURIOSITY", q: "Chercher des opportunités de progression personnelle." },
  { type: "CURIOSITY", q: "Explorer les différentes façons de faire les choses." },
  { type: "CURIOSITY", q: "Approfondir les questions qui me semblent importantes." },
  { type: "CURIOSITY", q: "Devenir curieux(se) de nouvelles opportunités." },
  { type: "CURIOSITY", q: "Étudier les différents rôles que je pourrais jouer." },
  // CONFIDENCE (6 items) · Confiance
  { type: "CONFIDENCE", q: "Accomplir des tâches efficacement." },
  { type: "CONFIDENCE", q: "Prendre soin de bien faire les choses." },
  { type: "CONFIDENCE", q: "Apprendre de nouvelles compétences." },
  { type: "CONFIDENCE", q: "Travailler à la hauteur de mes capacités." },
  { type: "CONFIDENCE", q: "Surmonter les obstacles." },
  { type: "CONFIDENCE", q: "Résoudre des problèmes." },
];

const TYPE_META = {
  CONCERN:    { l: "Concern · Anticiper",  c: "#00897B", short: "Préoccupation pour le futur" },
  CONTROL:    { l: "Control · Décider",    c: "#00695C", short: "Autonomie, responsabilité" },
  CURIOSITY:  { l: "Curiosity · Explorer", c: "#00ACC1", short: "Curiosité, exploration" },
  CONFIDENCE: { l: "Confidence · Oser",    c: "#0097A7", short: "Confiance, résolution" },
};
const STORAGE_KEY = "proxxie-caas-answers";

const getTypeMeta = (q) => ({ label: TYPE_META[q.type].l, color: TYPE_META[q.type].c });

const computeResults = (answers) => {
  const dims = { CONCERN: 0, CONTROL: 0, CURIOSITY: 0, CONFIDENCE: 0 };
  const counts = { CONCERN: 0, CONTROL: 0, CURIOSITY: 0, CONFIDENCE: 0 };
  QUESTIONS.forEach((q, idx) => {
    if (answers[idx] == null) return;
    dims[q.type] += answers[idx];
    counts[q.type]++;
  });
  const avgs = {};
  for (const k of Object.keys(dims)) {
    avgs[k] = counts[k] > 0 ? Math.round((dims[k] / counts[k]) * 100) / 100 : 0;
  }
  const total = Math.round(((avgs.CONCERN + avgs.CONTROL + avgs.CURIOSITY + avgs.CONFIDENCE) / 4) * 100) / 100;
  let level = "faible";
  if (total >= 4.0) level = "très fort";
  else if (total >= 3.5) level = "fort";
  else if (total >= 2.5) level = "moyen";
  const sortedAsc = Object.entries(avgs).sort((a, b) => a[1] - b[1]);
  const weakest = sortedAsc[0][0];
  const strongest = sortedAsc[sortedAsc.length - 1][0];
  const archetypes = {
    CONCERN: "L'Anticipateur · vous voyez loin et préparez les coups",
    CONTROL: "Le Stratège · vous décidez et tenez votre cap",
    CURIOSITY: "L'Explorateur · vous découvrez et apprenez sans cesse",
    CONFIDENCE: "L'Audacieux · vous osez et trouvez des solutions",
  };
  return { avgs, total, level, weakest, strongest, archetype: archetypes[strongest] };
};

const DIMENSION_ADVICE = {
  CONCERN: ["Écrire en 1 page sa vie idéale dans 5 ans (lieu, métier, rythme, entourage). Relire 1 fois par mois.", "Lister 3 décisions actuelles qui auront un impact dans 5 ans. Les classer par importance.", "Visiter un salon métiers (ou 3 vidéos métiers/semaine sur YouTube) pour ancrer le futur dans le concret."],
  CONTROL: ["Prendre 3 décisions par semaine sans demander l'avis des parents (même petites : activité, achat, planning).", "Tenir un journal de décisions : ce que j'ai décidé, sur quoi, le résultat. Bilan mensuel.", "Refuser une demande des parents 1 fois/semaine avec une vraie justification."],
  CURIOSITY: ["Interviewer 3 adultes/trimestre dans des métiers très différents (15 min, 5 questions).", "Tester 1 activité totalement nouvelle par mois (sport, art, langue, code, bénévolat).", "S'abonner à 3 podcasts ou newsletters sur des univers professionnels variés."],
  CONFIDENCE: ["Lister chaque dimanche 3 choses difficiles réussies dans la semaine. Le cerveau retient les échecs, contre-balancer.", "S'engager dans 1 projet 'légèrement trop ambitieux' par trimestre (concours, projet, présentation).", "Identifier 1 mentor (prof, voisin, parent d'ami) qui croit en vous et demander un retour franc tous les 2 mois."],
};

const DisclaimerBanner = () => (
  <div style={{
    background: "#E0F2F1", borderLeft: "4px solid #00897B",
    padding: "14px 20px", marginBottom: 30, borderRadius: 8,
    fontSize: 13.5, color: "#0A0E2C", lineHeight: 1.55,
  }}>
    <strong>ℹ️ L'adaptabilité se travaille à tout âge.</strong> Le CAAS (Savickas & Porfeli, 2012) mesure 4 capacités d'adaptation carrière. Un score faible aujourd'hui n'est pas un verdict, ces capacités se développent avec des exercices structurés sur 3 mois.
  </div>
);

const TestHero = ({ onStart }) => (
  <section style={{ paddingTop: 70, paddingBottom: 80, position: "relative", overflow: "hidden" }}>
    <Pill color="rgba(245,235,63,.5)" w={260} h={130} style={{ position: "absolute", top: 110, right: -60, borderRadius: 999 }} />
    <Half color="rgba(0,137,123,.18)" side="t" w={300} h={120} style={{ position: "absolute", bottom: -10, left: -40 }} />
    <div className="shell" style={{ position: "relative", display: "grid", gridTemplateColumns: "1.1fr 1fr", gap: 60, alignItems: "center" }}>
      <div>
        <span className="chip" style={{ background: "rgba(0,137,123,.15)", color: "#00897B" }}>
          <Icon.spark style={{ width: 14, height: 14 }} /> Futur du travail · Savickas
        </span>
        <h1 style={{ marginTop: 22, marginBottom: 22 }}>
          Test <span style={{ background: "linear-gradient(180deg, transparent 60%, #F5EB3F 60%)", paddingInline: 4 }}>Adaptabilité Carrière</span> · armé pour 2040 ?
        </h1>
        <p style={{ fontSize: 18, color: "var(--c-ink-2)", maxWidth: 520, marginBottom: 28 }}>
          65% des métiers de 2040 n'existent pas encore (OCDE). Le <strong>CAAS</strong> mesure les 4 muscles de l'adaptabilité carrière : anticiper, décider, explorer, oser. Validé dans 18 pays. 24 questions, 7 minutes.
        </p>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 22 }}>
          <button className="btn btn-orange btn-lg btn-arrow" onClick={onStart}>Démarrer le test</button>
          <a href="#methode" className="btn btn-ghost btn-lg"><Icon.play /> Comment ça marche</a>
        </div>
        <div style={{ display: "flex", gap: 22, fontSize: 13, color: "var(--c-muted)", flexWrap: "wrap" }}>
          <span><Icon.shield style={{ width: 13, height: 13, verticalAlign: "-2px", marginRight: 4 }} /> Données privées · stockées en local</span>
          <span>⏱ 7 min · 24 questions</span>
          <span>📋 CAAS (Savickas 2012)</span>
        </div>
      </div>
      <div style={{ position: "relative" }}>
        <div style={{ background: "white", borderRadius: 24, padding: 28, boxShadow: "var(--shadow-md)", border: "1px solid var(--c-line)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 18 }}>
            <span style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--c-muted)" }}>Question 9 / 24</span>
            <span style={{ fontSize: 12, color: "#00897B", fontWeight: 600 }}>● Curiosity</span>
          </div>
          <div style={{ height: 4, background: "var(--c-cream)", borderRadius: 2, marginBottom: 24, overflow: "hidden" }}>
            <div style={{ width: "37%", height: "100%", background: "#00897B" }} />
          </div>
          <h3 style={{ fontSize: 19, lineHeight: 1.35, fontWeight: 600, marginBottom: 22, fontFamily: "var(--font-display)", letterSpacing: "-0.02em" }}>
            "Explorer ce qui m'entoure."
          </h3>
          <div style={{ display: "flex", gap: 8, justifyContent: "space-between" }}>
            {["Pas du tout fort", "Un peu fort", "Moyennement", "Très fort", "Extrêmement fort"].map((label, n) => (
              <div key={n} style={{
                flex: 1, padding: "10px 4px", borderRadius: 10, textAlign: "center",
                background: n === 3 ? "linear-gradient(160deg, #00897B, #00695C)" : "var(--c-cream)",
                color: n === 3 ? "white" : "var(--c-ink)",
                fontWeight: 600, fontSize: 9.5,
                border: n === 3 ? "none" : "1px solid var(--c-line)",
              }}>{label}</div>
            ))}
          </div>
        </div>
        <div style={{ position: "absolute", bottom: -18, right: -18, background: "#0A0E2C", color: "white", padding: "12px 16px", borderRadius: 14, fontSize: 12, display: "flex", alignItems: "center", gap: 10, boxShadow: "var(--shadow-md)" }}>
          <Icon.brain style={{ color: "#F5EB3F" }} /> Validé · 18 pays
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
        <h2 style={{ marginTop: 14 }}>CAAS, 4 dimensions, 6 items chacune.</h2>
        <p style={{ fontSize: 17, color: "var(--c-ink-2)", marginTop: 16 }}>
          Le Career Adapt-Abilities Scale mesure 4 muscles distincts : <strong>Concern</strong> (anticiper), <strong>Control</strong> (décider), <strong>Curiosity</strong> (explorer), <strong>Confidence</strong> (oser). Méta-analyse Rudolph 2017 : forte association avec satisfaction carrière et performance.
        </p>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, maxWidth: 920, margin: "0 auto" }}>
        {[
          { n: "1", t: "24 questions", d: "6 par dimension. Échelle 1 (pas du tout fort) à 5 (extrêmement fort). 7 minutes." },
          { n: "2", t: "Score par axe", d: "Moyenne par dimension. Profil archétype basé sur la dimension dominante." },
          { n: "3", t: "Dimension à muscler", d: "La plus basse est identifiée, avec 3 exercices concrets sur 30 jours pour la renforcer." },
        ].map((s) => (
          <div key={s.n} style={{ background: "var(--c-cream-light)", padding: 22, borderRadius: 16, border: "1px solid var(--c-line)" }}>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: "linear-gradient(135deg, #00897B, #00695C)", color: "white", display: "grid", placeItems: "center", fontWeight: 700, fontFamily: "var(--font-num)", marginBottom: 14 }}>{s.n}</div>
            <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 6 }}>{s.t}</div>
            <p style={{ fontSize: 13.5, color: "var(--c-muted)", lineHeight: 1.55 }}>{s.d}</p>
          </div>
        ))}
      </div>
    </div>
  </section>
);

const LEVEL_COPY = {
  "très fort": { color: "#00897B", body: "Adaptabilité carrière exceptionnelle. Outillé pour naviguer un marché du travail incertain. Les 4 muscles sont solides. Atout majeur à l'ère de l'IA." },
  "fort": { color: "#00ACC1", body: "Adaptabilité solide. Capable de pivoter, d'apprendre, de décider. Muscler la dimension la plus basse pour atteindre un profil complet." },
  "moyen": { color: "#FFA726", body: "Adaptabilité dans la moyenne. Marge de progression nette. Une dimension peut freiner face aux transitions (réorientation, nouvelle filière, monde du travail). Travailler la plus faible pendant 3 mois." },
  "faible": { color: "#C62828", body: "Adaptabilité à renforcer en priorité. Risque de subir les choix plus que de les faire. L'adaptabilité se travaille à tout âge. Programme structuré : 1 exercice par dimension, 3 mois." },
};

const Results = ({ results, onRestart }) => {
  const { avgs, total, level, weakest, strongest, archetype } = results;
  const copy = LEVEL_COPY[level];
  const dimColors = { CONCERN: "#00897B", CONTROL: "#00695C", CURIOSITY: "#00ACC1", CONFIDENCE: "#0097A7" };
  return (
    <section style={{ paddingTop: 60, paddingBottom: 100 }}>
      <div className="shell" style={{ maxWidth: 820 }}>
        <DisclaimerBanner />
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <span className="chip" style={{ background: "rgba(34,160,107,.15)", color: "#22A06B" }}>
            <Icon.check /> Test terminé · 24 réponses analysées
          </span>
          <h1 style={{ marginTop: 18, fontSize: 36 }}>
            Adaptabilité <span style={{ background: "linear-gradient(180deg, transparent 60%, " + copy.color + "55 60%)", paddingInline: 8 }}>{level}</span>
          </h1>
          <p style={{ fontSize: 17, color: "var(--c-muted)", marginTop: 12 }}><strong>{archetype}</strong></p>
        </div>

        <div style={{
          background: "linear-gradient(160deg, " + copy.color + ", #004D40)",
          color: "white", borderRadius: 24, padding: "32px 28px", marginBottom: 24, textAlign: "center",
        }}>
          <div style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", opacity: 0.85, marginBottom: 8 }}>Score CAAS global</div>
          <div style={{ fontFamily: "var(--font-display)", fontSize: 80, fontWeight: 700, lineHeight: 1, marginBottom: 8 }}>{total} / 5</div>
          <p style={{ fontSize: 15, maxWidth: 540, margin: "0 auto", lineHeight: 1.55 }}>{copy.body}</p>
        </div>

        <div style={{ background: "white", borderRadius: 20, padding: 24, border: "1px solid var(--c-line)", marginBottom: 24 }}>
          <h2 style={{ fontSize: 18, marginBottom: 16 }}>Détail par dimension</h2>
          {Object.entries(avgs).map(([dim, val]) => (
            <div key={dim} style={{ marginBottom: 14 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6, fontSize: 13 }}>
                <span style={{ fontWeight: 600 }}>{TYPE_META[dim].l}</span>
                <span style={{ fontFamily: "var(--font-num)", fontWeight: 700, color: dimColors[dim] }}>{val} / 5</span>
              </div>
              <div style={{ height: 8, background: "var(--c-cream)", borderRadius: 4, overflow: "hidden" }}>
                <div style={{ width: `${(val/5)*100}%`, height: "100%", background: dimColors[dim] }} />
              </div>
              <div style={{ fontSize: 12, color: "var(--c-muted)", marginTop: 4 }}>{TYPE_META[dim].short}</div>
            </div>
          ))}
        </div>

        <div style={{ background: "#0A0E2C", color: "white", borderRadius: 20, padding: "32px 28px", marginBottom: 24 }}>
          <h2 style={{ color: "white", fontSize: 22, marginBottom: 6 }}>🎯 Dimension à muscler : {TYPE_META[weakest].l}</h2>
          <p style={{ fontSize: 14, opacity: 0.85, marginBottom: 18 }}>3 exercices concrets sur 30 jours pour la renforcer.</p>
          <ul style={{ paddingLeft: 22, marginBottom: 18, opacity: 0.92, lineHeight: 1.7, fontSize: 14.5 }}>
            {(DIMENSION_ADVICE[weakest] || []).map((e, i) => <li key={i} style={{ marginBottom: 6 }}>{e}</li>)}
          </ul>
          <a href="https://calendly.com/proxxie/entretien" target="_blank" rel="noopener noreferrer" className="btn btn-orange">
            30 min avec Charles pour bâtir le plan
          </a>
        </div>

        <div style={{ background: "var(--c-cream-light)", borderRadius: 20, padding: 24, border: "1px solid var(--c-line)" }}>
          <h3 style={{ fontSize: 16, marginBottom: 10 }}>📍 L'adaptabilité s'appuie sur des bases</h3>
          <p style={{ fontSize: 13.5, color: "var(--c-muted)", lineHeight: 1.55, marginBottom: 14 }}>
            Pour orienter l'adaptabilité, l'ado a besoin de connaître ses intérêts, sa personnalité, ses valeurs.
          </p>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <a href="Proxxie Test.html" style={{ background: "white", padding: "10px 14px", borderRadius: 99, fontSize: 13, fontWeight: 600, color: "#1320CE", border: "1px solid var(--c-line)", textDecoration: "none" }}>OCEAN-X</a>
            <a href="Proxxie Test RIASEC.html" style={{ background: "white", padding: "10px 14px", borderRadius: 99, fontSize: 13, fontWeight: 600, color: "#FD6936", border: "1px solid var(--c-line)", textDecoration: "none" }}>RIASEC</a>
            <a href="Proxxie Test Valeurs.html" style={{ background: "white", padding: "10px 14px", borderRadius: 99, fontSize: 13, fontWeight: 600, color: "#F5EB3F", border: "1px solid var(--c-line)", textDecoration: "none" }}>Valeurs</a>
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
  const gap = Math.abs(pR.total - tR.total);
  return (
    <div style={{ marginBottom: 40 }}>
      <DisclaimerBanner />
      <div style={{ background: "linear-gradient(160deg, #00897B, #004D40)", color: "white", borderRadius: 24, padding: "32px 28px", marginBottom: 24, textAlign: "center" }}>
        <div style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", opacity: 0.85, marginBottom: 8 }}>Comparaison · CAAS</div>
        <div style={{ display: "flex", justifyContent: "center", gap: 40, fontFamily: "var(--font-display)", fontSize: 56 }}>
          <div>
            <div style={{ fontSize: 11, opacity: 0.8, fontFamily: "inherit", marginBottom: 4 }}>{parentName || "Parent"} pensait</div>
            <div>{pR.total} / 5</div>
            <div style={{ fontSize: 13, opacity: 0.85, marginTop: 4 }}>{pR.level}</div>
          </div>
          <div style={{ opacity: 0.6, fontSize: 36 }}>→</div>
          <div>
            <div style={{ fontSize: 11, opacity: 0.8, fontFamily: "inherit", marginBottom: 4 }}>Réel</div>
            <div>{tR.total} / 5</div>
            <div style={{ fontSize: 13, opacity: 0.85, marginTop: 4 }}>{tR.level}</div>
          </div>
        </div>
        <p style={{ marginTop: 16, opacity: 0.92, fontSize: 15, maxWidth: 520, marginInline: "auto" }}>
          {gap >= 1.0 ? "Écart significatif. Votre lecture de son adaptabilité diffère nettement de la sienne." : gap >= 0.5 ? "Écart modéré. À discuter ensemble." : "Perception alignée."}
        </p>
      </div>
    </div>
  );
};

const buildEmailSummary = (results) => {
  const { avgs, total, level, weakest, strongest, archetype } = results;
  return "Test Adaptabilité Carrière (CAAS Savickas)\nScore global : " + total + "/5, " + level + "\nArchétype : " + archetype + "\nConcern " + avgs.CONCERN + " · Control " + avgs.CONTROL + " · Curiosity " + avgs.CURIOSITY + " · Confidence " + avgs.CONFIDENCE + "\nÀ muscler : " + TYPE_META[weakest].l;
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
    var testType = window.__proxxie_test_type || 'caas';
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
        test_type: window.__proxxie_test_type || 'caas',
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
      {mode === "picker" && <PersonaIntro testName="Adaptabilité" accent="#00897B" comingFromPredict={null} onPick={pickPersona} />}
      {mode === "compare-intro" && <PersonaIntro testName="Adaptabilité" accent="#00897B" comingFromPredict={PARENT_PREDICT} onPick={pickPersona} />}
      {mode === "test" && (
        <>
          {persona === "predict" && (<div style={{ background: "#F5EB3F", color: "#0A0E2C", padding: "10px 16px", textAlign: "center", fontSize: 13, fontWeight: 600 }}>🎯 Mode prédiction · Répondez comme vous pensez que votre ado répondrait</div>)}
          <TestFlowEngine questions={QUESTIONS} storageKey={storageKeyEffective} getTypeMeta={getTypeMeta} onExit={exitTest} onComplete={onComplete} />
        </>
      )}
      {mode === "results" && results && (
        <>
          {effectivePersona === "self_compare" && PARENT_PREDICT && (<section style={{ paddingTop: 40, paddingBottom: 0 }}><div className="shell" style={{ maxWidth: 820 }}><ComparePanel parentName={PARENT_PREDICT.n} parentAnswers={PARENT_PREDICT.a} teenAnswers={answers} /></div></section>)}
          {persona === "predict" && (<section style={{ paddingTop: 40, paddingBottom: 0 }}><div className="shell" style={{ maxWidth: 820 }}><ShareLinkPanel testCode="CAAS" accent="#00897B" answers={answers} defaultName="" onSkip={() => {}} /></div></section>)}
          <EmailResultsActions testCode="CAAS" testName="Adaptabilité Carrière (CAAS)" accent="#00897B" summary={buildEmailSummary(results)} answers={answers} />
          <Results results={results} onRestart={restart} />
        </>
      )}
      {mode === "results" && results && <SaveResultsCallout />}
      <Footer />
    </>
  );
};

ReactDOM.createRoot(document.getElementById("root")).render(<TestApp />);
'''


def build_caas(source_path: pathlib.Path, target_path: pathlib.Path) -> str:
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

    src = re.sub(r'const __PROXXIE_TEST_ID__\s*=\s*"[^"]*";', 'const __PROXXIE_TEST_ID__ = "caas";', src, count=1)
    boundary_match = re.search(r'(/\*\s*Test Proxxie Anxi[^/]*\*/\s*\n)?const QUESTIONS\s*=', src)
    if not boundary_match:
        return f"{target_path.name}: boundary introuvable"
    new_src = src[:boundary_match.start()] + CAAS_BLOCK

    nd = new_src.encode('utf-8')
    if comp:
        nd = gzip.compress(nd)
    entry['data'] = base64.b64encode(nd).decode('ascii')
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]

    new_html = re.sub(r'<title[^>]*>[^<]*</title>', '<title>Test Adaptabilité Carrière CAAS, Proxxie</title>', new_html, count=1)
    new_html = re.sub(r'<title[^>]*>[^<]*<\\/title>', 'Test Adaptabilité Carrière CAAS, Proxxie<\\/title>'.replace('Test', '<title>Test', 1) if False else '<title>Test Adaptabilité Carrière CAAS, Proxxie<\\/title>', new_html, count=1)

    target_path.write_text(new_html, encoding='utf-8')
    return f"{target_path.name}: built (asset {uuid[:8]}, src {len(src)} → {len(new_src)})"


if __name__ == "__main__":
    print(build_caas(SOURCE, TARGET))
    print(build_caas(SOURCE, TARGET_LOWER))

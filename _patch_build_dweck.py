#!/usr/bin/env python3
"""Construit Proxxie Test Dweck.html (Mindset fixed vs growth).

Source : Dweck (2006) « Mindset » + Implicit Theories of Intelligence Scale.
16 items, 4 dimensions (Intelligence, Talent, Effort, Échec).
8 items « fixed » (inversés) + 8 items « growth » (directs).

Score growth_mindset_pct = pourcentage moyen d'orientation growth (0-100).

Pas un instrument clinique · outil éducatif. Carol Dweck a vendu 4M+
exemplaires de son livre, le concept est entré dans toutes les salles
de classe US.

Pattern identique à _patch_build_grit.py · clone Anxiete + swap JSX.
"""
import re
import json
import base64
import gzip
import pathlib
import _bridge_common
import shutil

REPO = pathlib.Path(__file__).parent
SOURCE = REPO / "Proxxie Test Anxiete.html"
TARGET = REPO / "Proxxie Test Dweck.html"
TARGET_LOWER = REPO / "test-dweck.html"
ASSET_UUID_PREFIX = "61feca88"

DWECK_BLOCK = r'''/* Test Proxxie Mindset (Dweck 2006) · fixed vs growth.
   16 items répartis sur 4 dimensions, 8 fixed (reverse) + 8 growth (direct).
   Outil éducatif, pas instrument clinique validé. */

const QUESTIONS = [
  // === INT · Intelligence (4 items, 2 fixed reverse + 2 growth direct) ===
  { type: "INT", q: "Ton intelligence est quelque chose que tu ne peux pas vraiment changer.", reverse: true },
  { type: "INT", q: "Tu peux apprendre des choses, mais ton niveau d'intelligence reste à peu près le même.", reverse: true },
  { type: "INT", q: "Tu peux développer ton intelligence en t'entraînant et en apprenant régulièrement.", reverse: false },
  { type: "INT", q: "Plus tu fais d'efforts, plus tu deviens vraiment intelligent(e), pas juste plus expérimenté(e).", reverse: false },

  // === ABI · Talent / Aptitude (4 items, 2 fixed + 2 growth) ===
  { type: "ABI", q: "On a un talent pour certaines choses et pas d'autres, c'est ainsi.", reverse: true },
  { type: "ABI", q: "Quand quelqu'un est doué dans un domaine, c'est qu'il est né comme ça.", reverse: true },
  { type: "ABI", q: "Avec assez de travail, presque tout le monde peut devenir bon dans presque n'importe quoi.", reverse: false },
  { type: "ABI", q: "Les meilleurs dans un domaine sont surtout ceux qui ont le plus pratiqué, pas les plus doués au départ.", reverse: false },

  // === EFF · Effort (4 items, 2 fixed + 2 growth) ===
  { type: "EFF", q: "Si tu dois fournir beaucoup d'efforts pour quelque chose, c'est probablement que tu n'es pas fait(e) pour.", reverse: true },
  { type: "EFF", q: "Avoir du talent, c'est faire les choses facilement, sans avoir à se forcer.", reverse: true },
  { type: "EFF", q: "L'effort, c'est ce qui transforme un talent en vraie compétence.", reverse: false },
  { type: "EFF", q: "Galérer sur quelque chose est en général un signe que tu es en train d'apprendre.", reverse: false },

  // === FAI · Échec (4 items, 2 fixed + 2 growth) ===
  { type: "FAI", q: "Échouer publiquement à quelque chose en dit beaucoup sur ton niveau réel.", reverse: true },
  { type: "FAI", q: "Quand je rate quelque chose d'important, je préfère arrêter d'essayer plutôt que continuer.", reverse: true },
  { type: "FAI", q: "Un échec est une info utile, pas une preuve que tu n'es pas capable.", reverse: false },
  { type: "FAI", q: "Quand je rate quelque chose, je veux comprendre ce qui s'est passé pour mieux faire la fois suivante.", reverse: false },
];

const TYPE_META = {
  INT: { l: "Intelligence", c: "#0EA5E9", short: "Le QI est-il fixe ou se développe-t-il ?" },
  ABI: { l: "Talent / aptitude", c: "#06B6D4", short: "On naît doué, ou on le devient ?" },
  EFF: { l: "Effort", c: "#0891B2", short: "Forcer = ne pas être fait pour, ou condition de la maîtrise ?" },
  FAI: { l: "Échec", c: "#0E7490", short: "Verdict sur soi, ou info pour la prochaine fois ?" },
};

const STORAGE_KEY = "proxxie-dweck-answers";

const getTypeMeta = (q) => ({ label: TYPE_META[q.type].l, color: TYPE_META[q.type].c });

const computeResults = (answers) => {
  // Score growth par item : 1-5 si direct, 6-raw si reverse
  // Puis on convertit en % growth (1→0%, 5→100%)
  const dims = ["INT", "ABI", "EFF", "FAI"];
  const dimScores = {};
  dims.forEach((d) => { dimScores[d] = { sum: 0, count: 0 }; });
  QUESTIONS.forEach((q, idx) => {
    if (answers[idx] == null) return;
    const growthRaw = q.reverse ? 6 - answers[idx] : answers[idx];
    dimScores[q.type].sum += growthRaw;
    dimScores[q.type].count += 1;
  });
  const dimPct = {};
  dims.forEach((d) => {
    const avg = dimScores[d].count > 0 ? dimScores[d].sum / dimScores[d].count : 0;
    dimPct[d] = Math.round(((avg - 1) / 4) * 100);
  });
  // Global = moyenne des 4 dimensions
  const total = Math.round((dimPct.INT + dimPct.ABI + dimPct.EFF + dimPct.FAI) / 4);

  let level = "fixed marqué", levelColor = "#9CA3AF";
  if (total >= 80) { level = "growth solide"; levelColor = "#059669"; }
  else if (total >= 65) { level = "plutôt growth"; levelColor = "#0EA5E9"; }
  else if (total >= 50) { level = "mixte"; levelColor = "#0891B2"; }
  else if (total >= 35) { level = "plutôt fixed"; levelColor = "#D97706"; }

  // Dimension la plus fixe = focus du travail
  const mostFixed = dims.reduce((a, b) => dimPct[a] <= dimPct[b] ? a : b);

  return { total, dimPct, level, levelColor, mostFixed };
};

const LEVEL_COPY = {
  "growth solide": {
    title: "Tu as un growth mindset solide",
    sub: "Tu vois clairement que l'intelligence, le talent, et la capacité à réussir se développent avec l'effort. Ton défi à présent : tenir cette croyance quand tu seras face à un vrai échec public.",
  },
  "plutôt growth": {
    title: "Tu penches du bon côté",
    sub: "Tu crois majoritairement au développement par l'effort, mais une ou deux dimensions montrent encore des réflexes fixed. Travaillerles pour passer en growth solide.",
  },
  "mixte": {
    title: "Mindset mixte",
    sub: "Tu oscilles entre les deux selon les domaines. C'est très courant chez les ados et c'est le moment idéal pour basculer · les croyances qui se renforcent à 16 ans deviennent dures à déplacer à 30.",
  },
  "plutôt fixed": {
    title: "Mindset plutôt fixed",
    sub: "Tu crois souvent que les capacités sont innées et que l'effort est un signe de manque de talent. Cette croyance limite tes prises de risque et tes apprentissages. Bonne nouvelle · ça se déplace.",
  },
  "fixed marqué": {
    title: "Mindset fixed marqué",
    sub: "Tu crois fortement que l'intelligence et le talent sont figés. Conséquence directe · tu évites les défis où tu pourrais échouer, et tu interprètes les difficultés comme des verdicts sur toi. À retravailler en priorité avant Parcoursup.",
  },
};

const ACTIONS_BY_DIM = {
  INT: [
    "Choisis un cours où tu galères et identifie 1 raison concrète pour laquelle tu progressé(e) le mois dernier.",
    "Écoute « Mindset » de Carol Dweck (audio FR sur Audible ou via le résumé Blinkist).",
    "Quand tu te dis « je suis nul(le) en X », reformule : « je ne suis pas encore bon(ne) en X » (le mot « encore » change tout).",
  ],
  ABI: [
    "Choisis un domaine où tu te crois sans talent. Pratique-le 20 min/jour pendant 30 jours. Compare le résultat.",
    "Lis l'histoire d'un sportif ou artiste qui a commencé tard et a réussi (ex : Vera Wang, designer mariée à 40 ans).",
    "Pose à tes parents : « Vous avez raté quoi quand vous aviez mon âge et vous êtes devenus bons après ? »",
  ],
  EFF: [
    "Quand tu commences à forcer sur quelque chose, dis-toi à voix haute : « C'est exactement le moment où le cerveau apprend. »",
    "Tiens un journal d'effort 2 semaines · note chaque jour 1 truc où tu as forcé et ce que tu en as appris.",
    "Regarde une vidéo de Magnus Carlsen ou Lionel Messi qui parlent de leurs heures d'entraînement (pas de leur talent).",
  ],
  FAI: [
    "Liste 3 échecs récents et pour chacun, écris « j'ai appris que… ».",
    "Quand tu rates quelque chose en classe, prends 5 minutes pour identifier 1 chose à changer la prochaine fois.",
    "Pose-toi cette question hebdo : « Qu'est-ce que j'ai raté cette semaine qui m'a fait progresser ? »",
  ],
};

const DisclaimerBanner = () => (
  <div style={{
    background: "#ECFEFF", borderLeft: "4px solid #0EA5E9",
    padding: "14px 20px", marginBottom: 30, borderRadius: 8,
    fontSize: 13.5, color: "#0A0E2C", lineHeight: 1.55,
  }}>
    <strong>ℹ️ Le mindset se change.</strong> Le concept de growth mindset vient des travaux de Carol Dweck (Stanford, 2006). Il est devenu central en éducation US et au-delà. Ce test te dit où tu en es <em>maintenant</em>, pas qui tu es à jamais. La science montre que la croyance peut bouger en quelques semaines avec les bonnes pratiques.
  </div>
);

const TestHero = ({ onStart }) => (
  <section style={{ paddingTop: 70, paddingBottom: 80, position: "relative", overflow: "hidden" }}>
    <Pill color="rgba(14,165,233,.45)" w={260} h={130} style={{ position: "absolute", top: 110, right: -60, borderRadius: 999 }} />
    <Half color="rgba(245,235,63,.4)" side="t" w={300} h={120} style={{ position: "absolute", bottom: -10, left: -40 }} />
    <div className="shell" style={{ position: "relative", display: "grid", gridTemplateColumns: "1.1fr 1fr", gap: 60, alignItems: "center" }}>
      <div>
        <span className="chip" style={{ background: "rgba(14,165,233,.15)", color: "#0EA5E9" }}>
          <Icon.spark style={{ width: 14, height: 14 }} /> Mindset · Carol Dweck (Stanford)
        </span>
        <h1 style={{ marginTop: 22, marginBottom: 22 }}>
          Mindset <span style={{ background: "linear-gradient(180deg, transparent 60%, #F5EB3F 60%)", paddingInline: 4 }}>growth</span> ou fixed ?
        </h1>
        <p style={{ fontSize: 18, color: "var(--c-ink-2)", maxWidth: 540, marginBottom: 28 }}>
          Tu crois que l'intelligence se travaille, ou qu'on naît avec ? Cette croyance change tout : prises de risque, apprentissages, réaction à l'échec. <strong>Carol Dweck (Stanford) a vendu 4 millions d'exemplaires</strong> de son livre · ce test mesure où tu en es. 16 questions, 4 minutes.
        </p>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 22 }}>
          <button className="btn btn-orange btn-lg btn-arrow" onClick={onStart}>Démarrer le test</button>
          <a href="#methode" className="btn btn-ghost btn-lg"><Icon.play /> Comment ça marche</a>
        </div>
        <div style={{ display: "flex", gap: 22, fontSize: 13, color: "var(--c-muted)", flexWrap: "wrap" }}>
          <span><Icon.shield style={{ width: 13, height: 13, verticalAlign: "-2px", marginRight: 4 }} /> Données privées · stockées en local</span>
          <span>⏱ 4 min · 16 questions</span>
          <span>📋 Dweck 2006 (Stanford)</span>
        </div>
      </div>
      <div style={{ position: "relative" }}>
        <div style={{ background: "white", borderRadius: 24, padding: 28, boxShadow: "var(--shadow-md)", border: "1px solid var(--c-line)" }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: "#0EA5E9", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 14 }}>4 dimensions mesurées</div>
          {Object.keys(TYPE_META).map((t, i, arr) => (
            <div key={t} style={{ display: "flex", alignItems: "center", gap: 14, padding: "12px 0", borderBottom: i < arr.length - 1 ? "1px solid var(--c-line)" : "none" }}>
              <div style={{ width: 36, height: 36, borderRadius: 10, background: TYPE_META[t].c, color: "white", display: "grid", placeItems: "center", fontWeight: 700, fontSize: 13, fontFamily: "var(--font-display)" }}>{t}</div>
              <div>
                <div style={{ fontWeight: 700, fontSize: 14.5, color: "var(--c-ink)" }}>{TYPE_META[t].l}</div>
                <div style={{ fontSize: 12.5, color: "var(--c-muted)" }}>{TYPE_META[t].short}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  </section>
);

const HowItWorks = () => (
  <section id="methode" style={{ paddingTop: 60, paddingBottom: 80, background: "var(--c-cream-light, #FAF6EE)" }}>
    <div className="shell" style={{ maxWidth: 880 }}>
      <h2 style={{ textAlign: "center", marginBottom: 16 }}>Pourquoi le mindset change tout</h2>
      <p style={{ textAlign: "center", fontSize: 16, color: "var(--c-muted)", marginBottom: 40, maxWidth: 720, margin: "0 auto 40px" }}>
        Une étude de Stanford sur 12 000 ados a montré qu'un changement de mindset (juste expliquer que le cerveau se développe) améliore les notes en moyenne de 0,1 point sur 4. Pas magique, mais réel et durable.
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
        <div style={{ background: "white", borderRadius: 18, padding: 22, border: "1px solid #FED7AA" }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: "#D97706", marginBottom: 8 }}>FIXED MINDSET</div>
          <div style={{ fontWeight: 700, fontSize: 16, color: "var(--c-ink)", marginBottom: 8 }}>« Je suis nul(le) en maths »</div>
          <ul style={{ fontSize: 13.5, color: "var(--c-muted)", lineHeight: 1.6, paddingLeft: 18, margin: 0 }}>
            <li>Évite les défis (peur de l'échec public)</li>
            <li>L'effort = signe de manque de talent</li>
            <li>Échec = verdict sur soi</li>
            <li>Plafonne tôt</li>
          </ul>
        </div>
        <div style={{ background: "white", borderRadius: 18, padding: 22, border: "1px solid #BFDBFE" }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: "#0EA5E9", marginBottom: 8 }}>GROWTH MINDSET</div>
          <div style={{ fontWeight: 700, fontSize: 16, color: "var(--c-ink)", marginBottom: 8 }}>« Je ne suis pas encore bon(ne) en maths »</div>
          <ul style={{ fontSize: 13.5, color: "var(--c-muted)", lineHeight: 1.6, paddingLeft: 18, margin: 0 }}>
            <li>Cherche les défis (occasion d'apprendre)</li>
            <li>L'effort = condition de la maîtrise</li>
            <li>Échec = info, pas verdict</li>
            <li>Continue à progresser longtemps</li>
          </ul>
        </div>
      </div>
    </div>
  </section>
);

const Results = ({ results, onRestart }) => {
  const { total, dimPct, level, levelColor, mostFixed } = results;
  const levelCopy = LEVEL_COPY[level] || LEVEL_COPY["mixte"];
  const actions = ACTIONS_BY_DIM[mostFixed] || [];
  return (
    <section style={{ paddingTop: 60, paddingBottom: 30 }}>
      <div className="shell" style={{ maxWidth: 820 }}>
        <DisclaimerBanner />

        {/* Hero score */}
        <div style={{ textAlign: "center", marginBottom: 50 }}>
          <span className="chip" style={{ background: "rgba(14,165,233,.15)", color: "#0EA5E9" }}>
            <Icon.spark style={{ width: 14, height: 14 }} /> Ton mindset
          </span>
          <h1 style={{ marginTop: 20, marginBottom: 12, fontSize: 56, color: levelColor, fontFamily: "var(--font-display)", letterSpacing: "-0.03em" }}>
            {total}<span style={{ fontSize: 24, color: "var(--c-muted)" }}>%</span>
          </h1>
          <p style={{ fontSize: 14, color: "var(--c-muted)", marginBottom: 16 }}>de growth mindset</p>
          <h2 style={{ fontSize: 26, color: "var(--c-ink)", marginBottom: 12, fontWeight: 600 }}>{levelCopy.title}</h2>
          <p style={{ fontSize: 16, color: "var(--c-ink-2)", maxWidth: 600, margin: "0 auto", lineHeight: 1.6 }}>{levelCopy.sub}</p>
        </div>

        {/* 4 dimensions */}
        <div style={{ background: "white", borderRadius: 20, padding: 32, border: "1px solid var(--c-line)", marginBottom: 24 }}>
          <h2 style={{ fontSize: 22, marginBottom: 24, color: "var(--c-ink)" }}>Tes 4 dimensions</h2>
          <div style={{ display: "grid", gap: 18 }}>
            {Object.keys(TYPE_META).map((t) => (
              <div key={t}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 8 }}>
                  <div>
                    <span style={{ display: "inline-block", width: 28, height: 28, borderRadius: 7, background: TYPE_META[t].c, color: "white", textAlign: "center", lineHeight: "28px", fontWeight: 700, marginRight: 12, fontFamily: "var(--font-display)", fontSize: 11 }}>{t}</span>
                    <strong style={{ color: "var(--c-ink)", fontSize: 15.5 }}>{TYPE_META[t].l}</strong>
                  </div>
                  <span style={{ fontFamily: "var(--font-num)", fontWeight: 700, fontSize: 22, color: TYPE_META[t].c }}>{dimPct[t]}<span style={{ fontSize: 13, color: "var(--c-muted)", fontWeight: 500 }}>%</span></span>
                </div>
                <div style={{ height: 10, background: "var(--c-cream)", borderRadius: 5, overflow: "hidden" }}>
                  <div style={{ width: `${dimPct[t]}%`, height: "100%", background: TYPE_META[t].c, transition: "width .8s cubic-bezier(.2,.8,.2,1)" }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 3 actions sur la dimension la plus fixe */}
        {actions.length > 0 && (
          <div style={{ background: "linear-gradient(160deg, #ECFEFF, #FAF6EE)", borderRadius: 20, padding: 32, border: "1px solid #BFDBFE", marginBottom: 24 }}>
            <h2 style={{ fontSize: 24, marginBottom: 8, color: "var(--c-ink)" }}>3 actions sur {TYPE_META[mostFixed].l}</h2>
            <p style={{ fontSize: 14, color: "var(--c-muted)", marginBottom: 24 }}>Ta dimension la plus fixed · c'est là que basculer en growth aura le plus d'impact.</p>
            <div style={{ display: "grid", gap: 12 }}>
              {actions.map((a, i) => (
                <div key={i} style={{ display: "flex", gap: 14, padding: "14px 18px", background: "white", borderRadius: 12, border: "1px solid var(--c-line)" }}>
                  <div style={{ flexShrink: 0, width: 28, height: 28, borderRadius: 14, background: TYPE_META[mostFixed].c, color: "white", display: "grid", placeItems: "center", fontWeight: 700, fontSize: 13, fontFamily: "var(--font-display)" }}>{i+1}</div>
                  <div style={{ flex: 1, fontSize: 14.5, color: "var(--c-ink)", lineHeight: 1.55 }}>{a}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );
};

const ComparePanel = ({ parentName, parentAnswers, teenAnswers }) => {
  const pR = computeResults(parentAnswers);
  const tR = computeResults(teenAnswers);
  const gap = Math.abs(pR.total - tR.total);
  return (
    <div style={{ background: "white", borderRadius: 20, padding: 28, border: "1px solid var(--c-line)", marginBottom: 30 }}>
      <h2 style={{ fontSize: 20, marginBottom: 18 }}>Comparaison mindset avec {parentName}</h2>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
        <div style={{ padding: 18, background: "var(--c-cream-light, #FAF6EE)", borderRadius: 12 }}>
          <div style={{ fontSize: 12, color: "var(--c-muted)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>{parentName}</div>
          <div style={{ fontSize: 32, fontWeight: 700, color: "var(--c-ink)", fontFamily: "var(--font-display)" }}>{pR.total}<span style={{ fontSize: 14 }}>%</span></div>
        </div>
        <div style={{ padding: 18, background: "rgba(14,165,233,.08)", borderRadius: 12 }}>
          <div style={{ fontSize: 12, color: "#0EA5E9", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>Tu réponds</div>
          <div style={{ fontSize: 32, fontWeight: 700, color: "#0EA5E9", fontFamily: "var(--font-display)" }}>{tR.total}<span style={{ fontSize: 14 }}>%</span></div>
        </div>
      </div>
      <p style={{ marginTop: 18, fontSize: 14, color: "var(--c-muted)", lineHeight: 1.55 }}>
        Écart de <strong>{gap} points</strong>. Le mindset se transmet beaucoup entre parents et enfants, par les phrases du quotidien (« t'es nul(le) en maths » vs « t'as pas encore trouvé le truc »).
      </p>
    </div>
  );
};

const buildEmailSummary = (results) => {
  const { total, dimPct, level, mostFixed } = results;
  let summary = `Mindset Dweck : ${total}% growth (${level})\n\n`;
  summary += `Dimensions :\n`;
  Object.keys(TYPE_META).forEach((t) => { summary += `- ${TYPE_META[t].l} : ${dimPct[t]}%\n`; });
  summary += `\nDimension la plus fixe : ${TYPE_META[mostFixed].l}\n`;
  return summary;
};

const TestApp = () => {
  // Ponts statiques (zéro backend) · #predict= (parent→ado) et #results= (ado→parent).
  // Même pattern canonique que les autres tests. Définis dans le préfixe du bundle.
  const PARENT_PREDICT = React.useMemo(() => readPredictHash(), []);
  const RESULTS_HASH = React.useMemo(() => readResultsHash(), []);
  const [persona, setPersona] = React.useState(null);
  const [mode, setMode] = React.useState(RESULTS_HASH ? "results" : (PARENT_PREDICT ? "compare-intro" : "landing"));
  const [results, setResults] = React.useState(RESULTS_HASH ? computeResults(RESULTS_HASH.a) : null);
  const [answers, setAnswers] = React.useState(RESULTS_HASH ? RESULTS_HASH.a : null);
  const goPicker = () => { setMode("picker"); window.scrollTo({ top: 0, behavior: "smooth" }); };
  const pickPersona = (p) => {
    var testType = window.__proxxie_test_type || 'dweck';
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
    try { window.localStorage.setItem("proxxie.tests.dweck", "done"); } catch(e){}
    if (window.trackEvent) {
      var inProgress = window.__proxxie_test_in_progress;
      var elapsed = inProgress && inProgress.startedAt ? (Date.now() - inProgress.startedAt) : null;
      window.trackEvent('test_completed', {
        test_type: window.__proxxie_test_type || 'dweck',
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
      {mode === "picker" && <PersonaIntro testName="Mindset Dweck" accent="#0EA5E9" comingFromPredict={null} onPick={pickPersona} />}
      {mode === "compare-intro" && <PersonaIntro testName="Mindset Dweck" accent="#0EA5E9" comingFromPredict={PARENT_PREDICT} onPick={pickPersona} />}
      {mode === "test" && (
        <>
          {persona === "predict" && (<div style={{ background: "#F5EB3F", color: "#0A0E2C", padding: "10px 16px", textAlign: "center", fontSize: 13, fontWeight: 600 }}>🎯 Mode prédiction · Répondez comme vous pensez que votre ado répondrait</div>)}
          <TestFlowEngine questions={QUESTIONS} storageKey={storageKeyEffective} getTypeMeta={getTypeMeta} onExit={exitTest} onComplete={onComplete} />
        </>
      )}
      {mode === "results" && results && (
        <>
          {effectivePersona === "self_compare" && PARENT_PREDICT && (<section style={{ paddingTop: 40, paddingBottom: 0 }}><div className="shell" style={{ maxWidth: 820 }}><ComparePanel parentName={PARENT_PREDICT.n} parentAnswers={PARENT_PREDICT.a} teenAnswers={answers} /></div></section>)}
          {persona === "predict" && (<section style={{ paddingTop: 40, paddingBottom: 0 }}><div className="shell" style={{ maxWidth: 820 }}><ShareLinkPanel testCode="Dweck" accent="#0EA5E9" answers={answers} defaultName="" onSkip={() => {}} /></div></section>)}
          <EmailResultsActions testCode="Dweck" testName="Mindset Dweck (fixed vs growth)" accent="#0EA5E9" summary={buildEmailSummary(results)} answers={answers} />
          <Results results={results} onRestart={restart} />
        </>
      )}
      <Footer />
    </>
  );
};

ReactDOM.createRoot(document.getElementById("root")).render(<TestApp />);
'''


def build(source_path: pathlib.Path, target_path: pathlib.Path) -> str:
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
    raw = base64.b64decode(entry["data"])
    comp = entry.get("compressed", False)
    src = gzip.decompress(raw).decode("utf-8") if comp else raw.decode("utf-8")

    src = re.sub(
        r'const __PROXXIE_TEST_ID__\s*=\s*"[^"]*";',
        'const __PROXXIE_TEST_ID__ = "dweck";',
        src,
        count=1,
    )
    boundary_match = re.search(
        r"(/\*\s*Test Proxxie [^/]*\*/\s*\n)?const QUESTIONS\s*=", src
    )
    if not boundary_match:
        return f"{target_path.name}: boundary introuvable"
    new_src = src[: boundary_match.start()] + _bridge_common.wire_bridge(DWECK_BLOCK, "dweck", "Proxxie%20Test%20Dweck.html")

    nd = new_src.encode("utf-8")
    if comp:
        nd = gzip.compress(nd)
    entry["data"] = base64.b64encode(nd).decode("ascii")
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[: m.start(2)] + new_manifest_json + html[m.end(2) :]

    new_html = re.sub(
        r"<title[^>]*>[^<]*</title>",
        "<title>Test Mindset Dweck, Proxxie</title>",
        new_html,
        count=1,
    )
    new_html = re.sub(
        r"<title[^>]*>[^<]*<\\/title>",
        "<title>Test Mindset Dweck, Proxxie<\\/title>",
        new_html,
        count=1,
    )

    target_path.write_text(new_html, encoding="utf-8")
    return f"{target_path.name}: built (asset {uuid[:8]}, src {len(src)} → {len(new_src)})"


if __name__ == "__main__":
    print(build(SOURCE, TARGET))
    print(build(SOURCE, TARGET_LOWER))

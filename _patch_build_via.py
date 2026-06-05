#!/usr/bin/env python3
"""Construit Proxxie Test VIA.html (Forces de caractère) depuis Anxiete.

Source psychométrique : VIA Inventory of Strengths (Peterson & Seligman 2004).
24 forces organisées en 6 vertus universelles, validées sur 10M+ d'utilisateurs.

Notre version courte : 24 items, 1 par force, Likert 1-5.
- Avantage : ultra court (~6 min), facile pour ados
- Compromis : fiabilité inférieure à VIA-IS-120 officiel · positionnement,
  pas évaluation clinique. Mentionné dans le disclaimer.

Output :
- Top 5 « forces signatures » à valoriser dans le quotidien
- Bottom 5 « zones de développement » à éveiller (sans culpabiliser)
- Cartographie des 6 vertus (radar)

Pattern identique à _patch_build_grit.py · clone Anxiete + swap JSX.
"""
import re
import json
import base64
import gzip
import pathlib
import shutil

REPO = pathlib.Path(__file__).parent
SOURCE = REPO / "Proxxie Test Anxiete.html"
TARGET = REPO / "Proxxie Test VIA.html"
TARGET_LOWER = REPO / "test-via.html"
ASSET_UUID_PREFIX = "61feca88"

VIA_BLOCK = r'''/* Test Proxxie VIA Strengths, forces de caractère (Peterson & Seligman 2004).
   Version courte : 1 item par force = 24 items au total. Pas validé
   psychométriquement comme la version VIA-IS-120 officielle, mais utile
   pour identifier ses 5 forces signatures et les valoriser. */

const QUESTIONS = [
  // === Vertu 1 · Sagesse et connaissance (cognitif) ===
  { type: "CR", q: "J'aime trouver de nouvelles façons de faire les choses, même quand l'ancienne marche très bien." },
  { type: "CU", q: "Je m'intéresse à des sujets très différents les uns des autres." },
  { type: "EC", q: "Je vérifie ce que je crois savoir, je n'accepte pas une info juste parce qu'elle est répétée." },
  { type: "AL", q: "Apprendre une nouvelle compétence me donne de l'énergie, même sans note à la clé." },
  { type: "SA", q: "Mes amis viennent souvent me demander conseil quand ils ont une décision compliquée à prendre." },

  // === Vertu 2 · Courage (émotionnel) ===
  { type: "CO", q: "Quand je crois à quelque chose, je le défends même si la majorité pense le contraire." },
  { type: "PE", q: "Je termine ce que je commence, même quand c'est plus dur que prévu." },
  { type: "HO", q: "Je préfère dire ce que je pense plutôt que ce que les gens veulent entendre." },
  { type: "VI", q: "Je me réveille en général avec de l'énergie pour la journée." },

  // === Vertu 3 · Humanité (interpersonnel) ===
  { type: "AM", q: "J'ai au moins une personne avec qui je peux être totalement moi-même." },
  { type: "BO", q: "Faire quelque chose pour quelqu'un sans rien attendre en retour me rend heureux(se)." },
  { type: "IS", q: "Je devine assez vite ce qui se joue émotionnellement dans un groupe." },

  // === Vertu 4 · Justice (civique) ===
  { type: "EQ", q: "Je trouve naturellement ma place dans un groupe et je tire les autres vers le haut." },
  { type: "EF", q: "Je suis incapable de profiter d'une situation si je sais que quelqu'un est lésé." },
  { type: "LE", q: "Quand un projet a besoin de quelqu'un qui prend en main, je peux le faire." },

  // === Vertu 5 · Tempérance (protecteur) ===
  { type: "PA", q: "Je n'aime pas garder rancune longtemps, ça me fatigue." },
  { type: "HU", q: "Je connais mes points faibles et je peux les reconnaître sans drame." },
  { type: "PR", q: "Avant une décision importante, je prends le temps de peser le pour et le contre." },
  { type: "MS", q: "Quand je suis énervé(e), j'arrive à attendre avant de réagir ou répondre." },

  // === Vertu 6 · Transcendance (existentiel) ===
  { type: "SB", q: "Une musique, un paysage, une œuvre d'art peuvent m'arrêter net." },
  { type: "GR", q: "Je remarque souvent les petites choses qui me font du bien dans la journée." },
  { type: "ES", q: "Quand les choses vont mal, je crois généralement qu'elles vont s'améliorer." },
  { type: "HM", q: "J'aime faire rire les autres, et je sais rire de moi-même." },
  { type: "SE", q: "J'ai le sentiment que ma vie a un sens, ou je cherche activement à le trouver." },
];

const TYPE_META = {
  // Vertu Sagesse · violet
  CR: { l: "Créativité", v: "Sagesse", c: "#7C3AED", icon: "✨" },
  CU: { l: "Curiosité", v: "Sagesse", c: "#7C3AED", icon: "🧭" },
  EC: { l: "Esprit critique", v: "Sagesse", c: "#7C3AED", icon: "🔍" },
  AL: { l: "Amour d'apprendre", v: "Sagesse", c: "#7C3AED", icon: "📚" },
  SA: { l: "Sagesse / perspective", v: "Sagesse", c: "#7C3AED", icon: "🦉" },
  // Vertu Courage · rouge brique
  CO: { l: "Courage", v: "Courage", c: "#DC2626", icon: "🦁" },
  PE: { l: "Persévérance", v: "Courage", c: "#DC2626", icon: "🏔️" },
  HO: { l: "Honnêteté", v: "Courage", c: "#DC2626", icon: "🤝" },
  VI: { l: "Vitalité", v: "Courage", c: "#DC2626", icon: "⚡" },
  // Vertu Humanité · rose
  AM: { l: "Capacité d'aimer", v: "Humanité", c: "#DB2777", icon: "💛" },
  BO: { l: "Bonté", v: "Humanité", c: "#DB2777", icon: "🫶" },
  IS: { l: "Intelligence sociale", v: "Humanité", c: "#DB2777", icon: "👁️" },
  // Vertu Justice · vert
  EQ: { l: "Esprit d'équipe", v: "Justice", c: "#059669", icon: "👥" },
  EF: { l: "Sens de l'équité", v: "Justice", c: "#059669", icon: "⚖️" },
  LE: { l: "Leadership", v: "Justice", c: "#059669", icon: "🎯" },
  // Vertu Tempérance · bleu marine
  PA: { l: "Pardon", v: "Tempérance", c: "#1E3A8A", icon: "🕊️" },
  HU: { l: "Humilité", v: "Tempérance", c: "#1E3A8A", icon: "🌱" },
  PR: { l: "Prudence", v: "Tempérance", c: "#1E3A8A", icon: "🧭" },
  MS: { l: "Maîtrise de soi", v: "Tempérance", c: "#1E3A8A", icon: "🎼" },
  // Vertu Transcendance · ocre
  SB: { l: "Sens du beau", v: "Transcendance", c: "#D97706", icon: "🎨" },
  GR: { l: "Gratitude", v: "Transcendance", c: "#D97706", icon: "🙏" },
  ES: { l: "Espoir", v: "Transcendance", c: "#D97706", icon: "🌅" },
  HM: { l: "Humour", v: "Transcendance", c: "#D97706", icon: "😄" },
  SE: { l: "Sens / spiritualité", v: "Transcendance", c: "#D97706", icon: "🌌" },
};

const VIRTUE_META = {
  "Sagesse": { c: "#7C3AED", desc: "Connaître, apprendre, comprendre, juger." },
  "Courage": { c: "#DC2626", desc: "Tenir, oser, être vrai même quand c'est dur." },
  "Humanité": { c: "#DB2777", desc: "Aimer, prendre soin, comprendre l'autre." },
  "Justice": { c: "#059669", desc: "Vivre avec les autres, contribuer, mener." },
  "Tempérance": { c: "#1E3A8A", desc: "Se modérer, se connaître, durer." },
  "Transcendance": { c: "#D97706", desc: "Se relier à plus grand que soi, espérer." },
};

const STORAGE_KEY = "proxxie-via-answers";

const getTypeMeta = (q) => ({ label: TYPE_META[q.type].l, color: TYPE_META[q.type].c });

const computeResults = (answers) => {
  // Score 1-5 par force
  const strengths = QUESTIONS.map((q, idx) => ({
    code: q.type,
    label: TYPE_META[q.type].l,
    virtue: TYPE_META[q.type].v,
    color: TYPE_META[q.type].c,
    icon: TYPE_META[q.type].icon,
    score: answers[idx] || 0,
  }));
  const sorted = [...strengths].sort((a, b) => b.score - a.score);
  const top5 = sorted.slice(0, 5);
  const bottom5 = sorted.slice(-5).reverse();

  // Score par vertu : moyenne sur 100
  const virtueScores = {};
  Object.keys(VIRTUE_META).forEach((v) => {
    const items = strengths.filter((s) => s.virtue === v);
    const sum = items.reduce((a, s) => a + s.score, 0);
    const avg = items.length > 0 ? sum / items.length : 0;
    virtueScores[v] = Math.round(((avg - 1) / 4) * 100);
  });
  const dominantVirtue = Object.keys(virtueScores).reduce((a, b) =>
    virtueScores[a] >= virtueScores[b] ? a : b
  );

  return { strengths, top5, bottom5, virtueScores, dominantVirtue };
};

const DisclaimerBanner = () => (
  <div style={{
    background: "#F5F3FF", borderLeft: "4px solid #7C3AED",
    padding: "14px 20px", marginBottom: 30, borderRadius: 8,
    fontSize: 13.5, color: "#0A0E2C", lineHeight: 1.55,
  }}>
    <strong>ℹ️ Forces à valoriser, pas à juger.</strong> Le VIA (Peterson & Seligman, 2004) part d'une idée simple : tu as déjà des forces, identifies-les et utilises-les. Cette version courte (1 item par force) sert au positionnement, pas à l'évaluation clinique. Pour la version longue, voir <a href="https://www.viacharacter.org/survey/account/register" target="_blank" rel="noopener" style={{ color: "#7C3AED" }}>VIA officiel</a>.
  </div>
);

const TestHero = ({ onStart }) => (
  <section style={{ paddingTop: 70, paddingBottom: 80, position: "relative", overflow: "hidden" }}>
    <Pill color="rgba(124,58,237,.45)" w={260} h={130} style={{ position: "absolute", top: 110, right: -60, borderRadius: 999 }} />
    <Half color="rgba(217,119,6,.18)" side="t" w={300} h={120} style={{ position: "absolute", bottom: -10, left: -40 }} />
    <div className="shell" style={{ position: "relative", display: "grid", gridTemplateColumns: "1.1fr 1fr", gap: 60, alignItems: "center" }}>
      <div>
        <span className="chip" style={{ background: "rgba(124,58,237,.15)", color: "#7C3AED" }}>
          <Icon.spark style={{ width: 14, height: 14 }} /> Psychologie positive · Peterson & Seligman
        </span>
        <h1 style={{ marginTop: 22, marginBottom: 22 }}>
          Tes <span style={{ background: "linear-gradient(180deg, transparent 60%, #F5EB3F 60%)", paddingInline: 4 }}>5 forces</span> de caractère
        </h1>
        <p style={{ fontSize: 18, color: "var(--c-ink-2)", maxWidth: 540, marginBottom: 28 }}>
          Le test <strong>VIA Strengths</strong> mesure 24 forces universelles, organisées en 6 vertus. Validé sur 10M+ d'utilisateurs depuis 2004. Au lieu de chercher tes défauts, on identifie ce qui te rend toi et comment t'appuyer dessus. <strong>6 minutes, 24 questions</strong>.
        </p>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 22 }}>
          <button className="btn btn-orange btn-lg btn-arrow" onClick={onStart}>Démarrer le test</button>
          <a href="#methode" className="btn btn-ghost btn-lg"><Icon.play /> Comment ça marche</a>
        </div>
        <div style={{ display: "flex", gap: 22, fontSize: 13, color: "var(--c-muted)", flexWrap: "wrap" }}>
          <span><Icon.shield style={{ width: 13, height: 13, verticalAlign: "-2px", marginRight: 4 }} /> Données privées · stockées en local</span>
          <span>⏱ 6 min · 24 questions</span>
          <span>📋 VIA Peterson & Seligman 2004</span>
        </div>
      </div>
      <div style={{ position: "relative" }}>
        <div style={{ background: "white", borderRadius: 24, padding: 28, boxShadow: "var(--shadow-md)", border: "1px solid var(--c-line)" }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: "#7C3AED", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 14 }}>6 vertus mesurées</div>
          {Object.keys(VIRTUE_META).map((v, i, arr) => (
            <div key={v} style={{ display: "flex", alignItems: "center", gap: 14, padding: "10px 0", borderBottom: i < arr.length - 1 ? "1px solid var(--c-line)" : "none" }}>
              <div style={{ width: 32, height: 32, borderRadius: 8, background: VIRTUE_META[v].c, color: "white", display: "grid", placeItems: "center", fontWeight: 700, fontSize: 12, fontFamily: "var(--font-display)" }}>{v[0]}</div>
              <div>
                <div style={{ fontWeight: 700, fontSize: 14, color: "var(--c-ink)" }}>{v}</div>
                <div style={{ fontSize: 12.5, color: "var(--c-muted)" }}>{VIRTUE_META[v].desc}</div>
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
      <h2 style={{ textAlign: "center", marginBottom: 16 }}>Forces signatures, pas forces parfaites</h2>
      <p style={{ textAlign: "center", fontSize: 16, color: "var(--c-muted)", marginBottom: 40, maxWidth: 720, margin: "0 auto 40px" }}>
        Tes 5 forces signatures sont celles que tu utilises naturellement et avec énergie. La recherche montre qu'utiliser ses forces signatures au quotidien augmente bien-être et performance, plus que de corriger ses faiblesses.
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 18 }}>
        {[
          { t: "Identifie", d: "On classe tes 24 forces du score le plus haut au plus bas." },
          { t: "Valorise", d: "Tes 5 forces signatures = ce sur quoi t'appuyer pour orientation, projets, métiers." },
          { t: "Éveille", d: "Tes 5 zones de développement = un terrain de jeu, pas une honte." },
        ].map((s, i) => (
          <div key={i} style={{ background: "white", borderRadius: 18, padding: 22, border: "1px solid var(--c-line)" }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: "#7C3AED", marginBottom: 8 }}>Étape {i+1}</div>
            <div style={{ fontWeight: 700, fontSize: 16, color: "var(--c-ink)", marginBottom: 8 }}>{s.t}</div>
            <p style={{ fontSize: 13.5, color: "var(--c-muted)", lineHeight: 1.55 }}>{s.d}</p>
          </div>
        ))}
      </div>
    </div>
  </section>
);

const Results = ({ results, onRestart }) => {
  const { top5, bottom5, virtueScores, dominantVirtue } = results;
  return (
    <section style={{ paddingTop: 60, paddingBottom: 30 }}>
      <div className="shell" style={{ maxWidth: 820 }}>
        <DisclaimerBanner />

        {/* Hero · vertu dominante */}
        <div style={{ textAlign: "center", marginBottom: 50 }}>
          <span className="chip" style={{ background: "rgba(124,58,237,.15)", color: "#7C3AED" }}>
            <Icon.spark style={{ width: 14, height: 14 }} /> Tes forces de caractère
          </span>
          <h1 style={{ marginTop: 20, marginBottom: 12, fontSize: 38, color: "var(--c-ink)", fontFamily: "var(--font-display)", letterSpacing: "-0.02em" }}>
            Vertu dominante : <span style={{ color: VIRTUE_META[dominantVirtue].c }}>{dominantVirtue}</span>
          </h1>
          <p style={{ fontSize: 16, color: "var(--c-ink-2)", maxWidth: 600, margin: "0 auto", lineHeight: 1.6 }}>{VIRTUE_META[dominantVirtue].desc}</p>
        </div>

        {/* Top 5 signature strengths */}
        <div style={{ background: "white", borderRadius: 20, padding: 32, border: "1px solid var(--c-line)", marginBottom: 24 }}>
          <h2 style={{ fontSize: 24, marginBottom: 8, color: "var(--c-ink)" }}>Tes 5 forces signatures</h2>
          <p style={{ fontSize: 14, color: "var(--c-muted)", marginBottom: 24 }}>Ce sur quoi t'appuyer dans ton orientation, tes projets, tes choix.</p>
          <div style={{ display: "grid", gap: 12 }}>
            {top5.map((s, i) => (
              <div key={s.code} style={{ display: "flex", alignItems: "center", gap: 14, padding: "14px 18px", background: "var(--c-cream-light, #FAF6EE)", borderRadius: 12, border: "1px solid var(--c-line)" }}>
                <div style={{ flexShrink: 0, width: 32, fontWeight: 700, fontSize: 20, fontFamily: "var(--font-display)", color: "var(--c-muted)" }}>#{i+1}</div>
                <div style={{ fontSize: 28 }}>{s.icon}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: 16, color: "var(--c-ink)" }}>{s.label}</div>
                  <div style={{ fontSize: 12.5, color: "var(--c-muted)" }}>Vertu · {s.virtue}</div>
                </div>
                <div style={{ fontFamily: "var(--font-num)", fontWeight: 700, fontSize: 20, color: s.color }}>{s.score}<span style={{ fontSize: 12, color: "var(--c-muted)" }}>/5</span></div>
              </div>
            ))}
          </div>
        </div>

        {/* 6 vertus · radar */}
        <div style={{ background: "white", borderRadius: 20, padding: 32, border: "1px solid var(--c-line)", marginBottom: 24 }}>
          <h2 style={{ fontSize: 22, marginBottom: 24, color: "var(--c-ink)" }}>Ta cartographie des 6 vertus</h2>
          <div style={{ display: "grid", gap: 14 }}>
            {Object.keys(VIRTUE_META).map((v) => (
              <div key={v}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 6 }}>
                  <strong style={{ color: "var(--c-ink)", fontSize: 14.5 }}>{v}</strong>
                  <span style={{ fontFamily: "var(--font-num)", fontWeight: 700, fontSize: 16, color: VIRTUE_META[v].c }}>{virtueScores[v]}<span style={{ fontSize: 11, color: "var(--c-muted)" }}>/100</span></span>
                </div>
                <div style={{ height: 8, background: "var(--c-cream)", borderRadius: 4, overflow: "hidden" }}>
                  <div style={{ width: `${virtueScores[v]}%`, height: "100%", background: VIRTUE_META[v].c, transition: "width .8s cubic-bezier(.2,.8,.2,1)" }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom 5 · zones de développement */}
        <div style={{ background: "linear-gradient(160deg, #FFF7ED, #FAF6EE)", borderRadius: 20, padding: 32, border: "1px solid #FED7AA", marginBottom: 24 }}>
          <h2 style={{ fontSize: 24, marginBottom: 8, color: "var(--c-ink)" }}>5 forces à éveiller</h2>
          <p style={{ fontSize: 14, color: "var(--c-muted)", marginBottom: 24 }}>Pas des défauts, des forces qui dorment. En choisir UNE à pratiquer 30 jours change beaucoup plus que de tout vouloir améliorer.</p>
          <div style={{ display: "grid", gap: 10 }}>
            {bottom5.map((s) => (
              <div key={s.code} style={{ display: "flex", alignItems: "center", gap: 14, padding: "12px 16px", background: "white", borderRadius: 12, border: "1px solid var(--c-line)" }}>
                <div style={{ fontSize: 22, opacity: 0.6 }}>{s.icon}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, fontSize: 15, color: "var(--c-ink)" }}>{s.label}</div>
                  <div style={{ fontSize: 12, color: "var(--c-muted)" }}>{s.virtue}</div>
                </div>
                <div style={{ fontFamily: "var(--font-num)", fontWeight: 600, fontSize: 15, color: "var(--c-muted)" }}>{s.score}/5</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

const ComparePanel = ({ parentName, parentAnswers, teenAnswers }) => {
  const parentRes = computeResults(parentAnswers);
  const teenRes = computeResults(teenAnswers);
  const sharedTop = parentRes.top5.filter(s =>
    teenRes.top5.some(t => t.code === s.code)
  );
  return (
    <div style={{ background: "white", borderRadius: 20, padding: 28, border: "1px solid var(--c-line)", marginBottom: 30 }}>
      <h2 style={{ fontSize: 20, marginBottom: 18 }}>Comparaison avec {parentName}</h2>
      <p style={{ fontSize: 14, color: "var(--c-muted)", marginBottom: 16 }}>
        Forces signatures partagées : <strong style={{ color: "#7C3AED" }}>{sharedTop.length}</strong> sur 5.
      </p>
      {sharedTop.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {sharedTop.map(s => (
            <span key={s.code} style={{ background: "var(--c-cream-light, #FAF6EE)", padding: "6px 12px", borderRadius: 99, fontSize: 13, fontWeight: 600, color: s.color }}>
              {s.icon} {s.label}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

const buildEmailSummary = (results) => {
  const { top5, bottom5, virtueScores, dominantVirtue } = results;
  let summary = `VIA Strengths · vertu dominante : ${dominantVirtue}\n\n`;
  summary += `5 forces signatures :\n`;
  top5.forEach((s, i) => { summary += `${i+1}. ${s.label} (${s.virtue}) · ${s.score}/5\n`; });
  summary += `\n5 forces à éveiller :\n`;
  bottom5.forEach((s, i) => { summary += `${i+1}. ${s.label} (${s.virtue}) · ${s.score}/5\n`; });
  summary += `\nVertus (0-100) :\n`;
  Object.keys(virtueScores).forEach((v) => { summary += `- ${v} : ${virtueScores[v]}\n`; });
  return summary;
};

const TestApp = () => {
  const [mode, setMode] = React.useState("landing");
  const [persona, setPersona] = React.useState(null);
  const [answers, setAnswers] = React.useState([]);
  const [results, setResults] = React.useState(null);
  const PARENT_PREDICT = null;

  const goPicker = () => setMode("picker");
  const pickPersona = (p) => { setPersona(p); setMode("test"); };
  const exitTest = () => setMode("landing");
  const onComplete = (ans) => {
    setAnswers(ans);
    setResults(computeResults(ans));
    setMode("results");
    try { window.localStorage.setItem("proxxie.tests.via", "done"); } catch(e){}
  };
  const restart = () => { setAnswers([]); setResults(null); setMode("landing"); };

  const effectivePersona = persona;
  const storageKeyEffective = persona === "predict" ? STORAGE_KEY + ":predict" : STORAGE_KEY;
  return (
    <>
      <ProxxieNav />
      {mode === "landing" && (<><TestHero onStart={goPicker} /><HowItWorks /></>)}
      {mode === "picker" && <PersonaIntro testName="VIA Strengths" accent="#7C3AED" comingFromPredict={null} onPick={pickPersona} />}
      {mode === "compare-intro" && <PersonaIntro testName="VIA Strengths" accent="#7C3AED" comingFromPredict={PARENT_PREDICT} onPick={pickPersona} />}
      {mode === "test" && (
        <>
          {persona === "predict" && (<div style={{ background: "#F5EB3F", color: "#0A0E2C", padding: "10px 16px", textAlign: "center", fontSize: 13, fontWeight: 600 }}>🎯 Mode prédiction · Répondez comme vous pensez que votre ado répondrait</div>)}
          <TestFlowEngine questions={QUESTIONS} storageKey={storageKeyEffective} getTypeMeta={getTypeMeta} onExit={exitTest} onComplete={onComplete} />
        </>
      )}
      {mode === "results" && results && (
        <>
          {effectivePersona === "self_compare" && PARENT_PREDICT && (<section style={{ paddingTop: 40, paddingBottom: 0 }}><div className="shell" style={{ maxWidth: 820 }}><ComparePanel parentName={PARENT_PREDICT.n} parentAnswers={PARENT_PREDICT.a} teenAnswers={answers} /></div></section>)}
          {persona === "predict" && (<section style={{ paddingTop: 40, paddingBottom: 0 }}><div className="shell" style={{ maxWidth: 820 }}><ShareLinkPanel testCode="VIA" accent="#7C3AED" answers={answers} defaultName="" onSkip={() => {}} /></div></section>)}
          <EmailResultsActions testCode="VIA" testName="VIA Strengths (forces de caractère)" accent="#7C3AED" summary={buildEmailSummary(results)} answers={answers} />
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
        'const __PROXXIE_TEST_ID__ = "via";',
        src,
        count=1,
    )
    boundary_match = re.search(
        r"(/\*\s*Test Proxxie [^/]*\*/\s*\n)?const QUESTIONS\s*=", src
    )
    if not boundary_match:
        return f"{target_path.name}: boundary introuvable"
    new_src = src[: boundary_match.start()] + VIA_BLOCK

    nd = new_src.encode("utf-8")
    if comp:
        nd = gzip.compress(nd)
    entry["data"] = base64.b64encode(nd).decode("ascii")
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[: m.start(2)] + new_manifest_json + html[m.end(2) :]

    new_html = re.sub(
        r"<title[^>]*>[^<]*</title>",
        "<title>Test VIA Strengths, Proxxie</title>",
        new_html,
        count=1,
    )
    new_html = re.sub(
        r"<title[^>]*>[^<]*<\\/title>",
        "<title>Test VIA Strengths, Proxxie<\\/title>",
        new_html,
        count=1,
    )

    target_path.write_text(new_html, encoding="utf-8")
    return f"{target_path.name}: built (asset {uuid[:8]}, src {len(src)} → {len(new_src)})"


if __name__ == "__main__":
    print(build(SOURCE, TARGET))
    print(build(SOURCE, TARGET_LOWER))

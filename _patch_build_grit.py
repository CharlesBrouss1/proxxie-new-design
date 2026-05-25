#!/usr/bin/env python3
"""Construit Proxxie Test Grit.html depuis Proxxie Test Anxiete.html.

Pattern identique à _patch_build_phq9.py · clone + swap JSX test-spécifique.

Source psychométrique : Grit-S (Duckworth & Quinn 2009), 8 items, Likert 1-5.
4 items inversés (CI), 4 items directs (PE). Score = moyenne sur 5.
Pas un screening clinique, pas de disclaimer médical.
"""
import re, json, base64, gzip, pathlib, shutil

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
          <div style={{ fontFamily: "var(--font-display)", fontSize: 80, fontWeight: 700, lineHeight: 1, marginBottom: 8 }}>{total} / 5</div>
          <div style={{ fontSize: 14, opacity: 0.92, marginBottom: 16 }}>
            <strong>Profil : {profile}</strong> · CI {ciAvg} · PE {peAvg}
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

const ComparePanel = ({ parentName, parentAnswers, teenAnswers }) => {
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
          {gap >= 1.0
            ? "Écart significatif. Vous surestimez ou sous-estimez nettement la persévérance de votre ado. Conversation prioritaire pour calibrer."
            : gap >= 0.5
              ? "Écart modéré. À discuter ensemble."
              : "Perception alignée."}
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
          {effectivePersona === "self_compare" && PARENT_PREDICT && (<section style={{ paddingTop: 40, paddingBottom: 0 }}><div className="shell" style={{ maxWidth: 820 }}><ComparePanel parentName={PARENT_PREDICT.n} parentAnswers={PARENT_PREDICT.a} teenAnswers={answers} /></div></section>)}
          {persona === "predict" && (<section style={{ paddingTop: 40, paddingBottom: 0 }}><div className="shell" style={{ maxWidth: 820 }}><ShareLinkPanel testCode="Grit" accent="#6B46C1" answers={answers} defaultName="" onSkip={() => {}} /></div></section>)}
          <EmailResultsActions testCode="Grit" testName="Grit (Duckworth)" accent="#6B46C1" summary={buildEmailSummary(results)} answers={answers} />
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
    new_src = src[:boundary_match.start()] + GRIT_BLOCK

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

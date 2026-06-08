#!/usr/bin/env python3
"""Construit Proxxie Test BRIEF.html depuis Proxxie Test Anxiete.html.

Test des fonctions exécutives à l'ado, inspiré du BDEFS-CA (Barkley Deficits
in Executive Functioning Scale, version courte 20 items, 2012).

4 sous-échelles · 5 items chacune :
- ORG · Auto-organisation et résolution de problèmes
- TIME · Gestion du temps
- EMO · Auto-régulation émotionnelle
- WM · Mémoire de travail et concentration

Likert 1-5 (toujours · souvent · parfois · rarement · jamais)
Score : moyenne par sous-échelle + global.

Pas un diagnostic. Outil de psychologie cognitive grand public.
"""
import re, json, base64, gzip, pathlib, shutil
import _bridge_common

REPO = pathlib.Path(__file__).parent
SOURCE = REPO / "Proxxie Test Anxiete.html"
TARGET = REPO / "Proxxie Test BRIEF.html"
TARGET_LOWER = REPO / "test-brief.html"
ASSET_UUID_PREFIX = "61feca88"

BRIEF_BLOCK = r'''/* Test Proxxie BRIEF, fonctions exécutives (inspiré BDEFS-CA Barkley 2012)
   20 items en 4 sous-échelles, Likert 5 points. Outil de psychologie cognitive
   grand public · pas un diagnostic. */

const QUESTIONS = [
  // ORG · Auto-organisation et résolution de problèmes (5 items)
  { type: "ORG", q: "J'ai du mal à hiérarchiser mes tâches quand j'ai plusieurs choses à faire." },
  { type: "ORG", q: "Mon bureau, ma chambre ou mon sac sont souvent en désordre." },
  { type: "ORG", q: "Je commence beaucoup de projets que je ne finis pas." },
  { type: "ORG", q: "Quand un problème surgit, j'ai du mal à trouver plusieurs solutions différentes." },
  { type: "ORG", q: "Je perds des objets importants (clés, téléphone, papiers d'école)." },
  // TIME · Gestion du temps (5 items)
  { type: "TIME", q: "Je sous-estime le temps qu'une tâche va me prendre." },
  { type: "TIME", q: "Je suis souvent en retard à mes rendez-vous ou aux cours." },
  { type: "TIME", q: "Je procrastine sur les choses importantes mais non urgentes." },
  { type: "TIME", q: "Je gère mal mon temps pendant un contrôle ou un examen." },
  { type: "TIME", q: "Je remets les devoirs à la dernière minute." },
  // EMO · Auto-régulation émotionnelle (5 items)
  { type: "EMO", q: "Quand je suis énervé(e), j'ai du mal à me calmer rapidement." },
  { type: "EMO", q: "Je réagis plus fort que les autres aux petites frustrations." },
  { type: "EMO", q: "Mon humeur change brutalement plusieurs fois dans la même journée." },
  { type: "EMO", q: "Je dis des choses que je regrette quand je suis énervé(e)." },
  { type: "EMO", q: "Je suis souvent ramené(e) vers des émotions négatives sans raison claire." },
  // WM · Mémoire de travail et concentration (5 items)
  { type: "WM", q: "J'oublie ce que je devais faire dans la minute qui suit." },
  { type: "WM", q: "Je perds le fil quand quelqu'un me donne plusieurs instructions à la suite." },
  { type: "WM", q: "J'ai du mal à rester concentré(e) plus de 20 minutes sur une tâche pas passionnante." },
  { type: "WM", q: "Je relis le même paragraphe plusieurs fois sans en retenir grand-chose." },
  { type: "WM", q: "Je suis facilement distrait(e) par mon téléphone ou par les bruits autour." },
];

const TYPE_META = {
  ORG:  { l: "Auto-organisation",         c: "#0EA5E9", short: "Hiérarchiser, ranger, résoudre" },
  TIME: { l: "Gestion du temps",          c: "#06B6D4", short: "Planifier, anticiper, respecter" },
  EMO:  { l: "Auto-régulation émotion",   c: "#8B5CF6", short: "Calmer ses pics, lisser l'humeur" },
  WM:   { l: "Mémoire de travail",        c: "#3B82F6", short: "Tenir une info, rester concentré" },
};
const STORAGE_KEY = "proxxie-brief-answers";

const getTypeMeta = (q) => ({ label: TYPE_META[q.type].l, color: TYPE_META[q.type].c });

const computeResults = (answers) => {
  // Échelle 1 (jamais) à 5 (toujours). Score = somme par sous-échelle (sur 25 max chacune).
  // Plus le score est élevé, plus la difficulté est marquée (sens inverse intuitif).
  const dims = { ORG: 0, TIME: 0, EMO: 0, WM: 0 };
  const counts = { ORG: 0, TIME: 0, EMO: 0, WM: 0 };
  QUESTIONS.forEach((q, idx) => {
    if (answers[idx] == null) return;
    dims[q.type] += answers[idx];
    counts[q.type]++;
  });
  const avgs = {};
  for (const k of Object.keys(dims)) {
    avgs[k] = counts[k] > 0 ? Math.round((dims[k] / counts[k]) * 100) / 100 : 0;
  }
  const total = Math.round(((avgs.ORG + avgs.TIME + avgs.EMO + avgs.WM) / 4) * 100) / 100;
  // Niveau global · plus bas = plus fluide. Seuils empiriques pour ado.
  let level = "fluide";
  if (total >= 3.8) level = "très difficile";
  else if (total >= 3.0) level = "difficile";
  else if (total >= 2.2) level = "à muscler";
  // Identifier la dimension la plus problématique
  const sortedDesc = Object.entries(avgs).sort((a, b) => b[1] - a[1]);
  const weakest = sortedDesc[0][0];
  const strongest = sortedDesc[sortedDesc.length - 1][0];
  return { avgs, total, level, weakest, strongest };
};

const DisclaimerBanner = () => (
  <div style={{
    background: "#E0F2FE", borderLeft: "4px solid #0EA5E9",
    padding: "14px 20px", marginBottom: 30, borderRadius: 8,
    fontSize: 13.5, color: "#0A0E2C", lineHeight: 1.55,
  }}>
    <strong>ℹ️ Les fonctions exécutives se travaillent.</strong> Inspiré du BDEFS-CA de Russell Barkley (2012). Mesure 4 capacités cognitives qui prédisent l'autonomie scolaire et professionnelle. Pas un diagnostic clinique. Pour un bilan complet, consulter un neuropsychologue.
  </div>
);

const TestHero = ({ onStart }) => (
  <section style={{ paddingTop: 70, paddingBottom: 80, position: "relative", overflow: "hidden" }}>
    <Pill color="rgba(245,235,63,.5)" w={260} h={130} style={{ position: "absolute", top: 110, right: -60, borderRadius: 999 }} />
    <Half color="rgba(14,165,233,.18)" side="t" w={300} h={120} style={{ position: "absolute", bottom: -10, left: -40 }} />
    <div className="shell" style={{ position: "relative", display: "grid", gridTemplateColumns: "1.1fr 1fr", gap: 60, alignItems: "center" }}>
      <div>
        <span className="chip" style={{ background: "rgba(14,165,233,.15)", color: "#0EA5E9" }}>
          <Icon.spark style={{ width: 14, height: 14 }} /> Fonctions exécutives · Barkley
        </span>
        <h1 style={{ marginTop: 22, marginBottom: 22 }}>
          Test <span style={{ background: "linear-gradient(180deg, transparent 60%, #F5EB3F 60%)", paddingInline: 4 }}>Fonctions exécutives</span> · ce qui se passe entre vouloir et faire.
        </h1>
        <p style={{ fontSize: 18, color: "var(--c-ink-2)", maxWidth: 520, marginBottom: 28 }}>
          Inspiré du <strong>BDEFS-CA</strong> (Barkley 2012). Mesure 4 muscles cognitifs qui prédisent l'autonomie scolaire et professionnelle : organisation, gestion du temps, régulation émotionnelle, mémoire de travail.
        </p>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 22 }}>
          <button className="btn btn-orange btn-lg btn-arrow" onClick={onStart}>Démarrer le test</button>
          <a href="#methode" className="btn btn-ghost btn-lg"><Icon.play /> Comment ça marche</a>
        </div>
        <div style={{ display: "flex", gap: 22, fontSize: 13, color: "var(--c-muted)", flexWrap: "wrap" }}>
          <span><Icon.shield style={{ width: 13, height: 13, verticalAlign: "-2px", marginRight: 4 }} /> Données privées · stockées en local</span>
          <span>⏱ 6 min · 20 questions</span>
          <span>📋 BDEFS-CA (Barkley 2012)</span>
        </div>
      </div>
      <div style={{ position: "relative" }}>
        <div style={{ background: "white", borderRadius: 24, padding: 28, boxShadow: "var(--shadow-md)", border: "1px solid var(--c-line)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 18 }}>
            <span style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--c-muted)" }}>Question 7 / 20</span>
            <span style={{ fontSize: 12, color: "#0EA5E9", fontWeight: 600 }}>● Gestion du temps</span>
          </div>
          <div style={{ height: 4, background: "var(--c-cream)", borderRadius: 2, marginBottom: 24, overflow: "hidden" }}>
            <div style={{ width: "35%", height: "100%", background: "#0EA5E9" }} />
          </div>
          <h3 style={{ fontSize: 19, lineHeight: 1.35, fontWeight: 600, marginBottom: 22, fontFamily: "var(--font-display)", letterSpacing: "-0.02em" }}>
            "Je sous-estime le temps qu'une tâche va me prendre."
          </h3>
          <div style={{ display: "flex", gap: 8, justifyContent: "space-between" }}>
            {["Jamais", "Rarement", "Parfois", "Souvent", "Toujours"].map((label, n) => (
              <div key={n} style={{
                flex: 1, padding: "10px 4px", borderRadius: 10, textAlign: "center",
                background: n === 3 ? "linear-gradient(160deg, #0EA5E9, #0369A1)" : "var(--c-cream)",
                color: n === 3 ? "white" : "var(--c-ink)",
                fontWeight: 600, fontSize: 9.5,
                border: n === 3 ? "none" : "1px solid var(--c-line)",
              }}>{label}</div>
            ))}
          </div>
        </div>
        <div style={{ position: "absolute", bottom: -18, right: -18, background: "#0A0E2C", color: "white", padding: "12px 16px", borderRadius: 14, fontSize: 12, display: "flex", alignItems: "center", gap: 10, boxShadow: "var(--shadow-md)" }}>
          <Icon.brain style={{ color: "#F5EB3F" }} /> Référence Barkley · 30+ ans
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
        <h2 style={{ marginTop: 14 }}>4 muscles cognitifs, 20 questions.</h2>
        <p style={{ fontSize: 17, color: "var(--c-ink-2)", marginTop: 16 }}>
          Russell Barkley a passé 40 ans à étudier les fonctions exécutives chez l'enfant et l'ado. Le BDEFS-CA mesure 4 dimensions qui prédisent autonomie, réussite scolaire et professionnelle, parfois mieux que le QI lui-même.
        </p>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, maxWidth: 920, margin: "0 auto" }}>
        {[
          { n: "1", t: "20 questions", d: "5 par dimension. Échelle 1 (jamais) à 5 (toujours). 6 minutes." },
          { n: "2", t: "Profil 4 axes", d: "Score par dimension + global. La dimension la plus haute (= la plus difficile) est ton chantier." },
          { n: "3", t: "Pistes concrètes", d: "3 leviers par dimension à travailler sur 30 jours. Effets mesurables." },
        ].map((s) => (
          <div key={s.n} style={{ background: "var(--c-cream-light)", padding: 22, borderRadius: 16, border: "1px solid var(--c-line)" }}>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: "linear-gradient(135deg, #0EA5E9, #0369A1)", color: "white", display: "grid", placeItems: "center", fontWeight: 700, fontFamily: "var(--font-num)", marginBottom: 14 }}>{s.n}</div>
            <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 6 }}>{s.t}</div>
            <p style={{ fontSize: 13.5, color: "var(--c-muted)", lineHeight: 1.55 }}>{s.d}</p>
          </div>
        ))}
      </div>
    </div>
  </section>
);

const LEVEL_COPY = {
  "fluide": { color: "#22A06B", body: "Fonctions exécutives fluides. Outillage cognitif solide pour autonomie scolaire et future vie pro. Aucune dimension n'est un frein." },
  "à muscler": { color: "#0EA5E9", body: "Fonctions exécutives dans la moyenne, avec 1-2 dimensions à muscler. Marge de progression nette en 30-60 jours d'exercices ciblés." },
  "difficile": { color: "#FD6936", body: "Plusieurs dimensions exécutives sont des freins concrets. Impacte études, organisation, autonomie. Travail dédié recommandé + faire les tests TDAH (ASRS) si pas déjà fait." },
  "très difficile": { color: "#C62828", body: "Fonctions exécutives très en difficulté. Score qui justifie une évaluation neuropsy (bilan complet WISC + Stroop + Test Tour de Londres) pour identifier la cause et adapter l'orientation." },
};

// Verdict par dimension sur l'échelle inversée (bas = fluide, haut = en difficulté).
const DIM_VERDICT = (val) => {
  if (val < 2.0) return { label: "Point fort",      color: "#22A06B" };
  if (val < 3.0) return { label: "Plutôt à l'aise", color: "#0EA5E9" };
  if (val < 3.8) return { label: "À muscler",       color: "#FD6936" };
  return            { label: "En difficulté",   color: "#C62828" };
};

const DIMENSION_TIPS = {
  ORG: ["Routine du dimanche soir : lister les 3 tâches majeures de la semaine sur un papier visible.", "Méthode Bullet Journal · 10 min/jour pour ranger ses idées.", "Règle des 2 min : si une tâche prend moins de 2 min, la faire immédiatement, pas la noter."],
  TIME: ["Estimer le temps de chaque devoir × 1,5 (les ados sous-estiment systématiquement).", "Time-blocking : bloquer dans Google Calendar les créneaux de travail comme des RDV.", "Technique Pomodoro : 25 min focus + 5 min break, max 4 cycles puis vraie pause."],
  EMO: ["STOP technique : Stop · Take breath · Observe · Proceed. Avant de réagir, 3 respirations.", "Journal d'émotion 1x/jour : 1 phrase sur l'émotion + sa cause. Décharge mentale.", "Sport régulier (3x/semaine, 30 min) : impact direct sur la régulation émotionnelle."],
  WM: ["Pas de multitâche : 1 chose à la fois, téléphone hors de portée.", "Externaliser : tout ce qui doit être retenu va sur papier ou dans Notes.", "Sommeil 8h+ : la mémoire de travail s'effondre dès 6h-7h de sommeil."],
};

const Results = ({ results, onRestart }) => {
  const { avgs, total, level, weakest, strongest } = results;
  const copy = LEVEL_COPY[level];
  return (
    <section style={{ paddingTop: 60, paddingBottom: 100 }}>
      <div className="shell" style={{ maxWidth: 820 }}>
        <DisclaimerBanner />
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <span className="chip" style={{ background: "rgba(34,160,107,.15)", color: "#22A06B" }}>
            <Icon.check /> Test terminé · 20 réponses analysées
          </span>
          <h1 style={{ marginTop: 18, fontSize: 36 }}>
            Fonctions <span style={{ background: "linear-gradient(180deg, transparent 60%, " + copy.color + "55 60%)", paddingInline: 8 }}>{level}</span>
          </h1>
        </div>

        <div style={{
          background: "linear-gradient(160deg, " + copy.color + ", #0369A1)",
          color: "white", borderRadius: 24, padding: "32px 28px", marginBottom: 24, textAlign: "center",
        }}>
          <div style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", opacity: 0.85, marginBottom: 8 }}>Score moyen fonctions exécutives</div>
          <div style={{ fontFamily: "var(--font-display)", fontSize: 80, fontWeight: 700, lineHeight: 1, marginBottom: 12 }}>{total} / 5</div>
          <div style={{ maxWidth: 360, margin: "0 auto 10px" }}>
            <div style={{ height: 6, borderRadius: 3, background: "linear-gradient(90deg,#22A06B,#0EA5E9,#FD6936,#C62828)" }} />
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, opacity: 0.9, marginTop: 5 }}>
              <span>1 · tout fluide</span><span>5 · en difficulté</span>
            </div>
          </div>
          <div style={{ fontSize: 14, opacity: 0.95, marginBottom: 16 }}>Échelle inversée : <strong>plus le score est bas, mieux c'est</strong>.</div>
          <p style={{ fontSize: 15, maxWidth: 540, margin: "0 auto", lineHeight: 1.55 }}>{copy.body}</p>
        </div>

        <div style={{ background: "white", borderRadius: 20, padding: 24, border: "1px solid var(--c-line)", marginBottom: 24 }}>
          <h2 style={{ fontSize: 18, marginBottom: 4 }}>Détail par dimension</h2>
          <div style={{ fontSize: 12.5, color: "var(--c-muted)", marginBottom: 18, lineHeight: 1.5 }}>
            Barre courte et verte = tu es à l'aise. Barre longue et rouge = c'est un point à travailler.
          </div>
          {Object.entries(avgs).map(([dim, val]) => {
            const v = DIM_VERDICT(val);
            return (
            <div key={dim} style={{ marginBottom: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6, fontSize: 13, gap: 10, flexWrap: "wrap" }}>
                <span style={{ fontWeight: 600 }}>{TYPE_META[dim].l}</span>
                <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: v.color, background: v.color + "1A", padding: "2px 9px", borderRadius: 99 }}>{v.label}</span>
                  <span style={{ fontFamily: "var(--font-num)", fontWeight: 700, color: v.color }}>{val} / 5</span>
                </span>
              </div>
              <div style={{ height: 8, background: "var(--c-cream)", borderRadius: 4, overflow: "hidden" }}>
                <div style={{ width: `${(val/5)*100}%`, height: "100%", background: v.color }} />
              </div>
              <div style={{ fontSize: 12, color: "var(--c-muted)", marginTop: 4 }}>{TYPE_META[dim].short}</div>
            </div>
            );
          })}
        </div>

        <div style={{ background: "#0A0E2C", color: "white", borderRadius: 20, padding: "32px 28px", marginBottom: 24 }}>
          <h2 style={{ color: "white", fontSize: 22, marginBottom: 6 }}>🎯 Chantier prioritaire : {TYPE_META[weakest].l}</h2>
          <p style={{ fontSize: 14, opacity: 0.85, marginBottom: 18 }}>3 exercices concrets à faire sur 30 jours pour cette dimension.</p>
          <ul style={{ paddingLeft: 22, marginBottom: 18, opacity: 0.92, lineHeight: 1.7, fontSize: 14.5 }}>
            {(DIMENSION_TIPS[weakest] || []).map((e, i) => <li key={i} style={{ marginBottom: 6 }}>{e}</li>)}
          </ul>
          <a href="https://calendly.com/proxxie/entretien" target="_blank" rel="noopener noreferrer" className="btn btn-orange">
            30 min avec Charles pour bâtir un plan d'attaque
          </a>
        </div>

        <div style={{ background: "var(--c-cream-light)", borderRadius: 20, padding: 24, border: "1px solid var(--c-line)" }}>
          <h3 style={{ fontSize: 16, marginBottom: 10 }}>📍 Les fonctions exécutives, c'est souvent intriqué</h3>
          <p style={{ fontSize: 13.5, color: "var(--c-muted)", lineHeight: 1.55, marginBottom: 14 }}>
            Score élevé = à creuser. Faire le test TDAH (ASRS) qui est corrélé. Ou consulter un neuropsy pour un bilan complet.
          </p>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <a href="Proxxie Test TDAH.html" style={{ background: "white", padding: "10px 14px", borderRadius: 99, fontSize: 13, fontWeight: 600, color: "#FD6936", border: "1px solid var(--c-line)", textDecoration: "none" }}>TDAH</a>
            <a href="Proxxie Test.html" style={{ background: "white", padding: "10px 14px", borderRadius: 99, fontSize: 13, fontWeight: 600, color: "#1320CE", border: "1px solid var(--c-line)", textDecoration: "none" }}>OCEAN-X</a>
            <a href="Proxxie Test Grit.html" style={{ background: "white", padding: "10px 14px", borderRadius: 99, fontSize: 13, fontWeight: 600, color: "#6B46C1", border: "1px solid var(--c-line)", textDecoration: "none" }}>Grit</a>
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
      <div style={{ background: "linear-gradient(160deg, #0EA5E9, #0369A1)", color: "white", borderRadius: 24, padding: "32px 28px", marginBottom: 24, textAlign: "center" }}>
        <div style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", opacity: 0.85, marginBottom: 8 }}>Comparaison · Fonctions exécutives</div>
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
          {gap >= 1.0 ? "Écart significatif. Vos deux profils diffèrent nettement." : gap >= 0.5 ? "Écart modéré. À discuter ensemble." : "Profils alignés."}
        </p>
      </div>
    </div>
  );
};

const buildEmailSummary = (results) => {
  const { avgs, total, level, weakest } = results;
  return "Test Fonctions exécutives (BDEFS-CA Barkley)\nScore moyen : " + total + "/5, " + level + "\nDétail : Organisation " + avgs.ORG + " · Temps " + avgs.TIME + " · Émotion " + avgs.EMO + " · Mémoire de travail " + avgs.WM + "\nChantier prioritaire : " + TYPE_META[weakest].l;
};

const TestApp = () => {
  const PARENT_PREDICT = React.useMemo(() => readPredictHash(), []);
  const RESULTS_HASH = React.useMemo(() => readResultsHash(), []);
  const [persona, setPersona] = React.useState(null);
  const [mode, setMode] = React.useState(RESULTS_HASH ? "results" : (PARENT_PREDICT ? "compare-intro" : "landing"));
  const [results, setResults] = React.useState(RESULTS_HASH ? computeResults(RESULTS_HASH.a) : null);
  const [answers, setAnswers] = React.useState(RESULTS_HASH ? RESULTS_HASH.a : null);
  const goPicker = () => { setMode("picker"); window.scrollTo({ top: 0, behavior: "smooth" }); };
  const pickPersona = (p) => { setPersona(p); setMode("test"); window.scrollTo({ top: 0, behavior: "smooth" }); };
  const exitTest = () => { setMode(PARENT_PREDICT ? "compare-intro" : "landing"); setPersona(null); window.scrollTo({ top: 0, behavior: "smooth" }); };
  const onComplete = (ans) => { setAnswers(ans); setResults(computeResults(ans)); setMode("results"); window.scrollTo({ top: 0, behavior: "smooth" }); };
  const restart = () => { try { window.localStorage.removeItem(STORAGE_KEY); } catch (e) {} setResults(null); setAnswers(null); setMode("test"); window.scrollTo({ top: 0, behavior: "smooth" }); };
  const effectivePersona = PARENT_PREDICT ? "self_compare" : persona;
  const storageKeyEffective = effectivePersona === "predict" ? STORAGE_KEY + ":predict" : STORAGE_KEY;
  return (
    <>
      <ProxxieNav />
      {mode === "landing" && (<><TestHero onStart={goPicker} /><HowItWorks /></>)}
      {mode === "picker" && <PersonaIntro testName="Fonctions exécutives" accent="#0EA5E9" comingFromPredict={null} onPick={pickPersona} />}
      {mode === "compare-intro" && <PersonaIntro testName="Fonctions exécutives" accent="#0EA5E9" comingFromPredict={PARENT_PREDICT} onPick={pickPersona} />}
      {mode === "test" && (
        <>
          {persona === "predict" && (<div style={{ background: "#F5EB3F", color: "#0A0E2C", padding: "10px 16px", textAlign: "center", fontSize: 13, fontWeight: 600 }}>🎯 Mode prédiction · Répondez comme vous pensez que votre ado répondrait</div>)}
          <TestFlowEngine questions={QUESTIONS} storageKey={storageKeyEffective} getTypeMeta={getTypeMeta} onExit={exitTest} onComplete={onComplete} />
        </>
      )}
      {mode === "results" && results && (
        <>
          {effectivePersona === "self_compare" && PARENT_PREDICT && (<section style={{ paddingTop: 40, paddingBottom: 0 }}><div className="shell" style={{ maxWidth: 820 }}><ComparePanel peerLabel={PARENT_PREDICT.peerLabel} selfLabel={PARENT_PREDICT.selfLabel} parentAnswers={PARENT_PREDICT.a} teenAnswers={answers} /></div></section>)}
          {persona === "predict" && (<section style={{ paddingTop: 40, paddingBottom: 0 }}><div className="shell" style={{ maxWidth: 820 }}><ShareLinkPanel testCode="BRIEF" accent="#0EA5E9" answers={answers} defaultName="" onSkip={() => {}} /></div></section>)}
          <EmailResultsActions testCode="BRIEF" testName="Fonctions exécutives (BDEFS-CA)" accent="#0EA5E9" summary={buildEmailSummary(results)} answers={answers} />
          <Results results={results} onRestart={restart} />
        </>
      )}
      <Footer />
    </>
  );
};

ReactDOM.createRoot(document.getElementById("root")).render(<TestApp />);
'''


def build_brief(source_path: pathlib.Path, target_path: pathlib.Path) -> str:
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
    src = re.sub(r'const __PROXXIE_TEST_ID__\s*=\s*"[^"]*";', 'const __PROXXIE_TEST_ID__ = "brief";', src, count=1)
    boundary_match = re.search(r'(/\*\s*Test Proxxie Anxi[^/]*\*/\s*\n)?const QUESTIONS\s*=', src)
    if not boundary_match:
        return f"{target_path.name}: boundary introuvable"
    new_src = _bridge_common.patch_persona_intro(src[:boundary_match.start()]) + _bridge_common.wire_bridge(BRIEF_BLOCK, "brief", "Proxxie%20Test%20BRIEF.html")
    nd = new_src.encode('utf-8')
    if comp:
        nd = gzip.compress(nd)
    entry['data'] = base64.b64encode(nd).decode('ascii')
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]
    new_html = re.sub(r'<title[^>]*>[^<]*</title>', '<title>Test Fonctions exécutives BDEFS-CA, Proxxie</title>', new_html, count=1)
    new_html = re.sub(r'<title[^>]*>[^<]*<\\/title>', '<title>Test Fonctions exécutives BDEFS-CA, Proxxie<\\/title>', new_html, count=1)
    target_path.write_text(new_html, encoding='utf-8')
    return f"{target_path.name}: built (asset {uuid[:8]}, src {len(src)} → {len(new_src)})"


if __name__ == "__main__":
    print(build_brief(SOURCE, TARGET))
    print(build_brief(SOURCE, TARGET_LOWER))

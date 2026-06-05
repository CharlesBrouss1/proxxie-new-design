#!/usr/bin/env python3
"""Construit Proxxie Test FuturProof.html (Score Future-Proof 2035) depuis
Proxxie Test Anxiete.html.

Test signature Proxxie · NON validé scientifiquement comme un instrument
psychométrique, mais construit sur 3 frameworks crédibles :
- WEF Future of Jobs Report 2025 (top 10 skills 2030)
- OECD Skills Outlook 2023
- McKinsey Global Institute · Generative AI and the future of work (2024)

Le test mesure 3 piliers (10 items chacun, Likert 1-5) :
- A · Capacités intrinsèquement humaines (créativité, empathie, éthique, leadership)
- B · Capacité à augmenter l'humain par l'IA (prompting, esprit critique, systémique, learn)
- C · Adaptation au monde post-IA (tolérance incertitude, identité fluide, réseau, entreprise)

Output : score global 0-100 + radar 3 piliers + 5 familles de métiers où ce
profil a un avantage durable.

Pattern identique à _patch_build_grit.py · clone Anxiete + swap JSX.
"""
import re, json, base64, gzip, pathlib, shutil

REPO = pathlib.Path(__file__).parent
SOURCE = REPO / "Proxxie Test Anxiete.html"
TARGET = REPO / "Proxxie Test FuturProof.html"
TARGET_LOWER = REPO / "test-futureproof.html"
ASSET_UUID_PREFIX = "61feca88"

FUTUREPROOF_BLOCK = r'''/* Test Proxxie Future-Proof 2035, score IA-résilience.
   Construit sur WEF Future of Jobs 2025 + OECD Skills Outlook 2023 +
   McKinsey GenAI & Future of Work 2024. Pas un instrument psychométrique
   validé · outil de positionnement orienté coaching. */

const QUESTIONS = [
  // === PILLAR A · Humain (10 items) ===
  // Créativité originale (3)
  { type: "A", q: "Quand je résous un problème, j'aime trouver une approche que personne n'a essayée." },
  { type: "A", q: "Je passe du temps à imaginer des choses qui n'existent pas encore : idées, histoires, projets." },
  { type: "A", q: "Quand une idée me vient, j'essaie de la concrétiser même si je ne suis pas sûr qu'elle marchera." },
  // Empathie / intelligence sociale (3)
  { type: "A", q: "Je remarque souvent quand quelqu'un autour de moi ne va pas, même s'il ne dit rien." },
  { type: "A", q: "Je peux adapter ma façon de parler selon la personne en face de moi." },
  { type: "A", q: "Je comprends ce qui motive les gens, même quand leurs choix me paraissent étranges." },
  // Jugement éthique (2)
  { type: "A", q: "Avant une décision importante, je pense à qui peut être impacté positivement ou négativement." },
  { type: "A", q: "Je peux changer d'avis quand quelqu'un me présente un argument que je n'avais pas considéré." },
  // Leadership émotionnel (2)
  { type: "A", q: "Quand un groupe est tendu, je sais comment apaiser la situation." },
  { type: "A", q: "Les gens viennent souvent me demander mon avis quand ils ont une décision à prendre." },

  // === PILLAR B · Augmentation par l'IA (10 items) ===
  // Prompting / cadrage (3)
  { type: "B", q: "Quand je pose une question à ChatGPT (ou un outil IA), je sais reformuler si la première réponse n'est pas bonne." },
  { type: "B", q: "Je sais découper un problème complexe en sous-questions plus simples." },
  { type: "B", q: "Je vois rapidement comment un outil IA peut m'aider sur une tâche concrète." },
  // Esprit critique sur les sorties IA (2)
  { type: "B", q: "Quand je lis une info, je me demande systématiquement d'où elle vient." },
  { type: "B", q: "Je sais repérer quand une réponse d'IA est fausse, inventée ou trop générique." },
  // Pensée systémique (3)
  { type: "B", q: "J'arrive à voir comment plusieurs éléments d'un problème sont liés entre eux." },
  { type: "B", q: "Je comprends rapidement pourquoi une décision dans un domaine a des conséquences dans un autre." },
  { type: "B", q: "Quand je découvre un nouveau sujet, je cherche à comprendre comment il s'articule avec ce que je connais déjà." },
  // Apprentissage continu (2)
  { type: "B", q: "Quand un nouvel outil sort, j'ai envie de le tester par curiosité." },
  { type: "B", q: "J'apprends régulièrement des choses sans qu'on me le demande : vidéos, livres, projets perso." },

  // === PILLAR C · Adaptation post-IA (10 items) ===
  // Tolérance à l'incertitude / pivot (3)
  { type: "C", q: "Si mon plan ne marche pas, je trouve assez vite un plan B sans paniquer." },
  { type: "C", q: "Je peux travailler sur quelque chose sans savoir exactement où ça va me mener." },
  { type: "C", q: "Quand tout change autour de moi, je trouve ça plus stimulant qu'angoissant." },
  // Identité pro non figée (2)
  { type: "C", q: "Je suis à l'aise avec l'idée que je n'exercerai peut-être pas le même métier toute ma vie." },
  { type: "C", q: "Quand on me demande « tu veux faire quoi plus tard ? », je peux donner plusieurs réponses possibles." },
  // Réseau & collaboration (2)
  { type: "C", q: "J'arrive à demander de l'aide à des gens que je connais peu." },
  { type: "C", q: "Quand je travaille en groupe, je trouve naturellement ma place et je contribue." },
  // Esprit entreprenant (3)
  { type: "C", q: "J'ai déjà lancé, ou j'ai vraiment envie de lancer, un projet à moi : asso, business, blog, chaîne, événement." },
  { type: "C", q: "Quand je vois quelque chose qui ne marche pas bien, j'ai envie de proposer une solution plutôt que de me plaindre." },
  { type: "C", q: "Je préfère essayer et me tromper plutôt qu'attendre d'être sûr à 100%." },
];

const TYPE_META = {
  A: { l: "Capacités humaines", c: "#C2410C", short: "Ce que l'IA ne réplique pas (créativité, empathie, éthique, leadership)" },
  B: { l: "Augmentation par l'IA", c: "#0E7490", short: "Travailler AVEC l'IA, pas contre (prompting, critique, systémique)" },
  C: { l: "Adaptation post-IA", c: "#7C2D12", short: "Pivot, identité fluide, esprit entreprenant" },
};

const STORAGE_KEY = "proxxie-futureproof-answers";

const getTypeMeta = (q) => ({ label: TYPE_META[q.type].l, color: TYPE_META[q.type].c });

const computeResults = (answers) => {
  const sums = { A: 0, B: 0, C: 0 };
  const counts = { A: 0, B: 0, C: 0 };
  QUESTIONS.forEach((q, idx) => {
    if (answers[idx] == null) return;
    sums[q.type] += answers[idx];
    counts[q.type] += 1;
  });
  // Score 0-100 par pilier (échelle Likert 1-5 → (avg-1)/4 × 100)
  const pillarScore = (t) => counts[t] > 0 ? Math.round(((sums[t] / counts[t]) - 1) / 4 * 100) : 0;
  const a = pillarScore("A");
  const b = pillarScore("B");
  const c = pillarScore("C");
  // Score global · moyenne équipondérée
  const total = Math.round((a + b + c) / 3);
  let level = "à recadrer";
  let levelColor = "#9CA3AF";
  if (total >= 80) { level = "architecte de l'avenir"; levelColor = "#FD6936"; }
  else if (total >= 65) { level = "solide"; levelColor = "#0E7490"; }
  else if (total >= 50) { level = "en construction"; levelColor = "#7C2D12"; }
  else if (total >= 35) { level = "à renforcer"; levelColor = "#C2410C"; }

  // Famille de métiers : règles de mapping basées sur les top piliers
  const families = [];
  // Créateur : haut A (créativité) + B (curation) modéré
  if (a >= 65) families.push({
    code: "createur",
    label: "Créateur",
    desc: "Designer, artiste, écrivain, marketeur créatif, vidéaste. Ton avantage : ce que tu produis n'existait pas avant.",
    fit: a + Math.round(b * 0.3),
  });
  // Soignant·éducateur : haut A (empathie + leadership)
  if (a >= 60) families.push({
    code: "soignant",
    label: "Soignant · éducateur",
    desc: "Psy, médecin, enseignant, coach, soignant. Ton avantage : la relation humaine est irremplaçable.",
    fit: a + Math.round(c * 0.2),
  });
  // Expert systémique : haut B (systémique + IA-aug)
  if (b >= 65) families.push({
    code: "expert",
    label: "Expert systémique",
    desc: "Analyste, consultant stratégie, architecte data, chercheur. Ton avantage : tu orchestres des outils complexes.",
    fit: b + Math.round(a * 0.2),
  });
  // Leader·entrepreneur : haut C (pivot + entreprenant) + A (leadership)
  if (c >= 65) families.push({
    code: "leader",
    label: "Leader · entrepreneur",
    desc: "Fondateur, chef de projet, manager, dirigeant. Ton avantage : tu mets le mouvement, tu fais décider.",
    fit: c + Math.round(a * 0.3),
  });
  // Artisan physique : haut A (présence) + C (entreprenant)
  if (a >= 55 && c >= 55) families.push({
    code: "artisan",
    label: "Artisan · métier d'incarnation",
    desc: "Chef, métier d'art, soin corporel, sport, artisanat. Ton avantage : ta présence et tes mains sont uniques.",
    fit: Math.round((a + c) / 2),
  });
  // Tri par fit décroissant, top 3 max
  families.sort((x, y) => y.fit - x.fit);
  const topFamilies = families.slice(0, 3);

  // Top forces : les 3 sous-piliers avec la moyenne la plus haute
  // (on simplifie · on prend juste les top items individuels)
  const itemScores = QUESTIONS.map((q, idx) => ({
    q: q.q, type: q.type, score: answers[idx] || 0
  }));
  const topItems = [...itemScores].sort((x, y) => y.score - x.score).slice(0, 3);
  const lowItems = [...itemScores].filter(x => x.score > 0).sort((x, y) => x.score - y.score).slice(0, 3);

  return { total, a, b, c, level, levelColor, topFamilies, topItems, lowItems };
};

const DisclaimerBanner = () => (
  <div style={{
    background: "#FFF7ED", borderLeft: "4px solid #FD6936",
    padding: "14px 20px", marginBottom: 30, borderRadius: 8,
    fontSize: 13.5, color: "#0A0E2C", lineHeight: 1.55,
  }}>
    <strong>ℹ️ Outil de positionnement, pas une boule de cristal.</strong> Ce score combine 3 frameworks crédibles (WEF Future of Jobs 2025, OECD Skills 2023, McKinsey 2024) mais ne prédit rien. Il te dit où tu en es <em>aujourd'hui</em> et sur quoi appuyer pour rester pertinent en 2035. Ces compétences se développent toutes.
  </div>
);

const TestHero = ({ onStart }) => (
  <section style={{ paddingTop: 70, paddingBottom: 80, position: "relative", overflow: "hidden" }}>
    <Pill color="rgba(253,105,54,.45)" w={260} h={130} style={{ position: "absolute", top: 110, right: -60, borderRadius: 999 }} />
    <Half color="rgba(14,116,144,.18)" side="t" w={300} h={120} style={{ position: "absolute", bottom: -10, left: -40 }} />
    <div className="shell" style={{ position: "relative", display: "grid", gridTemplateColumns: "1.1fr 1fr", gap: 60, alignItems: "center" }}>
      <div>
        <span className="chip" style={{ background: "rgba(253,105,54,.15)", color: "#C2410C" }}>
          <Icon.spark style={{ width: 14, height: 14 }} /> Test signature Proxxie · 2025
        </span>
        <h1 style={{ marginTop: 22, marginBottom: 22 }}>
          Test <span style={{ background: "linear-gradient(180deg, transparent 60%, #F5EB3F 60%)", paddingInline: 4 }}>Future-Proof</span> · auras-tu un métier en 2035 ?
        </h1>
        <p style={{ fontSize: 18, color: "var(--c-ink-2)", maxWidth: 540, marginBottom: 28 }}>
          ChatGPT, Claude, Mistral redessinent le travail. Ce test mesure trois choses : ce que l'IA ne pourra pas faire à ta place, ce qu'elle peut <em>augmenter</em> chez toi, et ta capacité à pivoter quand tout change. <strong>30 questions, 5 minutes</strong>, un score d'IA-résilience et 3 familles de métiers où tu as un avantage durable.
        </p>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 22 }}>
          <button className="btn btn-orange btn-lg btn-arrow" onClick={onStart}>Démarrer le test</button>
          <a href="#methode" className="btn btn-ghost btn-lg"><Icon.play /> Comment ça marche</a>
        </div>
        <div style={{ display: "flex", gap: 22, fontSize: 13, color: "var(--c-muted)", flexWrap: "wrap" }}>
          <span><Icon.shield style={{ width: 13, height: 13, verticalAlign: "-2px", marginRight: 4 }} /> Données privées · stockées en local</span>
          <span>⏱ 5 min · 30 questions</span>
          <span>📋 WEF + OECD + McKinsey 2024-25</span>
        </div>
      </div>
      <div style={{ position: "relative" }}>
        <div style={{ background: "white", borderRadius: 24, padding: 28, boxShadow: "var(--shadow-md)", border: "1px solid var(--c-line)" }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: "#C2410C", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 14 }}>3 piliers mesurés</div>
          {[
            { l: "Capacités humaines", v: "ce que l'IA ne fait pas", c: "#C2410C" },
            { l: "Augmentation IA", v: "travailler avec l'IA", c: "#0E7490" },
            { l: "Adaptation post-IA", v: "pivoter, entreprendre", c: "#7C2D12" },
          ].map((row, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 14, padding: "12px 0", borderBottom: i < 2 ? "1px solid var(--c-line)" : "none" }}>
              <div style={{ width: 36, height: 36, borderRadius: 10, background: row.c, color: "white", display: "grid", placeItems: "center", fontWeight: 700, fontSize: 14, fontFamily: "var(--font-display)" }}>{"ABC"[i]}</div>
              <div>
                <div style={{ fontWeight: 700, fontSize: 14.5, color: "var(--c-ink)" }}>{row.l}</div>
                <div style={{ fontSize: 13, color: "var(--c-muted)" }}>{row.v}</div>
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
      <h2 style={{ textAlign: "center", marginBottom: 16 }}>Comment ce test est construit</h2>
      <p style={{ textAlign: "center", fontSize: 16, color: "var(--c-muted)", marginBottom: 40, maxWidth: 660, margin: "0 auto 40px" }}>
        Pas un test psychométrique validé : un outil de positionnement basé sur 3 rapports de référence et orienté action.
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 18 }}>
        {[
          { t: "WEF Future of Jobs 2025", d: "Le top 10 des compétences clés à horizon 2030 selon les DRH mondiaux." },
          { t: "OECD Skills Outlook 2023", d: "Quelles compétences l'IA complémente vs remplace, par profession." },
          { t: "McKinsey · GenAI 2024", d: "Les 3 familles de tâches transformées : créatives, analytiques, relationnelles." },
        ].map((s, i) => (
          <div key={i} style={{ background: "white", borderRadius: 18, padding: 22, border: "1px solid var(--c-line)" }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: "#C2410C", marginBottom: 8 }}>📚 Source {i+1}</div>
            <div style={{ fontWeight: 700, fontSize: 16, color: "var(--c-ink)", marginBottom: 8 }}>{s.t}</div>
            <p style={{ fontSize: 13.5, color: "var(--c-muted)", lineHeight: 1.55 }}>{s.d}</p>
          </div>
        ))}
      </div>
    </div>
  </section>
);

const LEVEL_COPY = {
  "architecte de l'avenir": { color: "#FD6936", title: "Architecte de l'avenir (top 10%)", sub: "Tu as déjà internalisé ce que les rapports 2025 décrivent comme « le profil 2030 ». Continue à pousser sur tes piliers les plus bas pour devenir injouable." },
  "solide": { color: "#0E7490", title: "Solide", sub: "Tu coches les bonnes cases sur 2 piliers minimum. La marche pour passer à « architecte » est claire : identifier ton pilier le plus bas et le travailler 6 mois." },
  "en construction": { color: "#7C2D12", title: "En construction", sub: "Tu es dans la médiane. C'est l'année pour faire un saut. Choisis UN levier concret (pas trois) et investis-le sérieusement." },
  "à renforcer": { color: "#C2410C", title: "À renforcer", sub: "Plusieurs piliers sont fragiles. Pas de panique : tout se développe. La clé, c'est d'éviter les filières « pures exécution » et de chercher des contextes qui te forcent à pratiquer ces compétences." },
  "à recadrer": { color: "#9CA3AF", title: "À recadrer", sub: "Tu réponds peut-être trop modestement, ou ces compétences ne sont pas encore exercées. Une conversation avec Charles permettra de cartographier ce qui se passe vraiment." },
};

const RichAnalysisSection = ({ pillars, families, topItems, lowItems, level }) => (
  <section style={{ paddingTop: 50, paddingBottom: 30 }}>
    <div className="shell" style={{ maxWidth: 820 }}>
      <div style={{ background: "white", borderRadius: 20, padding: 32, border: "1px solid var(--c-line)", marginBottom: 24 }}>
        <h2 style={{ fontSize: 24, marginBottom: 8, color: "var(--c-ink)" }}>Tes 3 forces du moment</h2>
        <p style={{ fontSize: 14, color: "var(--c-muted)", marginBottom: 24 }}>Les items où tu as répondu le plus haut · à ancrer dans ton parcours.</p>
        <div style={{ display: "grid", gap: 12 }}>
          {topItems.map((it, i) => (
            <div key={i} style={{ display: "flex", gap: 14, padding: "14px 16px", background: "var(--c-cream-light, #FAF6EE)", borderRadius: 12, border: "1px solid var(--c-line)" }}>
              <div style={{ flexShrink: 0, width: 32, height: 32, borderRadius: 8, background: TYPE_META[it.type].c, color: "white", display: "grid", placeItems: "center", fontWeight: 700, fontFamily: "var(--font-display)" }}>{it.type}</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 14.5, color: "var(--c-ink)", lineHeight: 1.5 }}>{it.q}</div>
                <div style={{ fontSize: 12, color: "var(--c-muted)", marginTop: 4 }}>Pilier {TYPE_META[it.type].l}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ background: "white", borderRadius: 20, padding: 32, border: "1px solid var(--c-line)", marginBottom: 24 }}>
        <h2 style={{ fontSize: 24, marginBottom: 8, color: "var(--c-ink)" }}>3 leviers à travailler dans les 6 mois</h2>
        <p style={{ fontSize: 14, color: "var(--c-muted)", marginBottom: 24 }}>Les items où tu as répondu le plus bas · ne pas chercher à les transformer tous, en choisir UN et le pratiquer.</p>
        <div style={{ display: "grid", gap: 12 }}>
          {lowItems.map((it, i) => (
            <div key={i} style={{ display: "flex", gap: 14, padding: "14px 16px", background: "#FFF7ED", borderRadius: 12, border: "1px solid #FED7AA" }}>
              <div style={{ flexShrink: 0, width: 32, height: 32, borderRadius: 8, background: TYPE_META[it.type].c, color: "white", display: "grid", placeItems: "center", fontWeight: 700, fontFamily: "var(--font-display)" }}>{it.type}</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 14.5, color: "var(--c-ink)", lineHeight: 1.5 }}>{it.q}</div>
                <div style={{ fontSize: 12, color: "var(--c-muted)", marginTop: 4 }}>Pilier {TYPE_META[it.type].l}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  </section>
);

const Results = ({ results, onRestart }) => {
  const { total, a, b, c, level, topFamilies, topItems, lowItems } = results;
  const levelCopy = LEVEL_COPY[level] || LEVEL_COPY["en construction"];
  return (
    <section style={{ paddingTop: 60, paddingBottom: 30 }}>
      <div className="shell" style={{ maxWidth: 820 }}>
        <DisclaimerBanner />

        {/* Hero score */}
        <div style={{ textAlign: "center", marginBottom: 50 }}>
          <span className="chip" style={{ background: "rgba(253,105,54,.15)", color: "#C2410C" }}>
            <Icon.spark style={{ width: 14, height: 14 }} /> Score Future-Proof 2035
          </span>
          <h1 style={{ marginTop: 20, marginBottom: 12, fontSize: 56, color: levelCopy.color, fontFamily: "var(--font-display)", letterSpacing: "-0.03em" }}>
            {total} <span style={{ fontSize: 24, color: "var(--c-muted)" }}>/ 100</span>
          </h1>
          <h2 style={{ fontSize: 26, color: "var(--c-ink)", marginBottom: 12, fontWeight: 600 }}>{levelCopy.title}</h2>
          <p style={{ fontSize: 16, color: "var(--c-ink-2)", maxWidth: 600, margin: "0 auto", lineHeight: 1.6 }}>{levelCopy.sub}</p>
        </div>

        {/* Radar 3 piliers */}
        <div style={{ background: "white", borderRadius: 20, padding: 32, border: "1px solid var(--c-line)", marginBottom: 30 }}>
          <h2 style={{ fontSize: 22, marginBottom: 24, color: "var(--c-ink)" }}>Tes 3 piliers</h2>
          <div style={{ display: "grid", gap: 18 }}>
            {[
              { code: "A", score: a, meta: TYPE_META.A },
              { code: "B", score: b, meta: TYPE_META.B },
              { code: "C", score: c, meta: TYPE_META.C },
            ].map((row) => (
              <div key={row.code}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 8 }}>
                  <div>
                    <span style={{ display: "inline-block", width: 28, height: 28, borderRadius: 7, background: row.meta.c, color: "white", textAlign: "center", lineHeight: "28px", fontWeight: 700, marginRight: 12, fontFamily: "var(--font-display)" }}>{row.code}</span>
                    <strong style={{ color: "var(--c-ink)", fontSize: 15.5 }}>{row.meta.l}</strong>
                  </div>
                  <span style={{ fontFamily: "var(--font-num)", fontWeight: 700, fontSize: 22, color: row.meta.c }}>{row.score}<span style={{ fontSize: 13, color: "var(--c-muted)", fontWeight: 500 }}> / 100</span></span>
                </div>
                <div style={{ height: 10, background: "var(--c-cream)", borderRadius: 5, overflow: "hidden", marginBottom: 6 }}>
                  <div style={{ width: `${row.score}%`, height: "100%", background: row.meta.c, transition: "width .8s cubic-bezier(.2,.8,.2,1)" }} />
                </div>
                <p style={{ fontSize: 13.5, color: "var(--c-muted)", lineHeight: 1.5, marginTop: 6, marginLeft: 40 }}>{row.meta.short}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Familles de métiers */}
        {topFamilies.length > 0 && (
          <div style={{ background: "linear-gradient(160deg, #FFF7ED, #FAF6EE)", borderRadius: 20, padding: 32, border: "1px solid #FED7AA", marginBottom: 30 }}>
            <h2 style={{ fontSize: 24, marginBottom: 8, color: "var(--c-ink)" }}>3 familles de métiers où tu as un avantage</h2>
            <p style={{ fontSize: 14, color: "var(--c-muted)", marginBottom: 24 }}>D'après ton profil sur les 3 piliers · pas une prescription, une boussole.</p>
            <div style={{ display: "grid", gap: 16 }}>
              {topFamilies.map((f, i) => (
                <div key={f.code} style={{ background: "white", borderRadius: 14, padding: "18px 22px", border: "1px solid var(--c-line)", position: "relative" }}>
                  <div style={{ position: "absolute", top: -8, left: 18, background: "#FD6936", color: "white", fontSize: 11, fontWeight: 700, padding: "3px 10px", borderRadius: 99, letterSpacing: "0.04em", textTransform: "uppercase" }}>
                    {i === 0 ? "Top fit" : `Alternative ${i}`}
                  </div>
                  <h3 style={{ fontSize: 18, marginTop: 6, marginBottom: 8, color: "var(--c-ink)" }}>{f.label}</h3>
                  <p style={{ fontSize: 14, color: "var(--c-ink-2)", lineHeight: 1.55, margin: 0 }}>{f.desc}</p>
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
  const parentResults = computeResults(parentAnswers);
  const teenResults = computeResults(teenAnswers);
  const gapTotal = Math.abs(parentResults.total - teenResults.total);
  return (
    <div style={{ background: "white", borderRadius: 20, padding: 28, border: "1px solid var(--c-line)", marginBottom: 30 }}>
      <h2 style={{ fontSize: 20, marginBottom: 18 }}>Comparaison avec la prédiction parent</h2>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
        <div style={{ padding: 18, background: "var(--c-cream-light, #FAF6EE)", borderRadius: 12 }}>
          <div style={{ fontSize: 12, color: "var(--c-muted)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>{parentName} pense</div>
          <div style={{ fontSize: 32, fontWeight: 700, color: "var(--c-ink)", fontFamily: "var(--font-display)" }}>{parentResults.total}<span style={{ fontSize: 14, color: "var(--c-muted)" }}>/100</span></div>
        </div>
        <div style={{ padding: 18, background: "rgba(253,105,54,.08)", borderRadius: 12 }}>
          <div style={{ fontSize: 12, color: "#C2410C", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>Tu réponds</div>
          <div style={{ fontSize: 32, fontWeight: 700, color: "#C2410C", fontFamily: "var(--font-display)" }}>{teenResults.total}<span style={{ fontSize: 14 }}>/100</span></div>
        </div>
      </div>
      <p style={{ marginTop: 18, fontSize: 14, color: "var(--c-muted)", lineHeight: 1.55 }}>
        Écart de <strong>{gapTotal} points</strong>. {gapTotal <= 10 ? "Vous voyez à peu près la même chose, c'est rare." : gapTotal <= 25 ? "Écart modéré · à creuser sur quels piliers exactement." : "Écart important · vraie occasion de discuter ce que chacun voit différemment."}
      </p>
    </div>
  );
};

const buildEmailSummary = (results) => {
  const { total, a, b, c, level, topFamilies } = results;
  let summary = `Score Future-Proof 2035 : ${total}/100 (${level})\n`;
  summary += `- Pilier Humain : ${a}/100\n`;
  summary += `- Pilier Augmentation IA : ${b}/100\n`;
  summary += `- Pilier Adaptation : ${c}/100\n`;
  if (topFamilies.length > 0) {
    summary += `\nFamilles de métiers les mieux alignées :\n`;
    topFamilies.forEach(f => { summary += `- ${f.label}\n`; });
  }
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
    try { window.localStorage.setItem("proxxie.tests.futureproof", "done"); } catch(e){}
  };
  const restart = () => { setAnswers([]); setResults(null); setMode("landing"); };

  const effectivePersona = persona;
  const storageKeyEffective = persona === "predict" ? STORAGE_KEY + ":predict" : STORAGE_KEY;
  return (
    <>
      <ProxxieNav />
      {mode === "landing" && (<><TestHero onStart={goPicker} /><HowItWorks /></>)}
      {mode === "picker" && <PersonaIntro testName="Future-Proof 2035" accent="#C2410C" comingFromPredict={null} onPick={pickPersona} />}
      {mode === "compare-intro" && <PersonaIntro testName="Future-Proof 2035" accent="#C2410C" comingFromPredict={PARENT_PREDICT} onPick={pickPersona} />}
      {mode === "test" && (
        <>
          {persona === "predict" && (<div style={{ background: "#F5EB3F", color: "#0A0E2C", padding: "10px 16px", textAlign: "center", fontSize: 13, fontWeight: 600 }}>🎯 Mode prédiction · Répondez comme vous pensez que votre ado répondrait</div>)}
          <TestFlowEngine questions={QUESTIONS} storageKey={storageKeyEffective} getTypeMeta={getTypeMeta} onExit={exitTest} onComplete={onComplete} />
        </>
      )}
      {mode === "results" && results && (
        <>
          {effectivePersona === "self_compare" && PARENT_PREDICT && (<section style={{ paddingTop: 40, paddingBottom: 0 }}><div className="shell" style={{ maxWidth: 820 }}><ComparePanel parentName={PARENT_PREDICT.n} parentAnswers={PARENT_PREDICT.a} teenAnswers={answers} /></div></section>)}
          {persona === "predict" && (<section style={{ paddingTop: 40, paddingBottom: 0 }}><div className="shell" style={{ maxWidth: 820 }}><ShareLinkPanel testCode="FuturProof" accent="#C2410C" answers={answers} defaultName="" onSkip={() => {}} /></div></section>)}
          <EmailResultsActions testCode="FuturProof" testName="Future-Proof 2035" accent="#C2410C" summary={buildEmailSummary(results)} answers={answers} />
          <Results results={results} onRestart={restart} />
          <RichAnalysisSection pillars={results} families={results.topFamilies} topItems={results.topItems} lowItems={results.lowItems} level={results.level} />
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
        'const __PROXXIE_TEST_ID__ = "futureproof";',
        src,
        count=1,
    )
    boundary_match = re.search(
        r"(/\*\s*Test Proxxie Anxi[^/]*\*/\s*\n)?const QUESTIONS\s*=", src
    )
    if not boundary_match:
        return f"{target_path.name}: boundary introuvable"
    new_src = src[: boundary_match.start()] + FUTUREPROOF_BLOCK

    nd = new_src.encode("utf-8")
    if comp:
        nd = gzip.compress(nd)
    entry["data"] = base64.b64encode(nd).decode("ascii")
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[: m.start(2)] + new_manifest_json + html[m.end(2) :]

    new_html = re.sub(
        r"<title[^>]*>[^<]*</title>",
        "<title>Test Future-Proof 2035, Proxxie</title>",
        new_html,
        count=1,
    )
    new_html = re.sub(
        r"<title[^>]*>[^<]*<\\/title>",
        "<title>Test Future-Proof 2035, Proxxie<\\/title>",
        new_html,
        count=1,
    )

    target_path.write_text(new_html, encoding="utf-8")
    return f"{target_path.name}: built (asset {uuid[:8]}, src {len(src)} → {len(new_src)})"


if __name__ == "__main__":
    print(build(SOURCE, TARGET))
    print(build(SOURCE, TARGET_LOWER))

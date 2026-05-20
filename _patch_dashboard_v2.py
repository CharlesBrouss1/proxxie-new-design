#!/usr/bin/env python3
"""Dashboard rev 2 · gamification + docs push + re-engagement + invitation.

Adds four React components to the dashboard manifest asset and wires them
into the Dashboard return·

  - ReengagementBanner  · top of page, date-aware "upload latest bulletin"
  - GamificationPanel   · ado-only XP/level/badges card
  - DocsCompletenessPanel · "Data completeness" meter with missing-doc list
  - InvitationModal + InvitationCTA · "Inviter mon parent/ado" with code

Idempotent· skipped if marker present.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
TARGETS = ["dashboard.html", "Proxxie Dashboard.html"]
DASHBOARD_ASSET = "5a278f70-3fa5-4bc0-bdb2-349143947f86"
MARKER = "/* __proxxie_dashboard_v2__ */"


COMPONENTS_JSX = r"""
/* __proxxie_dashboard_v2__ */

/* ---------------- role helpers ---------------- */
const PROXXIE_LEVELS = [
  { min: 0,    name: "Curieux",     emoji: "✨" },
  { min: 100,  name: "Explorateur", emoji: "🧭" },
  { min: 300,  name: "Cartographe", emoji: "🗺️" },
  { min: 700,  name: "Stratège",    emoji: "♟️" },
  { min: 1500, name: "Architecte",  emoji: "🏛️" },
];
const PROXXIE_BADGES = [
  { id: "premier_test", name: "Premier test",   emoji: "🎯", hint: "Passe ton premier test psychométrique" },
  { id: "3_tests",      name: "3 tests passés", emoji: "🔬", hint: "Passe 3 tests différents" },
  { id: "5_tests",      name: "5 tests passés", emoji: "🧪", hint: "Passe 5 tests différents" },
  { id: "tous_tests",   name: "Carte complète", emoji: "🌟", hint: "Passe les 11 tests" },
  { id: "premier_doc",  name: "Premier doc",    emoji: "📎", hint: "Upload ton premier document" },
  { id: "5_docs",       name: "5 docs",         emoji: "📚", hint: "Upload 5 documents" },
  { id: "coach",        name: "Premier RDV",    emoji: "📅", hint: "Effectue ton premier RDV coach" },
  { id: "semaine",      name: "1 semaine",      emoji: "🔥", hint: "Connecte-toi 7 jours d'affilée" },
  { id: "lien",         name: "Lié à ton parent", emoji: "🔗", hint: "Lie ton compte à un parent (ou inverse)" },
  { id: "compare",      name: "Comparaison",    emoji: "👯", hint: "Compare ton profil avec ton parent" },
];

const _proxxieGetXP = () => {
  try { return parseInt(localStorage.getItem("proxxie.xp"), 10) || 280; } catch (e) { return 280; }
};
const _proxxieGetBadges = () => {
  try {
    const raw = localStorage.getItem("proxxie.badges");
    if (raw) return JSON.parse(raw);
  } catch (e) {}
  return ["premier_test", "premier_doc", "coach"];
};
const _proxxieLevel = (xp) => {
  let cur = PROXXIE_LEVELS[0], next = null;
  for (let i = 0; i < PROXXIE_LEVELS.length; i++) {
    if (xp >= PROXXIE_LEVELS[i].min) { cur = PROXXIE_LEVELS[i]; next = PROXXIE_LEVELS[i + 1] || null; }
  }
  return { cur, next };
};

/* ---------------- ReengagementBanner ---------------- */
const ReengagementBanner = () => {
  const [dismissed, setDismissed] = React.useState(() => {
    try { return localStorage.getItem("proxxie.reengage.dismissed") === "1"; } catch (e) { return false; }
  });
  const role = useProxxieRole();
  if (dismissed) return null;
  const isEnfant = role === "enfant";
  const now = new Date();
  const m = now.getMonth() + 1;
  let target = null;
  if (m >= 11 || m <= 1) target = { item: "Bulletins du 1er trimestre", kind: "Bulletins T1" };
  else if (m >= 2 && m <= 4) target = { item: "Bulletins du 2e trimestre", kind: "Bulletins T2" };
  else if (m >= 5 && m <= 7) target = { item: "Bulletins du 3e trimestre + dernier devoir de maths", kind: "Bulletins T3" };
  else target = { item: "Devoirs de fin d'année + relevé Parcoursup", kind: "Synthèse" };

  const title = isEnfant
    ? "C'est la période · " + target.item + " sont prêts ?"
    : "C'est la période · " + target.item + " sont disponibles ?";
  const sub = isEnfant
    ? "Upload-les en 30 sec pour que ton rapport reste à jour. Plus on a de data, plus on peut t'aider."
    : "Uploadez-les pour que le rapport de votre ado reste à jour. Plus on a de data, plus on peut vous aider.";
  const cta = isEnfant ? "Uploader maintenant" : "Uploader maintenant";

  return (
    <div style={{ background: "linear-gradient(135deg, #FFF6E0 0%, #FFE7C7 100%)", borderBottom: "1px solid rgba(253,105,54,.18)" }}>
      <div className="shell" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16, padding: "14px 0", flexWrap: "wrap" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14, flex: 1, minWidth: 280 }}>
          <div style={{ width: 38, height: 38, borderRadius: 10, background: "#FD6936", color: "white", display: "grid", placeItems: "center", fontSize: 18, flexShrink: 0 }}>📅</div>
          <div>
            <div style={{ fontWeight: 600, fontSize: 14, color: "#0A0E2C", marginBottom: 2 }}>{title}</div>
            <div style={{ fontSize: 13, color: "rgba(10,14,44,.6)" }}>{sub}</div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <a href="Proxxie Documents.html" className="btn btn-orange" style={{ padding: "10px 18px", fontSize: 13, borderRadius: 10, textDecoration: "none" }}>{cta} →</a>
          <button
            onClick={() => { try { localStorage.setItem("proxxie.reengage.dismissed", "1"); } catch (e) {} setDismissed(true); }}
            style={{ background: "transparent", border: "none", fontSize: 13, color: "rgba(10,14,44,.5)", cursor: "pointer", padding: "10px 12px", fontFamily: "inherit" }}
          >Plus tard</button>
        </div>
      </div>
    </div>
  );
};

/* ---------------- GamificationPanel (ado only) ---------------- */
const GamificationPanel = () => {
  const role = useProxxieRole();
  const [xp] = React.useState(_proxxieGetXP);
  const [badges] = React.useState(_proxxieGetBadges);
  if (role !== "enfant") return null;
  const { cur, next } = _proxxieLevel(xp);
  const progress = next ? Math.min(100, Math.round(((xp - cur.min) / (next.min - cur.min)) * 100)) : 100;
  const toGo = next ? next.min - xp : 0;

  return (
    <section style={{ margin: "0 auto 24px", padding: "0 24px", maxWidth: 1280 }}>
      <div style={{
        background: "linear-gradient(135deg, #1320CE 0%, #0A0E2C 100%)",
        color: "white", borderRadius: 20, padding: "26px 28px", position: "relative", overflow: "hidden",
      }}>
        <div style={{ position: "absolute", top: -40, right: -40, width: 200, height: 200, borderRadius: "50%", background: "rgba(245,235,63,.10)" }} />
        <div style={{ position: "absolute", bottom: -60, left: -60, width: 240, height: 240, borderRadius: "50%", background: "rgba(72,122,255,.18)" }} />

        <div style={{ position: "relative", zIndex: 1, display: "grid", gridTemplateColumns: "minmax(0, 1fr) auto", gap: 24, alignItems: "center" }}>
          <div>
            <span style={{ display: "inline-flex", alignItems: "center", gap: 8, padding: "5px 12px", borderRadius: 999, background: "rgba(255,255,255,.10)", fontSize: 11, fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 12 }}>
              <span>{cur.emoji}</span> Ton parcours Proxxie
            </span>
            <h2 style={{ fontFamily: "var(--font-display)", fontSize: 30, fontWeight: 600, letterSpacing: "-0.02em", margin: "0 0 6px" }}>
              Niveau {PROXXIE_LEVELS.indexOf(cur) + 1} · {cur.name}
            </h2>
            <p style={{ fontSize: 14, color: "rgba(255,255,255,.75)", margin: "0 0 18px", lineHeight: 1.5 }}>
              {next
                ? "Encore " + toGo + " XP pour passer " + next.name + " " + next.emoji + ". Passe un test, upload un doc, ou vois ton coach."
                : "Niveau max atteint, bravo ! Tu peux quand même empiler les badges en passant les tests manquants."}
            </p>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 6 }}>
              <div style={{ flex: 1, height: 10, borderRadius: 999, background: "rgba(255,255,255,.12)", overflow: "hidden" }}>
                <div style={{ width: progress + "%", height: "100%", background: "linear-gradient(90deg, #F5EB3F 0%, #FD6936 100%)", transition: "width .4s ease" }} />
              </div>
              <span style={{ fontFamily: "var(--font-num)", fontWeight: 700, fontSize: 16, color: "#F5EB3F", minWidth: 64, textAlign: "right" }}>
                {xp}{next ? " / " + next.min : ""} XP
              </span>
            </div>
            <div style={{ display: "flex", gap: 14, marginTop: 18, flexWrap: "wrap" }}>
              {PROXXIE_BADGES.slice(0, 6).map((b) => {
                const got = badges.indexOf(b.id) >= 0;
                return (
                  <div key={b.id} title={b.hint} style={{
                    display: "flex", alignItems: "center", gap: 8,
                    padding: "8px 12px", borderRadius: 999,
                    background: got ? "rgba(245,235,63,.15)" : "rgba(255,255,255,.06)",
                    border: "1px solid " + (got ? "rgba(245,235,63,.4)" : "rgba(255,255,255,.10)"),
                    opacity: got ? 1 : 0.5,
                  }}>
                    <span style={{ fontSize: 16, filter: got ? "none" : "grayscale(1)" }}>{b.emoji}</span>
                    <span style={{ fontSize: 12, fontWeight: 600, color: got ? "#F5EB3F" : "rgba(255,255,255,.55)" }}>{b.name}</span>
                  </div>
                );
              })}
              <a href="#" onClick={(e) => e.preventDefault()} style={{ fontSize: 12, fontWeight: 600, color: "rgba(255,255,255,.85)", textDecoration: "underline", alignSelf: "center" }}>
                + {PROXXIE_BADGES.length - 6} autres badges
              </a>
            </div>
          </div>
          <div style={{
            width: 140, height: 140, borderRadius: "50%",
            background: "rgba(245,235,63,.12)",
            border: "2px solid rgba(245,235,63,.35)",
            display: "grid", placeItems: "center",
            position: "relative",
          }}>
            <div style={{ fontSize: 56 }}>{cur.emoji}</div>
            <div style={{ position: "absolute", bottom: -10, left: "50%", transform: "translateX(-50%)", padding: "4px 12px", borderRadius: 999, background: "#F5EB3F", color: "#0A0E2C", fontFamily: "var(--font-num)", fontWeight: 700, fontSize: 14, whiteSpace: "nowrap" }}>
              Niv. {PROXXIE_LEVELS.indexOf(cur) + 1}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

/* ---------------- DocsCompletenessPanel ---------------- */
const DOCS_EXPECTED = [
  { id: "bull_t1",  label: "Bulletins T1 (année en cours)", critical: true,  def: true  },
  { id: "bull_t2",  label: "Bulletins T2 (année en cours)", critical: true,  def: true  },
  { id: "bull_t3",  label: "Bulletins T3 (année en cours)", critical: true,  def: false },
  { id: "bull_n1",  label: "Bulletins année précédente",    critical: false, def: true  },
  { id: "maths",    label: "Dernier devoir de maths",       critical: false, def: false },
  { id: "lm",       label: "Lettre de motivation Parcoursup", critical: false, def: false },
  { id: "cv",       label: "CV / activités extra-scolaires",  critical: false, def: false },
  { id: "test_oc",  label: "Résultats OCEAN-X",              critical: true,  def: true  },
];
const _proxxieGetDocs = () => {
  const out = {};
  for (const d of DOCS_EXPECTED) {
    let v = d.def;
    try { const s = localStorage.getItem("proxxie.docs." + d.id); if (s != null) v = s === "1"; } catch (e) {}
    out[d.id] = v;
  }
  return out;
};

const DocsCompletenessPanel = () => {
  const role = useProxxieRole();
  const isEnfant = role === "enfant";
  const docs = _proxxieGetDocs();
  const total = DOCS_EXPECTED.length;
  const done = DOCS_EXPECTED.filter((d) => docs[d.id]).length;
  const pct = Math.round((done / total) * 100);
  const missing = DOCS_EXPECTED.filter((d) => !docs[d.id]);

  return (
    <section style={{ margin: "0 auto 32px", padding: "0 24px", maxWidth: 1280 }}>
      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 24, alignItems: "stretch" }}>
        {/* Left· meter + pitch */}
        <div className="card" style={{ background: "white", border: "1px solid rgba(10,14,44,0.08)", borderRadius: 20, padding: 26 }}>
          <span className="eyebrow"><span className="dot"></span>Complétude du dossier</span>
          <h3 style={{ fontFamily: "var(--font-display)", fontSize: 24, fontWeight: 600, letterSpacing: "-0.02em", margin: "10px 0 6px" }}>
            {isEnfant
              ? "Plus de data = plus d'aide. Ton dossier est à " + pct + "%."
              : "Plus de data = plus d'aide. Le dossier est à " + pct + "%."}
          </h3>
          <p style={{ color: "rgba(10,14,44,.55)", fontSize: 14, margin: "0 0 18px", lineHeight: 1.5 }}>
            {isEnfant
              ? "Plus tu nous donnes d'éléments (bulletins, devoirs, motivations), plus ton rapport et tes recommandations sont précis. Tu peux ajouter de la data à tout moment."
              : "Plus vous nous donnez d'éléments (bulletins, devoirs, motivations), plus le rapport et les recommandations sont précis. Vous pouvez ajouter de la data à tout moment."}
          </p>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <div style={{ flex: 1, height: 14, borderRadius: 999, background: "rgba(10,14,44,.06)", overflow: "hidden" }}>
              <div style={{ width: pct + "%", height: "100%", background: pct >= 75 ? "#22A06B" : pct >= 40 ? "#FD6936" : "#FD6936", transition: "width .4s ease" }} />
            </div>
            <span style={{ fontFamily: "var(--font-num)", fontWeight: 700, fontSize: 22, color: pct >= 75 ? "#22A06B" : "#0A0E2C" }}>
              {done}/{total}
            </span>
          </div>
          <a href="Proxxie Documents.html" className="btn btn-orange" style={{ marginTop: 20, display: "inline-flex", padding: "12px 20px", fontSize: 14, borderRadius: 12, textDecoration: "none" }}>
            {isEnfant ? "Ajouter un document →" : "Ajouter un document →"}
          </a>
        </div>

        {/* Right· missing items */}
        <div className="card" style={{ background: "white", border: "1px solid rgba(10,14,44,0.08)", borderRadius: 20, padding: 26 }}>
          <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 14 }}>
            <h4 style={{ fontSize: 16, fontWeight: 600, margin: 0 }}>{missing.length === 0 ? "Tout est là !" : "À ajouter pour faire grimper le score"}</h4>
            <span style={{ fontSize: 12, color: "rgba(10,14,44,.5)" }}>{missing.length} en attente</span>
          </div>
          {missing.length === 0 ? (
            <p style={{ fontSize: 13, color: "rgba(10,14,44,.55)", margin: 0, lineHeight: 1.5 }}>
              Bravo, le dossier est complet. {isEnfant ? "Tu peux revenir uploader le dernier bulletin ou le dernier devoir quand tu en as." : "Vous pouvez revenir uploader le dernier bulletin ou le dernier devoir quand vous en avez."}
            </p>
          ) : (
            <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: 10 }}>
              {missing.slice(0, 5).map((d) => (
                <li key={d.id} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 0", borderBottom: "1px solid rgba(10,14,44,.04)" }}>
                  <div style={{ width: 26, height: 26, borderRadius: 8, background: d.critical ? "rgba(253,105,54,.10)" : "rgba(72,122,255,.08)", color: d.critical ? "#FD6936" : "#487AFF", display: "grid", placeItems: "center", fontSize: 14, flexShrink: 0 }}>
                    {d.critical ? "!" : "+"}
                  </div>
                  <div style={{ flex: 1, fontSize: 13.5, color: "#0A0E2C" }}>
                    {d.label}
                    {d.critical && <span style={{ marginLeft: 6, fontSize: 11, color: "#FD6936", fontWeight: 600 }}>critique</span>}
                  </div>
                  <a href="Proxxie Documents.html" style={{ fontSize: 12, fontWeight: 600, color: "#1320CE", textDecoration: "none", padding: "6px 10px", borderRadius: 8, border: "1px solid rgba(10,14,44,.1)" }}>Uploader</a>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
};

/* ---------------- InvitationModal + CTA ---------------- */
const _proxxieGetLinkCode = () => {
  try {
    let c = localStorage.getItem("proxxie.linkCode");
    if (!c) {
      const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
      let r = "PRX-";
      for (let i = 0; i < 4; i++) r += chars.charAt(Math.floor(Math.random() * chars.length));
      c = r;
      localStorage.setItem("proxxie.linkCode", c);
    }
    return c;
  } catch (e) { return "PRX-DEMO"; }
};

const InvitationCTA = ({ onOpen }) => {
  const role = useProxxieRole();
  const isEnfant = role === "enfant";
  return (
    <section style={{ margin: "0 auto 32px", padding: "0 24px", maxWidth: 1280 }}>
      <div style={{
        background: "linear-gradient(135deg, #F5EB3F 0%, #FFD86A 100%)",
        borderRadius: 20, padding: "26px 28px",
        display: "grid", gridTemplateColumns: "1fr auto", gap: 24, alignItems: "center",
      }}>
        <div>
          <span className="eyebrow"><span className="dot"></span>Comparer · 2 perspectives valent mieux qu'une</span>
          <h3 style={{ fontFamily: "var(--font-display)", fontSize: 24, fontWeight: 600, letterSpacing: "-0.02em", margin: "10px 0 6px", color: "#0A0E2C" }}>
            {isEnfant ? "Invite ton parent à passer les mêmes tests" : "Invitez votre ado à passer les mêmes tests"}
          </h3>
          <p style={{ color: "rgba(10,14,44,.7)", fontSize: 14, margin: 0, lineHeight: 1.5, maxWidth: 720 }}>
            {isEnfant
              ? "Quand ton parent passe aussi RIASEC, MBTI ou les valeurs, on compare les deux profils côte à côte. Les écarts sont souvent là où les conversations s'ouvrent."
              : "Quand votre ado passe les mêmes tests, on compare les deux profils côte à côte. Les écarts sont souvent là où les conversations s'ouvrent."}
          </p>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 8, alignItems: "flex-end" }}>
          <button onClick={onOpen} className="btn btn-orange" style={{ padding: "14px 22px", fontSize: 14, borderRadius: 12, whiteSpace: "nowrap" }}>
            {isEnfant ? "Inviter mon parent →" : "Inviter mon ado →"}
          </button>
          <a href="comparaison.html" style={{ fontSize: 12, fontWeight: 600, color: "#0A0E2C", textDecoration: "underline", textDecorationColor: "rgba(10,14,44,.35)", whiteSpace: "nowrap" }}>
            Voir un aperçu de la comparaison →
          </a>
        </div>
      </div>
    </section>
  );
};

const InvitationModal = ({ open, onClose }) => {
  const role = useProxxieRole();
  const isEnfant = role === "enfant";
  const [code] = React.useState(_proxxieGetLinkCode);
  const [copied, setCopied] = React.useState(false);
  if (!open) return null;
  const target = isEnfant ? "parent" : "ado";
  const targetCap = isEnfant ? "parent" : "ado";

  const copy = () => {
    try { navigator.clipboard.writeText(code); setCopied(true); setTimeout(() => setCopied(false), 1600); } catch (e) {}
  };

  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, background: "rgba(10,14,44,.55)", display: "grid", placeItems: "center", zIndex: 200, padding: 20 }}>
      <div onClick={(e) => e.stopPropagation()} style={{ background: "white", borderRadius: 24, maxWidth: 480, width: "100%", padding: 32, boxShadow: "0 20px 60px rgba(10,14,44,.25)" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
          <span className="eyebrow"><span className="dot"></span>Inviter mon {target}</span>
          <button onClick={onClose} style={{ background: "transparent", border: "none", fontSize: 22, color: "rgba(10,14,44,.5)", cursor: "pointer", padding: 4, lineHeight: 1, fontFamily: "inherit" }} aria-label="Fermer">×</button>
        </div>
        <h3 style={{ fontFamily: "var(--font-display)", fontSize: 26, fontWeight: 600, letterSpacing: "-0.02em", margin: "0 0 10px" }}>
          {isEnfant ? "Partage ce code à ton parent" : "Partagez ce code à votre ado"}
        </h3>
        <p style={{ fontSize: 14, color: "rgba(10,14,44,.55)", margin: "0 0 20px", lineHeight: 1.5 }}>
          {isEnfant
            ? "À l'inscription, ton " + targetCap + " colle ce code et vos comptes sont liés. Les tests passés des deux côtés deviennent comparables."
            : "À l'inscription, votre " + targetCap + " colle ce code et vos comptes sont liés. Les tests passés des deux côtés deviennent comparables."}
        </p>
        <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "14px 18px", border: "1.5px dashed rgba(19,32,206,.25)", borderRadius: 14, background: "rgba(19,32,206,.03)", marginBottom: 20 }}>
          <span style={{ flex: 1, fontFamily: "var(--font-num)", fontSize: 22, fontWeight: 700, color: "#1320CE", letterSpacing: "0.08em" }}>{code}</span>
          <button onClick={copy} className="btn btn-orange" style={{ padding: "10px 16px", fontSize: 13, borderRadius: 10 }}>
            {copied ? "Copié ✓" : "Copier"}
          </button>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
          <a href={"mailto:?subject=" + encodeURIComponent("Rejoins-moi sur Proxxie") + "&body=" + encodeURIComponent((isEnfant ? "Salut, " : "Bonjour, ") + "rejoins-moi sur Proxxie avec mon code · " + code + "\n\nhttps://www.proxxie.co/connexion")} style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8, padding: "12px 14px", borderRadius: 10, border: "1px solid rgba(10,14,44,.12)", fontSize: 13, fontWeight: 600, textDecoration: "none", color: "#0A0E2C" }}>📧 Email</a>
          <a href={"sms:?body=" + encodeURIComponent((isEnfant ? "Salut, " : "Bonjour, ") + "rejoins-moi sur Proxxie avec mon code · " + code + " https://www.proxxie.co/connexion")} style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8, padding: "12px 14px", borderRadius: 10, border: "1px solid rgba(10,14,44,.12)", fontSize: 13, fontWeight: 600, textDecoration: "none", color: "#0A0E2C" }}>💬 SMS</a>
        </div>
        <p style={{ fontSize: 12, color: "rgba(10,14,44,.45)", margin: "16px 0 0", lineHeight: 1.4 }}>
          {isEnfant
            ? "Une fois ton parent inscrit, vous verrez tous les deux la page de comparaison sur vos dashboards."
            : "Une fois votre ado inscrit, vous verrez tous les deux la page de comparaison sur vos dashboards."}
        </p>
      </div>
    </div>
  );
};
"""

# JSX insertion points in the existing Dashboard return
RETURN_ANCHOR_HEADER = '<DashHeader />'
RETURN_ANCHOR_AFTER_WELCOME = '<WelcomeBanner onOpen={openDrawer} audit={t.audit} />'
RETURN_ANCHOR_AFTER_TESTS = '<TestsPanel />'
RETURN_ANCHOR_REFERRAL_MODAL = '<ReferralModal open={referralOpen} onClose={() => setReferralOpen(false)} invited={invited} setInvited={setInvited} />'

# State hook to add: inviteOpen
STATE_HOOK_ANCHOR = 'const [referralOpen, setReferralOpen] = React.useState(false);'
STATE_HOOK_INSERTION = STATE_HOOK_ANCHOR + '\n  const [inviteOpen, setInviteOpen] = React.useState(false);'


def patch_asset_text(src: str) -> str:
    if MARKER in src:
        raise SystemExit("asset already patched")

    if "const Dashboard = () =>" not in src:
        raise SystemExit("Dashboard component not found")
    if STATE_HOOK_ANCHOR not in src:
        raise SystemExit("State hook anchor not found")
    if RETURN_ANCHOR_HEADER not in src:
        raise SystemExit("DashHeader anchor not found")
    if RETURN_ANCHOR_AFTER_WELCOME not in src:
        raise SystemExit("WelcomeBanner anchor not found")
    if RETURN_ANCHOR_AFTER_TESTS not in src:
        raise SystemExit("TestsPanel anchor not found (run _patch_tests_panel.py first)")
    if RETURN_ANCHOR_REFERRAL_MODAL not in src:
        raise SystemExit("ReferralModal anchor not found")

    # 1. Inject component defs before const Dashboard
    src = src.replace("const Dashboard = () =>", COMPONENTS_JSX + "\nconst Dashboard = () =>", 1)
    # 2. Add inviteOpen state
    src = src.replace(STATE_HOOK_ANCHOR, STATE_HOOK_INSERTION, 1)
    # 3. Inject ReengagementBanner right after DashHeader
    src = src.replace(RETURN_ANCHOR_HEADER, RETURN_ANCHOR_HEADER + '\n      <ReengagementBanner />', 1)
    # 4. Inject GamificationPanel after WelcomeBanner
    src = src.replace(RETURN_ANCHOR_AFTER_WELCOME, RETURN_ANCHOR_AFTER_WELCOME + '\n      <GamificationPanel />', 1)
    # 5. Inject DocsCompleteness + InvitationCTA after TestsPanel
    src = src.replace(RETURN_ANCHOR_AFTER_TESTS,
                      RETURN_ANCHOR_AFTER_TESTS + '\n      <DocsCompletenessPanel />\n      <InvitationCTA onOpen={() => setInviteOpen(true)} />', 1)
    # 6. Inject InvitationModal next to ReferralModal
    src = src.replace(RETURN_ANCHOR_REFERRAL_MODAL,
                      RETURN_ANCHOR_REFERRAL_MODAL + '\n      <InvitationModal open={inviteOpen} onClose={() => setInviteOpen(false)} />', 1)
    return src


def extract_template(html: str):
    start_m = re.search(r'<script[^>]*type="__bundler/template"[^>]*>', html)
    if not start_m: return None
    last_close = html.rfind("</script>")
    if last_close <= start_m.end(): return None
    raw = html[start_m.end():last_close]
    return start_m.end(), last_close, json.loads(raw.strip())


def patch_manifest_asset(html: str, uuid: str) -> tuple:
    m = re.search(r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)', html, re.DOTALL)
    if not m: return html, "no manifest"
    manifest = json.loads(m.group(2))
    if uuid not in manifest: return html, f"asset {uuid[:8]} not found"
    entry = manifest[uuid]
    data = base64.b64decode(entry["data"])
    compressed = entry.get("compressed", False)
    if compressed: data = gzip.decompress(data)
    src = data.decode("utf-8")
    if MARKER in src:
        return html, "asset already patched"
    new_src = patch_asset_text(src)
    new_data = new_src.encode("utf-8")
    if compressed: new_data = gzip.compress(new_data)
    entry["data"] = base64.b64encode(new_data).decode("ascii")
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]
    return new_html, f"asset patched ({len(src)} -> {len(new_src)} chars)"


STRIP_RE = re.compile(
    r'\n/\* __proxxie_dashboard_v2__ \*/.*?(?=\nconst Dashboard = \(\) =>)',
    flags=re.S,
)


def strip_v2(src: str) -> str:
    """Reverse the patch in-place so we can re-apply with fresh JSX. Removes
    the component block AND the JSX insertions inside Dashboard()."""
    src = STRIP_RE.sub("", src)
    src = src.replace(STATE_HOOK_INSERTION, STATE_HOOK_ANCHOR, 1)
    src = src.replace(RETURN_ANCHOR_HEADER + '\n      <ReengagementBanner />', RETURN_ANCHOR_HEADER, 1)
    src = src.replace(RETURN_ANCHOR_AFTER_WELCOME + '\n      <GamificationPanel />', RETURN_ANCHOR_AFTER_WELCOME, 1)
    src = src.replace(RETURN_ANCHOR_AFTER_TESTS + '\n      <DocsCompletenessPanel />\n      <InvitationCTA onOpen={() => setInviteOpen(true)} />', RETURN_ANCHOR_AFTER_TESTS, 1)
    src = src.replace(RETURN_ANCHOR_REFERRAL_MODAL + '\n      <InvitationModal open={inviteOpen} onClose={() => setInviteOpen(false)} />', RETURN_ANCHOR_REFERRAL_MODAL, 1)
    return src


def patch_one(target: pathlib.Path) -> str:
    if not target.exists(): return "SKIP missing"
    html = target.read_text(encoding="utf-8")

    # If already patched, strip the existing block from the asset so we can re-apply.
    m = re.search(r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)', html, re.DOTALL)
    if m:
        manifest = json.loads(m.group(2))
        if DASHBOARD_ASSET in manifest:
            entry = manifest[DASHBOARD_ASSET]
            data = base64.b64decode(entry["data"])
            comp = entry.get("compressed", False)
            if comp: data = gzip.decompress(data)
            src = data.decode("utf-8")
            if MARKER in src:
                src = strip_v2(src)
                nd = src.encode("utf-8")
                if comp: nd = gzip.compress(nd)
                entry["data"] = base64.b64encode(nd).decode("ascii")
                new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
                html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]

    new_html, status = patch_manifest_asset(html, DASHBOARD_ASSET)
    if new_html != html:
        target.write_text(new_html, encoding="utf-8")
    return status


if __name__ == "__main__":
    for fn in TARGETS:
        p = REPO / fn
        try:
            print(f"{fn}: {patch_one(p)}")
        except SystemExit as e:
            print(f"{fn}: ERROR · {e}")

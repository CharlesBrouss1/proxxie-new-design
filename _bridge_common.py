"""Pont backend Proxxie · transform partagé (retour automatique).

wire_bridge(block, test_id, page_filename) transforme un BLOCK d'app de test
(ancien pont statique #predict=/#results=) en pont API comparison :
  parent prédit -> POST create -> lien ?code=PXC-XXXX
  l'ado ouvre le lien -> GET -> test self_compare -> POST child (relance mail)
  le parent revient via ?code=...&role=parent -> GET les deux -> ComparePanel

Anchors vérifiés byte-identiques sur brief/caas/dweck/grit/via.
"""

# Helpers agnostiques injectés juste avant `const TestApp = () => {`.
# Tokens remplacés : __TEST_ID__, __PAGE_FILENAME__.
HELPERS = '''
// === Pont backend Proxxie · retour automatique (l'ado ne fait pas l'effort) ===
const API_BASE = "https://proxxie-app-seven.vercel.app";
const PAGE_URL = "https://charlesbrouss1.github.io/proxxie-new-design/__PAGE_FILENAME__";
const TEST_ID = "__TEST_ID__";

const getUrlParam = (name) => {
  try { return new URLSearchParams(window.location.search).get(name); } catch (e) { return null; }
};

const apiPost = (path, body) =>
  fetch(API_BASE + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }).then((r) => r.json());

const BridgeScreen = ({ title, sub }) => (
  <section style={{ paddingTop: 90, paddingBottom: 120 }}>
    <div className="shell" style={{ maxWidth: 560, textAlign: "center" }}>
      <h1 style={{ fontSize: 28, marginBottom: 14, color: "var(--c-ink)" }}>{title}</h1>
      <p style={{ fontSize: 16, color: "var(--c-muted)", lineHeight: 1.6 }}>{sub}</p>
    </div>
  </section>
);

// Panneau parent · crée le code de comparaison + capture l'email pour la relance.
const ApiShareLinkPanel = ({ answers, accent }) => {
  const [name, setName] = React.useState("");
  const [status, setStatus] = React.useState("idle"); // idle | loading | done | error
  const [link, setLink] = React.useState("");
  const [code, setCode] = React.useState("");
  const [copied, setCopied] = React.useState(false);
  const [email, setEmail] = React.useState("");
  const [emailStatus, setEmailStatus] = React.useState("idle"); // idle | loading | done | error

  const createCode = () => {
    setStatus("loading");
    apiPost("/api/comparison", {
      parentResults: { [TEST_ID]: { a: answers, n: name || "Le parent" } },
      tests: [TEST_ID],
    })
      .then((data) => {
        if (!data || !data.ok || !data.code) { setStatus("error"); return; }
        setCode(data.code);
        setLink(PAGE_URL + "?code=" + encodeURIComponent(data.code));
        setStatus("done");
      })
      .catch(() => setStatus("error"));
  };

  const copyLink = () => {
    try {
      navigator.clipboard.writeText(link);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {}
  };

  const sendLead = () => {
    if (!email || !code) return;
    setEmailStatus("loading");
    apiPost("/api/comparison/" + encodeURIComponent(code) + "/lead", { email: email, consent: true })
      .then((data) => setEmailStatus(data && data.ok ? "done" : "error"))
      .catch(() => setEmailStatus("error"));
  };

  return (
    <div style={{ background: "white", borderRadius: 20, padding: 28, border: "1px solid var(--c-line)", marginBottom: 30 }}>
      <h2 style={{ fontSize: 20, marginBottom: 8 }}>Envoie le test à ton ado</h2>
      <p style={{ fontSize: 14, color: "var(--c-muted)", lineHeight: 1.55, marginBottom: 18 }}>
        Il répond pour de vrai, et la comparaison avec ta prédiction revient ici automatiquement. Pas de copier-coller, pas d'effort de sa part.
      </p>

      {status !== "done" && (
        <div style={{ display: "grid", gap: 12 }}>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Comment ton ado te connaît (Papa, Maman…)"
            style={{ padding: "12px 14px", borderRadius: 10, border: "1px solid var(--c-line)", fontSize: 15, fontFamily: "inherit" }}
          />
          <button className="btn btn-orange btn-lg" onClick={createCode} disabled={status === "loading"} style={{ background: accent }}>
            {status === "loading" ? "Création du lien…" : "Générer le lien à partager"}
          </button>
          {status === "error" && <div style={{ color: "#C2410C", fontSize: 13.5 }}>Une erreur est survenue. Réessaie dans un instant.</div>}
        </div>
      )}

      {status === "done" && (
        <div style={{ display: "grid", gap: 16 }}>
          <div style={{ display: "grid", gap: 8 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: accent }}>Lien à envoyer à ton ado</div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <input readOnly value={link} style={{ flex: 1, minWidth: 220, padding: "11px 13px", borderRadius: 10, border: "1px solid var(--c-line)", fontSize: 13.5, fontFamily: "inherit", color: "var(--c-ink-2)" }} />
              <button className="btn btn-ghost" onClick={copyLink}>{copied ? "Copié ✓" : "Copier"}</button>
            </div>
          </div>
          <div style={{ borderTop: "1px solid var(--c-line)", paddingTop: 16, display: "grid", gap: 8 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--c-ink)" }}>Reçois un email quand il a répondu</div>
            <p style={{ fontSize: 13, color: "var(--c-muted)", margin: 0, lineHeight: 1.5 }}>On te prévient dès que la comparaison est prête.</p>
            {emailStatus !== "done" && (
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="ton@email.com"
                  style={{ flex: 1, minWidth: 200, padding: "11px 13px", borderRadius: 10, border: "1px solid var(--c-line)", fontSize: 14, fontFamily: "inherit" }}
                />
                <button className="btn btn-orange" onClick={sendLead} disabled={emailStatus === "loading"} style={{ background: accent }}>
                  {emailStatus === "loading" ? "…" : "Me prévenir"}
                </button>
              </div>
            )}
            {emailStatus === "done" && <div style={{ fontSize: 13.5, color: "#0E7490", fontWeight: 600 }}>C'est noté, on te prévient par email ✓</div>}
            {emailStatus === "error" && <div style={{ color: "#C2410C", fontSize: 13 }}>Email non enregistré, réessaie.</div>}
          </div>
        </div>
      )}
    </div>
  );
};

'''

# Ancien head (6 lignes d'état hash). Byte-identique sur les 5 patchers.
OLD_HEAD = '''  const PARENT_PREDICT = React.useMemo(() => readPredictHash(), []);
  const RESULTS_HASH = React.useMemo(() => readResultsHash(), []);
  const [persona, setPersona] = React.useState(null);
  const [mode, setMode] = React.useState(RESULTS_HASH ? "results" : (PARENT_PREDICT ? "compare-intro" : "landing"));
  const [results, setResults] = React.useState(RESULTS_HASH ? computeResults(RESULTS_HASH.a) : null);
  const [answers, setAnswers] = React.useState(RESULTS_HASH ? RESULTS_HASH.a : null);'''

# Nouveau head · CODE/ROLE + bridge state + useEffect GET + variables dérivées.
NEW_HEAD = '''  // Pont backend · ?code=PXC-XXXX (+ ?role=parent au retour). Sans code -> flux normal.
  const CODE = React.useMemo(() => getUrlParam("code"), []);
  const ROLE = React.useMemo(() => getUrlParam("role"), []);
  const [bridge, setBridge] = React.useState(null);
  const [persona, setPersona] = React.useState(null);
  const [mode, setMode] = React.useState(CODE ? "bridge-loading" : "landing");
  const [results, setResults] = React.useState(null);
  const [answers, setAnswers] = React.useState(null);

  React.useEffect(() => {
    if (!CODE) return;
    let cancelled = false;
    fetch(API_BASE + "/api/comparison/" + encodeURIComponent(CODE))
      .then((r) => r.json())
      .then((data) => {
        if (cancelled) return;
        if (!data || !data.ok) { setBridge({ status: "error" }); setMode("bridge-error"); return; }
        const pr = data.parentResults && data.parentResults[TEST_ID];
        const parentAnswers = pr && pr.a ? pr.a : null;
        const parentName = (pr && pr.n) || "Le parent";
        if (ROLE === "parent") {
          const cr = data.childResults && data.childResults[TEST_ID];
          if (data.childDone && cr && cr.a) {
            setBridge({ status: "parent-return", code: CODE, parentName: parentName, parentAnswers: parentAnswers, teenAnswers: cr.a });
            setAnswers(cr.a);
            setResults(computeResults(cr.a));
            setMode("results");
          } else {
            setBridge({ status: "parent-waiting", code: CODE });
            setMode("bridge-waiting");
          }
        } else {
          setBridge({ status: "teen", code: CODE, parentName: parentName, parentAnswers: parentAnswers });
          setMode("compare-intro");
        }
      })
      .catch(() => { if (!cancelled) { setBridge({ status: "error" }); setMode("bridge-error"); } });
    return () => { cancelled = true; };
  }, [CODE, ROLE]);

  const isTeenBridge = bridge && bridge.status === "teen";
  const isParentReturn = bridge && bridge.status === "parent-return";
  const PARENT_PREDICT = (isTeenBridge || isParentReturn) ? { n: bridge.parentName, a: bridge.parentAnswers } : null;'''

# onComplete · variante multi-ligne (caas/dweck/grit/via) : insère le POST child
# juste avant le bloc trackEvent.
ONCOMPLETE_MULTILINE_ANCHOR = '''    if (window.trackEvent) {'''
ONCOMPLETE_MULTILINE_REPLACE = '''    if (isTeenBridge && bridge && bridge.code) {
      apiPost("/api/comparison/" + encodeURIComponent(bridge.code) + "/child", {
        childResults: { [TEST_ID]: { a: ans } },
        consent: true,
      }).catch(() => {});
    }
    if (window.trackEvent) {'''

# onComplete · variante une ligne (brief).
ONCOMPLETE_ONELINE_ANCHOR = '''  const onComplete = (ans) => { setAnswers(ans); setResults(computeResults(ans)); setMode("results"); window.scrollTo({ top: 0, behavior: "smooth" }); };'''
ONCOMPLETE_ONELINE_REPLACE = '''  const onComplete = (ans) => {
    setAnswers(ans); setResults(computeResults(ans)); setMode("results");
    window.scrollTo({ top: 0, behavior: "smooth" });
    if (isTeenBridge && bridge && bridge.code) {
      apiPost("/api/comparison/" + encodeURIComponent(bridge.code) + "/child", { childResults: { [TEST_ID]: { a: ans } }, consent: true }).catch(() => {});
    }
  };'''

# Écrans de pont insérés juste après <ProxxieNav />.
PROXXIENAV_ANCHOR = '''      <ProxxieNav />'''
PROXXIENAV_REPLACE = '''      <ProxxieNav />
      {mode === "bridge-loading" && <BridgeScreen title="Chargement…" sub="On récupère le test qu'on t'a partagé." />}
      {mode === "bridge-error" && <BridgeScreen title="Lien introuvable" sub="Ce lien de comparaison n'existe plus ou a expiré. Demande à la personne de t'en renvoyer un." />}
      {mode === "bridge-waiting" && <BridgeScreen title="Ton ado n'a pas encore répondu" sub="Dès qu'il aura passé le test, la comparaison s'affichera ici. On t'envoie un email si tu as laissé ton adresse." />}'''

OLD_EFFECTIVE = '''  const effectivePersona = PARENT_PREDICT ? "self_compare" : persona;'''
NEW_EFFECTIVE = '''  const effectivePersona = (isTeenBridge || isParentReturn) ? "self_compare" : persona;'''

# ShareLinkPanel -> ApiShareLinkPanel (accent conservé via backreference).
import re

SHARELINK_RE = re.compile(
    r'<ShareLinkPanel testCode="[^"]*" accent="(#[0-9A-Fa-f]{6})" answers=\{answers\} defaultName="" onSkip=\{\(\) => \{\}\} />'
)
SHARELINK_REPLACE = r'<ApiShareLinkPanel answers={answers} accent="\1" />'

TESTAPP_ANCHOR = '''const TestApp = () => {'''


def _replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise ValueError(f"wire_bridge: anchor '{label}' trouvé {n} fois (attendu 1)")
    return text.replace(old, new, 1)


def wire_bridge(block: str, test_id: str, page_filename: str) -> str:
    """Transforme un BLOCK old-bridge en API-bridge. Idempotence non requise."""
    if "ApiShareLinkPanel" in block:
        raise ValueError("wire_bridge: BLOCK déjà transformé (ApiShareLinkPanel présent)")

    helpers = HELPERS.replace("__TEST_ID__", test_id).replace("__PAGE_FILENAME__", page_filename)

    # 1. Injecter les helpers juste avant const TestApp.
    out = _replace_once(block, TESTAPP_ANCHOR, helpers + TESTAPP_ANCHOR, "TestApp")

    # 2. Remplacer le head hash par le head API.
    out = _replace_once(out, OLD_HEAD, NEW_HEAD, "OLD_HEAD")

    # 3. onComplete · POST child (multi-ligne sinon une ligne).
    if ONCOMPLETE_MULTILINE_ANCHOR in out:
        out = _replace_once(out, ONCOMPLETE_MULTILINE_ANCHOR, ONCOMPLETE_MULTILINE_REPLACE, "onComplete(multi)")
    elif ONCOMPLETE_ONELINE_ANCHOR in out:
        out = _replace_once(out, ONCOMPLETE_ONELINE_ANCHOR, ONCOMPLETE_ONELINE_REPLACE, "onComplete(one)")
    else:
        raise ValueError("wire_bridge: aucun anchor onComplete trouvé")

    # 4. effectivePersona.
    out = _replace_once(out, OLD_EFFECTIVE, NEW_EFFECTIVE, "effectivePersona")

    # 5. Écrans de pont après ProxxieNav.
    out = _replace_once(out, PROXXIENAV_ANCHOR, PROXXIENAV_REPLACE, "ProxxieNav")

    # 6. ShareLinkPanel -> ApiShareLinkPanel.
    new_out, n = SHARELINK_RE.subn(SHARELINK_REPLACE, out)
    if n != 1:
        raise ValueError(f"wire_bridge: ShareLinkPanel matché {n} fois (attendu 1)")
    return new_out

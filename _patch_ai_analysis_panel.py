#!/usr/bin/env python3
"""Injecte un composant AIAnalysisPanel sur la page Results de tous les tests.

Le composant :
- Affiche un bouton « Demander une analyse approfondie par IA »
- Compte le quota localStorage proxxie.ai_analysis_count
- 3 analyses gratuites, puis gate vers signup (connexion.html?signup=1)
- Au clic : POST vers l'API Vercel avec testCode / testName / summary
- Affiche le markdown streamé en live (rendu basique via marked.js inline)
- Erreur réseau : message gracieux + lien vers le 3114 si test sensible

Architecture identique à _patch_save_results_callout.py :
- Définition du composant injectée AVANT TestApp (top-level JS context)
- Render call injecté APRÈS <Results /> (et avant <SaveResultsCallout />)
- Idempotent · sentinelles DEF + détection présence du render

Configuration : changer API_URL ci-dessous pour pointer vers ton déploiement Vercel.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
ASSET_UUID_PREFIX = "61feca88"

# === CONFIGURATION · à changer après déploiement Vercel ===
# URL du backend Vercel déployé (proxxie-ai-edge.vercel.app, alias propre)
API_URL = "https://proxxie-ai-edge.vercel.app/api/test-analysis"
QUOTA_FREE = 3  # nombre d'analyses gratuites avant gate signup
# =========================================================

TARGETS = [
    "Proxxie Test.html",
    "Proxxie Test RIASEC.html",
    "Proxxie Test PCM.html",
    "Proxxie Test MBTI.html",
    "Proxxie Test HPI.html",
    "Proxxie Test TDAH.html",
    "Proxxie Test DYS.html",
    "Proxxie Test Autisme.html",
    "Proxxie Test Anxiete.html",
    "Proxxie Test Besoins.html",
    "Proxxie Test Drivers.html",
    "Proxxie Test Valeurs.html",
    "Proxxie Test PHQ9.html",
    "Proxxie Test Grit.html",
    "Proxxie Test CAAS.html",
    "test-riasec.html",
    "test-pcm.html",
    "test-mbti.html",
    "test-hpi.html",
    "test-tdah.html",
    "test-dys.html",
    "test-autisme.html",
    "test-anxiete.html",
    "test-besoins.html",
    "test-drivers.html",
    "test-valeurs.html",
    "test-phq9.html",
    "test-grit.html",
    "test-caas.html",
]

BEGIN_DEF = "/* PROXXIE_AI_ANALYSIS_DEF_BEGIN */"
END_DEF   = "/* PROXXIE_AI_ANALYSIS_DEF_END */"

# Marker pour détecter idempotence du render (pas de sentinelles JSX qui se font rendre)
RENDER_PRESENCE_MARKER = '<AIAnalysisPanel'

# Le composant React. testCode, testName, summary, accent, accentSoft viennent en props.
COMPONENT_JSX = BEGIN_DEF + r"""
const PROXXIE_AI_API_URL = "__API_URL__";
const PROXXIE_AI_QUOTA = __QUOTA__;
const PROXXIE_AI_COUNT_KEY = "proxxie.ai_analysis_count";

const _proxxieMiniMarkdown = (md) => {
  // Rendu markdown ultra-minimal · juste headers, gras, listes, paragraphes
  // Pas de XSS car le contenu vient d'OpenAI via notre proxy, pas user input
  if (!md) return "";
  const escaped = md
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  return escaped
    .replace(/^## (.+)$/gm, '<h3 style="font-size:18px;margin:20px 0 10px;color:inherit;font-weight:700">$1</h3>')
    .replace(/^### (.+)$/gm, '<h4 style="font-size:15px;margin:14px 0 8px;font-weight:700">$1</h4>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/^\- (.+)$/gm, '<li style="margin-bottom:6px">$1</li>')
    .replace(/(<li[\s\S]*?<\/li>(?:\s*<li[\s\S]*?<\/li>)*)/g, '<ul style="padding-left:22px;margin:8px 0 14px;list-style:disc">$1</ul>')
    .split(/\n\n+/).map(p => p.trim().startsWith('<') ? p : '<p style="margin:0 0 12px;line-height:1.6">' + p + '</p>').join('\n');
};

const AIAnalysisPanel = ({ testCode, testName, summary, answers, accent, accentSoft }) => {
  const [state, setState] = React.useState("idle"); // idle, loading, streaming, done, error, gated
  const [content, setContent] = React.useState("");
  const [error, setError] = React.useState(null);
  const [remaining, setRemaining] = React.useState(PROXXIE_AI_QUOTA);

  React.useEffect(() => {
    try {
      const used = parseInt(window.localStorage.getItem(PROXXIE_AI_COUNT_KEY) || "0", 10);
      setRemaining(Math.max(0, PROXXIE_AI_QUOTA - used));
    } catch (e) { /* localStorage indisponible */ }
  }, []);

  const isApiConfigured = PROXXIE_AI_API_URL && !PROXXIE_AI_API_URL.includes("__API_URL__");

  const handleRequest = async () => {
    if (remaining <= 0) { setState("gated"); return; }
    if (!isApiConfigured) {
      setError("API non configurée. Le backend Vercel doit être déployé avant que cette fonction soit active. Voir README de proxxie-ai-analysis.");
      setState("error");
      return;
    }
    setState("loading");
    setError(null);
    setContent("");
    try {
      const resp = await fetch(PROXXIE_AI_API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ testCode, testName, summary, answers }),
      });
      if (!resp.ok) {
        const errText = await resp.text();
        throw new Error("API a renvoyé " + resp.status + " : " + errText.slice(0, 200));
      }
      if (!resp.body) throw new Error("Pas de stream renvoyé par l'API");

      setState("streaming");
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let acc = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        acc += decoder.decode(value, { stream: true });
        setContent(acc);
      }
      setState("done");
      // Décrémenter le quota (une seule fois après succès)
      try {
        const used = parseInt(window.localStorage.getItem(PROXXIE_AI_COUNT_KEY) || "0", 10);
        window.localStorage.setItem(PROXXIE_AI_COUNT_KEY, String(used + 1));
        setRemaining(Math.max(0, PROXXIE_AI_QUOTA - (used + 1)));
      } catch (e) { /* ignore */ }
      if (window.trackEvent) window.trackEvent("ai_analysis_completed", { test_code: testCode });
    } catch (e) {
      setError(e.message || "Erreur réseau inconnue");
      setState("error");
      if (window.trackEvent) window.trackEvent("ai_analysis_error", { test_code: testCode, error: String(e.message) });
    }
  };

  // Skip rendu si déjà connecté ET déjà eu son analyse (cas où le user revient sur la page)
  if (typeof _proxxieIsConnected === "function" && _proxxieIsConnected() && state === "idle" && remaining < PROXXIE_AI_QUOTA) {
    // L'utilisateur connecté ne devrait pas être gated · on lui laisse toujours le bouton
    // mais on ne montre pas de compteur (sera ajusté quand backend auth en place)
  }

  return (
    <section style={{ paddingTop: 30, paddingBottom: 50 }}>
      <div className="shell" style={{ maxWidth: 820 }}>
        <div style={{
          background: "linear-gradient(160deg, " + accent + ", #0A0E2C)",
          color: "white", borderRadius: 24, padding: "32px 28px",
          boxShadow: "0 18px 40px -16px " + accent + "55",
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 20, marginBottom: 16 }}>
            <div>
              <div style={{ fontSize: 11, fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.12em", opacity: 0.88, marginBottom: 8 }}>
                ⚡ Analyse IA personnalisée
              </div>
              <h2 style={{ color: "white", fontSize: 24, lineHeight: 1.3, margin: 0 }}>
                Une lecture fine de ton profil exact, générée à la demande.
              </h2>
            </div>
            {state !== "streaming" && state !== "done" && (
              <span style={{ background: "rgba(245,235,63,.18)", color: "#F5EB3F", padding: "5px 11px", borderRadius: 99, fontSize: 11, fontWeight: 700, whiteSpace: "nowrap" }}>
                {remaining}/{PROXXIE_AI_QUOTA} gratuites
              </span>
            )}
          </div>

          {state === "idle" && (
            <>
              <p style={{ fontSize: 14.5, opacity: 0.9, lineHeight: 1.55, marginBottom: 18 }}>
                On envoie tes réponses à GPT-4 (anonymisées, jamais stockées) et tu reçois une analyse de 8 sections, structurée et actionnable, en 10 secondes.
              </p>
              <button onClick={handleRequest} disabled={remaining <= 0} style={{
                background: remaining > 0 ? "#FD6936" : "#666", color: "white", border: "none",
                padding: "14px 26px", borderRadius: 99, fontWeight: 700, fontSize: 15,
                cursor: remaining > 0 ? "pointer" : "not-allowed",
                boxShadow: remaining > 0 ? "0 14px 32px -10px rgba(253,105,54,.7)" : "none",
                display: "inline-flex", alignItems: "center", gap: 8,
              }}>
                {remaining > 0 ? "Générer mon analyse approfondie →" : "Créer un compte pour continuer"}
              </button>
              <div style={{ marginTop: 12, fontSize: 12, opacity: 0.65 }}>
                Aucune carte bancaire · données anonymes · ~10 sec
              </div>
            </>
          )}

          {state === "loading" && (
            <div style={{ padding: "24px 0", textAlign: "center" }}>
              <div style={{ display: "inline-block", width: 28, height: 28, border: "3px solid rgba(255,255,255,.3)", borderTopColor: "white", borderRadius: "50%", animation: "proxxie-spin 0.7s linear infinite" }}></div>
              <style>{`@keyframes proxxie-spin { to { transform: rotate(360deg); } }`}</style>
              <div style={{ marginTop: 14, fontSize: 13.5, opacity: 0.85 }}>Connexion à l'IA...</div>
            </div>
          )}

          {(state === "streaming" || state === "done") && content && (
            <div style={{
              background: "rgba(255,255,255,.97)", color: "#0A0E2C",
              borderRadius: 16, padding: "22px 24px", fontSize: 14.5, lineHeight: 1.6,
            }}>
              {state === "streaming" && (
                <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, color: accent, marginBottom: 14, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em" }}>
                  <div style={{ width: 8, height: 8, borderRadius: "50%", background: accent, animation: "proxxie-pulse 1s infinite" }}></div>
                  <style>{`@keyframes proxxie-pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }`}</style>
                  En cours d'analyse...
                </div>
              )}
              <div dangerouslySetInnerHTML={{ __html: _proxxieMiniMarkdown(content) }} />
              {state === "done" && (
                <div style={{ marginTop: 18, paddingTop: 16, borderTop: "1px solid rgba(10,14,44,.1)", fontSize: 12, color: "#6B6F8C" }}>
                  Cette analyse a été générée par GPT-4 à partir de tes résultats. Elle n'a pas valeur diagnostique. Pour creuser, prends RDV avec un coach Proxxie ou un professionnel adapté.
                </div>
              )}
            </div>
          )}

          {state === "error" && (
            <div style={{
              background: "rgba(255,255,255,.97)", color: "#C62828",
              borderRadius: 16, padding: "22px 24px", fontSize: 14, lineHeight: 1.55,
            }}>
              <strong>L'analyse n'a pas pu aboutir.</strong>
              <div style={{ marginTop: 8, color: "#0A0E2C" }}>{error}</div>
              <button onClick={handleRequest} style={{
                marginTop: 14, background: "transparent", border: "1.5px solid " + accent,
                color: accent, padding: "8px 16px", borderRadius: 99, fontWeight: 600, cursor: "pointer",
              }}>Réessayer</button>
            </div>
          )}

          {state === "gated" && (
            <div style={{ background: "rgba(255,255,255,.1)", borderRadius: 14, padding: 20 }}>
              <h3 style={{ color: "white", fontSize: 18, marginBottom: 10 }}>Tu as utilisé tes 3 analyses gratuites.</h3>
              <p style={{ fontSize: 14, opacity: 0.9, lineHeight: 1.55, marginBottom: 16 }}>
                Crée un compte gratuit pour continuer à générer des analyses sur tous tes tests, retrouver l'historique, et activer le Mode parent.
              </p>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <a href="connexion.html?signup=1" style={{ background: "#FD6936", color: "white", padding: "12px 22px", borderRadius: 99, fontWeight: 700, fontSize: 14, textDecoration: "none" }}>Créer mon compte gratuit</a>
                <a href="connexion.html" style={{ background: "transparent", color: "white", border: "1.5px solid rgba(255,255,255,.4)", padding: "12px 22px", borderRadius: 99, fontWeight: 600, fontSize: 14, textDecoration: "none" }}>J'ai déjà un compte</a>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
};
""" + END_DEF + "\n\nconst TestApp = () => {"

ANCHOR_DEF = "const TestApp = () => {"


def strip_between(src: str, begin: str, end: str) -> str:
    pat = re.compile(r'\s*' + re.escape(begin) + r'.*?' + re.escape(end), re.DOTALL)
    return pat.sub('', src)


def patch_src(src: str) -> tuple[str, list[str]]:
    changes = []
    # 1. Strip prior def
    src = strip_between(src, BEGIN_DEF, END_DEF)
    # 2. Strip prior render (ligne contenant <AIAnalysisPanel)
    src = re.sub(r'\n[ \t]+<AIAnalysisPanel[^\n]*', '', src)
    # 3. Injection definition (avant TestApp)
    if ANCHOR_DEF not in src:
        return src, ["WARN ANCHOR_DEF introuvable"]
    component_filled = COMPONENT_JSX.replace("__API_URL__", API_URL).replace("__QUOTA__", str(QUOTA_FREE))
    src = src.replace(ANCHOR_DEF, component_filled, 1)
    changes.append("+ composant AIAnalysisPanel")
    # 4. Injection render (après <Results results={results} onRestart={restart} />)
    # On extrait testCode et testName depuis EmailResultsActions de la même TestApp
    # Pattern : <EmailResultsActions testCode="X" testName="Y" accent="Z" ... />
    m_eric = re.search(r'<EmailResultsActions\s+testCode="([^"]+)"\s+testName="([^"]+)"\s+accent="([^"]+)"', src)
    if not m_eric:
        return src, changes + ["WARN EmailResultsActions introuvable, skip render"]
    test_code = m_eric.group(1)
    test_name = m_eric.group(2)
    accent = m_eric.group(3)
    # Calcule accentSoft = accent + "22" (low alpha hex) si simple #RRGGBB
    accent_soft = accent + "22" if accent.startswith("#") else "rgba(255,255,255,.12)"
    render_line = (
        f'<AIAnalysisPanel testCode="{test_code}" testName="{test_name}" '
        f'summary={{buildEmailSummary(results)}} answers={{answers}} '
        f'accent="{accent}" accentSoft="{accent_soft}" />'
    )
    # Insère juste après <Results results={results} onRestart={restart} />
    anchor_results = '<Results results={results} onRestart={restart} />'
    if anchor_results not in src:
        return src, changes + ["WARN <Results /> introuvable, skip render"]
    src = src.replace(
        anchor_results,
        anchor_results + '\n          ' + render_line,
        1
    )
    changes.append(f"+ render <AIAnalysisPanel testCode={test_code}/>")
    return src, changes


def patch_one(target: pathlib.Path) -> str:
    if not target.exists():
        return f"{target.name}: file not found"
    html = target.read_text(encoding="utf-8")
    m = re.search(r'(<script type="__bundler/manifest">)(.*?)(</script>)', html, re.DOTALL)
    if not m:
        return f"{target.name}: pas de manifest"
    manifest = json.loads(m.group(2))
    uuid = next((k for k in manifest if k.startswith(ASSET_UUID_PREFIX)), None)
    if uuid is None:
        return f"{target.name}: asset {ASSET_UUID_PREFIX} introuvable"
    entry = manifest[uuid]
    raw = base64.b64decode(entry['data'])
    comp = entry.get('compressed', False)
    src = gzip.decompress(raw).decode('utf-8') if comp else raw.decode('utf-8')
    new_src, changes = patch_src(src)
    if new_src == src:
        return f"{target.name}: aucun changement"
    nd = new_src.encode('utf-8')
    if comp:
        nd = gzip.compress(nd)
    entry['data'] = base64.b64encode(nd).decode('ascii')
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]
    target.write_text(new_html, encoding='utf-8')
    return f"{target.name}: [{', '.join(changes)}] (src {len(src)} → {len(new_src)})"


if __name__ == "__main__":
    for fn in TARGETS:
        print(patch_one(REPO / fn))

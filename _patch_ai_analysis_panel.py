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
    "Proxxie Test BRIEF.html",
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
    "test-brief.html",
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
  const [open, setOpen] = React.useState(false);
  const [state, setState] = React.useState("idle"); // idle, loading, streaming, done, error
  const [content, setContent] = React.useState("");
  const [error, setError] = React.useState(null);
  const [remaining, setRemaining] = React.useState(PROXXIE_AI_QUOTA);

  React.useEffect(() => {
    try {
      const used = parseInt(window.localStorage.getItem(PROXXIE_AI_COUNT_KEY) || "0", 10);
      setRemaining(Math.max(0, PROXXIE_AI_QUOTA - used));
    } catch (e) { /* localStorage indisponible */ }
  }, []);

  // Bloque le scroll body quand la modale est ouverte
  React.useEffect(() => {
    if (open) {
      const prev = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      return () => { document.body.style.overflow = prev; };
    }
  }, [open]);

  // L'API est considérée configurée si l'URL est définie et commence par https://
  const isApiConfigured = PROXXIE_AI_API_URL && PROXXIE_AI_API_URL.indexOf("https://") === 0;
  const isGated = remaining <= 0;

  const requestAnalysis = async () => {
    setOpen(true);
    if (isGated) return;
    if (!isApiConfigured) {
      setError("API non configurée. Le backend Vercel doit être déployé avant que cette fonction soit active.");
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

  const closeModal = () => {
    // On ne ferme PAS pendant le streaming pour éviter de perdre l'analyse en cours
    if (state === "streaming" || state === "loading") return;
    setOpen(false);
  };

  return (
    <>
      {/* === Section CTA · carte crème "post-it" signée, pas un bandeau AI === */}
      <section style={{ paddingTop: 30, paddingBottom: 50 }}>
        <div className="shell" style={{ maxWidth: 820 }}>
          <div style={{
            background: "var(--c-cream-light, #FAF6EE)",
            border: "1px solid var(--c-line, rgba(10,14,44,.08))",
            borderRadius: 20, padding: "28px 28px",
            position: "relative",
          }}>
            {/* Petit liseré accent à gauche, comme une note coachée */}
            <div style={{
              position: "absolute", top: 24, bottom: 24, left: 0,
              width: 3, borderRadius: 3, background: accent,
            }} />
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 28, flexWrap: "wrap", paddingLeft: 14 }}>
              <div style={{ flex: "1 1 360px", minWidth: 260 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: accent, marginBottom: 8 }}>
                  Une lecture personnalisée de ton profil
                </div>
                <h2 style={{ color: "var(--c-ink, #0A0E2C)", fontSize: 24, lineHeight: 1.25, margin: 0, fontFamily: "var(--font-display, Goldplay, Mulish, serif)", letterSpacing: "-0.015em" }}>
                  On a regardé tes réponses pour toi.
                </h2>
                <p style={{ fontSize: 15, color: "var(--c-ink-2, #2A2F4F)", lineHeight: 1.55, marginTop: 10, marginBottom: 0 }}>
                  Tes forces, ce sur quoi rester vigilant, des pistes concrètes côté parent et côté ado, et l'impact sur ton orientation. Lecture en une page.
                </p>
              </div>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 8, flexShrink: 0 }}>
                <button onClick={requestAnalysis} style={{
                  background: "#FD6936", color: "white", border: "none",
                  padding: "13px 22px", borderRadius: 99, fontWeight: 600, fontSize: 14.5,
                  cursor: "pointer", boxShadow: "0 12px 28px -10px rgba(253,105,54,.6)",
                  display: "inline-flex", alignItems: "center", gap: 8, whiteSpace: "nowrap",
                  fontFamily: "inherit",
                }}>
                  Lire ma lecture personnalisée →
                </button>
                <div style={{ fontSize: 12, color: "var(--c-muted, #6B6F8C)" }}>
                  {isGated ? "Connecte-toi pour continuer" : (remaining === PROXXIE_AI_QUOTA ? "Gratuit, sans inscription" : `Encore ${remaining} sur ${PROXXIE_AI_QUOTA} avant inscription`)}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* === Modale · plus sobre, fond crème, sans gradient "AI" === */}
      {open && (
        <div onClick={closeModal} style={{
          position: "fixed", inset: 0, zIndex: 99998,
          background: "rgba(10,14,44,.45)",
          display: "grid", placeItems: "center", padding: 16,
          animation: "proxxie-fade-in 0.25s ease-out",
        }}>
          <style>{`
            @keyframes proxxie-fade-in { from { opacity: 0; } to { opacity: 1; } }
            @keyframes proxxie-modal-up { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
            @keyframes proxxie-dots { 0%, 20% { opacity: 0.3; } 50% { opacity: 1; } 80%, 100% { opacity: 0.3; } }
          `}</style>
          <div onClick={(e) => e.stopPropagation()} style={{
            background: "var(--c-cream, #F7F2E9)", borderRadius: 20,
            maxWidth: 760, width: "100%", maxHeight: "92vh",
            display: "flex", flexDirection: "column",
            boxShadow: "0 24px 60px -16px rgba(10,14,44,.3)",
            animation: "proxxie-modal-up 0.3s ease-out",
            overflow: "hidden",
            border: "1px solid rgba(10,14,44,.06)",
          }}>
            {/* Header modale · crème pas gradient, titre sérif */}
            <div style={{
              padding: "22px 28px 18px",
              borderBottom: "1px solid rgba(10,14,44,.08)",
              display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16,
            }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 12.5, color: accent, fontWeight: 600, marginBottom: 6 }}>
                  Ta lecture Proxxie
                </div>
                <h2 style={{ fontSize: 22, lineHeight: 1.25, margin: 0, color: "var(--c-ink, #0A0E2C)", fontFamily: "var(--font-display, Goldplay, Mulish, serif)", letterSpacing: "-0.015em", fontWeight: 600 }}>
                  {state === "loading" ? "On regarde ton profil..." :
                   state === "streaming" ? "On regarde ton profil..." :
                   state === "done" ? "Ce qu'on voit dans ton profil " + testName :
                   state === "error" ? "On n'a pas pu finir la lecture" :
                   "Ta lecture personnalisée"}
                </h2>
              </div>
              <button onClick={closeModal} disabled={state === "streaming" || state === "loading"} style={{
                background: "transparent", border: "1px solid rgba(10,14,44,.15)",
                color: "var(--c-ink, #0A0E2C)",
                width: 32, height: 32, borderRadius: "50%",
                cursor: (state === "streaming" || state === "loading") ? "not-allowed" : "pointer",
                fontSize: 14, opacity: (state === "streaming" || state === "loading") ? 0.3 : 1,
                display: "grid", placeItems: "center", lineHeight: 1, flexShrink: 0,
                fontFamily: "inherit",
              }} aria-label="Fermer">
                ✕
              </button>
            </div>

            {/* Body modale (scrollable) · fond blanc pour lisibilité du texte long */}
            <div style={{ flex: 1, overflowY: "auto", padding: "26px 28px", background: "white" }}>
              {isGated && state === "idle" && (
                <div style={{ textAlign: "center", padding: "20px 0 30px" }}>
                  <h3 style={{ fontSize: 22, marginBottom: 12, fontFamily: "var(--font-display, Goldplay, Mulish, serif)", fontWeight: 600, color: "var(--c-ink, #0A0E2C)" }}>
                    Tu as déjà eu tes 3 lectures gratuites.
                  </h3>
                  <p style={{ fontSize: 15, color: "var(--c-ink-2, #2A2F4F)", lineHeight: 1.55, marginBottom: 24, maxWidth: 480, marginInline: "auto" }}>
                    Crée un compte gratuit pour continuer à recevoir ta lecture sur chaque test, retrouver ton historique, et activer le mode parent.
                  </p>
                  <div style={{ display: "flex", gap: 10, flexWrap: "wrap", justifyContent: "center" }}>
                    <a href="connexion.html?signup=1" style={{ background: "#FD6936", color: "white", padding: "12px 22px", borderRadius: 99, fontWeight: 600, fontSize: 14, textDecoration: "none" }}>Créer mon compte</a>
                    <a href="connexion.html" style={{ background: "transparent", color: "var(--c-ink, #0A0E2C)", border: "1px solid rgba(10,14,44,.2)", padding: "12px 22px", borderRadius: 99, fontWeight: 600, fontSize: 14, textDecoration: "none" }}>J'ai déjà un compte</a>
                  </div>
                </div>
              )}

              {state === "loading" && (
                <div style={{ padding: "60px 0", textAlign: "center" }}>
                  <div style={{ display: "inline-flex", gap: 6, marginBottom: 14 }}>
                    <span style={{ width: 6, height: 6, borderRadius: "50%", background: accent, animation: "proxxie-dots 1.4s infinite", animationDelay: "0s" }}></span>
                    <span style={{ width: 6, height: 6, borderRadius: "50%", background: accent, animation: "proxxie-dots 1.4s infinite", animationDelay: "0.2s" }}></span>
                    <span style={{ width: 6, height: 6, borderRadius: "50%", background: accent, animation: "proxxie-dots 1.4s infinite", animationDelay: "0.4s" }}></span>
                  </div>
                  <div style={{ fontSize: 14, color: "var(--c-muted, #6B6F8C)" }}>On lit ton profil...</div>
                </div>
              )}

              {(state === "streaming" || state === "done") && (
                <div style={{ fontSize: 14.5, lineHeight: 1.65, color: "var(--c-ink, #0A0E2C)" }}>
                  <div dangerouslySetInnerHTML={{ __html: _proxxieMiniMarkdown(content) }} />

                  {state === "done" && (
                    <>
                      {/* CTA Charles · style "encart coaching" pas "AI dégradé" */}
                      <div style={{
                        marginTop: 32, padding: "26px 26px", borderRadius: 16,
                        background: "var(--c-cream-light, #FAF6EE)",
                        border: "1px solid rgba(10,14,44,.08)",
                        position: "relative",
                      }}>
                        <div style={{
                          position: "absolute", top: 22, bottom: 22, left: 0,
                          width: 3, borderRadius: 3, background: "#FD6936",
                        }} />
                        <div style={{ paddingLeft: 16 }}>
                          <div style={{ fontSize: 12.5, color: "#FD6936", fontWeight: 600, marginBottom: 8 }}>
                            Pour aller plus loin
                          </div>
                          <h3 style={{ color: "var(--c-ink, #0A0E2C)", fontSize: 21, lineHeight: 1.3, margin: "0 0 12px", fontFamily: "var(--font-display, Goldplay, Mulish, serif)", fontWeight: 600, letterSpacing: "-0.015em" }}>
                            Charles peut t'aider à creuser.
                          </h3>
                          <p style={{ fontSize: 14.5, color: "var(--c-ink-2, #2A2F4F)", lineHeight: 1.55, marginBottom: 20, marginTop: 0 }}>
                            30 minutes en visio, sans engagement. On part de cette lecture, on cartographie ce qui compte pour la suite (orientation, Parcoursup, parcours alternatifs), on identifie 2 ou 3 actions concrètes.
                          </p>
                          <a href="https://calendly.com/proxxie/entretien" target="_blank" rel="noopener noreferrer" style={{
                            background: "#FD6936", color: "white", padding: "12px 24px", borderRadius: 99,
                            fontWeight: 600, fontSize: 14.5, textDecoration: "none",
                            display: "inline-flex", alignItems: "center", gap: 8,
                            boxShadow: "0 10px 24px -10px rgba(253,105,54,.5)",
                            fontFamily: "inherit",
                          }}>
                            Réserver 30 min avec Charles
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M13 5l7 7-7 7"/></svg>
                          </a>
                          <div style={{ marginTop: 12, fontSize: 12.5, color: "var(--c-muted, #6B6F8C)" }}>
                            Gratuit, sans carte bancaire, créneaux sous 7 jours
                          </div>
                        </div>
                      </div>

                      {/* Disclaimer en pied de modale, discret */}
                      <div style={{ marginTop: 20, paddingTop: 16, borderTop: "1px solid rgba(10,14,44,.06)", fontSize: 11.5, color: "var(--c-muted, #6B6F8C)", lineHeight: 1.5 }}>
                        Cette lecture est produite à partir de tes seules réponses au test. Elle ne remplace pas un avis professionnel (psychologue, médecin, conseiller d'orientation) si la situation l'exige.
                      </div>
                    </>
                  )}
                </div>
              )}

              {state === "error" && (
                <div style={{ padding: "20px 0" }}>
                  <div style={{ background: "#FFF4F0", border: "1px solid rgba(198,40,40,.2)", color: "var(--c-ink, #0A0E2C)", padding: "16px 18px", borderRadius: 12, fontSize: 14, lineHeight: 1.55 }}>
                    <strong style={{ color: "#C62828", display: "block", marginBottom: 6 }}>On n'a pas pu finir la lecture.</strong>
                    <div style={{ color: "var(--c-muted, #6B6F8C)", fontSize: 13 }}>{error}</div>
                  </div>
                  <div style={{ display: "flex", gap: 10, marginTop: 18, justifyContent: "center" }}>
                    <button onClick={requestAnalysis} style={{
                      background: accent, border: "none", color: "white",
                      padding: "10px 20px", borderRadius: 99, fontWeight: 600, cursor: "pointer", fontSize: 14,
                      fontFamily: "inherit",
                    }}>Réessayer</button>
                    <button onClick={() => setOpen(false)} style={{
                      background: "transparent", border: "1px solid rgba(10,14,44,.15)", color: "var(--c-ink, #0A0E2C)",
                      padding: "10px 20px", borderRadius: 99, fontWeight: 600, cursor: "pointer", fontSize: 14,
                      fontFamily: "inherit",
                    }}>Fermer</button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
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

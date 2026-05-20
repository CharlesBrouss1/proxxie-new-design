#!/usr/bin/env python3
"""Add a first-visit "demo vs personal" mode choice·

  - ChooseModeModal · auto-fires on first visit (when proxxie.mode is not
    set). Two big choices·
      · "Voir l'exemple complet"  → mode=demo (current behaviour)
      · "Démarrer mon parcours perso" → mode=personal
  - ModeBanner · subtle bar at the top of the dashboard showing current
    mode + a switch button.
  - In personal mode, a sticky in-page banner sits below the ModeBanner
    explaining "ce que tu vois ci-dessous est un exemple" with a pointer
    to the OnboardingChecklist. Demo cards get visually de-emphasized
    via a CSS filter (grayscale + opacity) so the user sees the
    structure without confusing it for real data.

Wires into the Dashboard return at the very top (just inside the root
div) so the modal can render above everything else.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
TARGETS = ["dashboard.html", "Proxxie Dashboard.html"]
DASHBOARD_ASSET = "5a278f70-3fa5-4bc0-bdb2-349143947f86"
MARKER = "/* __proxxie_mode_choice_v1__ */"


COMPONENTS_JSX = r"""
/* __proxxie_mode_choice_v1__ */

const useProxxieMode = () => {
  const [mode, setMode] = React.useState(() => {
    try {
      const u = new URLSearchParams(window.location.search).get("mode");
      if (u === "demo" || u === "personal") return u;
      const s = localStorage.getItem("proxxie.mode");
      if (s === "demo" || s === "personal") return s;
    } catch (e) {}
    return null; /* null · user hasn't chosen yet */
  });
  const update = React.useCallback((m) => {
    try { localStorage.setItem("proxxie.mode", m); } catch (e) {}
    setMode(m);
    /* Reload so KPIs / WelcomeBanner pick up the new mode at module init. */
    setTimeout(() => { try { window.location.reload(); } catch (e) {} }, 100);
  }, []);
  return [mode, update];
};

const ChooseModeModal = ({ open, onPick }) => {
  const role = useProxxieRole();
  const isEnfant = role === "enfant";
  if (!open) return null;

  const cardStyle = (accent) => ({
    flex: 1,
    display: "flex", flexDirection: "column", gap: 12,
    padding: "26px 24px",
    borderRadius: 18,
    border: "1.5px solid rgba(10,14,44,.08)",
    background: "white",
    cursor: "pointer",
    transition: "transform .15s ease, border-color .15s ease, box-shadow .15s ease",
    textAlign: "left",
    fontFamily: "inherit",
  });
  const hover = (e, accent, on) => {
    e.currentTarget.style.transform = on ? "translateY(-2px)" : "translateY(0)";
    e.currentTarget.style.borderColor = on ? accent : "rgba(10,14,44,.08)";
    e.currentTarget.style.boxShadow = on ? "0 8px 22px " + accent.replace("rgb", "rgba").replace(")", ",.18)") : "none";
  };

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(10,14,44,.7)", display: "grid", placeItems: "center", zIndex: 220, padding: 20 }}>
      <div style={{ background: "white", borderRadius: 24, maxWidth: 720, width: "100%", padding: 36, boxShadow: "0 24px 70px rgba(10,14,44,.35)" }}>
        <div style={{ textAlign: "center", marginBottom: 28 }}>
          <span className="eyebrow" style={{ justifyContent: "center" }}><span className="dot"></span>Bienvenue sur Proxxie</span>
          <h2 style={{ fontFamily: "var(--font-display)", fontSize: 32, fontWeight: 600, letterSpacing: "-0.02em", margin: "12px 0 8px", color: "#0A0E2C" }}>
            {isEnfant ? "Comment veux-tu commencer ?" : "Comment voulez-vous commencer ?"}
          </h2>
          <p style={{ fontSize: 14, color: "rgba(10,14,44,.55)", margin: 0, lineHeight: 1.55, maxWidth: 520, marginLeft: "auto", marginRight: "auto" }}>
            {isEnfant
              ? "Tu peux explorer un dashboard rempli d'exemples pour comprendre, ou démarrer ton parcours perso tout de suite."
              : "Vous pouvez explorer un dashboard rempli d'exemples pour comprendre ce que produit Proxxie, ou démarrer votre parcours perso tout de suite."}
          </p>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          <button type="button" onClick={() => onPick("demo")} style={cardStyle("#487AFF")}
                  onMouseEnter={(e) => hover(e, "#487AFF", true)} onMouseLeave={(e) => hover(e, "#487AFF", false)}>
            <div style={{ width: 44, height: 44, borderRadius: 12, background: "rgba(72,122,255,.10)", color: "#487AFF", display: "grid", placeItems: "center", fontSize: 22 }}>🔍</div>
            <div>
              <div style={{ fontFamily: "var(--font-display)", fontSize: 19, fontWeight: 600, color: "#0A0E2C", marginBottom: 4 }}>
                Voir l'exemple complet
              </div>
              <div style={{ fontSize: 13, color: "rgba(10,14,44,.55)", lineHeight: 1.5 }}>
                {isEnfant
                  ? "Un dashboard avec Arthur en Terminale, ses tests, ses vœux. Pour comprendre ce que tu peux attendre."
                  : "Un dashboard avec Arthur en Terminale, ses tests, ses vœux. Pour comprendre ce que vous pouvez attendre."}
              </div>
            </div>
            <span style={{ fontSize: 12, fontWeight: 700, color: "#487AFF", textTransform: "uppercase", letterSpacing: "0.06em", marginTop: "auto" }}>Explorer la démo →</span>
          </button>

          <button type="button" onClick={() => onPick("personal")} style={cardStyle("#FD6936")}
                  onMouseEnter={(e) => hover(e, "#FD6936", true)} onMouseLeave={(e) => hover(e, "#FD6936", false)}>
            <div style={{ width: 44, height: 44, borderRadius: 12, background: "rgba(253,105,54,.10)", color: "#FD6936", display: "grid", placeItems: "center", fontSize: 22 }}>🚀</div>
            <div>
              <div style={{ fontFamily: "var(--font-display)", fontSize: 19, fontWeight: 600, color: "#0A0E2C", marginBottom: 4 }}>
                {isEnfant ? "Démarrer mon parcours" : "Démarrer le parcours de mon ado"}
              </div>
              <div style={{ fontSize: 13, color: "rgba(10,14,44,.55)", lineHeight: 1.5 }}>
                {isEnfant
                  ? "Tableau de bord vierge, on suit ta mise en route en 3 étapes pour le remplir avec tes données."
                  : "Tableau de bord vierge, on suit votre mise en route en 3 étapes pour le remplir avec les vraies données."}
              </div>
            </div>
            <span style={{ fontSize: 12, fontWeight: 700, color: "#FD6936", textTransform: "uppercase", letterSpacing: "0.06em", marginTop: "auto" }}>Commencer →</span>
          </button>
        </div>

        <p style={{ fontSize: 12, color: "rgba(10,14,44,.45)", margin: "22px 0 0", textAlign: "center", lineHeight: 1.5 }}>
          Tu peux basculer entre les deux modes à tout moment depuis le bandeau en haut du dashboard.
        </p>
      </div>
    </div>
  );
};

const ModeBanner = ({ mode, onSwitch }) => {
  const role = useProxxieRole();
  const isEnfant = role === "enfant";
  const isPersonal = mode === "personal";
  const bg = isPersonal ? "rgba(253,105,54,.08)" : "rgba(72,122,255,.06)";
  const border = isPersonal ? "rgba(253,105,54,.20)" : "rgba(72,122,255,.18)";
  const dotColor = isPersonal ? "#FD6936" : "#487AFF";
  return (
    <div style={{ background: bg, borderBottom: "1px solid " + border }}>
      <div className="shell" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16, padding: "10px 0", flexWrap: "wrap" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 12, color: "rgba(10,14,44,.7)" }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: dotColor }}></span>
          <span style={{ fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase", color: dotColor }}>
            {isPersonal ? "Mode perso" : "Mode démo"}
          </span>
          <span style={{ color: "rgba(10,14,44,.55)" }}>
            {isPersonal
              ? (isEnfant
                  ? "· les exemples ci-dessous seront remplacés par tes données."
                  : "· les exemples ci-dessous seront remplacés par vos données.")
              : (isEnfant
                  ? "· tu explores le dashboard d'un ado fictif."
                  : "· vous explorez le dashboard d'un ado fictif.")}
          </span>
        </div>
        <button onClick={() => onSwitch(isPersonal ? "demo" : "personal")} style={{ background: "transparent", border: "1px solid " + border, color: dotColor, fontSize: 12, fontWeight: 600, padding: "6px 12px", borderRadius: 999, cursor: "pointer", fontFamily: "inherit" }}>
          {isPersonal ? "Revoir l'exemple démo" : "Passer en mode perso"} →
        </button>
      </div>
    </div>
  );
};

const PersonalModeBlurb = () => {
  const role = useProxxieRole();
  const isEnfant = role === "enfant";
  return (
    <section style={{ margin: "0 auto 24px", padding: "0 24px", maxWidth: 1280 }}>
      <div style={{
        background: "linear-gradient(135deg, #FFF6E0 0%, #FFE7C7 100%)",
        border: "1px solid rgba(253,105,54,.20)",
        borderRadius: 16, padding: "18px 22px",
        display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap",
      }}>
        <div style={{ width: 40, height: 40, borderRadius: 10, background: "#FD6936", color: "white", display: "grid", placeItems: "center", fontSize: 18, flexShrink: 0 }}>↑</div>
        <div style={{ flex: 1, minWidth: 240 }}>
          <div style={{ fontWeight: 600, fontSize: 14, color: "#0A0E2C", marginBottom: 2 }}>
            {isEnfant ? "Ce que tu vois ci-dessous est un exemple" : "Ce que vous voyez ci-dessous est un exemple"}
          </div>
          <div style={{ fontSize: 13, color: "rgba(10,14,44,.65)", lineHeight: 1.45 }}>
            {isEnfant
              ? "Complète ta mise en route en haut pour que ces cartes se remplissent avec tes vraies données (profil, tests, vœux, documents)."
              : "Complétez la mise en route en haut pour que ces cartes se remplissent avec les vraies données de votre ado."}
          </div>
        </div>
      </div>
    </section>
  );
};
"""

# Personal-mode CSS · de-emphasize demo cards so the user sees structure without
# confusing them for real data. Doesn't touch header, banners, modals, or the
# onboarding checklist.
PERSONAL_MODE_CSS = r"""
[data-proxxie-mode="personal"] [data-demo-zone] {
  filter: grayscale(0.65) opacity(0.55);
  transition: filter .3s ease;
  pointer-events: none;
}
[data-proxxie-mode="personal"] [data-demo-zone]:hover {
  filter: grayscale(0.45) opacity(0.7);
}
"""

# Insertion anchors in the existing Dashboard component
ROOT_ANCHOR = '<div data-audit={t.audit ? "on" : "off"} style={{ background: "var(--c-cream-light)", minHeight: "100vh" }}>'
ROOT_REPLACE = '<div data-audit={t.audit ? "on" : "off"} data-proxxie-mode={mode || "demo"} style={{ background: "var(--c-cream-light)", minHeight: "100vh" }}>'

HEADER_ANCHOR = '<DashHeader />'
HEADER_REPLACE = '<DashHeader />\n      <ModeBanner mode={mode || "demo"} onSwitch={setMode} />\n      <ChooseModeModal open={mode === null} onPick={setMode} />\n      {mode === "personal" && <PersonalModeBlurb />}'

STATE_HOOK_ANCHOR = 'const [referralOpen, setReferralOpen] = React.useState(false);'
STATE_HOOK_INSERT = STATE_HOOK_ANCHOR + '\n  const [mode, setMode] = useProxxieMode();'

# Wrap demo content with data-demo-zone so personal-mode CSS can de-emphasize.
WRAP_TARGETS = [
    ('<WelcomeBanner onOpen={openDrawer} audit={t.audit} />',
     '<div data-demo-zone="welcome"><WelcomeBanner onOpen={openDrawer} audit={t.audit} /></div>'),
    ('<KPICards onOpenReferral={() => setReferralOpen(true)} onOpen={openDrawer} audit={t.audit} invited={invited} />',
     '<div data-demo-zone="kpi"><KPICards onOpenReferral={() => setReferralOpen(true)} onOpen={openDrawer} audit={t.audit} invited={invited} /></div>'),
    ('<DashGrid onOpen={openDrawer} audit={t.audit} />',
     '<div data-demo-zone="grid"><DashGrid onOpen={openDrawer} audit={t.audit} /></div>'),
]


STRIP_RE = re.compile(
    r'\n/\* __proxxie_mode_choice_v1__ \*/.*?(?=\n(?:/\* __proxxie_|const Dashboard = \(\) =>))',
    flags=re.S,
)


def strip_v1(src: str) -> str:
    src = STRIP_RE.sub("", src)
    src = src.replace(ROOT_REPLACE, ROOT_ANCHOR, 1)
    src = src.replace(HEADER_REPLACE, HEADER_ANCHOR, 1)
    src = src.replace(STATE_HOOK_INSERT, STATE_HOOK_ANCHOR, 1)
    for old, new in WRAP_TARGETS:
        src = src.replace(new, old, 1)
    # Remove the personal-mode CSS injection
    src = src.replace(_css_injection(), "", 1)
    return src


def _css_injection() -> str:
    return (
        '\nif (typeof document !== "undefined" && !document.getElementById("__proxxie-mode-css")) {\n'
        '  const s = document.createElement("style");\n'
        '  s.id = "__proxxie-mode-css";\n'
        '  s.textContent = ' + json.dumps(PERSONAL_MODE_CSS, ensure_ascii=False) + ';\n'
        '  document.head.appendChild(s);\n'
        '}\n'
    )


def patch_asset(src: str) -> str:
    if MARKER in src:
        src = strip_v1(src)
    if ROOT_ANCHOR not in src:
        raise SystemExit("Root div anchor not found")
    if HEADER_ANCHOR not in src:
        raise SystemExit("DashHeader anchor not found")
    if STATE_HOOK_ANCHOR not in src:
        raise SystemExit("State hook anchor not found")
    for old, _ in WRAP_TARGETS:
        if old not in src:
            raise SystemExit(f"WRAP target not found· {old[:40]}")

    # Component definitions
    src = src.replace("const Dashboard = () =>", COMPONENTS_JSX + _css_injection() + "\nconst Dashboard = () =>", 1)
    src = src.replace(STATE_HOOK_ANCHOR, STATE_HOOK_INSERT, 1)
    src = src.replace(ROOT_ANCHOR, ROOT_REPLACE, 1)
    src = src.replace(HEADER_ANCHOR, HEADER_REPLACE, 1)
    for old, new in WRAP_TARGETS:
        src = src.replace(old, new, 1)
    return src


def patch_one(target: pathlib.Path) -> str:
    if not target.exists(): return "SKIP missing"
    html = target.read_text(encoding="utf-8")
    m = re.search(r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)', html, re.DOTALL)
    if not m: return "no manifest"
    manifest = json.loads(m.group(2))
    if DASHBOARD_ASSET not in manifest: return "asset not found"
    entry = manifest[DASHBOARD_ASSET]
    data = base64.b64decode(entry["data"])
    comp = entry.get("compressed", False)
    if comp: data = gzip.decompress(data)
    src = data.decode("utf-8")
    was_patched = MARKER in src
    new_src = patch_asset(src)
    nd = new_src.encode("utf-8")
    if comp: nd = gzip.compress(nd)
    entry["data"] = base64.b64encode(nd).decode("ascii")
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]
    target.write_text(new_html, encoding="utf-8")
    verb = "re-patched" if was_patched else "patched"
    return f"{verb} (asset {len(new_src)} chars)"


if __name__ == "__main__":
    for fn in TARGETS:
        try:
            print(f"{fn}: {patch_one(REPO / fn)}")
        except SystemExit as e:
            print(f"{fn}: ERROR · {e}")

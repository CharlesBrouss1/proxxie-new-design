#!/usr/bin/env python3
"""Dashboard focus · un hub calme : 1 action, statut lecture seule, le reste replié.

Le dashboard empilait ~10 sections concurrentes (héros, feed, welcome démo,
gamification, KPI, grille analyse, 11 cartes de tests, complétude docs, CTA
invitation, CTA conversion, newsletter). Trop de boutons, parcours brouillé.

Cette refonte (validée en /plan-design-review) le réduit à :
  1. NextBestAction · l'unique action du moment (déjà en place)
  2. ProxxieBetaIntro · l'intro mode démo (conservée)
  3. StatusStrip · statut en lecture seule (Tests x/11 · Documents x/8 ·
     Prochain RDV) + un lien discret vers le rapport
  4. WhatsNewFeed · le fil « depuis ta dernière visite »
  5. ProxxieFocusCards · 2 cartes résumé (Tests, Documents) qui ouvrent chacune
     une MODALE, + une ligne « accompagnement » qui ouvre la ProxxieConversionModal

Tout le reste (WelcomeBanner, GamificationPanel, KPICards, DashGrid, TestsPanel,
DocsCompletenessPanel, InvitationCTA, PaidConversionCTA, NewsletterCard) est
retiré du rendu de la page d'accueil. Les définitions des composants restent
intactes (aucune référence cassée · les modales du bas (Referral, Invitation,
EditProfile, InfoDrawer) sont rendues après le Footer et ne dépendent pas des
composants retirés).

Composants nouveaux auto-portés (chacun gère son propre état de modale, comme
PaidConversionCTA + ProxxieConversionModal en F4). Réutilise TESTS_LIST,
PROXXIE_TEST_CATS, _proxxieTestMin, ProxxieDualStatus, DOCS_EXPECTED,
_proxxieGetDocs, ProxxieConversionModal, FIRST_NAME, useProxxieRole.

Idempotent · bloc composant en strip-and-readd entre marqueurs ; le rendu est
remplacé par ancre exacte (no-op si déjà au format focus).
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
FILES = ["Proxxie Dashboard.html", "dashboard.html"]

BEGIN = "/* PROXXIE_DASH_FOCUS_BEGIN */"
END = "/* PROXXIE_DASH_FOCUS_END */"
CREATE_ROOT = 'ReactDOM.createRoot(document.getElementById("root")).render(<Dashboard />);'

COMPONENT = BEGIN + r"""
/* ---------------- Dashboard focus · composants ---------------- */
const _proxxieTestsDone = (role) => {
  let c = 0;
  for (const t of TESTS_LIST) {
    try {
      const rk = localStorage.getItem("proxxie.tests." + t.id + "." + role);
      const lg = localStorage.getItem("proxxie.tests." + t.id);
      if ((rk || lg || t.def) === "done") c++;
    } catch (e) {}
  }
  return c;
};

const _proxxieCard = { background: "white", border: "1px solid var(--c-line)", borderRadius: 18, padding: "22px 24px" };
const _proxxieGhostBtn = { display: "inline-flex", alignItems: "center", gap: 6, padding: "10px 16px", borderRadius: 10, border: "1px solid var(--c-line)", background: "white", fontSize: 13, fontWeight: 600, color: "var(--c-blue)", cursor: "pointer", fontFamily: "inherit", textDecoration: "none" };
const _proxxieOverlay = { position: "fixed", inset: 0, background: "rgba(10,14,44,.55)", display: "grid", placeItems: "center", zIndex: 200, padding: 20, overflowY: "auto" };

const TestsModal = ({ open, onClose, role }) => {
  if (!open) return null;
  // Accès libre · seuls OCEAN-X (Big Five) et RIASEC sont accessibles sans RDV.
  const freeTests = [
    { id: "big5", title: "OCEAN-X (Big Five)", href: "Proxxie Test.html" },
    TESTS_LIST.find((t) => t.id === "riasec"),
  ].filter(Boolean);
  const freeRow = (t) => (
    <a key={t.id} href={t.href} style={{ display: "flex", alignItems: "center", gap: 12, padding: "11px 0", borderTop: "1px solid var(--c-line)", textDecoration: "none", color: "inherit" }}>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 14, fontWeight: 600 }}>{t.title}</div>
        <div style={{ fontSize: 11, color: "var(--c-muted)", fontFamily: "var(--font-num)" }}>⏱ ~{_proxxieTestMin(t.id)} min</div>
      </div>
      <ProxxieDualStatus t={t} role={role} />
      <span style={{ fontSize: 16, color: "var(--c-muted)", flexShrink: 0 }}>→</span>
    </a>
  );
  return (
    <div onClick={onClose} style={_proxxieOverlay}>
      <div onClick={(e) => e.stopPropagation()} style={{ background: "white", borderRadius: 24, maxWidth: 640, width: "100%", maxHeight: "86vh", overflowY: "auto", boxShadow: "0 24px 70px rgba(10,14,44,.3)" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "22px 26px 16px", borderBottom: "1px solid var(--c-line)", position: "sticky", top: 0, background: "white" }}>
          <h3 style={{ fontFamily: "var(--font-display)", fontSize: 20, fontWeight: 600 }}>Tests psychométriques</h3>
          <button onClick={onClose} aria-label="Fermer" style={{ background: "transparent", border: "none", fontSize: 24, color: "var(--c-muted)", cursor: "pointer", lineHeight: 1, fontFamily: "inherit" }}>×</button>
        </div>
        <div style={{ padding: "8px 26px 22px" }}>
          <div style={{ display: "flex", gap: 10, alignItems: "flex-start", background: "rgba(34,160,107,.07)", border: "1px solid rgba(34,160,107,.25)", borderRadius: 12, padding: "12px 14px", margin: "12px 0 4px", fontSize: 13, color: "var(--c-ink)", lineHeight: 1.45 }}>
            <span style={{ flexShrink: 0 }}>🔓</span>
            <span><strong>OCEAN-X et RIASEC</strong> sont en accès libre. Les autres tests se débloquent après le premier RDV de cadrage avec Charles.</span>
          </div>
          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase", color: "#1d7a52", margin: "16px 0 4px" }}>Accès libre</div>
          {freeTests.map(freeRow)}
          {PROXXIE_TEST_CATS.map((cat) => {
            const tests = cat.ids.map((id) => TESTS_LIST.find((t) => t.id === id)).filter(Boolean).filter((t) => t.id !== "riasec");
            if (!tests.length) return null;
            return (
              <div key={cat.id}>
                <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase", color: "var(--c-muted)", margin: "16px 0 4px" }}>{cat.label}</div>
                {tests.map((t) => (
                  <div key={t.id} style={{ display: "flex", alignItems: "center", gap: 12, padding: "11px 0", borderTop: "1px solid var(--c-line)", opacity: 0.55 }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 14, fontWeight: 600 }}>{t.title}</div>
                      <div style={{ fontSize: 11, color: "var(--c-muted)", fontFamily: "var(--font-num)" }}>⏱ ~{_proxxieTestMin(t.id)} min</div>
                    </div>
                    <span style={{ fontSize: 11, fontWeight: 600, color: "var(--c-muted)", flexShrink: 0, display: "inline-flex", alignItems: "center", gap: 5, background: "rgba(10,14,44,.05)", borderRadius: 999, padding: "5px 10px", whiteSpace: "nowrap" }}>🔒 Après le RDV</span>
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

const TestsSummaryCard = () => {
  const role = useProxxieRole();
  const [open, setOpen] = React.useState(false);
  const done = _proxxieTestsDone(role);
  const total = TESTS_LIST.length;
  const pct = Math.round((done / total) * 100);
  return (
    <div style={_proxxieCard}>
      <h3 style={{ fontFamily: "var(--font-display)", fontSize: 18, fontWeight: 600, marginBottom: 4 }}>Tests psychométriques</h3>
      <div style={{ fontSize: 13, color: "var(--c-muted)", marginBottom: 12 }}>
        {done} sur {total} passés{done < total ? " · " + (total - done) + " à découvrir" : " · complet ✓"}
      </div>
      <div style={{ height: 8, borderRadius: 999, background: "rgba(10,14,44,.06)", overflow: "hidden", marginBottom: 14 }}>
        <div style={{ width: pct + "%", height: "100%", background: done === total ? "#22A06B" : "linear-gradient(90deg,#FD6936,#F5EB3F)", transition: "width .4s ease" }} />
      </div>
      <button onClick={() => setOpen(true)} style={_proxxieGhostBtn}>Voir les tests →</button>
      <TestsModal open={open} onClose={() => setOpen(false)} role={role} />
    </div>
  );
};

const DocsModal = ({ open, onClose }) => {
  if (!open) return null;
  const docs = _proxxieGetDocs();
  return (
    <div onClick={onClose} style={_proxxieOverlay}>
      <div onClick={(e) => e.stopPropagation()} style={{ background: "white", borderRadius: 24, maxWidth: 520, width: "100%", boxShadow: "0 24px 70px rgba(10,14,44,.3)" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "22px 26px 16px", borderBottom: "1px solid var(--c-line)" }}>
          <h3 style={{ fontFamily: "var(--font-display)", fontSize: 20, fontWeight: 600 }}>Documents attendus</h3>
          <button onClick={onClose} aria-label="Fermer" style={{ background: "transparent", border: "none", fontSize: 24, color: "var(--c-muted)", cursor: "pointer", lineHeight: 1, fontFamily: "inherit" }}>×</button>
        </div>
        <div style={{ padding: "16px 26px 22px" }}>
          <div style={{ display: "grid", gap: 9, marginBottom: 18 }}>
            {DOCS_EXPECTED.map((d, i) => {
              const ok = docs[d.id];
              return (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 13 }}>
                  <span style={{ width: 18, height: 18, borderRadius: "50%", flexShrink: 0, display: "grid", placeItems: "center", background: ok ? "rgba(34,160,107,.15)" : "rgba(10,14,44,.06)", color: ok ? "#22A06B" : "var(--c-muted)", fontSize: 11 }}>{ok ? "✓" : "·"}</span>
                  <span style={{ color: ok ? "var(--c-ink)" : "var(--c-muted)" }}>{d.label}</span>
                </div>
              );
            })}
          </div>
          <a href="Proxxie Documents.html" className="btn btn-orange" style={{ display: "inline-flex", padding: "12px 20px", fontSize: 14, borderRadius: 10, textDecoration: "none" }}>Gérer mes documents →</a>
        </div>
      </div>
    </div>
  );
};

const DocsSummaryCard = () => {
  const [open, setOpen] = React.useState(false);
  const docs = _proxxieGetDocs();
  const done = DOCS_EXPECTED.filter((d) => docs[d.id]).length;
  const total = DOCS_EXPECTED.length;
  const pct = Math.round((done / total) * 100);
  return (
    <div style={_proxxieCard}>
      <h3 style={{ fontFamily: "var(--font-display)", fontSize: 18, fontWeight: 600, marginBottom: 4 }}>Documents</h3>
      <div style={{ fontSize: 13, color: "var(--c-muted)", marginBottom: 12 }}>
        {done} sur {total} reçus{done < total ? " · " + (total - done) + " manquant" + (total - done > 1 ? "s" : "") : " · complet ✓"}
      </div>
      <div style={{ height: 8, borderRadius: 999, background: "rgba(10,14,44,.06)", overflow: "hidden", marginBottom: 14 }}>
        <div style={{ width: pct + "%", height: "100%", background: done === total ? "#22A06B" : "linear-gradient(90deg,#487AFF,#1320CE)", transition: "width .4s ease" }} />
      </div>
      <button onClick={() => setOpen(true)} style={_proxxieGhostBtn}>Voir les documents →</button>
      <DocsModal open={open} onClose={() => setOpen(false)} />
    </div>
  );
};

const AccompagnementCard = () => {
  const role = useProxxieRole();
  const isEnfant = role === "enfant";
  const [open, setOpen] = React.useState(false);
  const testsDone = _proxxieTestsDone(role);
  return (
    <section style={{ margin: "0 auto 28px", padding: "0 24px", maxWidth: 1280 }}>
      <div style={{ background: "white", border: "1px solid var(--c-line)", borderRadius: 18, padding: "20px 24px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 18, flexWrap: "wrap" }}>
        <div>
          <h3 style={{ fontFamily: "var(--font-display)", fontSize: 18, fontWeight: 600, marginBottom: 2 }}>
            {isEnfant ? "Prêt à rencontrer ton coach ?" : "Prêt pour l'accompagnement ?"}
          </h3>
          <div style={{ fontSize: 13, color: "var(--c-muted)" }}>Un premier RDV de cadrage offert avec Charles, votre coach.</div>
        </div>
        <button onClick={() => setOpen(true)} style={_proxxieGhostBtn}>Découvrir →</button>
      </div>
      <ProxxieConversionModal open={open} onClose={() => setOpen(false)} role={role} testsDone={testsDone} />
    </section>
  );
};

const RapportSummaryCard = () => {
  const role = useProxxieRole();
  const isEnfant = role === "enfant";
  return (
    <div style={_proxxieCard}>
      <h3 style={{ fontFamily: "var(--font-display)", fontSize: 18, fontWeight: 600, marginBottom: 4 }}>Rapport d'orientation</h3>
      <div style={{ fontSize: 13, color: "var(--c-muted)", marginBottom: 14 }}>
        {isEnfant ? "Ta synthèse complète, mise à jour à chaque test." : "La synthèse complète d'" + FIRST_NAME + ", mise à jour à chaque test."}
      </div>
      <a href={isEnfant ? "Proxxie Bilan.html" : "Proxxie Rapport.html"} style={_proxxieGhostBtn}>Ouvrir le rapport →</a>
    </div>
  );
};

const ProxxieFocusCards = () => (
  <React.Fragment>
    <section style={{ margin: "0 auto 18px", padding: "0 24px", maxWidth: 1280 }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 18 }}>
        <TestsSummaryCard />
        <DocsSummaryCard />
        <RapportSummaryCard />
      </div>
    </section>
  </React.Fragment>
);
""" + END + "\n\n" + CREATE_ROOT

# --- render tree · target the calm focus layout ---
# The original sprawling block (first migration from the pre-focus dashboard).
RENDER_OLD = """      <NextBestAction onOpenProfile={() => setProfileOpen(true)} onOpenInvite={() => setInviteOpen(true)} />
      <WhatsNewFeed />
      <ProxxieBetaIntro />
      <div data-demo-zone="welcome"><WelcomeBanner onOpen={openDrawer} audit={t.audit} /></div>
      <GamificationPanel />
      <div data-demo-zone="kpi"><KPICards onOpenReferral={() => setReferralOpen(true)} onOpen={openDrawer} audit={t.audit} invited={invited} /></div>
      <div data-demo-zone="grid"><DashGrid onOpen={openDrawer} audit={t.audit} /></div>
      <TestsPanel />
      <DocsCompletenessPanel />
      <InvitationCTA onOpen={() => setInviteOpen(true)} />
      <PaidConversionCTA />
      <NewsletterCard />
"""
# Focus body · hero + feed + summary cards. No status strip, no beta intro here.
RENDER_NEW = """      <NextBestAction onOpenProfile={() => setProfileOpen(true)} onOpenInvite={() => setInviteOpen(true)} />
      <WhatsNewFeed />
      <ProxxieFocusCards />
"""

# Idempotent line-ops applied after the block swap · work from either the
# original sprawling asset or an earlier focus build.
PERSONAL_BLURB = '      {mode === "personal" && <PersonalModeBlurb />}\n'   # redundant banner · drop
STATUS_STRIP = "      <StatusStrip />\n"                                   # redundant metrics · drop
BETA = "      <ProxxieBetaIntro />\n"                                      # move to the very bottom
FOOTER = "      <Footer />"


def find_dash_asset(manifest):
    for uuid, entry in manifest.items():
        data = base64.b64decode(entry["data"])
        comp = entry.get("compressed", False)
        if comp:
            try: data = gzip.decompress(data)
            except Exception: continue
        try: src = data.decode("utf-8")
        except UnicodeDecodeError: continue
        if 'render(<Dashboard />)' in src:
            return uuid, src, comp
    return None, None, False


def patch_one(target: pathlib.Path) -> str:
    if not target.exists():
        return "SKIP missing"
    html = target.read_text(encoding="utf-8")
    m = re.search(r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)', html, re.DOTALL)
    if not m:
        return "no manifest"
    manifest = json.loads(m.group(2))
    uuid, src, comp = find_dash_asset(manifest)
    if not uuid:
        return "SKIP no dashboard asset"

    changes = []

    # 1 · components (strip-and-readd; readd re-attaches CREATE_ROOT)
    src = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n\n", "", src, flags=re.DOTALL)
    if CREATE_ROOT not in src:
        return "SKIP no createRoot anchor"
    src = src.replace(CREATE_ROOT, COMPONENT, 1)
    changes.append("components")

    # 2 · render · first migrate the sprawling block if still present.
    # (Later patches may legitimately remove <ProxxieFocusCards /> from the
    # render tree — e.g. the KPI/explore refactor. TestsModal is still reached
    # via ProxxieExploreCards, so we always re-write the component block.)
    if RENDER_OLD in src:
        src = src.replace(RENDER_OLD, RENDER_NEW, 1)
        changes.append("render")

    # 3 · idempotent tidy ops (drop redundant banners, move beta intro to bottom)
    if PERSONAL_BLURB in src:
        src = src.replace(PERSONAL_BLURB, "", 1); changes.append("-blurb")
    if STATUS_STRIP in src:
        src = src.replace(STATUS_STRIP, "", 1); changes.append("-statusstrip")
    # remove any in-flow beta intro, then re-place it just above the footer
    had_beta = BETA in src
    src = src.replace(BETA, "", 1) if had_beta else src
    if FOOTER in src and (BETA + FOOTER) not in src:
        src = src.replace(FOOTER, BETA + FOOTER, 1); changes.append("beta→bottom")

    nd = src.encode("utf-8")
    if comp:
        nd = gzip.compress(nd)
    manifest[uuid]["data"] = base64.b64encode(nd).decode("ascii")
    new_manifest = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest + html[m.end(2):]
    target.write_text(new_html, encoding="utf-8")
    return "patched [" + ", ".join(changes) + "] (asset " + uuid[:8] + ")"


if __name__ == "__main__":
    for fn in FILES:
        print("  " + fn + ": " + patch_one(REPO / fn))

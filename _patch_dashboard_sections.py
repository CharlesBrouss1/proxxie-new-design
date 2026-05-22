#!/usr/bin/env python3
"""Dashboard · réafficher la substance d'orientation + accès RDV, sans cadre démo.

Retour utilisateur : le dashboard focus avait trop épuré · il faut garder, sur la
même page, les sections d'orientation (Métiers, Parcours académiques, Spécialités
& filières) et un accès facile à « Réserver mon RDV ». Et le cadrage « ceci est un
exemple » n'a plus lieu d'être · on le retire, mais on garde un petit bouton
« Démo » en haut à droite qui ouvre un aperçu d'un dossier complété.

Changements (sur l'asset dashboard) :
  · retire ModeBanner, ChooseModeModal, ProxxieBetaIntro du rendu (plus de
    disclaimer « exemple »),
  · ProxxieDemoPreview · petit bouton haut-droite → DemoModal (dossier complet
    pré-rempli, résultats finaux après accompagnement),
  · RdvCard · section « Réserver mon RDV » bien visible (bouton direct Calendly
    + lien « comment ça se passe ? » qui ouvre ProxxieConversionModal),
  · ProxxieOrientationSections · réintègre MetiersCard (Métiers) + ParcoursCard
    (Parcours académiques, nouveau) + FiliereCard (Spécialités & filières),
    chacune sous un titre clair, après les cartes résumé.

Réutilise MetiersCard / FiliereCard / ProxxieConversionModal / _proxxieTestsDone /
useProxxieRole / FIRST_NAME (tous définis plus haut dans l'asset). À lancer APRÈS
_patch_dashboard_focus.py (qui définit _proxxieTestsDone / ProxxieFocusCards).

Idempotent · bloc composant en strip-and-readd ; retraits/insertions de rendu
gardés par sentinelles.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
FILES = ["Proxxie Dashboard.html", "dashboard.html"]

BEGIN = "/* PROXXIE_DASH_SECTIONS_BEGIN */"
END = "/* PROXXIE_DASH_SECTIONS_END */"
CREATE_ROOT = 'ReactDOM.createRoot(document.getElementById("root")).render(<Dashboard />);'

COMPONENT = BEGIN + r"""
/* ---------------- Dashboard · sections d'orientation + RDV + démo ---------------- */

/* Parcours académiques · voies post-bac (démo, persona Terminale sciences). */
const ParcoursCard = () => {
  const voies = [
    { n: "École d'ingénieur post-bac", ex: "INSA · Polytech · UTC", a: "Cible", c: "#22A06B", d: "Cohérent avec le profil maths / sciences appliquées." },
    { n: "BUT · Bachelor universitaire", ex: "Génie civil · MMI · Réseaux", a: "Solide", c: "#487AFF", d: "Professionnalisant, passerelles vers l'ingénierie." },
    { n: "Licence + Master", ex: "Maths · Informatique · Physique", a: "Ouvert", c: "#487AFF", d: "Si projet recherche ou enseignement." },
    { n: "CPGE", ex: "MP2I · PCSI", a: "Exigeant", c: "#FD6936", d: "Voie sélective vers les grandes écoles." },
  ];
  return (
    <div className="card" style={{ padding: 28 }}>
      <div style={{ marginBottom: 16 }}>
        <h3 style={{ fontSize: 20 }}>Parcours académiques</h3>
        <div style={{ fontSize: 12, color: "var(--c-muted)", marginTop: 2 }}>Les voies post-bac alignées sur le profil</div>
      </div>
      <div style={{ display: "grid", gap: 8 }}>
        {voies.map((v, i) => (
          <div key={i} style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 12, alignItems: "center", padding: "13px 14px", borderRadius: 10, border: "1px solid var(--c-line)", background: i === 0 ? "rgba(34,160,107,.05)" : "white" }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 600 }}>{v.n}</div>
              <div style={{ fontSize: 11, color: "var(--c-muted)" }}>{v.ex} · {v.d}</div>
            </div>
            <span style={{ fontSize: 11, fontWeight: 600, color: v.c, padding: "3px 10px", borderRadius: 99, background: v.c + "1a", whiteSpace: "nowrap" }}>{v.a}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

/* Réserver mon RDV · accès direct + détail en modale. */
const RdvCard = () => {
  const role = useProxxieRole();
  const isEnfant = role === "enfant";
  const [open, setOpen] = React.useState(false);
  let testsDone = 0;
  try { testsDone = _proxxieTestsDone(role); } catch (e) {}
  return (
    <section style={{ margin: "0 auto 22px", padding: "0 24px", maxWidth: 1280 }}>
      <div style={{ background: "linear-gradient(135deg, #1320CE 0%, #0A0E2C 100%)", color: "white", borderRadius: 20, padding: "24px 28px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 24, flexWrap: "wrap", position: "relative", overflow: "hidden" }}>
        <div style={{ position: "absolute", top: -50, right: -50, width: 180, height: 180, borderRadius: "50%", background: "rgba(253,105,54,.18)" }} />
        <div style={{ position: "relative", zIndex: 1, minWidth: 260 }}>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 7, fontSize: 11, fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase", color: "#F5EB3F" }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#F5EB3F" }} /> Accompagnement
          </span>
          <h3 style={{ fontFamily: "var(--font-display)", fontSize: 22, fontWeight: 600, margin: "10px 0 4px" }}>
            {isEnfant ? "Réserve ton RDV avec Charles" : "Réservez votre RDV avec Charles"}
          </h3>
          <p style={{ fontSize: 14, color: "rgba(255,255,255,.8)", margin: 0 }}>Premier RDV de cadrage offert · 30 min en visio, sans engagement.</p>
        </div>
        <div style={{ position: "relative", zIndex: 1, display: "flex", flexDirection: "column", gap: 8, alignItems: "stretch" }}>
          <a href="https://calendly.com/proxxie/cadrage" target="_blank" rel="noopener noreferrer" style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", gap: 8, padding: "14px 24px", borderRadius: 12, background: "white", color: "#0A0E2C", fontWeight: 700, fontSize: 15, textDecoration: "none", whiteSpace: "nowrap" }}>
            {isEnfant ? "Réserver mon RDV →" : "Réserver mon RDV →"}
          </a>
          <button onClick={() => setOpen(true)} style={{ background: "transparent", border: "none", color: "rgba(255,255,255,.85)", fontSize: 12, fontWeight: 600, cursor: "pointer", fontFamily: "inherit", textDecoration: "underline" }}>
            Comment ça se passe ?
          </button>
        </div>
      </div>
      <ProxxieConversionModal open={open} onClose={() => setOpen(false)} role={role} testsDone={testsDone} />
    </section>
  );
};

/* Aperçu d'un dossier complété · bouton discret haut-droite → modale showcase. */
const DemoModal = ({ open, onClose }) => {
  if (!open) return null;
  const metiers = [["Architecte UX", "94%"], ["Ingénieure biomédicale", "91%"], ["Designer produit", "88%"]];
  const voeux = [["INSA (Lyon · Rennes)", "Proposition acceptée", "#22A06B"], ["BUT GCCD Marne-la-Vallée", "En attente", "#FD6936"], ["Polytech (10 sous-vœux)", "Proposition reçue", "#22A06B"]];
  const sec = (title, children) => (
    <div style={{ marginBottom: 18 }}>
      <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase", color: "var(--c-muted)", marginBottom: 8 }}>{title}</div>
      {children}
    </div>
  );
  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, background: "rgba(10,14,44,.55)", display: "grid", placeItems: "center", zIndex: 210, padding: 20, overflowY: "auto" }}>
      <div onClick={(e) => e.stopPropagation()} style={{ background: "white", borderRadius: 24, maxWidth: 640, width: "100%", maxHeight: "88vh", overflowY: "auto", boxShadow: "0 24px 70px rgba(10,14,44,.3)" }}>
        <div style={{ background: "linear-gradient(135deg, #22A06B 0%, #1320CE 100%)", color: "white", padding: "24px 28px", position: "sticky", top: 0 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase", color: "rgba(255,255,255,.85)" }}>Exemple · dossier complété</span>
              <h3 style={{ fontFamily: "var(--font-display)", fontSize: 22, fontWeight: 600, margin: "8px 0 2px" }}>Le dossier d'Arthur, après l'accompagnement</h3>
              <p style={{ fontSize: 13, color: "rgba(255,255,255,.85)", margin: 0 }}>Voici ce que vous obtenez au bout du parcours complet.</p>
            </div>
            <button onClick={onClose} aria-label="Fermer" style={{ background: "transparent", border: "none", fontSize: 24, color: "rgba(255,255,255,.85)", cursor: "pointer", lineHeight: 1, fontFamily: "inherit" }}>×</button>
          </div>
        </div>
        <div style={{ padding: "22px 28px 26px" }}>
          {sec("Profil", (
            <div style={{ display: "flex", gap: 18, flexWrap: "wrap", fontSize: 14 }}>
              <span>✓ <b>11/11</b> tests passés</span>
              <span>✓ Rapport <b>91%</b></span>
              <span>✓ <b>8/8</b> documents</span>
              <span>✓ <b>10</b> séances coach</span>
            </div>
          ))}
          {sec("Top métiers identifiés", (
            <div style={{ display: "grid", gap: 6 }}>
              {metiers.map((m, i) => (
                <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "9px 12px", borderRadius: 8, background: "var(--c-cream)", fontSize: 13 }}>
                  <span style={{ fontWeight: 600 }}>{m[0]}</span>
                  <span style={{ fontFamily: "var(--font-num)", fontWeight: 700, color: "#1320CE" }}>{m[1]}</span>
                </div>
              ))}
            </div>
          ))}
          {sec("Vœux Parcoursup arbitrés", (
            <div style={{ display: "grid", gap: 6 }}>
              {voeux.map((v, i) => (
                <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "9px 12px", borderRadius: 8, border: "1px solid var(--c-line)", fontSize: 13 }}>
                  <span style={{ fontWeight: 600 }}>{v[0]}</span>
                  <span style={{ fontSize: 11, fontWeight: 600, color: v[2], padding: "3px 9px", borderRadius: 99, background: v[2] + "1a", whiteSpace: "nowrap" }}>{v[1]}</span>
                </div>
              ))}
            </div>
          ))}
          <div style={{ fontSize: 12, color: "var(--c-muted)", lineHeight: 1.5, marginTop: 4 }}>
            Ce dossier est un exemple. Le vôtre se construit au fil des tests, des documents et des séances avec Charles.
          </div>
        </div>
      </div>
    </div>
  );
};

const ProxxieDemoPreview = () => {
  const [open, setOpen] = React.useState(false);
  return (
    <section style={{ margin: "0 auto", padding: "14px 24px 0", maxWidth: 1280, display: "flex", justifyContent: "flex-end" }}>
      <button onClick={() => setOpen(true)} style={{ display: "inline-flex", alignItems: "center", gap: 7, padding: "7px 14px", borderRadius: 999, border: "1px solid var(--c-line)", background: "white", fontSize: 12, fontWeight: 600, color: "var(--c-blue)", cursor: "pointer", fontFamily: "inherit" }}>
        ✨ Voir un dossier complété
      </button>
      <DemoModal open={open} onClose={() => setOpen(false)} />
    </section>
  );
};

const ProxxieOrientationSections = ({ onOpen, audit }) => (
  <React.Fragment>
    <section style={{ margin: "0 auto 18px", padding: "0 24px", maxWidth: 1280 }}>
      <MetiersCard onOpen={onOpen} audit={audit} />
    </section>
    <section style={{ margin: "0 auto 18px", padding: "0 24px", maxWidth: 1280 }}>
      <ParcoursCard />
    </section>
    <section style={{ margin: "0 auto 28px", padding: "0 24px", maxWidth: 1280 }}>
      <FiliereCard mode="future" />
    </section>
  </React.Fragment>
);
""" + END + "\n\n" + CREATE_ROOT

# --- render edits (idempotent) ---
DROP = [
    '      <ModeBanner mode={mode || "demo"} onSwitch={setMode} />\n',
    '      <ChooseModeModal open={mode === null} onPick={setMode} />\n',
    "      <ProxxieBetaIntro />\n",
]
DEMO_ANCHOR = "      <DashHeader />\n"
DEMO_INSERT = DEMO_ANCHOR + "      <ProxxieDemoPreview />\n"
RDV_ANCHOR = "      <NextBestAction onOpenProfile={() => setProfileOpen(true)} onOpenInvite={() => setInviteOpen(true)} />\n"
RDV_INSERT = RDV_ANCHOR + "      <RdvCard />\n"
ORI_ANCHOR = "      <ProxxieFocusCards />\n"
ORI_INSERT = ORI_ANCHOR + "      <ProxxieOrientationSections onOpen={openDrawer} audit={t.audit} />\n"


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

    # 1 · components
    src = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n\n", "", src, flags=re.DOTALL)
    if CREATE_ROOT not in src:
        return "SKIP no createRoot anchor"
    src = src.replace(CREATE_ROOT, COMPONENT, 1)
    changes.append("components")

    # 2 · drop demo/example framing
    for d in DROP:
        if d in src:
            src = src.replace(d, "", 1); changes.append("-" + d.strip().split()[0].lstrip("<"))

    # 3 · demo preview button (top-right)
    if "<ProxxieDemoPreview />" not in src and DEMO_ANCHOR in src:
        src = src.replace(DEMO_ANCHOR, DEMO_INSERT, 1); changes.append("+demo")

    # 4 · RDV card after hero
    if "<RdvCard />" not in src and RDV_ANCHOR in src:
        src = src.replace(RDV_ANCHOR, RDV_INSERT, 1); changes.append("+rdv")

    # 5 · orientation sections after focus cards
    if "<ProxxieOrientationSections" not in src and ORI_ANCHOR in src:
        src = src.replace(ORI_ANCHOR, ORI_INSERT, 1); changes.append("+orientation")

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

#!/usr/bin/env python3
"""Dashboard · 4 cartes carrées en haut + Métiers/Parcours sur 2 colonnes.

Retour utilisateur (avec capture du design d'avant) : remettre une rangée de 4
cartes carrées tout en haut, mais repensées pour : Spécialités, Documents
uploadés, Avancement de l'ado dans le parcours, et RDV avec Charles (RDV pas en
bleu · trop violent). Et mettre Métiers et Parcours académiques côte à côte sur
2 colonnes. Les spés/filières remontent dans la carte carrée « Spécialités »
(clic → détail complet en modale).

Changements (asset dashboard) :
  · ProxxieKpiCards · 4 cartes carrées (Spécialités → FiliereModal, Documents →
    page Documents, Parcours Proxxie → page Parcours, RDV Charles → modale de
    conversion). Couleurs douces, RDV en vert (pas bleu).
  · FiliereModal · enveloppe FiliereCard dans une modale (détail spés/filières).
  · ProxxieMetiersParcours · MetiersCard + ParcoursCard sur 2 colonnes.
  · rendu : retire RdvCard, ProxxieFocusCards et ProxxieOrientationSections ;
    insère ProxxieKpiCards après le héros et ProxxieMetiersParcours après le fil.

Réutilise FiliereCard / MetiersCard / ParcoursCard / ProxxieConversionModal /
_proxxieGetDocs / DOCS_EXPECTED / _proxxieGetOnboardingState / useProxxieRole.
À lancer APRÈS focus + sections (qui définissent ParcoursCard / _proxxieTestsDone).

Idempotent · bloc composant en strip-and-readd ; rendu gardé par sentinelles.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
FILES = ["Proxxie Dashboard.html", "dashboard.html"]

BEGIN = "/* PROXXIE_DASH_KPIS_BEGIN */"
END = "/* PROXXIE_DASH_KPIS_END */"
CREATE_ROOT = 'ReactDOM.createRoot(document.getElementById("root")).render(<Dashboard />);'

COMPONENT = BEGIN + r"""
/* ---------------- Dashboard · 4 cartes carrées + Métiers/Parcours 2 colonnes ---------------- */

const FiliereModal = ({ open, onClose }) => {
  if (!open) return null;
  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, background: "rgba(10,14,44,.55)", display: "grid", placeItems: "center", zIndex: 210, padding: 20, overflowY: "auto" }}>
      <div onClick={(e) => e.stopPropagation()} style={{ maxWidth: 560, width: "100%", maxHeight: "88vh", overflowY: "auto", position: "relative" }}>
        <button onClick={onClose} aria-label="Fermer" style={{ position: "absolute", top: 16, right: 18, zIndex: 2, background: "white", border: "1px solid var(--c-line)", borderRadius: "50%", width: 30, height: 30, fontSize: 18, color: "var(--c-muted)", cursor: "pointer", lineHeight: 1, fontFamily: "inherit" }}>×</button>
        <FiliereCard mode="future" />
      </div>
    </div>
  );
};

const ProxxieKpiCards = () => {
  const role = useProxxieRole();
  const [filiereOpen, setFiliereOpen] = React.useState(false);
  const [rdvOpen, setRdvOpen] = React.useState(false);

  const docs = _proxxieGetDocs();
  const docsDone = DOCS_EXPECTED.filter((d) => docs[d.id]).length;

  let stepDone = 0;
  try {
    const st = _proxxieGetOnboardingState();
    stepDone = [st.profile, st.firstdoc, st.firsttest, st.invited].filter(Boolean).length;
    if (localStorage.getItem("proxxie.rdv.booked") === "1") stepDone += 1;
  } catch (e) {}

  const cards = [
    { label: "Spécialités", value: "Maths · NSI", sub: "à garder en Terminale", color: "#22A06B", onClick: () => setFiliereOpen(true) },
    { label: "Documents", value: docsDone + "/" + DOCS_EXPECTED.length, sub: "documents reçus", color: "#487AFF", href: "Proxxie Documents.html" },
    { label: "Parcours Proxxie", value: "Étape " + Math.min(stepDone + 1, 5) + "/5", sub: stepDone + " étape" + (stepDone > 1 ? "s" : "") + " complétée" + (stepDone > 1 ? "s" : ""), color: "#FD6936", href: "Proxxie Parcours.html" },
    { label: "RDV Charles", value: "À réserver", sub: "1er cadrage offert", color: "#1d7a52", bg: "rgba(34,160,107,.05)", onClick: () => setRdvOpen(true) },
  ];

  let testsDone = 0; try { testsDone = _proxxieTestsDone(role); } catch (e) {}

  const inner = (c) => (
    <React.Fragment>
      <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--c-muted)" }}>{c.label}</div>
      <div style={{ fontFamily: "var(--font-display)", fontSize: 28, fontWeight: 600, letterSpacing: "-0.02em", color: c.color, marginTop: 8, lineHeight: 1.1 }}>{c.value}</div>
      <div style={{ fontSize: 12, color: "var(--c-muted)", marginTop: 4 }}>{c.sub}</div>
    </React.Fragment>
  );
  const cardStyle = (c) => ({
    background: c.bg || "white", border: "1px solid var(--c-line)", borderRadius: 18, padding: "22px 24px",
    cursor: "pointer", textDecoration: "none", color: "inherit", display: "block",
    transition: "transform .15s, box-shadow .15s",
  });
  const hoverOn = (e) => { e.currentTarget.style.transform = "translateY(-2px)"; e.currentTarget.style.boxShadow = "0 10px 28px rgba(10,14,44,.08)"; };
  const hoverOff = (e) => { e.currentTarget.style.transform = "translateY(0)"; e.currentTarget.style.boxShadow = "none"; };

  return (
    <section style={{ margin: "0 auto 22px", padding: "0 24px", maxWidth: 1280 }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
        {cards.map((c, i) => (
          c.href
            ? <a key={i} href={c.href} style={cardStyle(c)} onMouseEnter={hoverOn} onMouseLeave={hoverOff}>{inner(c)}</a>
            : <div key={i} onClick={c.onClick} style={cardStyle(c)} onMouseEnter={hoverOn} onMouseLeave={hoverOff}>{inner(c)}</div>
        ))}
      </div>
      <FiliereModal open={filiereOpen} onClose={() => setFiliereOpen(false)} />
      <ProxxieConversionModal open={rdvOpen} onClose={() => setRdvOpen(false)} role={role} testsDone={testsDone} />
    </section>
  );
};

const ProxxieMetiersParcours = ({ onOpen, audit }) => (
  <section style={{ margin: "0 auto 18px", padding: "0 24px", maxWidth: 1280 }}>
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18, alignItems: "start" }}>
      <MetiersCard onOpen={onOpen} audit={audit} />
      <ParcoursCard />
    </div>
  </section>
);
""" + END + "\n\n" + CREATE_ROOT

# render edits
DROP = [
    "      <RdvCard />\n",
    "      <ProxxieFocusCards />\n",
    "      <ProxxieOrientationSections onOpen={openDrawer} audit={t.audit} />\n",
]
HERO_ANCHOR = "      <NextBestAction onOpenProfile={() => setProfileOpen(true)} onOpenInvite={() => setInviteOpen(true)} />\n"
HERO_INSERT = HERO_ANCHOR + "      <ProxxieKpiCards />\n"
FEED_ANCHOR = "      <WhatsNewFeed />\n"
FEED_INSERT = FEED_ANCHOR + "      <ProxxieMetiersParcours onOpen={openDrawer} audit={t.audit} />\n"


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

    src = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n\n", "", src, flags=re.DOTALL)
    if CREATE_ROOT not in src:
        return "SKIP no createRoot anchor"
    src = src.replace(CREATE_ROOT, COMPONENT, 1)
    changes.append("components")

    for d in DROP:
        if d in src:
            src = src.replace(d, "", 1); changes.append("-" + d.strip().split()[0].lstrip("<"))

    if "<ProxxieKpiCards />" not in src and HERO_ANCHOR in src:
        src = src.replace(HERO_ANCHOR, HERO_INSERT, 1); changes.append("+kpis")
    if "<ProxxieMetiersParcours" not in src and FEED_ANCHOR in src:
        src = src.replace(FEED_ANCHOR, FEED_INSERT, 1); changes.append("+metiersparcours")

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

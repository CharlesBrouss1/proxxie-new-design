#!/usr/bin/env python3
"""Dashboard · petites cartes « explore » qui s'ouvrent au clic (organisation light).

Retour utilisateur : reprendre une organisation à la Documents (cartes propres),
mais rester light · le détail ne s'affiche que si on clique. Le parcours doit
rester clair (le héros = quoi faire maintenant), et le contenu d'orientation doit
vivre dans de petites sections qui s'ouvrent au clic.

Au lieu d'étaler Métiers et Parcours académiques en pleines cartes, on les passe
en cartes compactes (titre + 1 ligne de teaser) qui ouvrent le détail en modale.
On ajoute Tests et Rapport dans la même rangée pour couvrir le parcours.

  · MetiersModal / ParcoursModal · enveloppent MetiersCard / ParcoursCard.
  · ProxxieExploreCards · 4 cartes compactes (Métiers → modale, Parcours
    académiques → modale, Tests psychométriques → TestsModal, Rapport → page),
    grille responsive.
  · rendu · retire ProxxieMetiersParcours, insère ProxxieExploreCards après le fil.

Réutilise MetiersCard / ParcoursCard / TestsModal / _proxxieTestsDone /
useProxxieRole / TESTS_LIST. À lancer APRÈS focus + sections + kpis.

Idempotent · bloc composant strip-and-readd ; rendu gardé par sentinelles.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
FILES = ["Proxxie Dashboard.html", "dashboard.html"]

BEGIN = "/* PROXXIE_DASH_EXPLORE_BEGIN */"
END = "/* PROXXIE_DASH_EXPLORE_END */"
CREATE_ROOT = 'ReactDOM.createRoot(document.getElementById("root")).render(<Dashboard />);'

COMPONENT = BEGIN + r"""
/* ---------------- Dashboard · cartes « explore » compactes (clic → modale) ---------------- */

const _proxxieModalShell = (onClose, child, maxW) => (
  <div onClick={onClose} style={{ position: "fixed", inset: 0, background: "rgba(10,14,44,.55)", display: "grid", placeItems: "center", zIndex: 210, padding: 20, overflowY: "auto" }}>
    <div onClick={(e) => e.stopPropagation()} style={{ maxWidth: maxW || 560, width: "100%", maxHeight: "88vh", overflowY: "auto", position: "relative" }}>
      <button onClick={onClose} aria-label="Fermer" style={{ position: "absolute", top: 16, right: 18, zIndex: 2, background: "white", border: "1px solid var(--c-line)", borderRadius: "50%", width: 30, height: 30, fontSize: 18, color: "var(--c-muted)", cursor: "pointer", lineHeight: 1, fontFamily: "inherit" }}>×</button>
      {child}
    </div>
  </div>
);

const MetiersModal = ({ open, onClose }) => open ? _proxxieModalShell(onClose, <MetiersCard onOpen={() => {}} audit={false} />, 560) : null;
const ParcoursModal = ({ open, onClose }) => open ? _proxxieModalShell(onClose, <ParcoursCard />, 560) : null;

const ProxxieExploreCards = () => {
  const role = useProxxieRole();
  const isEnfant = role === "enfant";
  const [metiers, setMetiers] = React.useState(false);
  const [parcours, setParcours] = React.useState(false);
  const [tests, setTests] = React.useState(false);
  let testsDone = 0; try { testsDone = _proxxieTestsDone(role); } catch (e) {}

  const cards = [
    { ic: "🧭", title: "Métiers compatibles", teaser: "Architecte UX · Ingénieure biomédicale · +11", onClick: () => setMetiers(true) },
    { ic: "🎓", title: "Parcours académiques", teaser: "École d'ingé · BUT · Licence · CPGE", onClick: () => setParcours(true) },
    { ic: "🧪", title: "Tests psychométriques", teaser: testsDone + " sur " + TESTS_LIST.length + " passés", onClick: () => setTests(true) },
    { ic: "📄", title: "Rapport d'orientation", teaser: isEnfant ? "Ta synthèse complète" : "La synthèse complète d'" + FIRST_NAME, href: isEnfant ? "Proxxie Bilan.html" : "Proxxie Rapport.html" },
  ];

  const inner = (c) => (
    <React.Fragment>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
        <span style={{ fontSize: 20 }}>{c.ic}</span>
        <span style={{ fontSize: 15, color: "var(--c-muted)" }}>→</span>
      </div>
      <div style={{ fontFamily: "var(--font-display)", fontSize: 17, fontWeight: 600, marginBottom: 3 }}>{c.title}</div>
      <div style={{ fontSize: 12, color: "var(--c-muted)", lineHeight: 1.4 }}>{c.teaser}</div>
    </React.Fragment>
  );
  const st = { background: "white", border: "1px solid var(--c-line)", borderRadius: 16, padding: "18px 20px", cursor: "pointer", textDecoration: "none", color: "inherit", display: "block", transition: "transform .15s, box-shadow .15s, border-color .15s" };
  const on = (e) => { e.currentTarget.style.transform = "translateY(-2px)"; e.currentTarget.style.borderColor = "var(--c-blue-2)"; e.currentTarget.style.boxShadow = "0 10px 26px rgba(10,14,44,.06)"; };
  const off = (e) => { e.currentTarget.style.transform = "translateY(0)"; e.currentTarget.style.borderColor = "var(--c-line)"; e.currentTarget.style.boxShadow = "none"; };

  return (
    <section style={{ margin: "0 auto 24px", padding: "0 24px", maxWidth: 1280 }}>
      <h2 style={{ fontFamily: "var(--font-display)", fontSize: 18, fontWeight: 600, margin: "0 0 14px", color: "var(--c-ink)" }}>
        {isEnfant ? "Explore ton orientation" : "Explorez l'orientation d'" + FIRST_NAME}
      </h2>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
        {cards.map((c, i) => (
          c.href
            ? <a key={i} href={c.href} style={st} onMouseEnter={on} onMouseLeave={off}>{inner(c)}</a>
            : <div key={i} onClick={c.onClick} style={st} onMouseEnter={on} onMouseLeave={off}>{inner(c)}</div>
        ))}
      </div>
      <MetiersModal open={metiers} onClose={() => setMetiers(false)} />
      <ParcoursModal open={parcours} onClose={() => setParcours(false)} />
      <TestsModal open={tests} onClose={() => setTests(false)} role={role} />
    </section>
  );
};
""" + END + "\n\n" + CREATE_ROOT

DROP = ["      <ProxxieMetiersParcours onOpen={openDrawer} audit={t.audit} />\n"]
FEED_ANCHOR = "      <WhatsNewFeed />\n"
FEED_INSERT = FEED_ANCHOR + "      <ProxxieExploreCards />\n"


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
            src = src.replace(d, "", 1); changes.append("-metiersparcours")

    if "<ProxxieExploreCards />" not in src and FEED_ANCHOR in src:
        src = src.replace(FEED_ANCHOR, FEED_INSERT, 1); changes.append("+explore")

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

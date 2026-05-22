#!/usr/bin/env python3
"""Page Rapport · écran verrouillé + rapport d'exemple (gating Hybride).

Pont vers le vrai produit · le rapport d'orientation ne doit pas prétendre
être prêt tant qu'il n'y a pas assez de données. On enveloppe <ReportApp />
dans un <ReportGate /> qui lit l'état de l'enfant (même contrat `child` que
le dashboard) ·

  rapport.etat === "complet"  → <ReportApp /> direct (vrai rapport)
  "apercu" / "verrouille"     → écran « pas encore débloqué » + bouton
                                « Voir un rapport d'exemple » qui révèle
                                <ReportApp /> sous un bandeau « exemple »
                                (le rapport d'un AUTRE jeune, clairement
                                étiqueté, jamais présenté comme celui de l'ado).

Source de l'état · ?etat=froid|tiede|chaud (démo) > localStorage.proxxie.child
> verrouillé par défaut. Cohérent avec _patch_parcours_states.py côté dashboard.

Idempotent · marker-based. Asset trouvé par contenu (robuste au changement d'UUID).
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
FILES = ["Proxxie Rapport.html", "rapport.html"]

MARKER = "/* __proxxie_rapport_lock_v1__ */"
RENDER_ANCHOR = '\nReactDOM.createRoot(document.getElementById("root")).render(<ReportApp />);'
RENDER_GATED = '\nReactDOM.createRoot(document.getElementById("root")).render(<ReportGate />);'

GATE = MARKER + r"""
const _pxGetChildR = () => {
  try {
    const MOCK = {
      froid: { prenom: "Arthur", rapport: { etat: "verrouille" } },
      tiede: { prenom: "Arthur", rapport: { etat: "apercu" } },
      chaud: { prenom: "Arthur", rapport: { etat: "complet" } },
    };
    const q = new URLSearchParams(window.location.search).get("etat");
    if (q && MOCK[q]) return MOCK[q];
    const raw = localStorage.getItem("proxxie.child");
    if (raw) return JSON.parse(raw);
  } catch (e) {}
  return { prenom: "votre ado", rapport: { etat: "verrouille" } };
};
const _PxSampleBanner = ({ prenom }) => (
  <div style={{ background: "#FFF6E0", borderBottom: "1px solid rgba(253,105,54,.25)", padding: "10px 16px", textAlign: "center", fontSize: 13, color: "#0A0E2C", fontFamily: "Inter, system-ui, sans-serif", position: "sticky", top: 0, zIndex: 100 }}>
    Exemple · rapport d'un autre jeune passé par Proxxie.{" "}
    <a href="Proxxie Dashboard.html" style={{ color: "#1320CE", fontWeight: 600, textDecoration: "none" }}>Débloquer celui de {prenom} →</a>
  </div>
);
const ReportGate = () => {
  const child = _pxGetChildR();
  const etat = (child.rapport && child.rapport.etat) || "verrouille";
  const prenom = child.prenom || "votre ado";
  const [revealed, setRevealed] = React.useState(false);
  if (etat === "complet") return <ReportApp />;
  if (revealed) return (<React.Fragment><_PxSampleBanner prenom={prenom} /><ReportApp /></React.Fragment>);
  const isApercu = etat === "apercu";
  return (
    <div style={{ minHeight: "100vh", background: "#F7F2E9", display: "flex", alignItems: "center", justifyContent: "center", padding: 24, fontFamily: "Inter, system-ui, sans-serif" }}>
      <div style={{ maxWidth: 560, width: "100%", background: "#fff", borderRadius: 24, padding: "40px 36px", boxShadow: "0 24px 70px rgba(10,14,44,.12)", textAlign: "center" }}>
        <div style={{ width: 56, height: 56, borderRadius: 16, background: "rgba(19,32,206,.08)", color: "#1320CE", display: "grid", placeItems: "center", fontSize: 26, margin: "0 auto 20px" }}>{isApercu ? "📊" : "🔒"}</div>
        <h1 style={{ fontFamily: "Fraunces, Georgia, serif", fontSize: 26, fontWeight: 600, color: "#0A0E2C", margin: "0 0 12px", lineHeight: 1.2 }}>
          {isApercu ? ("L'aperçu du rapport de " + prenom + " est prêt") : ("Le rapport de " + prenom + " n'est pas encore débloqué")}
        </h1>
        <p style={{ fontSize: 15, color: "rgba(10,14,44,.6)", lineHeight: 1.6, margin: "0 0 28px" }}>
          {isApercu
            ? "Le test OCEAN-X est fait. Ajoutez 2 bulletins pour croiser le profil avec les résultats scolaires et débloquer le rapport complet (métiers confirmés, vœux Parcoursup)."
            : "On n'a pas encore assez de données pour générer un rapport fiable. Faites le test OCEAN-X et ajoutez les bulletins pour le débloquer. En attendant, regardez un vrai rapport déjà produit pour un autre jeune."}
        </p>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <button onClick={() => setRevealed(true)} style={{ background: "#1320CE", color: "#fff", border: "none", borderRadius: 999, padding: "14px 22px", fontSize: 14, fontWeight: 600, cursor: "pointer", fontFamily: "inherit" }}>
            Voir un rapport d'exemple →
          </button>
          <a href="Proxxie Dashboard.html" style={{ color: "#1320CE", fontSize: 13, fontWeight: 600, textDecoration: "none", padding: 10 }}>
            {isApercu ? "Ajouter des bulletins" : "Retour au tableau de bord"}
          </a>
        </div>
        <p style={{ fontSize: 12, color: "rgba(10,14,44,.4)", margin: "22px 0 0" }}>
          L'exemple est le rapport d'un autre jeune passé par Proxxie, pas celui de {prenom}.
        </p>
      </div>
    </div>
  );
};
"""

STRIP_RE = re.compile(
    r'\n/\* __proxxie_rapport_lock_v1__ \*/.*?\nReactDOM\.createRoot\(document\.getElementById\("root"\)\)\.render\(<ReportGate />\);',
    flags=re.S,
)


def patch_asset(src: str) -> str:
    if MARKER in src:
        src = STRIP_RE.sub(RENDER_ANCHOR, src, count=1)
    if RENDER_ANCHOR not in src:
        raise SystemExit("render(<ReportApp />) anchor not found")
    src = src.replace(RENDER_ANCHOR, "\n" + GATE + RENDER_GATED, 1)
    return src


def patch_one(target: pathlib.Path) -> str:
    if not target.exists():
        return "SKIP missing"
    html = target.read_text(encoding="utf-8")
    m = re.search(r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)', html, re.DOTALL)
    if not m:
        return "no manifest"
    manifest = json.loads(m.group(2))

    target_uuid = None
    for uuid, entry in manifest.items():
        data = base64.b64decode(entry["data"])
        if entry.get("compressed", False):
            try:
                data = gzip.decompress(data)
            except OSError:
                continue
        try:
            s = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if "<ReportApp />" in s and "createRoot" in s:
            target_uuid = uuid
            break
    if target_uuid is None:
        return "asset with <ReportApp /> not found"

    entry = manifest[target_uuid]
    data = base64.b64decode(entry["data"])
    comp = entry.get("compressed", False)
    if comp:
        data = gzip.decompress(data)
    src = data.decode("utf-8")
    was = MARKER in src
    new_src = patch_asset(src)
    nd = new_src.encode("utf-8")
    if comp:
        nd = gzip.compress(nd)
    entry["data"] = base64.b64encode(nd).decode("ascii")
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]
    target.write_text(new_html, encoding="utf-8")
    return f"{'re-patched' if was else 'patched'} (asset {target_uuid[:8]}, {len(new_src)} chars)"


if __name__ == "__main__":
    for fn in FILES:
        try:
            print(f"{fn}: {patch_one(REPO / fn)}")
        except SystemExit as e:
            print(f"{fn}: ERROR · {e}")

#!/usr/bin/env python3
"""Modales Métiers / Parcours · gated par l'état de l'enfant (Pont · (b)).

Les modales ouvertes depuis les cartes "Explorez" affichaient toujours le
contenu démo riche (Architecte UX 94%, Ingénieure biomédicale 91%, etc.),
même en FROID/TIÈDE où aucun score n'est légitime.

On injecte des wrappers `_PxMetiersCard` / `_PxParcoursCard` qui lisent
le `child` et choisissent quoi rendre ·

  FROID  → écran verrouillé avec CTA "Lancer le test OCEAN-X"
  TIÈDE  → liste simple des `child.metiers` / `child.parcours` (noms +
           badge "Estimé", PAS de score · règle d'or anti-mensonge)
  CHAUD  → la carte originale (MetiersCard / ParcoursCard) avec son
           rendu riche (sector, growth %). Acceptable pour le Pont, à
           refondre quand le backend produira de vrais scores croisés.

Les modales `MetiersModal` / `ParcoursModal` (injectées par
_patch_dashboard_explore.py) sont retargettées vers les wrappers. Pas de
modif des composants originaux · seul le callsite des modales change.

Dépendances · `_pxGetChild` et `_pxStage` (parcours_states), `MetiersCard`
et `ParcoursCard` (bundle original + sections patch), `MetiersModal` et
`ParcoursModal` (explore patch). À lancer APRÈS tous ceux-là.

Idempotent · marker-based.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
FILES = ["Proxxie Dashboard.html", "dashboard.html"]

MARKER = "/* __proxxie_modals_gated_v1__ */"
ANCHOR = "const MetiersModal = "

COMPONENTS = MARKER + r"""
const _PxLockedCard = ({ kind }) => (
  <div className="card" style={{ padding: 28, textAlign: "center" }}>
    <div style={{ fontSize: 32, marginBottom: 12 }}>🔒</div>
    <h3 style={{ fontSize: 18, margin: "0 0 8px" }}>
      {kind === "metiers" ? "Métiers compatibles" : "Parcours académiques"}
    </h3>
    <p style={{ fontSize: 13, color: "var(--c-muted)", margin: "0 0 18px", lineHeight: 1.5 }}>
      {kind === "metiers"
        ? "Pas encore débloqué. Faites le test OCEAN-X pour découvrir les métiers compatibles avec le profil."
        : "Pas encore débloqué. Faites le test OCEAN-X pour voir les voies post-bac alignées sur le profil."}
    </p>
    <a href="Proxxie Test.html" style={{ display: "inline-block", padding: "12px 22px", borderRadius: 999, background: "#1320CE", color: "white", textDecoration: "none", fontSize: 14, fontWeight: 600, fontFamily: "inherit" }}>
      Lancer le test OCEAN-X →
    </a>
  </div>
);
const _PxEstimatedList = ({ title, sub, items }) => (
  <div className="card" style={{ padding: 28 }}>
    <div style={{ marginBottom: 16 }}>
      <h3 style={{ fontSize: 20 }}>{title}</h3>
      <div style={{ fontSize: 12, color: "var(--c-muted)", marginTop: 2 }}>{sub}</div>
    </div>
    <div style={{ display: "grid", gap: 8 }}>
      {items.map((x, i) => (
        <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "13px 14px", borderRadius: 10, border: "1px solid var(--c-line)", background: "white" }}>
          <div style={{ fontSize: 14, fontWeight: 600 }}>{x.nom}</div>
          <span style={{ fontSize: 11, fontWeight: 600, color: "#FD6936", padding: "3px 10px", borderRadius: 99, background: "rgba(253,105,54,.10)" }}>Estimé</span>
        </div>
      ))}
    </div>
  </div>
);
const _PxMetiersCard = () => {
  const child = _pxGetChild();
  const stage = _pxStage(child);
  if (stage === "FROID" || !child.metiers || !child.metiers.length) return <_PxLockedCard kind="metiers" />;
  if (stage === "CHAUD") return <MetiersCard onOpen={() => {}} audit={false} />;
  return <_PxEstimatedList title="Métiers compatibles" sub="Estimations d'après le test. Ajoutez 2 bulletins pour obtenir des scores fiables." items={child.metiers} />;
};
const _PxParcoursCard = () => {
  const child = _pxGetChild();
  const stage = _pxStage(child);
  if (stage === "FROID" || !child.parcours || !child.parcours.length) return <_PxLockedCard kind="parcours" />;
  if (stage === "CHAUD") return <ParcoursCard />;
  return <_PxEstimatedList title="Parcours académiques" sub="Voies estimées. La sélection se précise avec les bulletins." items={child.parcours} />;
};
"""

# Specific modal callsites to retarget (defined inside MetiersModal / ParcoursModal closures).
METIERS_OLD = '_proxxieModalShell(onClose, <MetiersCard onOpen={() => {}} audit={false} />, 560)'
METIERS_NEW = '_proxxieModalShell(onClose, <_PxMetiersCard />, 560)'
PARCOURS_OLD = '_proxxieModalShell(onClose, <ParcoursCard />, 560)'
PARCOURS_NEW = '_proxxieModalShell(onClose, <_PxParcoursCard />, 560)'

STRIP_RE = re.compile(
    r'\n/\* __proxxie_modals_gated_v1__ \*/.*?(?=\nconst MetiersModal = )',
    flags=re.S,
)


def patch_asset(src: str) -> str:
    if MARKER in src:
        src = STRIP_RE.sub("", src)
        src = src.replace(METIERS_NEW, METIERS_OLD, 1)
        src = src.replace(PARCOURS_NEW, PARCOURS_OLD, 1)
    for need in ["_pxGetChild", "_pxStage", "const MetiersCard", "const ParcoursCard", ANCHOR, METIERS_OLD, PARCOURS_OLD]:
        if need not in src:
            raise SystemExit(f"missing anchor · {need[:50]}")
    src = src.replace(ANCHOR, COMPONENTS + "\n" + ANCHOR, 1)
    src = src.replace(METIERS_OLD, METIERS_NEW, 1)
    src = src.replace(PARCOURS_OLD, PARCOURS_NEW, 1)
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
            try: data = gzip.decompress(data)
            except OSError: continue
        try: s = data.decode("utf-8")
        except UnicodeDecodeError: continue
        if "const MetiersModal = " in s and "_pxGetChild" in s:
            target_uuid = uuid
            break
    if target_uuid is None:
        return "asset with MetiersModal+_pxGetChild not found"
    entry = manifest[target_uuid]
    data = base64.b64decode(entry["data"])
    comp = entry.get("compressed", False)
    if comp: data = gzip.decompress(data)
    src = data.decode("utf-8")
    was = MARKER in src
    new_src = patch_asset(src)
    nd = new_src.encode("utf-8")
    if comp: nd = gzip.compress(nd)
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

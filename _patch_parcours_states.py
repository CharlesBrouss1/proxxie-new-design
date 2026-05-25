#!/usr/bin/env python3
"""Dashboard · cartes « explore » pilotées par l'état réel de l'enfant.

Pont vers le vrai produit (cf. revue eng /plan-ceo-review + /plan-eng-review) ·
au lieu d'afficher du contenu démo en dur (« Architecte UX · +11 », rapport
toujours « complet »), les cartes Métiers / Parcours / Rapport lisent un objet
`child` et dérivent un état FROID / TIEDE / CHAUD.

Contrat de données (le même servira d'API quand le backend existera) ·
  child = {
    ocean:     { statut: "todo"|"wip"|"done", scores: {...}|null },
    profil:    { complet: 0..6 },
    documents: { bulletins: N },
    metiers:   [{ nom, score?, source: "estime"|"confirme" }],
    parcours:  [{ nom }],
    rapport:   { etat: "verrouille"|"apercu"|"complet" }
  }

Source du child · `?etat=froid|tiede|chaud` (démo sans toucher au storage) >
  localStorage.proxxie.child (JSON) > MOCK_FROID (compte neuf par défaut).

Règle d'or · le % de compatibilité n'est rendu QUE si source === "confirme"
(état CHAUD). En TIEDE, métiers « estimés » sans %. Un score sur données
partielles est un mensonge qui coûte la confiance.

Mode Hybride (choix produit) ·
  FROID  · métiers masqués (« fais le test ») · rapport VERROUILLÉ + voir exemple
  TIEDE  · métiers estimés (sans %)           · rapport APERÇU (« ajoute 2 bulletins »)
  CHAUD  · métiers confirmés (avec %)         · rapport COMPLET

Idempotent · marker-based strip-and-readd. À lancer APRÈS _patch_dashboard_explore.py
(il réécrit le tableau `cards` de ProxxieExploreCards). Ne touche à aucun autre patch.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
FILES = ["Proxxie Dashboard.html", "dashboard.html"]

HELPER_MARKER = "/* __proxxie_parcours_states_v1__ */"
CARDS_MARKER = "/* __proxxie_px_cards_v1__ */"

HELPERS = HELPER_MARKER + r"""
/* Pont · état de l'enfant + dérivation FROID/TIEDE/CHAUD (données mockées). */
const PX_MOCK = {
  froid: { ocean: { statut: "todo", scores: null }, profil: { complet: 0 }, documents: { bulletins: 0 },
           metiers: [], parcours: [], rapport: { etat: "verrouille" } },
  tiede: { ocean: { statut: "done", scores: { O: 72, C: 60, E: 55, A: 68, N: 40 } }, profil: { complet: 3 }, documents: { bulletins: 0 },
           metiers: [{ nom: "Architecte UX", source: "estime" }, { nom: "Ingénieure biomédicale", source: "estime" }, { nom: "Designer produit", source: "estime" }],
           parcours: [{ nom: "École d'ingé" }, { nom: "BUT" }, { nom: "Licence" }], rapport: { etat: "apercu" } },
  chaud: { ocean: { statut: "done", scores: { O: 72, C: 60, E: 55, A: 68, N: 40 } }, profil: { complet: 6 }, documents: { bulletins: 3 },
           metiers: [{ nom: "Architecte UX", score: 94, source: "confirme" }, { nom: "Ingénieure biomédicale", score: 91, source: "confirme" }, { nom: "Designer produit", score: 88, source: "confirme" }],
           parcours: [{ nom: "École d'ingé" }, { nom: "BUT" }, { nom: "Licence" }, { nom: "CPGE" }], rapport: { etat: "complet" } },
};
const _pxGetChild = () => {
  try {
    const q = new URLSearchParams(window.location.search).get("etat");
    if (q && PX_MOCK[q]) return PX_MOCK[q];
    const raw = localStorage.getItem("proxxie.child");
    if (raw) return JSON.parse(raw);
  } catch (e) {}
  return PX_MOCK.froid; /* défaut · compte neuf */
};
const _pxStage = (c) => {
  if (!c || !c.ocean || c.ocean.statut !== "done") return "FROID";
  if (((c.documents && c.documents.bulletins) || 0) < 2 || ((c.profil && c.profil.complet) || 0) < 6) return "TIEDE";
  return "CHAUD";
};
const _pxMetiersTeaser = (c) => {
  const stage = _pxStage(c);
  if (stage === "FROID" || !c.metiers || !c.metiers.length) return "Fais le test pour découvrir tes métiers";
  const names = c.metiers.map((m) => m.nom);
  const head = names.slice(0, 2).join(" · ");
  const more = names.length > 2 ? " · +" + (names.length - 2) : "";
  /* % seulement en CHAUD (source confirmée) · jamais sur données partielles. */
  return (stage === "TIEDE" ? "Estimés · " : "") + head + more;
};
const _pxParcoursTeaser = (c) => {
  const stage = _pxStage(c);
  if (stage === "FROID" || !c.parcours || !c.parcours.length) return "Débloqué après ton profil OCEAN-X";
  return c.parcours.map((p) => p.nom).join(" · ");
};
"""

# Exact original block from the live bundle (ProxxieExploreCards `cards` array).
CARDS_OLD = """  const cards = [
    { ic: "🧭", title: "Métiers compatibles", teaser: "Architecte UX · Ingénieure biomédicale · +11", onClick: () => setMetiers(true) },
    { ic: "🎓", title: "Parcours académiques", teaser: "École d'ingé · BUT · Licence · CPGE", onClick: () => setParcours(true) },
    { ic: "🧪", title: "Tests psychométriques", teaser: testsDone + " sur " + TESTS_LIST.length + " passés", onClick: () => setTests(true) },
    { ic: "📄", title: "Rapport d'orientation", teaser: isEnfant ? "Ta synthèse complète" : "La synthèse complète d'" + FIRST_NAME, href: isEnfant ? "Proxxie Bilan.html" : "Proxxie Rapport.html" },
  ];"""

CARDS_NEW = """  """ + CARDS_MARKER + """
  const _pxChild = _pxGetChild();
  const _pxRetat = (_pxChild.rapport && _pxChild.rapport.etat) || "verrouille";
  const _pxRlocked = _pxRetat !== "complet";
  const _pxRteaser = _pxRetat === "complet"
    ? (isEnfant ? "Ta synthèse complète" : "La synthèse complète d'" + FIRST_NAME)
    : _pxRetat === "apercu"
      ? "Aperçu · ajoute 2 bulletins pour débloquer"
      : (isEnfant ? "Verrouillé · voir un exemple" : "Verrouillé · voir un rapport d'exemple");
  const cards = [
    { ic: "🧭", title: "Métiers compatibles", teaser: _pxMetiersTeaser(_pxChild), onClick: () => setMetiers(true) },
    { ic: "🎓", title: "Parcours académiques", teaser: _pxParcoursTeaser(_pxChild), onClick: () => setParcours(true) },
    { ic: "🧪", title: "Tests psychométriques", teaser: testsDone + " sur " + TESTS_LIST.length + " passés", onClick: () => setTests(true) },
    { ic: "📄", title: _pxRlocked ? "Rapport d'orientation 🔒" : "Rapport d'orientation", teaser: _pxRteaser, href: isEnfant ? "Proxxie Bilan.html" : "Proxxie Rapport.html" },
  ];"""

DASHBOARD_ANCHOR = "const Dashboard = () =>"

STRIP_RE = re.compile(
    r'\n/\* __proxxie_parcours_states_v1__ \*/.*?(?=\nconst Dashboard = \(\) =>)',
    flags=re.S,
)


def strip_v1(src: str) -> str:
    src = STRIP_RE.sub("", src)
    src = src.replace(CARDS_NEW, CARDS_OLD, 1)
    return src


def patch_asset(src: str) -> str:
    if HELPER_MARKER in src:
        src = strip_v1(src)
    if DASHBOARD_ANCHOR not in src:
        raise SystemExit("anchor 'const Dashboard = () =>' not found")
    if CARDS_OLD not in src:
        raise SystemExit("ProxxieExploreCards `cards` array not found (run _patch_dashboard_explore.py first?)")
    src = src.replace(DASHBOARD_ANCHOR, HELPERS + "\n" + DASHBOARD_ANCHOR, 1)
    src = src.replace(CARDS_OLD, CARDS_NEW, 1)
    return src


def patch_one(target: pathlib.Path) -> str:
    if not target.exists():
        return "SKIP missing"
    html = target.read_text(encoding="utf-8")
    m = re.search(r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)', html, re.DOTALL)
    if not m:
        return "no manifest"
    manifest = json.loads(m.group(2))

    # Find the asset that holds ProxxieExploreCards (robust to UUID changes).
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
        if "ProxxieExploreCards" in s and (CARDS_OLD in s or HELPER_MARKER in s):
            target_uuid = uuid
            break
    if target_uuid is None:
        return "asset with ProxxieExploreCards not found"

    entry = manifest[target_uuid]
    data = base64.b64decode(entry["data"])
    comp = entry.get("compressed", False)
    if comp:
        data = gzip.decompress(data)
    src = data.decode("utf-8")
    was_patched = HELPER_MARKER in src
    new_src = patch_asset(src)
    nd = new_src.encode("utf-8")
    if comp:
        nd = gzip.compress(nd)
    entry["data"] = base64.b64encode(nd).decode("ascii")
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]
    target.write_text(new_html, encoding="utf-8")
    verb = "re-patched" if was_patched else "patched"
    return f"{verb} (asset {target_uuid[:8]}, {len(new_src)} chars)"


if __name__ == "__main__":
    for fn in FILES:
        try:
            print(f"{fn}: {patch_one(REPO / fn)}")
        except SystemExit as e:
            print(f"{fn}: ERROR · {e}")

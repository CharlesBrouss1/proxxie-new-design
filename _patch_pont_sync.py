#!/usr/bin/env python3
"""Dashboard · synchronise l'état `child` (Pont) vers les clés localStorage
existantes que lisent les autres patches (NextBestAction, KPICards,
OnboardingChecklist, DocsCompletenessPanel).

Pourquoi · le Pont (_patch_parcours_states.py) a câblé les cartes
« Explorez » sur un objet `child` unique. Mais le hero « Votre prochaine
étape », les 4 KPI cartes et la checklist onboarding lisent encore des
clés legacy (`proxxie.onboarding.profile`, `proxxie.tests.big5.{role}`,
`proxxie.docs.{id}`, `proxxie.rdv.booked`). Au lieu de réécrire chaque
composant (fragile, multi-patch), on synchronise le `child` vers ces clés
au chargement de page. Tout le dashboard devient alors réactif au stage
en un seul point.

Garde · le sync ne s'active QUE si `?etat=froid|tiede|chaud` est en URL
(démo). Pour de vrais utilisateurs (pas de param), le localStorage existant
est laissé intact. Pas de mutation destructrice du vrai parcours d'un parent.

Dépendances · `_pxGetChild` et `_pxStage` doivent exister dans l'asset
(injectés par `_patch_parcours_states.py`). À lancer APRÈS celui-ci.

Idempotent · marker-based, strip-and-readd.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
FILES = ["Proxxie Dashboard.html", "dashboard.html"]

MARKER = "/* __proxxie_pont_sync_v1__ */"
ANCHOR = "const _pxMetiersTeaser = (c) =>"  # injected by parcours_states; we insert just before it

INJECT = MARKER + r"""
const _pxSyncToLegacy = (c) => {
  try {
    const role = localStorage.getItem("proxxie.role") || "parent";
    /* profil 6/6 ⇒ onboarding.profile */
    if (c.profil && c.profil.complet >= 6) localStorage.setItem("proxxie.onboarding.profile", "1");
    else localStorage.removeItem("proxxie.onboarding.profile");
    /* OCEAN-X ⇒ Big Five (legacy + role-scoped) */
    if (c.ocean && c.ocean.statut === "done") {
      localStorage.setItem("proxxie.tests.big5", "done");
      localStorage.setItem("proxxie.tests.big5." + role, "done");
    } else {
      localStorage.removeItem("proxxie.tests.big5");
      localStorage.removeItem("proxxie.tests.big5.parent");
      localStorage.removeItem("proxxie.tests.big5.enfant");
    }
    /* Tests secondaires (RIASEC etc.) · marqués done en CHAUD pour cohérence
       avec le hero "tout est en place". Pour l'instant on couvre RIASEC, qui
       est la 6ème étape du NextBestAction. À étendre si d'autres tests sont
       ajoutés au hero. */
    const stageNow = _pxStage(c);
    if (stageNow === "CHAUD") {
      localStorage.setItem("proxxie.tests.riasec", "done");
      localStorage.setItem("proxxie.tests.riasec." + role, "done");
    } else {
      localStorage.removeItem("proxxie.tests.riasec");
      localStorage.removeItem("proxxie.tests.riasec.parent");
      localStorage.removeItem("proxxie.tests.riasec.enfant");
    }
    /* Documents · DOCS_EXPECTED a des `def: true` pour bull_t1/t2/n1/test_oc,
       donc on doit poser les clés explicitement (sinon fallback aux defaults). */
    const bullSlots = ["bull_t1", "bull_t2", "bull_t3", "bull_n1"];
    const n = (c.documents && c.documents.bulletins) || 0;
    bullSlots.forEach((id, i) => {
      localStorage.setItem("proxxie.docs." + id, i < n ? "1" : "0");
    });
    /* test_oc · le doc « Résultats OCEAN-X » suit le statut du test */
    localStorage.setItem("proxxie.docs.test_oc", (c.ocean && c.ocean.statut === "done") ? "1" : "0");
    /* invited + RDV ⇒ état CHAUD uniquement */
    const stage = stageNow;
    if (stage === "CHAUD") {
      localStorage.setItem("proxxie.onboarding.invited", "1");
      localStorage.setItem("proxxie.rdv.booked", "1");
    } else {
      localStorage.removeItem("proxxie.onboarding.invited");
      localStorage.removeItem("proxxie.rdv.booked");
    }
  } catch (e) {}
};
/* IIFE · sync uniquement en mode démo (?etat=) pour ne jamais toucher
   au localStorage d'un vrai parent. */
(function () {
  try {
    const q = new URLSearchParams(window.location.search).get("etat");
    if (q && (q === "froid" || q === "tiede" || q === "chaud")) {
      _pxSyncToLegacy(_pxGetChild());
    }
  } catch (e) {}
})();
"""

STRIP_RE = re.compile(
    r'\n/\* __proxxie_pont_sync_v1__ \*/.*?(?=\nconst _pxMetiersTeaser = \(c\) =>)',
    flags=re.S,
)


def patch_asset(src: str) -> str:
    if MARKER in src:
        src = STRIP_RE.sub("", src)
    if "_pxGetChild" not in src or "_pxStage" not in src:
        raise SystemExit("missing _pxGetChild/_pxStage (run _patch_parcours_states.py first)")
    if ANCHOR not in src:
        raise SystemExit("anchor 'const _pxMetiersTeaser' not found")
    src = src.replace(ANCHOR, INJECT + "\n" + ANCHOR, 1)
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
        if "_pxGetChild" in s and "ProxxieExploreCards" in s:
            target_uuid = uuid
            break
    if target_uuid is None:
        return "asset with _pxGetChild not found"
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

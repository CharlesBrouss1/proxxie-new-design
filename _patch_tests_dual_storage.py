#!/usr/bin/env python3
"""Upgrade test page _proxxieMirrorDone helper to dual storage.

Phase 1 saved test completion to one key · localStorage.proxxie.tests.{id}.
This made parent and ado share the same status (whoever passes last
overwrites the other), and the comparison page had no real data to read.

This upgrade adds role-scoped storage · proxxie.tests.{id}.{role} alongside
the legacy key. For Big Five (the comparison page's anchor test), also
stores deterministic mock results per role.

Storage schema after this patch·
  proxxie.tests.riasec           = "done"                            (legacy, kept for backward compat with TestsPanel / onboarding)
  proxxie.tests.riasec.parent    = "done"                            (canonical)
  proxxie.tests.riasec.enfant    = "done"                            (canonical)
  proxxie.tests.big5.parent.results = {"O":72, "C":81, ...}          (used by comparaison.html)
  proxxie.tests.big5.enfant.results = {"O":88, "C":62, ...}

Targets the 24 test bundles patched in Phase 1.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
MARKER = "/* __proxxie_dual_storage_v1__ */"

TESTS = [
    ("Proxxie Test RIASEC.html", "Proxxie Test MBTI.html", "Proxxie Test PCM.html",
     "Proxxie Test HPI.html", "Proxxie Test TDAH.html", "Proxxie Test DYS.html",
     "Proxxie Test Autisme.html", "Proxxie Test Anxiete.html", "Proxxie Test Besoins.html",
     "Proxxie Test Drivers.html", "Proxxie Test Valeurs.html", "Proxxie Test.html",
     "test-riasec.html", "test-mbti.html", "test-pcm.html", "test-hpi.html",
     "test-tdah.html", "test-dys.html", "test-autisme.html", "test-anxiete.html",
     "test-besoins.html", "test-drivers.html", "test-valeurs.html", "test.html")
]
TESTS = TESTS[0]  # flatten

OLD_HELPER = '''const _proxxieMirrorDone = () => {
  try {
    if (!_proxxieIsConnected()) return;
    window.localStorage.setItem("proxxie.tests." + __PROXXIE_TEST_ID__, "done");
  } catch (e) {}
};'''

NEW_HELPER = '''/* __proxxie_dual_storage_v1__ */
const _proxxieMirrorDone = () => {
  try {
    if (!_proxxieIsConnected()) return;
    var role = window.localStorage.getItem("proxxie.role");
    if (role !== "parent" && role !== "enfant") return;
    /* Canonical · role-scoped storage for parent vs ado comparison */
    window.localStorage.setItem("proxxie.tests." + __PROXXIE_TEST_ID__ + "." + role, "done");
    /* Deterministic mock results for Big Five (comparaison.html reads this) */
    if (__PROXXIE_TEST_ID__ === "big5") {
      var mock = role === "parent"
        ? { O: 72, C: 81, E: 64, A: 86, N: 70, profile: "Coordinatrice empathique" }
        : { O: 88, C: 62, E: 48, A: 71, N: 76, profile: "Exploratrice analytique" };
      window.localStorage.setItem("proxxie.tests.big5." + role + ".results", JSON.stringify(mock));
    }
    /* Legacy · kept for backward compat (TestsPanel, onboarding checklist) */
    window.localStorage.setItem("proxxie.tests." + __PROXXIE_TEST_ID__, "done");
  } catch (e) {}
};'''


def find_main_asset(manifest):
    for uuid, entry in manifest.items():
        data = base64.b64decode(entry["data"])
        if entry.get("compressed"):
            try: data = gzip.decompress(data)
            except Exception: continue
        try: src = data.decode("utf-8")
        except UnicodeDecodeError: continue
        if "TestFlowEngine" in src and "_proxxieMirrorDone" in src:
            return uuid
    return None


def patch_asset_text(src: str) -> str:
    was_patched = MARKER in src
    if was_patched:
        # Strip · find the new helper block and revert to old
        src = src.replace(NEW_HELPER, OLD_HELPER, 1)
    if OLD_HELPER not in src:
        raise SystemExit("OLD_HELPER anchor not found (run _patch_test_pages_phase1.py first)")
    src = src.replace(OLD_HELPER, NEW_HELPER, 1)
    return src


def patch_one(target: pathlib.Path) -> str:
    if not target.exists(): return "SKIP missing"
    html = target.read_text(encoding="utf-8")
    m = re.search(r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)', html, re.DOTALL)
    if not m: return "no manifest"
    manifest = json.loads(m.group(2))
    uuid = find_main_asset(manifest)
    if not uuid: return "ERROR · main asset not found (Phase 1 not applied?)"
    entry = manifest[uuid]
    data = base64.b64decode(entry["data"])
    comp = entry.get("compressed", False)
    if comp: data = gzip.decompress(data)
    src = data.decode("utf-8")
    was_patched = MARKER in src
    try:
        new_src = patch_asset_text(src)
    except SystemExit as e:
        return f"ERROR · {e}"
    nd = new_src.encode("utf-8")
    if comp: nd = gzip.compress(nd)
    manifest[uuid]["data"] = base64.b64encode(nd).decode("ascii")
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]
    target.write_text(new_html, encoding="utf-8")
    return f"{'re-patched' if was_patched else 'patched'} (asset {uuid[:8]} {len(new_src)} chars)"


if __name__ == "__main__":
    for fn in TESTS:
        print(f"{fn}: {patch_one(REPO / fn)}")

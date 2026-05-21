#!/usr/bin/env python3
"""Phase 1 · fix bug "click test = teleport hors du connecté".

Each Proxxie Test {Name}.html (and lowercase twin) bundle currently has a
ProxxieNav that links to the marketing site (Proxxie Home.html). When the
user is connected (proxxie.role set), we want·
  1. A lite header pointing to Proxxie Dashboard.html instead.
  2. A save mirror on completion · localStorage.proxxie.tests.{id} = "done"
     so the dashboard TestsPanel reflects completion.
  3. A redirect after email-submit · Proxxie Dashboard.html?testCompleted={id}
     so the user lands back where they came from.

Detection · localStorage.proxxie.role is "parent" or "enfant".
Marker · /* __proxxie_test_phase1_v1__ */ (idempotent, strip+readd on re-run).
"""
import re, json, base64, gzip, pathlib, sys

REPO = pathlib.Path(__file__).parent
MARKER = "/* __proxxie_test_phase1_v1__ */"

# (filename, test_id) pairs · test_id maps to localStorage.proxxie.tests.{id}
# Big Five / OCEAN-X is the generic Proxxie Test.html (used by onboarding).
TESTS = [
    ("Proxxie Test RIASEC.html",   "riasec"),
    ("Proxxie Test MBTI.html",     "mbti"),
    ("Proxxie Test PCM.html",      "pcm"),
    ("Proxxie Test HPI.html",      "hpi"),
    ("Proxxie Test TDAH.html",     "tdah"),
    ("Proxxie Test DYS.html",      "dys"),
    ("Proxxie Test Autisme.html",  "autisme"),
    ("Proxxie Test Anxiete.html",  "anxiete"),
    ("Proxxie Test Besoins.html",  "besoins"),
    ("Proxxie Test Drivers.html",  "drivers"),
    ("Proxxie Test Valeurs.html",  "valeurs"),
    ("Proxxie Test.html",          "big5"),
    # lowercase twins
    ("test-riasec.html",   "riasec"),
    ("test-mbti.html",     "mbti"),
    ("test-pcm.html",      "pcm"),
    ("test-hpi.html",      "hpi"),
    ("test-tdah.html",     "tdah"),
    ("test-dys.html",      "dys"),
    ("test-autisme.html",  "autisme"),
    ("test-anxiete.html",  "anxiete"),
    ("test-besoins.html",  "besoins"),
    ("test-drivers.html",  "drivers"),
    ("test-valeurs.html",  "valeurs"),
    ("test.html",          "big5"),
]

# ---- JSX templates ----

HELPERS_TEMPLATE = r"""
__MARKER__
const __PROXXIE_TEST_ID__ = "__TEST_ID__";
const _proxxieIsConnected = () => {
  try {
    if (typeof window === "undefined" || !window.localStorage) return false;
    const r = window.localStorage.getItem("proxxie.role");
    return r === "parent" || r === "enfant";
  } catch (e) { return false; }
};
const _proxxieMirrorDone = () => {
  try {
    if (!_proxxieIsConnected()) return;
    window.localStorage.setItem("proxxie.tests." + __PROXXIE_TEST_ID__, "done");
  } catch (e) {}
};
const _proxxieRedirectDashboard = (delayMs) => {
  try {
    if (!_proxxieIsConnected()) return;
    setTimeout(() => {
      window.location.href = "Proxxie Dashboard.html?testCompleted=" + __PROXXIE_TEST_ID__;
    }, delayMs || 1200);
  } catch (e) {}
};

const ConnectedTestHeader = () => (
  <nav style={{
    position: "sticky", top: 0, zIndex: 50,
    background: "rgba(247,242,233,0.9)",
    backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)",
    borderBottom: "1px solid rgba(10,14,44,0.06)",
  }}>
    <div className="shell" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", height: 64 }}>
      <a href="Proxxie Dashboard.html" style={{ display: "flex", alignItems: "center", gap: 8, textDecoration: "none", color: "var(--c-ink)" }}>
        <ProxxieLogo size={22} />
      </a>
      <div style={{ display: "flex", alignItems: "center", gap: 14, fontSize: 12, color: "rgba(10,14,44,.55)" }}>
        <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
          <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#22A06B" }}></span>
          Test en cours <span style={{ opacity: 0.6 }}>· sauvegarde automatique</span>
        </span>
      </div>
      <a href="Proxxie Dashboard.html" style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 13, fontWeight: 600, color: "#1320CE", textDecoration: "none", padding: "8px 14px", borderRadius: 999, border: "1px solid rgba(19,32,206,.18)", background: "rgba(255,255,255,.5)" }}>
        ← Tableau de bord
      </a>
    </div>
  </nav>
);
"""

# Insertion anchors
PROXXIE_NAV_ANCHOR = "const ProxxieNav = () => {"
NAV_RETURN_ANCHOR = """  return (
  <>
    <nav style={{
      position: "sticky", top: 0, zIndex: 50,
      background: "rgba(247,242,233,0.9)","""
NAV_RETURN_REPLACE = """  if (_proxxieIsConnected()) return <ConnectedTestHeader />;
  return (
  <>
    <nav style={{
      position: "sticky", top: 0, zIndex: 50,
      background: "rgba(247,242,233,0.9)","""

# In TestFlowEngine, find `const done = i >= total;` and add useEffect after it
FLOW_DONE_ANCHOR = "const done = i >= total;"
FLOW_DONE_REPLACE = """const done = i >= total;
  React.useEffect(() => { if (done) _proxxieMirrorDone(); }, [done]);"""

# In EmailResultsActions, find setSubmitted(true) and add redirect after
SUBMIT_ANCHOR = "setSubmitted(true);"
SUBMIT_REPLACE = """setSubmitted(true);
    _proxxieRedirectDashboard(1500);"""


def find_main_asset(manifest):
    """Heuristic: largest JS asset containing 'TestFlowEngine'."""
    best_uuid, best_size = None, 0
    for uuid, entry in manifest.items():
        data = base64.b64decode(entry["data"])
        if entry.get("compressed"):
            try: data = gzip.decompress(data)
            except Exception: continue
        try: src = data.decode("utf-8")
        except UnicodeDecodeError: continue
        if "TestFlowEngine" in src and "ProxxieNav" in src and len(src) > best_size:
            best_uuid, best_size = uuid, len(src)
    return best_uuid


def strip_v1(src: str) -> str:
    """Reverse the patch so we can re-apply with updated code."""
    # Remove helpers block (from marker to end of ConnectedTestHeader)
    pattern = re.compile(
        r'\n' + re.escape(MARKER) + r'.*?const ConnectedTestHeader = \(\) => \(.*?\);\s*\n',
        flags=re.S,
    )
    src = pattern.sub("\n", src)
    # Revert JSX injections
    src = src.replace(NAV_RETURN_REPLACE, NAV_RETURN_ANCHOR, 1)
    src = src.replace(FLOW_DONE_REPLACE, FLOW_DONE_ANCHOR, 1)
    src = src.replace(SUBMIT_REPLACE, SUBMIT_ANCHOR, 1)
    return src


def patch_asset(src: str, test_id: str) -> str:
    was_patched = MARKER in src
    if was_patched:
        src = strip_v1(src)

    # Sanity checks
    if PROXXIE_NAV_ANCHOR not in src:
        raise SystemExit("ProxxieNav anchor not found")
    if NAV_RETURN_ANCHOR not in src:
        raise SystemExit("Nav return anchor not found")
    if FLOW_DONE_ANCHOR not in src:
        raise SystemExit("TestFlowEngine done anchor not found")
    if SUBMIT_ANCHOR not in src:
        raise SystemExit("setSubmitted(true) anchor not found")

    # 1. Inject helpers before const ProxxieNav
    helpers = HELPERS_TEMPLATE.replace("__MARKER__", MARKER).replace("__TEST_ID__", test_id)
    src = src.replace(PROXXIE_NAV_ANCHOR, helpers + "\n" + PROXXIE_NAV_ANCHOR, 1)

    # 2. Replace nav return for connected check
    src = src.replace(NAV_RETURN_ANCHOR, NAV_RETURN_REPLACE, 1)

    # 3. Inject save mirror after done computation
    src = src.replace(FLOW_DONE_ANCHOR, FLOW_DONE_REPLACE, 1)

    # 4. Inject redirect after setSubmitted(true)
    src = src.replace(SUBMIT_ANCHOR, SUBMIT_REPLACE, 1)

    return src


def patch_one(target: pathlib.Path, test_id: str) -> str:
    if not target.exists():
        return "SKIP missing"
    html = target.read_text(encoding="utf-8")
    m = re.search(r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)', html, re.DOTALL)
    if not m:
        return "no manifest"
    manifest = json.loads(m.group(2))

    main_uuid = find_main_asset(manifest)
    if not main_uuid:
        return "ERROR · main asset not found"

    entry = manifest[main_uuid]
    data = base64.b64decode(entry["data"])
    comp = entry.get("compressed", False)
    if comp: data = gzip.decompress(data)
    src = data.decode("utf-8")

    was_patched = MARKER in src
    try:
        new_src = patch_asset(src, test_id)
    except SystemExit as e:
        return f"ERROR · {e}"

    nd = new_src.encode("utf-8")
    if comp: nd = gzip.compress(nd)
    entry["data"] = base64.b64encode(nd).decode("ascii")
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]
    target.write_text(new_html, encoding="utf-8")
    verb = "re-patched" if was_patched else "patched"
    return f"{verb} (test_id={test_id}, asset {main_uuid[:8]} {len(new_src)} chars)"


if __name__ == "__main__":
    for fn, test_id in TESTS:
        print(f"{fn}: {patch_one(REPO / fn, test_id)}")

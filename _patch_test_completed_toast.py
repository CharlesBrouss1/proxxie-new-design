#!/usr/bin/env python3
"""Dashboard toast when arriving with ?testCompleted=<id>.

After a connected user submits a test (Phase 1 redirect), they land back on
the Dashboard with the query param. This patch adds a TestCompletedToast
component that·

  1. Reads ?testCompleted=<id> on mount.
  2. Looks up the test title from TESTS_LIST (defined in
     _patch_tests_panel.py, in scope on the dashboard).
  3. Renders a celebratory toast in the top-right for 5 seconds.
  4. Cleans the URL via history.replaceState so a refresh doesn't re-trigger.

Idempotent · stripped + re-added if MARKER present.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
TARGETS = ["dashboard.html", "Proxxie Dashboard.html"]
DASHBOARD_ASSET = "5a278f70-3fa5-4bc0-bdb2-349143947f86"
MARKER = "/* __proxxie_test_completed_toast_v1__ */"


COMPONENT_JSX = r"""
/* __proxxie_test_completed_toast_v1__ */
/* Capture testCompleted at module init. React 18 StrictMode mounts the
   component twice (dev only); if we read window.location.search inside
   the second mount AFTER the first mount cleaned it, state stays null
   and the toast never appears. Module-scope capture survives both. */
(function () {
  try {
    if (typeof window.__PROXXIE_INCOMING_TEST_ID === "undefined") {
      window.__PROXXIE_INCOMING_TEST_ID = new URLSearchParams(window.location.search).get("testCompleted");
    }
  } catch (e) { window.__PROXXIE_INCOMING_TEST_ID = null; }
})();

const TestCompletedToast = () => {
  const [completed, setCompleted] = React.useState(() => {
    const id = (typeof window !== "undefined") ? window.__PROXXIE_INCOMING_TEST_ID : null;
    if (!id) return null;
    const t = (typeof TESTS_LIST !== "undefined")
      ? TESTS_LIST.find((x) => x.id === id)
      : null;
    return { id, title: t ? t.title : id.toUpperCase() };
  });

  React.useEffect(() => {
    if (!completed) return undefined;
    /* Clean URL so refresh doesn't re-trigger. Safe to run multiple times. */
    try {
      const url = new URL(window.location.href);
      if (url.searchParams.has("testCompleted")) {
        url.searchParams.delete("testCompleted");
        window.history.replaceState({}, "", url.toString());
      }
    } catch (e) {}
    const tm = setTimeout(() => setCompleted(null), 5000);
    return () => clearTimeout(tm);
  }, [completed]);

  if (!completed) return null;
  return (
    <div style={{
      position: "fixed",
      top: 88, right: 24,
      zIndex: 300,
      background: "linear-gradient(135deg, #22A06B 0%, #1A7F54 100%)",
      color: "white",
      borderRadius: 16,
      padding: "16px 22px 16px 18px",
      boxShadow: "0 16px 40px rgba(34,160,107,.35)",
      display: "flex",
      alignItems: "center",
      gap: 14,
      maxWidth: 380,
    }}>
      <div style={{
        width: 38, height: 38, borderRadius: 12,
        background: "rgba(255,255,255,.22)",
        display: "grid", placeItems: "center",
        fontSize: 20, flexShrink: 0,
      }}>✓</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, fontWeight: 700, letterSpacing: "0.04em", textTransform: "uppercase", opacity: 0.85, marginBottom: 2 }}>
          Test terminé
        </div>
        <div style={{ fontSize: 16, fontWeight: 600, lineHeight: 1.3 }}>
          Bravo, {completed.title} validé · +50 XP
        </div>
      </div>
      <button onClick={() => setCompleted(null)} style={{
        background: "transparent", border: "none", color: "white",
        fontSize: 18, opacity: 0.7, cursor: "pointer", padding: 4, lineHeight: 1, fontFamily: "inherit",
      }} aria-label="Fermer">×</button>
    </div>
  );
};
"""

RETURN_ANCHOR = '<InvitationModal open={inviteOpen} onClose={() => setInviteOpen(false)} />'
RETURN_REPLACE = RETURN_ANCHOR + '\n      <TestCompletedToast />'


STRIP_RE = re.compile(
    r'\n/\* __proxxie_test_completed_toast_v1__ \*/.*?(?=\n(?:/\* __proxxie_|const Dashboard = \(\) =>))',
    flags=re.S,
)


def strip_v1(src: str) -> str:
    src = STRIP_RE.sub("", src)
    src = src.replace(RETURN_REPLACE, RETURN_ANCHOR, 1)
    return src


def patch_asset(src: str) -> str:
    if MARKER in src:
        src = strip_v1(src)
    if RETURN_ANCHOR not in src:
        raise SystemExit("InvitationModal anchor not found (run _patch_dashboard_v2.py first)")
    if "TESTS_LIST" not in src:
        raise SystemExit("TESTS_LIST not found (run _patch_tests_panel.py first)")

    src = src.replace("const Dashboard = () =>", COMPONENT_JSX + "\nconst Dashboard = () =>", 1)
    src = src.replace(RETURN_ANCHOR, RETURN_REPLACE, 1)
    return src


def patch_one(target: pathlib.Path) -> str:
    if not target.exists(): return "SKIP missing"
    html = target.read_text(encoding="utf-8")
    m = re.search(r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)', html, re.DOTALL)
    if not m: return "no manifest"
    manifest = json.loads(m.group(2))
    if DASHBOARD_ASSET not in manifest: return "asset not found"
    entry = manifest[DASHBOARD_ASSET]
    data = base64.b64decode(entry["data"])
    comp = entry.get("compressed", False)
    if comp: data = gzip.decompress(data)
    src = data.decode("utf-8")
    was_patched = MARKER in src
    new_src = patch_asset(src)
    nd = new_src.encode("utf-8")
    if comp: nd = gzip.compress(nd)
    entry["data"] = base64.b64encode(nd).decode("ascii")
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]
    target.write_text(new_html, encoding="utf-8")
    verb = "re-patched" if was_patched else "patched"
    return f"{verb} (asset {len(new_src)} chars)"


if __name__ == "__main__":
    for fn in TARGETS:
        try:
            print(f"{fn}: {patch_one(REPO / fn)}")
        except SystemExit as e:
            print(f"{fn}: ERROR · {e}")

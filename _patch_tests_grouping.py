#!/usr/bin/env python3
"""P2 · regrouper les tests par catégorie + durée et progression globale.

The dashboard TestsPanel listed 11 tests in a flat 4-column grid with no sense of
how long each takes or how far along you are, so it read as a long, abandonable
wall. The design-critique asked to group them (personnalité / neuro-atypies /
valeurs) and surface duration + global progress.

This patches the dashboard asset to:
  · inject a per-test duration + category map (PROXXIE_TEST_META / _CATS),
  · show « ⏱ ~X min » on each TestStatusCard,
  · add a progress bar « X/11 passés · ~Y min restantes » in the panel header,
  · replace the flat grid with grouped sections, each with a « N tests · ~M min »
    label.

Idempotent · the meta block is strip-and-readd between markers; the four
in-place edits are each guarded by a sentinel.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
FILES = ["Proxxie Dashboard.html", "dashboard.html"]

BEGIN = "/* PROXXIE_TESTS_GROUPING_BEGIN */"
END = "/* PROXXIE_TESTS_GROUPING_END */"
PANEL_ANCHOR = "const TestsPanel = () => {"

META = BEGIN + r"""
/* Durée estimée (min) + regroupement par famille. */
const PROXXIE_TEST_META = {
  big5: { min: 10 }, riasec: { min: 10 }, mbti: { min: 12 }, pcm: { min: 10 }, drivers: { min: 8 },
  hpi: { min: 8 }, tdah: { min: 6 }, dys: { min: 8 }, autisme: { min: 6 }, anxiete: { min: 6 },
  besoins: { min: 7 }, valeurs: { min: 8 },
};
const _proxxieTestMin = (id) => (PROXXIE_TEST_META[id] && PROXXIE_TEST_META[id].min) || 8;

const PROXXIE_TEST_CATS = [
  { id: "perso",   label: "Personnalité & orientation", ids: ["riasec", "mbti", "pcm", "drivers"] },
  { id: "neuro",   label: "Neuro-atypies & bien-être",  ids: ["hpi", "tdah", "dys", "autisme", "anxiete"] },
  { id: "valeurs", label: "Valeurs & besoins",          ids: ["besoins", "valeurs"] },
];

""" + END + "\n\n" + PANEL_ANCHOR

# 1 · duration on each card
DUR_OLD = (
    '      <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, fontWeight: 600, color: suggested ? "#FD6936" : ctaColor, marginTop: 4 }}>\n'
    "        {cta} →\n"
    "      </div>\n"
)
DUR_NEW = (
    '      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 6, marginTop: 4 }}>\n'
    '        <span style={{ fontSize: 11, color: "rgba(10,14,44,.45)", fontFamily: "var(--font-num)" }}>⏱ ~{_proxxieTestMin(t.id)} min</span>\n'
    '        <span style={{ fontSize: 13, fontWeight: 600, color: suggested ? "#FD6936" : ctaColor }}>{cta} →</span>\n'
    "      </div>\n"
)

# 2 · progress computations (after suggested)
PROG_OLD = "  const suggested = TESTS_LIST.find((t) => t.id === suggestedId);\n"
PROG_NEW = (
    PROG_OLD
    + "  const _testsDoneCount = TESTS_LIST.filter((t) => getStatus(t) === \"done\").length;\n"
    + "  const _testsPct = Math.round((_testsDoneCount / TESTS_LIST.length) * 100);\n"
    + "  const _testsRemainMin = TESTS_LIST.filter((t) => getStatus(t) !== \"done\").reduce((a, t) => a + _proxxieTestMin(t.id), 0);\n"
)

# 3 · progress bar in header (after the {sub} paragraph)
BAR_OLD = (
    '          <p style={{ color: "rgba(10,14,44,.55)", fontSize: 14, margin: 0, lineHeight: 1.5 }}>\n'
    "            {sub}\n"
    "          </p>\n"
)
BAR_NEW = (
    BAR_OLD
    + '          <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 14 }}>\n'
    + '            <div style={{ flex: "0 0 160px", maxWidth: 160, height: 8, borderRadius: 999, background: "rgba(10,14,44,.06)", overflow: "hidden" }}>\n'
    + '              <div style={{ width: _testsPct + "%", height: "100%", background: _testsDoneCount === TESTS_LIST.length ? "#22A06B" : "linear-gradient(90deg, #FD6936 0%, #F5EB3F 100%)", transition: "width .4s ease" }} />\n'
    + "            </div>\n"
    + '            <span style={{ fontSize: 13, color: "var(--c-muted)", fontFamily: "var(--font-num)" }}>\n'
    + "              {_testsDoneCount}/{TESTS_LIST.length} passés{_testsRemainMin > 0 ? \" · ~\" + _testsRemainMin + \" min restantes\" : \" · tout est fait\"}\n"
    + "            </span>\n"
    + "          </div>\n"
)

# 4 · grouped grid replaces the flat grid
GRID_OLD = (
    '      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14 }}>\n'
    "        {TESTS_LIST.map((t) => <TestStatusCard key={t.id} t={t} role={role} suggested={t.id === suggestedId} />)}\n"
    "      </div>\n"
)
GRID_NEW = (
    "      {PROXXIE_TEST_CATS.map((cat) => {\n"
    "        const _catTests = cat.ids.map((id) => TESTS_LIST.find((t) => t.id === id)).filter(Boolean);\n"
    "        if (!_catTests.length) return null;\n"
    "        const _catMin = _catTests.reduce((a, t) => a + _proxxieTestMin(t.id), 0);\n"
    "        return (\n"
    '          <div key={cat.id} style={{ marginBottom: 24 }}>\n'
    '            <div style={{ display: "flex", alignItems: "baseline", gap: 10, marginBottom: 12 }}>\n'
    '              <h3 style={{ fontFamily: "var(--font-display)", fontSize: 17, fontWeight: 600, letterSpacing: "-0.01em", margin: 0 }}>{cat.label}</h3>\n'
    '              <span style={{ fontSize: 12, color: "var(--c-muted)", fontFamily: "var(--font-num)" }}>{_catTests.length} tests · ~{_catMin} min</span>\n'
    "            </div>\n"
    '            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14 }}>\n'
    "              {_catTests.map((t) => <TestStatusCard key={t.id} t={t} role={role} suggested={t.id === suggestedId} />)}\n"
    "            </div>\n"
    "          </div>\n"
    "        );\n"
    "      })}\n"
)


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

    # meta (strip-and-readd, readd re-attaches PANEL_ANCHOR)
    src = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n\n", "", src, flags=re.DOTALL)
    if PANEL_ANCHOR not in src:
        return "SKIP no TestsPanel anchor"
    src = src.replace(PANEL_ANCHOR, META, 1)
    changes.append("meta")

    # duration
    if "_proxxieTestMin(t.id)} min" in src:
        changes.append("dur(already)")
    elif DUR_OLD in src:
        src = src.replace(DUR_OLD, DUR_NEW, 1); changes.append("dur")
    else:
        return "SKIP duration anchor not found"

    # progress computations
    if "_testsRemainMin" in src:
        changes.append("prog(already)")
    elif PROG_OLD in src:
        src = src.replace(PROG_OLD, PROG_NEW, 1); changes.append("prog")
    else:
        return "SKIP suggested anchor not found"

    # progress bar
    if "min restantes" in src:
        changes.append("bar(already)")
    elif BAR_OLD in src:
        src = src.replace(BAR_OLD, BAR_NEW, 1); changes.append("bar")
    else:
        return "SKIP sub paragraph anchor not found"

    # grouped grid
    if "PROXXIE_TEST_CATS.map" in src:
        changes.append("grid(already)")
    elif GRID_OLD in src:
        src = src.replace(GRID_OLD, GRID_NEW, 1); changes.append("grid")
    else:
        return "SKIP flat grid anchor not found"

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

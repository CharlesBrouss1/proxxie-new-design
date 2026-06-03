#!/usr/bin/env python3
"""Insert a proof-led OCEAN-X 'va plus loin' card on the Results screen of the
6 orientation/personality test pages (MBTI, RIASEC, PCM, Drivers, Valeurs,
Besoins), right before the existing gradient closing CTA. Clinical/screening
tests and the OCEAN-X test itself are intentionally left untouched.

Each patched 'Proxxie Test X.html' is then mirrored to its byte-identical
slug duplicate (test-x.html) so the two stay in sync.

Edits only asset 61feca88 inside each file's bundler manifest. Sanity-checks
markers before writing so a bad edit can't ship.
"""
import re, json, base64, gzip, pathlib, shutil

REPO = pathlib.Path(__file__).parent
MAIN = "61feca88-84c8-4b75-a93b-7138c831ebd9"
GRAD = 'background: "radial-gradient(circle at 20% 0%, #487AFF 0%, #1320CE 60%, #0A0E2C 100%)"'
ANCHOR = '\n\n        <div style={{\n          ' + GRAD
TRACK = 'data-track="oceanx_results_crosssell"'

# proper file name (without extension stem) -> (slug file, displayed label)
TESTS = {
    "Proxxie Test MBTI.html":    ("test-mbti.html",    "le MBTI"),
    "Proxxie Test RIASEC.html":  ("test-riasec.html",  "le RIASEC"),
    "Proxxie Test PCM.html":     ("test-pcm.html",     "la Process Com (PCM)"),
    "Proxxie Test Drivers.html": ("test-drivers.html", "les Drivers"),
    "Proxxie Test Valeurs.html": ("test-valeurs.html", "le test des Valeurs"),
    "Proxxie Test Besoins.html": ("test-besoins.html", "le test des Besoins"),
}

def card(label):
    label_cap = label[0].upper() + label[1:]
    return (
'        <div ' + TRACK + ' style={{ background: "var(--c-cream, #FBF7F0)", border: "1px solid var(--c-line)", borderRadius: 28, padding: "40px 36px", marginBottom: 30, position: "relative", overflow: "hidden" }}>\n'
'          <span className="chip" style={{ background: "rgba(19,32,206,.08)", color: "#1320CE" }}>Le test signature Proxxie</span>\n'
'          <h2 style={{ marginTop: 16, fontSize: 30, letterSpacing: "-0.03em", fontFamily: "var(--font-display)", lineHeight: 1.1 }}>\n'
'            Tu viens de tester ' + label + '. <span style={{ background: "linear-gradient(180deg, transparent 60%, #F5EB3F 60%)", paddingInline: 8 }}>OCEAN-X va plus loin.</span>\n'
'          </h2>\n'
'          <p style={{ fontSize: 16, color: "var(--c-ink-2)", marginTop: 14, maxWidth: 640, lineHeight: 1.6 }}>\n'
'            ' + label_cap + ' est un excellent point de départ, et il reste gratuit. Notre test propriétaire <strong>OCEAN-X</strong> réunit personnalité, valeurs, motivations et style d\'apprentissage en un seul profil, accompagné par un humain, pour t\'aider à te projeter sereinement vers l\'avenir.\n'
'          </p>\n'
'          <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 10, margin: "20px 0 24px" }}>\n'
'            <span style={{ fontSize: 13, fontWeight: 600, color: "var(--c-muted)" }}>Ancré dans le Big Five</span>\n'
'            <span style={{ color: "var(--c-line)" }}>·</span>\n'
'            <span style={{ fontSize: 13, fontWeight: 600, color: "var(--c-muted)" }}>30 ans de recherche</span>\n'
'            <span style={{ color: "var(--c-line)" }}>·</span>\n'
'            <span style={{ fontSize: 13, fontWeight: 600, color: "var(--c-muted)" }}>Accompagné par un coach</span>\n'
'          </div>\n'
'          <a href="Proxxie Test.html" className="btn btn-orange btn-lg btn-arrow">Commencer OCEAN-X gratuitement</a>\n'
'          <p style={{ fontSize: 13, color: "var(--c-muted)", marginTop: 12 }}>15 min · profil OCEAN-X complet · inscription gratuite</p>\n'
'        </div>'
    )

def decode(entry):
    data = base64.b64decode(entry["data"])
    if entry.get("compressed", False):
        data = gzip.decompress(data)
    return data.decode("utf-8")

def encode(entry, text):
    data = text.encode("utf-8")
    if entry.get("compressed", False):
        data = gzip.compress(data)
    entry["data"] = base64.b64encode(data).decode("ascii")

for proper, (slug, label) in TESTS.items():
    path = REPO / proper
    html = path.read_text(encoding="utf-8")
    m = re.search(r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)', html, re.DOTALL)
    if not m:
        raise SystemExit(f"{proper}: manifest not found")
    manifest = json.loads(m.group(2))
    if MAIN not in manifest:
        raise SystemExit(f"{proper}: asset {MAIN} missing")
    entry = manifest[MAIN]
    txt = decode(entry)

    if TRACK in txt:
        raise SystemExit(f"{proper}: card already present, aborting")
    if txt.count(ANCHOR) != 1:
        raise SystemExit(f"{proper}: anchor count {txt.count(ANCHOR)} != 1, aborting")

    new_txt = txt.replace(ANCHOR, "\n\n" + card(label) + ANCHOR, 1)

    # sanity markers
    for mk in (TRACK, GRAD, "Voir tous les tests", "Commencer OCEAN-X gratuitement"):
        if mk not in new_txt:
            raise SystemExit(f"{proper}: marker missing after edit: {mk!r}")
    if len(new_txt) <= len(txt):
        raise SystemExit(f"{proper}: text did not grow, aborting")

    encode(entry, new_txt)
    new_manifest = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest + html[m.end(2):]
    path.write_text(new_html, encoding="utf-8")

    # mirror to slug duplicate (was byte-identical before edit)
    shutil.copyfile(path, REPO / slug)
    print(f"OK {proper}: +{len(new_txt)-len(txt)} chars  -> mirrored to {slug}")

print("done")

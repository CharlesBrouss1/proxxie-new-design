#!/usr/bin/env python3
"""Mobile responsive · inject a global mobile stylesheet into bundle templates.

The React-bundled pages (Dashboard, Documents, Rapport, Coach, Tests, Test,
and the per-test pages) render their layout from inline-styled grids inside the
asset JS. Those grids have no mobile breakpoint, so on a 375px viewport their
2-column tracks (e.g. `grid-template-columns: 1fr 1fr`) sum well past the
viewport and force horizontal scroll (measured: Dashboard 587px, Tests 1084px,
Rapport 511px, etc.).

Class-based CSS lives in the asset and is hard to reach, but every bundle's
HTML shell (the `<script type="__bundler/template">` JSON string) has a real
`<head>`. We inject one `<style id='proxxie-mobile'>` block there. It:

  * collapses any inline `grid-template-columns` to a single shrinkable column
    (`minmax(0, 1fr)`) at <=640px, which is the correct mobile reflow,
  * sets `min-width: 0` on those grid items so flex/grid children can shrink
    instead of forcing the track wider than the viewport,
  * adds `body { overflow-x: hidden }` as a belt-and-suspenders guard.

Single quotes are used in the CSS so no double-quote escaping is needed inside
the JSON string; only `</style>` is escaped to `<\\/style>`. We do a string-level
insert before the escaped `<\\/head>` rather than round-tripping the whole
template through json, to keep the diff minimal and avoid re-encoding surprises.

Idempotent · re-applying is a no-op (skips if `proxxie-mobile` already present).
"""
import pathlib, re

REPO = pathlib.Path(__file__).parent

# All candidate bundle files (both naming conventions). Non-bundle files
# (no template script) are skipped automatically.
FILES = [
    "Proxxie Dashboard.html", "dashboard.html",
    "Proxxie Documents.html", "documents.html",
    "Proxxie Rapport.html",   "rapport.html",
    "Proxxie Coach.html",     "coach.html",
    "Proxxie Tests.html",     "tests.html",
    "Proxxie Test.html",      "test.html",
    "Proxxie Test Anxiete.html", "test-anxiete.html",
    "Proxxie Test Autisme.html", "test-autisme.html",
    "Proxxie Test Besoins.html", "test-besoins.html",
    "Proxxie Test DYS.html",     "test-dys.html",
    "Proxxie Test Drivers.html", "test-drivers.html",
    "Proxxie Test HPI.html",     "test-hpi.html",
    "Proxxie Test MBTI.html",    "test-mbti.html",
    "Proxxie Test PCM.html",     "test-pcm.html",
    "Proxxie Test RIASEC.html",  "test-riasec.html",
    "Proxxie Test TDAH.html",    "test-tdah.html",
    "Proxxie Test Valeurs.html", "test-valeurs.html",
    "Proxxie Ressources.html",   "ressources.html",
]

# CSS body (single quotes, no unescaped double quotes). The `</style>` close is
# templated so we can match each bundle's escaping convention: some bundlers
# escape every `</` as `<\/` inside the JSON template, others leave `</head>`
# and `</style>` literal (only `</script>` must be escaped to survive HTML
# parsing of the outer <script type=template>).
def _css(style_close: str) -> str:
    return (
        "<style id='proxxie-mobile'>"
        "@media (max-width:640px){"
        # collapse any inline 2+ column grid to one shrinkable column
        "[style*='grid-template-columns']{grid-template-columns:minmax(0,1fr) !important}"
        "[style*='grid-template-columns']>*{min-width:0 !important}"
        # let inline flex rows wrap instead of forcing the viewport wider
        "[style*='display: flex']{flex-wrap:wrap}"
        "[style*='display:flex']{flex-wrap:wrap}"
        # nowrap labels/numbers are the other overflow source; allow wrapping
        "[style*='white-space: nowrap']{white-space:normal !important;overflow-wrap:anywhere}"
        "[style*='white-space:nowrap']{white-space:normal !important;overflow-wrap:anywhere}"
        "body{overflow-x:hidden}"
        "}"
        + style_close
    )

# Matches a previously-injected block (either escaping convention) for
# strip-and-readd idempotency, so re-running updates the CSS in place.
_EXISTING_RE = re.compile(r"<style id='proxxie-mobile'>.*?<(?:\\/|/)style>", re.DOTALL)

# (head_close_token, matching_style_close) pairs, tried in order.
HEAD_VARIANTS = [
    ("<\\/head>", "<\\/style>"),  # fully-escaped templates (coach, tests, ...)
    ("</head>",   "</style>"),    # literal-close templates (dashboard, ...)
]


def patch_one(target: pathlib.Path) -> str:
    if not target.exists():
        return "SKIP missing"
    html = target.read_text(encoding="utf-8")
    marker = '<script type="__bundler/template">'
    start = html.find(marker)
    if start == -1:
        return "SKIP no template"
    body_start = start + len(marker)
    end = html.find("</script>", body_start)
    if end == -1:
        return "SKIP malformed template"
    template = html[body_start:end]
    # strip any previously-injected block so we re-add the current CSS
    had_existing = bool(_EXISTING_RE.search(template))
    template = _EXISTING_RE.sub("", template)
    for head_close, style_close in HEAD_VARIANTS:
        if head_close in template:
            new_template = template.replace(head_close, _css(style_close) + head_close, 1)
            new_html = html[:body_start] + new_template + html[end:]
            target.write_text(new_html, encoding="utf-8")
            return f"re-patched ({head_close})" if had_existing else f"patched ({head_close})"
    return "SKIP no </head> in template"


if __name__ == "__main__":
    for fn in FILES:
        print(f"  {fn}: {patch_one(REPO / fn)}")

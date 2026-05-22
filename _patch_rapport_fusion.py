#!/usr/bin/env python3
"""PR2 · Fusion Rapport + Documents (light).

The "Rapport" tab was removed from nav in Phase 2, but its content was
left orphaned on Proxxie Rapport.html. This patch consolidates by·

  1. Adding a "Rapport" summary card at the TOP of Proxxie Documents.html
     (above the existing upload UI). The card shows · status (version,
     dernière MAJ), 3 quick stats (Big Five passé, tests passés, docs
     uploadés), and CTAs · "Voir le rapport complet →" (links to
     Proxxie Rapport.html which still hosts the full report) + "Exporter
     en PDF".

  2. Adding a "Retour aux documents" breadcrumb banner at the top of
     Proxxie Rapport.html, so users who land there from a bookmark are
     guided back into the new consolidated entry point.

Implementation · runtime DOM injection via a <script> in the template.
The card is inserted as a sibling of #root (NOT inside it), so React's
reconciliation in the Documents app doesn't wipe it.

Idempotent · MARKER strip + readd.
"""
import re, json, pathlib

REPO = pathlib.Path(__file__).parent
MARKER = "/* __proxxie_rapport_fusion_v1__ */"


DOCUMENTS_TARGETS = ["Proxxie Documents.html", "documents.html"]
RAPPORT_TARGETS = ["Proxxie Rapport.html", "rapport.html"]


DOCUMENTS_INJECTION = r"""<script>
/* __proxxie_rapport_fusion_v1__ */
(function () {
  function role() {
    try {
      var u = new URLSearchParams(location.search).get("role");
      if (u === "parent" || u === "enfant") return u;
      var s = localStorage.getItem("proxxie.role");
      if (s === "parent" || s === "enfant") return s;
    } catch (e) {}
    return "parent";
  }
  function inject() {
    if (document.querySelector("[data-proxxie-rapport-card]")) return true;
    var root = document.getElementById("root");
    if (!root) return false;
    var r = role();
    var isEnfant = r === "enfant";

    /* Compute stats from localStorage */
    var bigFiveDone = false, testsCount = 0, docsCount = 0;
    try {
      var roleKey = "proxxie.tests.big5." + r;
      bigFiveDone = localStorage.getItem(roleKey) === "done" || localStorage.getItem("proxxie.tests.big5") === "done";
      var testIds = ["riasec","mbti","pcm","hpi","tdah","dys","autisme","anxiete","besoins","drivers","valeurs"];
      for (var i = 0; i < testIds.length; i++) {
        if (localStorage.getItem("proxxie.tests." + testIds[i] + "." + r) === "done" || localStorage.getItem("proxxie.tests." + testIds[i]) === "done") testsCount++;
      }
      for (var k = 0; k < localStorage.length; k++) {
        var key = localStorage.key(k);
        if (key && key.indexOf("proxxie.docs.") === 0 && localStorage.getItem(key) === "1") docsCount++;
      }
    } catch (e) {}

    var hasData = bigFiveDone || testsCount > 0 || docsCount > 0;
    var version = hasData ? "v" + Math.max(1, Math.min(9, testsCount + (docsCount > 0 ? 1 : 0) + (bigFiveDone ? 1 : 0))) : "—";

    var section = document.createElement("section");
    section.setAttribute("data-proxxie-rapport-card", "1");
    section.style.cssText = "padding: 30px 0 0;";
    section.innerHTML =
      '<div class="shell">' +
        '<div style="background: linear-gradient(135deg, rgba(19,32,206,.04) 0%, rgba(72,122,255,.06) 100%); border: 1px solid rgba(72,122,255,.18); border-radius: 24px; padding: 28px 32px;">' +
          '<div style="display: grid; grid-template-columns: 1fr auto; gap: 24px; align-items: flex-start; flex-wrap: wrap;">' +
            '<div style="min-width: 280px;">' +
              '<span class="eyebrow"><span class="dot"></span>Rapport d\'orientation</span>' +
              '<h2 style="font-family: var(--font-display); font-size: 28px; font-weight: 600; letter-spacing: -0.02em; margin: 10px 0 8px;">' +
                (isEnfant ? "Ton rapport en un coup d\'œil" : "Le rapport en un coup d\'œil") + '</h2>' +
              '<p style="color: var(--c-muted); font-size: 14px; margin: 0 0 18px;">' +
                (isEnfant
                  ? "Le rapport se met à jour automatiquement quand tu passes un test ou uploadis un document. Voici l\'état actuel."
                  : "Le rapport se met à jour automatiquement quand votre ado passe un test ou que vous uploadez un document. Voici l\'état actuel.") + '</p>' +
              '<div style="display: flex; gap: 22px; flex-wrap: wrap; font-size: 13px;">' +
                '<div><div style="font-family: var(--font-num); font-size: 22px; font-weight: 700; color: ' + (bigFiveDone ? "#22A06B" : "rgba(10,14,44,.35)") + ';">' + (bigFiveDone ? "✓" : "—") + '</div><div style="color: var(--c-muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 600; margin-top: 2px;">Big Five</div></div>' +
                '<div><div style="font-family: var(--font-num); font-size: 22px; font-weight: 700; color: #1320CE;">' + testsCount + '</div><div style="color: var(--c-muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 600; margin-top: 2px;">Tests passés</div></div>' +
                '<div><div style="font-family: var(--font-num); font-size: 22px; font-weight: 700; color: #FD6936;">' + docsCount + '</div><div style="color: var(--c-muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 600; margin-top: 2px;">Documents</div></div>' +
                '<div><div style="font-family: var(--font-num); font-size: 22px; font-weight: 700; color: #0A0E2C;">' + version + '</div><div style="color: var(--c-muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 600; margin-top: 2px;">Version</div></div>' +
              '</div>' +
            '</div>' +
            '<div style="display: flex; flex-direction: column; gap: 10px; align-items: stretch; min-width: 220px;">' +
              '<a href="Proxxie Rapport.html" class="btn btn-orange" style="text-decoration: none; padding: 13px 20px; font-size: 14px; border-radius: 12px; text-align: center;">' +
                (hasData ? "Voir le rapport complet →" : "Découvrir le rapport →") + '</a>' +
              '<button onclick="window.print()" style="background: white; border: 1px solid rgba(10,14,44,.12); color: var(--c-ink); padding: 11px 20px; font-size: 13px; border-radius: 12px; font-weight: 600; cursor: pointer; font-family: inherit;">📄 Exporter en PDF</button>' +
            '</div>' +
          '</div>' +
        '</div>' +
      '</div>';

    root.parentNode.insertBefore(section, root);
    return true;
  }
  function init() {
    if (inject()) return;
    var tries = 0;
    var iv = setInterval(function () {
      tries++;
      if (inject() || tries > 60) clearInterval(iv);
    }, 250);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
</script>"""


RAPPORT_INJECTION = r"""<script>
/* __proxxie_rapport_fusion_v1__ */
(function () {
  function inject() {
    if (document.querySelector("[data-proxxie-rapport-back]")) return true;
    var root = document.getElementById("root");
    if (!root) return false;
    var banner = document.createElement("section");
    banner.setAttribute("data-proxxie-rapport-back", "1");
    banner.style.cssText = "background: rgba(72,122,255,.06); border-bottom: 1px solid rgba(72,122,255,.18); padding: 12px 0;";
    banner.innerHTML =
      '<div class="shell" style="display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap;">' +
        '<div style="display: flex; align-items: center; gap: 10px; font-size: 13px; color: rgba(10,14,44,.7);">' +
          '<span style="display: inline-flex; align-items: center; gap: 6px;">' +
            '<span style="width: 6px; height: 6px; border-radius: 50%; background: #487AFF;"></span>' +
            '<span style="font-weight: 600; color: #1320CE; text-transform: uppercase; letter-spacing: 0.06em; font-size: 11px;">Nouveau</span>' +
          '</span>' +
          '<span>Le rapport est désormais accessible directement depuis l\'onglet <strong>Documents</strong>.</span>' +
        '</div>' +
        '<a href="Proxxie Documents.html" style="font-size: 13px; font-weight: 600; color: #1320CE; text-decoration: none; padding: 8px 14px; border-radius: 999px; border: 1px solid rgba(72,122,255,.25); background: white;">← Aller dans Documents</a>' +
      '</div>';
    root.parentNode.insertBefore(banner, root);
    return true;
  }
  function init() {
    if (inject()) return;
    var tries = 0;
    var iv = setInterval(function () {
      tries++;
      if (inject() || tries > 60) clearInterval(iv);
    }, 250);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
</script>"""


def encode_template(tpl_str):
    raw = json.dumps(tpl_str, ensure_ascii=False)
    return raw.replace("</script>", r"<\/script>")


def extract_template(html):
    start_m = re.search(r'<script[^>]*type="__bundler/template"[^>]*>', html)
    if not start_m: return None
    last_close = html.rfind("</script>")
    if last_close <= start_m.end(): return None
    raw = html[start_m.end():last_close]
    return start_m.end(), last_close, json.loads(raw.strip())


def strip_marker(tpl):
    pattern = re.compile(r'<script>\s*' + re.escape(MARKER) + r'.*?</script>\s*', flags=re.S)
    return pattern.sub("", tpl)


def patch_one(target, injection):
    if not target.exists(): return "SKIP missing"
    html = target.read_text(encoding="utf-8")
    ext = extract_template(html)
    if ext is None: return "SKIP no template"
    s, e, tpl = ext
    was_patched = MARKER in tpl
    if was_patched:
        tpl = strip_marker(tpl)
    if "</body>" not in tpl:
        return "SKIP no </body>"
    new_tpl = tpl.replace("</body>", injection + "\n</body>", 1)
    new_raw = encode_template(new_tpl)
    new_html = html[:s] + new_raw + html[e:]
    target.write_text(new_html, encoding="utf-8")
    return f"{'re-patched' if was_patched else 'patched'} ({len(new_tpl)} chars tpl)"


if __name__ == "__main__":
    print("== Documents · rapport summary card ==")
    for fn in DOCUMENTS_TARGETS:
        print(f"  {fn}: {patch_one(REPO / fn, DOCUMENTS_INJECTION)}")
    print("\n== Rapport · back-to-documents banner ==")
    for fn in RAPPORT_TARGETS:
        print(f"  {fn}: {patch_one(REPO / fn, RAPPORT_INJECTION)}")

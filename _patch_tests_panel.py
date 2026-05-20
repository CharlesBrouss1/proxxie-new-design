#!/usr/bin/env python3
"""Inject a TestsPanel React component into the dashboard.

Why JSX modification rather than runtime DOM injection:
  React reconciles its virtual DOM against the live DOM on every render. Any
  node we splice in from outside React is treated as foreign and removed on
  the next update (e.g. opening the beta intro modal). So we modify the JSX
  in the dashboard's manifest asset directly.

What this patches:
  - Manifest asset 5a278f70-* in (Proxxie) Dashboard.html: prepend a
    TestsPanel component definition before `const Dashboard = () =>` and
    insert `<TestsPanel />` after `<DashGrid ... />`.

Idempotent: skipped if marker is already present.
"""
import re, json, base64, gzip, pathlib, sys

REPO = pathlib.Path(__file__).parent
TARGETS = ["dashboard.html", "Proxxie Dashboard.html"]
DASHBOARD_ASSET = "5a278f70-3fa5-4bc0-bdb2-349143947f86"
MARKER = "/* __proxxie_tests_panel_jsx_v1__ */"

TESTS_PANEL_JSX = r"""
/* __proxxie_tests_panel_jsx_v1__ */
const TESTS_LIST = [
  { id: "riasec",  title: "RIASEC",   desc: "Profil d'orientation. 6 dimensions : Réaliste, Investigateur, Artistique, Social, Entreprenant, Conventionnel.", href: "Proxxie Test RIASEC.html",   def: "wip"  },
  { id: "mbti",    title: "MBTI",     desc: "Type de personnalité en 4 axes (E/I, S/N, T/F, J/P).",        href: "Proxxie Test MBTI.html",     def: "todo" },
  { id: "pcm",     title: "PCM",      desc: "Process Communication. 6 types et stratégies sous stress.",   href: "Proxxie Test PCM.html",      def: "todo" },
  { id: "hpi",     title: "HPI",      desc: "Indicateurs de haut potentiel intellectuel.",                 href: "Proxxie Test HPI.html",      def: "done" },
  { id: "tdah",    title: "TDAH",     desc: "Attention, hyperactivité, impulsivité (ASRS-v1.1).",          href: "Proxxie Test TDAH.html",     def: "todo" },
  { id: "dys",     title: "DYS",      desc: "Dyslexie, dyspraxie, dyscalculie, dysgraphie.",               href: "Proxxie Test DYS.html",      def: "todo" },
  { id: "autisme", title: "Autisme",  desc: "Indicateurs du spectre autistique (AQ-10).",                  href: "Proxxie Test Autisme.html",  def: "todo" },
  { id: "anxiete", title: "Anxiété",  desc: "Niveau et formes d'anxiété (GAD-7 + STAI).",                  href: "Proxxie Test Anxiete.html",  def: "todo" },
  { id: "besoins", title: "Besoins",  desc: "Besoins fondamentaux : autonomie, compétence, relation.",     href: "Proxxie Test Besoins.html",  def: "todo" },
  { id: "drivers", title: "Drivers",  desc: "Drivers internes (analyse transactionnelle).",                href: "Proxxie Test Drivers.html",  def: "todo" },
  { id: "valeurs", title: "Valeurs",  desc: "Valeurs personnelles et professionnelles (Schwartz).",        href: "Proxxie Test Valeurs.html",  def: "wip"  }
];

const TESTS_STATUS_MAP = {
  done: { label: "Passé",    bg: "rgba(34,160,107,.10)",  color: "#22A06B" },
  wip:  { label: "En cours", bg: "rgba(253,105,54,.10)",  color: "#FD6936" },
  todo: { label: "À passer", bg: "rgba(72,122,255,.08)",  color: "#487AFF" }
};

const useProxxieRole = () => {
  return React.useMemo(() => {
    try {
      const u = new URLSearchParams(window.location.search).get("role");
      if (u === "parent" || u === "enfant") return u;
      const s = localStorage.getItem("proxxie.role");
      if (s === "parent" || s === "enfant") return s;
    } catch (e) {}
    return "parent";
  }, []);
};

const TestStatusCard = ({ t, role, suggested }) => {
  const status = (() => {
    try { return localStorage.getItem("proxxie.tests." + t.id) || t.def; } catch (e) { return t.def; }
  })();
  const sb = TESTS_STATUS_MAP[status] || TESTS_STATUS_MAP.todo;
  const cta = status === "done" ? "Voir les résultats"
           : status === "wip"  ? "Reprendre"
           : (role === "enfant" ? "Commencer" : "Lancer le test");
  const ctaColor = status === "done" ? "#22A06B" : "#1320CE";
  const baseBorder = suggested ? "1.5px solid #F5EB3F" : "1px solid rgba(10,14,44,0.08)";
  const baseShadow = suggested ? "0 6px 22px rgba(245,235,63,.30)" : "none";
  return (
    <a
      href={t.href}
      data-test-id={t.id}
      style={{
        display: "flex", flexDirection: "column", gap: 10, padding: 18,
        background: suggested ? "linear-gradient(180deg, #FFFCEC 0%, #ffffff 60%)" : "#fff",
        border: baseBorder, borderRadius: 16,
        textDecoration: "none", color: "inherit",
        boxShadow: baseShadow,
        position: "relative",
        transition: "transform .15s ease, box-shadow .15s ease, border-color .15s ease",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = "translateY(-2px)";
        if (!suggested) e.currentTarget.style.borderColor = "#487AFF";
        e.currentTarget.style.boxShadow = suggested ? "0 8px 28px rgba(245,235,63,.40)" : "0 4px 14px rgba(19,32,206,.06)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = "translateY(0)";
        if (!suggested) e.currentTarget.style.borderColor = "rgba(10,14,44,0.08)";
        e.currentTarget.style.boxShadow = baseShadow;
      }}
    >
      {suggested && (
        <span style={{
          position: "absolute", top: -10, left: 14,
          padding: "3px 10px", borderRadius: 999,
          background: "#F5EB3F", color: "#0A0E2C",
          fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase",
          boxShadow: "0 2px 6px rgba(245,235,63,.4)",
        }}>★ Suggéré pour la suite</span>
      )}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "#487AFF" }}>{t.title}</span>
        <span style={{ fontSize: 11, fontWeight: 600, padding: "3px 9px", borderRadius: 999, background: sb.bg, color: sb.color }}>{sb.label}</span>
      </div>
      <div style={{ fontSize: 15, fontWeight: 600, lineHeight: 1.3, color: "#0A0E2C" }}>{t.title}</div>
      <div style={{ fontSize: 12, color: "rgba(10,14,44,.55)", flex: 1, lineHeight: 1.45 }}>{t.desc}</div>
      <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, fontWeight: 600, color: suggested ? "#FD6936" : ctaColor, marginTop: 4 }}>
        {cta} →
      </div>
    </a>
  );
};

const TestsPanel = () => {
  const role = useProxxieRole();
  const isEnfant = role === "enfant";
  /* Pick the first non-done test as "suggested next". 'wip' wins over 'todo'. */
  const getStatus = (t) => {
    try { return localStorage.getItem("proxxie.tests." + t.id) || t.def; } catch (e) { return t.def; }
  };
  let suggestedId = null;
  for (const t of TESTS_LIST) { if (getStatus(t) === "wip") { suggestedId = t.id; break; } }
  if (!suggestedId) for (const t of TESTS_LIST) { if (getStatus(t) === "todo") { suggestedId = t.id; break; } }
  const suggested = TESTS_LIST.find((t) => t.id === suggestedId);

  const h2 = isEnfant ? "Continue à creuser ton profil" : "Continuez à creuser le profil de votre ado";
  const sub = isEnfant
    ? (suggested
        ? "Ton prochain test suggéré · " + suggested.title + ". 11 tests scientifiques au total, en complément du Big Five. Plus tu en passes, plus ton rapport devient précis."
        : "Tu as passé tous les tests, bravo. Tu peux revenir compléter d'autres pistes.")
    : (suggested
        ? "Prochain test suggéré pour votre ado · " + suggested.title + ". 11 tests scientifiques au total, en complément du Big Five. Plus il/elle en passe, plus le rapport devient précis."
        : "Votre ado a passé tous les tests. Vous pouvez les passer aussi pour comparer.");
  return (
    <section style={{ margin: "0 auto 32px", padding: "0 24px", maxWidth: 1280 }}>
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: 24, marginBottom: 22, flexWrap: "wrap" }}>
        <div style={{ maxWidth: 680 }}>
          <span className="eyebrow"><span className="dot"></span>Aller plus loin · tests psychométriques</span>
          <h2 style={{ fontFamily: "var(--font-display)", fontSize: 28, fontWeight: 600, letterSpacing: "-0.02em", marginTop: 10, marginBottom: 6, color: "#0A0E2C" }}>
            {h2}
          </h2>
          <p style={{ color: "rgba(10,14,44,.55)", fontSize: 14, margin: 0, lineHeight: 1.5 }}>
            {sub}
          </p>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          {suggested && (
            <a href={suggested.href} className="btn btn-orange" style={{ padding: "12px 18px", fontSize: 14, borderRadius: 12, whiteSpace: "nowrap", textDecoration: "none" }}>
              {isEnfant ? "Passer " : "Lancer "}{suggested.title} →
            </a>
          )}
          <a href="Proxxie Tests.html" style={{ fontSize: 13, fontWeight: 600, color: "#1320CE", textDecoration: "none", padding: "12px 14px", borderRadius: 10, border: "1px solid rgba(10,14,44,0.12)", background: "#fff", whiteSpace: "nowrap" }}>
            Voir tous
          </a>
        </div>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14 }}>
        {TESTS_LIST.map((t) => <TestStatusCard key={t.id} t={t} role={role} suggested={t.id === suggestedId} />)}
      </div>
    </section>
  );
};
"""

# Where in the Dashboard JSX to insert <TestsPanel />: right after <DashGrid ... />
JSX_ANCHOR = '<DashGrid onOpen={openDrawer} audit={t.audit} />'
JSX_INSERTION = JSX_ANCHOR + '\n      <TestsPanel />'


def encode_template(tpl_str: str) -> str:
    raw = json.dumps(tpl_str, ensure_ascii=False)
    return raw.replace("</script>", r"<\/script>")


def extract_template(html: str):
    start_m = re.search(r'<script[^>]*type="__bundler/template"[^>]*>', html)
    if not start_m: return None
    last_close = html.rfind("</script>")
    if last_close <= start_m.end(): return None
    raw = html[start_m.end():last_close]
    return start_m.end(), last_close, json.loads(raw.strip())


# Match the tests_panel block but STOP at either the next /* __proxxie_*
# marker (if dashboard_v2 was layered on top) or 'const Dashboard'.
STRIP_BLOCK_RE = re.compile(
    r'\n/\* __proxxie_tests_panel_jsx_v1__ \*/.*?(?=\n(?:/\* __proxxie_|const Dashboard = \(\) =>))',
    flags=re.S,
)


def strip_v1(src: str) -> str:
    """Reverse the JSX patch so we can re-apply with updated code."""
    src = STRIP_BLOCK_RE.sub("", src)
    src = src.replace(JSX_INSERTION, JSX_ANCHOR, 1)
    return src


def patch_manifest_asset(html: str, uuid: str) -> tuple:
    """Returns (new_html, status_str). Modifies the named manifest asset by
    inserting the TestsPanel JSX. The manifest JSON section is rewritten in
    place. Re-runnable· strips a previous patch before re-applying."""
    m = re.search(r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)', html, re.DOTALL)
    if not m:
        return html, "no manifest"
    manifest = json.loads(m.group(2))
    if uuid not in manifest:
        return html, f"asset {uuid[:8]} not found"
    entry = manifest[uuid]
    data = base64.b64decode(entry["data"])
    compressed = entry.get("compressed", False)
    if compressed:
        data = gzip.decompress(data)
    src = data.decode("utf-8")

    was_patched = MARKER in src
    if was_patched:
        src = strip_v1(src)

    if "const Dashboard = () =>" not in src:
        return html, "Dashboard component not found in asset"
    if JSX_ANCHOR not in src:
        return html, "DashGrid JSX anchor not found"

    new_src = src.replace("const Dashboard = () =>", TESTS_PANEL_JSX + "\nconst Dashboard = () =>", 1)
    new_src = new_src.replace(JSX_ANCHOR, JSX_INSERTION, 1)

    new_data = new_src.encode("utf-8")
    if compressed:
        new_data = gzip.compress(new_data)
    entry["data"] = base64.b64encode(new_data).decode("ascii")

    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]
    verb = "re-patched" if was_patched else "patched"
    return new_html, f"asset {verb} ({len(new_src)} chars)"


# Cleanup: remove any prior <script>__proxxie_tests_panel_v1__</script> blocks
# that earlier runtime-injection attempts may have left in the template.
OLD_RUNTIME_RE = re.compile(
    r'<script>\s*/\*\s*__proxxie_tests_panel_v1__\s*\*/.*?</script>\s*',
    flags=re.S,
)


def strip_old_runtime(html: str) -> tuple:
    ext = extract_template(html)
    if ext is None:
        return html, False
    s, e, tpl = ext
    stripped, n = OLD_RUNTIME_RE.subn("", tpl)
    if n == 0:
        return html, False
    new_raw = encode_template(stripped)
    return html[:s] + new_raw + html[e:], True


def patch_one(target: pathlib.Path) -> str:
    if not target.exists():
        return "SKIP missing"
    html = target.read_text(encoding="utf-8")

    html, stripped = strip_old_runtime(html)

    html, status = patch_manifest_asset(html, DASHBOARD_ASSET)
    target.write_text(html, encoding="utf-8")
    prefix = "stripped old runtime + " if stripped else ""
    return prefix + status


if __name__ == "__main__":
    for fn in TARGETS:
        p = REPO / fn
        print(f"{fn}: {patch_one(p)}")

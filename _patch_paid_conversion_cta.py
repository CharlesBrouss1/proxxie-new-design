#!/usr/bin/env python3
"""Add a PaidConversionCTA card to the dashboard.

The parent-first journey culminates in booking a paid coaching session
with Charles. Until now, the only CTA pointing at this is the
"Calendly · entretien découverte" link buried in some headers. This
adds an explicit card on the dashboard that frames the paid
accompagnement as the destination.

Placement · after TestsPanel + DocsCompletenessPanel + InvitationCTA, so
the CTA appears late in the page but is clearly the next step once the
user has invested in the platform (passed tests, uploaded docs).

The card adapts to role and progress·
  - For ado · "Découvre Charles · échange gratuit, sans engagement"
    (gentler · ado is not the buyer)
  - For parent (low progress) · "Démarrer l'accompagnement Charles"
    explicit (the buyer · the parent)
  - For parent (high progress · 5+ tests done) · "Tu en sais maintenant
    assez pour démarrer · accompagnement à 290€/mois"

Idempotent · marker MARKER, strip + readd.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
TARGETS = ["dashboard.html", "Proxxie Dashboard.html"]
DASHBOARD_ASSET = "5a278f70-3fa5-4bc0-bdb2-349143947f86"
MARKER = "/* __proxxie_paid_conversion_cta_v1__ */"


COMPONENTS_JSX = r"""
/* __proxxie_paid_conversion_cta_v1__ */
const PaidConversionCTA = () => {
  const role = useProxxieRole();
  const isEnfant = role === "enfant";

  /* Compute progress signal · how many tests has the viewer passed? */
  const testsDone = React.useMemo(() => {
    let count = 0;
    try {
      const ids = ["big5","riasec","mbti","pcm","hpi","tdah","dys","autisme","anxiete","besoins","drivers","valeurs"];
      for (const id of ids) {
        const roleKey = "proxxie.tests." + id + "." + role;
        const legacy = "proxxie.tests." + id;
        if (localStorage.getItem(roleKey) === "done" || localStorage.getItem(legacy) === "done") count++;
      }
    } catch (e) {}
    return count;
  }, [role]);

  const isAdvanced = testsDone >= 5;

  const eyebrow = isEnfant ? "Étape suivante · rencontrer Charles" : "Étape suivante · accompagnement";
  const title = isEnfant
    ? (isAdvanced ? "Tu en sais assez pour rencontrer Charles" : "Découvre Charles, ton coach Proxxie")
    : (isAdvanced ? "Vous en savez assez pour démarrer l'accompagnement" : "Démarrer l'accompagnement avec Charles");
  const sub = isEnfant
    ? "Un échange de 30 min gratuit, sans engagement. Charles te connaît déjà via ton profil et tes tests. À toi de voir si le feeling passe."
    : (isAdvanced
        ? "Vous avez passé " + testsDone + " tests, le profil de votre ado est bien dessiné. L'accompagnement long format (3-6 mois) coûte 290€/mois avec annulation à 30 jours."
        : "Charles vous accompagne 3 à 6 mois sur l'orientation de votre ado · stratégie vœux, lettres de motivation, choix de spés. 290€/mois, premier RDV gratuit.");
  const ctaPrimary = isEnfant ? "Réserver mon échange gratuit →" : (isAdvanced ? "Réserver l'accompagnement →" : "RDV découverte gratuit →");
  const ctaSecondary = isEnfant ? null : (isAdvanced ? "Voir aussi RDV gratuit" : "Voir le détail tarifs");
  const calendlyUrl = isAdvanced && !isEnfant
    ? "https://calendly.com/proxxie/accompagnement"
    : "https://calendly.com/proxxie/entretien";

  return (
    <section style={{ margin: "0 auto 32px", padding: "0 24px", maxWidth: 1280 }}>
      <div style={{
        background: "linear-gradient(135deg, #0A0E2C 0%, #1320CE 100%)",
        color: "white",
        borderRadius: 24,
        padding: "32px 36px",
        position: "relative",
        overflow: "hidden",
      }}>
        <div style={{ position: "absolute", top: -60, right: -60, width: 240, height: 240, borderRadius: "50%", background: "rgba(253,105,54,.18)" }} />
        <div style={{ position: "absolute", bottom: -80, left: -80, width: 320, height: 320, borderRadius: "50%", background: "rgba(245,235,63,.10)" }} />

        <div style={{ position: "relative", zIndex: 1, display: "grid", gridTemplateColumns: "1fr auto", gap: 30, alignItems: "center", flexWrap: "wrap" }}>
          <div style={{ maxWidth: 640 }}>
            <span style={{ display: "inline-flex", alignItems: "center", gap: 8, padding: "5px 12px", borderRadius: 999, background: "rgba(245,235,63,.15)", color: "#F5EB3F", fontSize: 11, fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 14 }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#F5EB3F" }}></span>
              {eyebrow}
            </span>
            <h2 style={{ fontFamily: "var(--font-display)", fontSize: 28, fontWeight: 600, letterSpacing: "-0.02em", margin: "0 0 10px" }}>
              {title}
            </h2>
            <p style={{ fontSize: 15, color: "rgba(255,255,255,.78)", lineHeight: 1.5, margin: 0, maxWidth: 580 }}>
              {sub}
            </p>
            {!isEnfant && isAdvanced && (
              <div style={{ display: "flex", gap: 18, marginTop: 18, fontSize: 13, color: "rgba(255,255,255,.7)", flexWrap: "wrap" }}>
                <span>✓ {testsDone} tests passés</span>
                <span>✓ Profil consolidé prêt</span>
                <span>✓ Charles te connaît</span>
              </div>
            )}
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10, alignItems: "stretch", minWidth: 260 }}>
            <a href={calendlyUrl} target="_blank" rel="noopener noreferrer" className="btn btn-orange" style={{ padding: "14px 22px", fontSize: 14, borderRadius: 12, textDecoration: "none", textAlign: "center", whiteSpace: "nowrap" }}>
              {ctaPrimary}
            </a>
            {ctaSecondary && (
              <a href="https://calendly.com/proxxie/entretien" target="_blank" rel="noopener noreferrer" style={{ fontSize: 12, color: "rgba(255,255,255,.7)", textDecoration: "underline", textAlign: "center" }}>
                {ctaSecondary}
              </a>
            )}
          </div>
        </div>
      </div>
    </section>
  );
};
"""

RETURN_ANCHOR = '<InvitationCTA onOpen={() => setInviteOpen(true)} />'
RETURN_REPLACE = RETURN_ANCHOR + '\n      <PaidConversionCTA />'


STRIP_RE = re.compile(
    r'\n/\* __proxxie_paid_conversion_cta_v1__ \*/.*?(?=\n(?:/\* __proxxie_|const Dashboard = \(\) =>))',
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
        raise SystemExit("InvitationCTA anchor not found (run _patch_dashboard_v2.py first)")
    if "useProxxieRole" not in src:
        raise SystemExit("useProxxieRole not in scope (run earlier patches first)")
    src = src.replace("const Dashboard = () =>", COMPONENTS_JSX + "\nconst Dashboard = () =>", 1)
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
    return f"{'re-patched' if was_patched else 'patched'} (asset {len(new_src)} chars)"


if __name__ == "__main__":
    for fn in TARGETS:
        try:
            print(f"{fn}: {patch_one(REPO / fn)}")
        except SystemExit as e:
            print(f"{fn}: ERROR · {e}")

#!/usr/bin/env python3
"""Bonus PR · Newsletter subscription widget on the dashboard.

Closes one of the user's stated engagement loops · "s'abonner à des
newsletters". Adds a NewsletterCard component to the dashboard that·

  - Shows a soft yellow card after PaidConversionCTA
  - Email input + "S'inscrire" button
  - Mock signup · sets proxxie.newsletter.subscribed=email, shows
    "Inscrit ✓ · à vendredi pour le premier décryptage"
  - Skipped if already subscribed (replaced with thank-you state)

Idempotent · MARKER strip + readd.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
TARGETS = ["dashboard.html", "Proxxie Dashboard.html"]
DASHBOARD_ASSET = "5a278f70-3fa5-4bc0-bdb2-349143947f86"
MARKER = "/* __proxxie_newsletter_widget_v1__ */"


COMPONENT_JSX = r"""
/* __proxxie_newsletter_widget_v1__ */
const NewsletterCard = () => {
  const role = useProxxieRole();
  const isEnfant = role === "enfant";
  const [email, setEmail] = React.useState("");
  const [subscribed, setSubscribed] = React.useState(() => {
    try { return !!localStorage.getItem("proxxie.newsletter.subscribed"); } catch (e) { return false; }
  });
  const [error, setError] = React.useState("");

  const submit = (e) => {
    e.preventDefault();
    setError("");
    const trimmed = email.trim();
    if (!trimmed || trimmed.indexOf("@") < 0) {
      setError("Merci de saisir un email valide.");
      return;
    }
    try { localStorage.setItem("proxxie.newsletter.subscribed", trimmed); } catch (e) {}
    setSubscribed(true);
  };

  return (
    <section style={{ margin: "0 auto 32px", padding: "0 24px", maxWidth: 1280 }}>
      <div style={{
        background: "linear-gradient(135deg, rgba(245,235,63,.30) 0%, rgba(253,105,54,.10) 100%)",
        borderRadius: 20, padding: "26px 30px",
        display: "grid", gridTemplateColumns: "1fr auto", gap: 24, alignItems: "center", flexWrap: "wrap",
      }}>
        <div style={{ maxWidth: 580 }}>
          <span className="eyebrow"><span className="dot"></span>Newsletter Proxxie · hebdo</span>
          <h2 style={{ fontFamily: "var(--font-display)", fontSize: 24, fontWeight: 600, letterSpacing: "-0.02em", margin: "10px 0 6px", color: "#0A0E2C" }}>
            {isEnfant
              ? "Reçois nos décryptages chaque vendredi"
              : "Recevez nos décryptages orientation chaque vendredi"}
          </h2>
          <p style={{ color: "rgba(10,14,44,.65)", fontSize: 14, margin: 0, lineHeight: 1.5 }}>
            {isEnfant
              ? "Un email court le vendredi · une histoire d'orientation, un métier méconnu, et un conseil concret. Désinscription en 1 clic."
              : "Un email court le vendredi · les actus Parcoursup décodées, un métier porteur expliqué, et 1 conseil concret pour accompagner votre ado. Désinscription en 1 clic."}
          </p>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 8, minWidth: 280 }}>
          {subscribed ? (
            <div style={{ background: "rgba(34,160,107,.10)", border: "1px solid rgba(34,160,107,.25)", borderRadius: 12, padding: "14px 18px", display: "flex", alignItems: "center", gap: 12 }}>
              <div style={{ width: 28, height: 28, borderRadius: 8, background: "#22A06B", color: "white", display: "grid", placeItems: "center", fontWeight: 700, fontSize: 14, flexShrink: 0 }}>✓</div>
              <div style={{ fontSize: 13 }}>
                <div style={{ fontWeight: 600, color: "#0A0E2C", marginBottom: 2 }}>Inscrit{isEnfant ? "" : "(e)"} ✓</div>
                <div style={{ color: "var(--c-muted)" }}>À vendredi pour le premier décryptage.</div>
              </div>
            </div>
          ) : (
            <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={isEnfant ? "ton@email.com" : "votre@email.com"}
                style={{ padding: "13px 16px", borderRadius: 12, border: "1px solid rgba(10,14,44,0.12)", fontSize: 14, fontFamily: "inherit", outline: "none", background: "white" }}
                onFocus={(e) => e.target.style.borderColor = "#1320CE"}
                onBlur={(e) => e.target.style.borderColor = "rgba(10,14,44,0.12)"}
              />
              {error && <div style={{ fontSize: 12, color: "#FD6936" }}>{error}</div>}
              <button type="submit" className="btn btn-orange" style={{ padding: "13px 20px", fontSize: 14, borderRadius: 12, justifyContent: "center" }}>
                S'inscrire
              </button>
            </form>
          )}
          <p style={{ fontSize: 11, color: "var(--c-muted)", textAlign: "center", margin: 0, lineHeight: 1.4 }}>
            Gratuit · 1 email/semaine · pas de spam, désinscription 1 clic
          </p>
        </div>
      </div>
    </section>
  );
};
"""

RETURN_ANCHOR = '<PaidConversionCTA />'
RETURN_REPLACE = RETURN_ANCHOR + '\n      <NewsletterCard />'

STRIP_RE = re.compile(
    r'\n/\* __proxxie_newsletter_widget_v1__ \*/.*?(?=\n(?:/\* __proxxie_|const Dashboard = \(\) =>))',
    flags=re.S,
)


def strip_v1(src):
    src = STRIP_RE.sub("", src)
    src = src.replace(RETURN_REPLACE, RETURN_ANCHOR, 1)
    return src


def patch_asset(src):
    if MARKER in src:
        src = strip_v1(src)
    if RETURN_ANCHOR not in src:
        raise SystemExit("PaidConversionCTA anchor not found (run earlier patches first)")
    src = src.replace("const Dashboard = () =>", COMPONENT_JSX + "\nconst Dashboard = () =>", 1)
    src = src.replace(RETURN_ANCHOR, RETURN_REPLACE, 1)
    return src


def patch_one(target):
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
    return f"{'re-patched' if was_patched else 'patched'} ({len(new_src)} chars)"


if __name__ == "__main__":
    for fn in TARGETS:
        try:
            print(f"{fn}: {patch_one(REPO / fn)}")
        except SystemExit as e:
            print(f"{fn}: ERROR · {e}")

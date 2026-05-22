#!/usr/bin/env python3
"""F4 (volet dashboard) · modale de conversion ouverte depuis le dashboard.

The paid-conversion banner (PaidConversionCTA) sent straight to Calendly with no
preparation. F4 adds a « Comment ça se passe ? » button on that banner which
opens a ProxxieConversionModal: présentation du coach, déroulé de
l'accompagnement (4 étapes), bénéfices, témoignage, tarif, et CTA Calendly. It
gives the parent the « pourquoi » before the booking.

Two changes, both scoped to the PaidConversionCTA function so anchors stay
unique:
  · add local state (convOpen) + the secondary button + render the modal,
  · inject the ProxxieConversionModal component before PaidConversionCTA.

Role-aware (tu/vous) and tarif-aware (entretien gratuit vs accompagnement) via
the same testsDone signal the banner already computes.

Idempotent · the component is strip-and-readd between markers; the in-function
edits are guarded by the convOpen sentinel.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
FILES = ["Proxxie Dashboard.html", "dashboard.html"]

BEGIN = "/* PROXXIE_CONV_MODAL_BEGIN */"
END = "/* PROXXIE_CONV_MODAL_END */"

CTA_ANCHOR = "const PaidConversionCTA = () => {"
NEXT_MARKER = "/* __proxxie_onboarding_v1__ */"

COMPONENT = BEGIN + r"""
/* ---------------- ProxxieConversionModal · « comment ça se passe » ---------------- */
const ProxxieConversionModal = ({ open, onClose, role, testsDone }) => {
  if (!open) return null;
  const isEnfant = role === "enfant";
  const advanced = (testsDone || 0) >= 5 && !isEnfant;
  const calendlyUrl = advanced
    ? "https://calendly.com/proxxie/accompagnement"
    : "https://calendly.com/proxxie/entretien";

  const steps = [
    { n: "01", t: "RDV de cadrage offert", s: "On fait le point sur le rapport, les objectifs et les blocages.", c: "#FD6936", bg: "rgba(253,105,54,.10)" },
    { n: "02", t: "Séances régulières", s: "Visios de 30 min : stratégie vœux, choix de spés, méthodo.", c: "#487AFF", bg: "rgba(72,122,255,.10)" },
    { n: "03", t: "Plan d'action concret", s: "À chaque séance, des prochaines actions claires et suivies.", c: "#22A06B", bg: "rgba(34,160,107,.10)" },
    { n: "04", t: "Suivi dans la durée", s: "Messagerie, notes et replays entre les séances.", c: "#0A0E2C", bg: "rgba(10,14,44,.05)" },
  ];
  const benefits = isEnfant
    ? ["Un cap clair sur ton orientation", "Du temps gagné face à Parcoursup", "Quelqu'un qui connaît ton dossier"]
    : ["Des choix alignés sur le profil réel de votre ado", "Fini les heures à décrypter Parcoursup seul", "Un expert qui répond à vos questions"];

  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, background: "rgba(10,14,44,.55)", display: "grid", placeItems: "center", zIndex: 210, padding: 20, overflowY: "auto" }}>
      <div onClick={(e) => e.stopPropagation()} style={{ background: "white", borderRadius: 24, maxWidth: 680, width: "100%", overflow: "hidden", boxShadow: "0 24px 70px rgba(10,14,44,.35)" }}>

        {/* En-tête · coach */}
        <div style={{ background: "linear-gradient(135deg, #0A0E2C 0%, #1320CE 100%)", color: "white", padding: "26px 28px", position: "relative" }}>
          <button onClick={onClose} style={{ position: "absolute", top: 18, right: 20, background: "transparent", border: "none", fontSize: 24, color: "rgba(255,255,255,.7)", cursor: "pointer", lineHeight: 1, fontFamily: "inherit" }} aria-label="Fermer">×</button>
          <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase", color: "#F5EB3F" }}>L'accompagnement Proxxie</span>
          <div style={{ display: "flex", alignItems: "center", gap: 14, marginTop: 14 }}>
            <div style={{ width: 54, height: 54, borderRadius: "50%", background: "linear-gradient(135deg, #FD6936, #F5EB3F)", display: "grid", placeItems: "center", fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 22, color: "#0A0E2C", flexShrink: 0 }}>C</div>
            <div>
              <div style={{ fontFamily: "var(--font-display)", fontSize: 20, fontWeight: 600 }}>Charles · coach orientation</div>
              <div style={{ fontSize: 13, color: "rgba(255,255,255,.7)" }}>+150 ados accompagnés · ex-prof, formé à l'orientation</div>
            </div>
          </div>
        </div>

        {/* Corps */}
        <div style={{ padding: "24px 28px 26px" }}>
          <h3 style={{ fontFamily: "var(--font-display)", fontSize: 19, fontWeight: 600, margin: "0 0 14px" }}>
            {isEnfant ? "Comment se passent tes séances" : "Comment se passe l'accompagnement"}
          </h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 22 }}>
            {steps.map((s, i) => (
              <div key={i} style={{ background: s.bg, borderRadius: 12, padding: "13px 14px" }}>
                <div style={{ fontFamily: "var(--font-num)", fontSize: 12, fontWeight: 700, color: s.c, marginBottom: 5 }}>{s.n}</div>
                <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 2 }}>{s.t}</div>
                <div style={{ fontSize: 12, color: "var(--c-muted)", lineHeight: 1.4 }}>{s.s}</div>
              </div>
            ))}
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 20 }}>
            {benefits.map((b, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 14 }}>
                <span style={{ color: "#22A06B", fontWeight: 700, flexShrink: 0 }}>✓</span>
                <span>{b}</span>
              </div>
            ))}
          </div>

          <div style={{ padding: "14px 16px", background: "rgba(10,14,44,.02)", borderRadius: 12, marginBottom: 20 }}>
            <div style={{ fontSize: 13, fontStyle: "italic", lineHeight: 1.5, marginBottom: 5 }}>
              « En trois séances, on est passés de la panique des vœux à une liste qu'on assume tous les deux. »
            </div>
            <div style={{ fontSize: 12, color: "var(--c-muted)" }}>Sophie, maman de Léa (Terminale)</div>
          </div>

          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16, flexWrap: "wrap" }}>
            <div style={{ fontSize: 13, color: "var(--c-muted)" }}>
              <strong style={{ color: "var(--c-ink)", fontSize: 15 }}>Premier RDV offert</strong><br/>
              {isEnfant ? "Sans engagement · 30 min en visio" : "Puis 290€/mois, annulation à 30 jours"}
            </div>
            <a href={calendlyUrl} target="_blank" rel="noopener noreferrer" className="btn btn-orange" style={{ padding: "14px 24px", fontSize: 15, borderRadius: 12, textDecoration: "none", whiteSpace: "nowrap" }}>
              Réserver le RDV de cadrage →
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

""" + END + "\n\n" + CTA_ANCHOR

# In-function edits (applied only inside the PaidConversionCTA block)
STATE_OLD = "  const isAdvanced = testsDone >= 5;\n"
STATE_NEW = STATE_OLD + "  const [convOpen, setConvOpen] = React.useState(false);\n"

BTN_OLD = (
    '            <a href={calendlyUrl} target="_blank" rel="noopener noreferrer" className="btn btn-orange" style={{ padding: "14px 22px", fontSize: 14, borderRadius: 12, textDecoration: "none", textAlign: "center", whiteSpace: "nowrap" }}>\n'
    "              {ctaPrimary}\n"
    "            </a>\n"
)
BTN_NEW = (
    BTN_OLD
    + '            <button onClick={() => setConvOpen(true)} style={{ padding: "12px 22px", fontSize: 13, borderRadius: 12, fontFamily: "inherit", cursor: "pointer", background: "rgba(255,255,255,.12)", color: "white", border: "1px solid rgba(255,255,255,.28)", whiteSpace: "nowrap" }}>\n'
    "              Comment ça se passe ?\n"
    "            </button>\n"
)

MODAL_OLD = "    </section>\n  );\n};"
MODAL_NEW = (
    "      <ProxxieConversionModal open={convOpen} onClose={() => setConvOpen(false)} role={role} testsDone={testsDone} />\n"
    "    </section>\n  );\n};"
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

    # 1 · component (strip-and-readd; readd re-attaches CTA_ANCHOR)
    src = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n\n", "", src, flags=re.DOTALL)
    if CTA_ANCHOR not in src:
        return "SKIP no PaidConversionCTA anchor"
    src = src.replace(CTA_ANCHOR, COMPONENT, 1)
    changes.append("component")

    # 2 · in-function edits, scoped to the PaidConversionCTA block
    start = src.find(CTA_ANCHOR)
    end = src.find(NEXT_MARKER, start)
    if end == -1:
        return "SKIP no onboarding marker after CTA"
    block = src[start:end]

    if "convOpen" in block:
        changes.append("wiring(already)")
    else:
        if STATE_OLD not in block or BTN_OLD not in block or MODAL_OLD not in block:
            return "SKIP CTA inner anchors not found"
        block = block.replace(STATE_OLD, STATE_NEW, 1)
        block = block.replace(BTN_OLD, BTN_NEW, 1)
        block = block.replace(MODAL_OLD, MODAL_NEW, 1)
        changes.append("wiring")
        src = src[:start] + block + src[end:]

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

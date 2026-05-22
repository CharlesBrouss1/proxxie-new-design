#!/usr/bin/env python3
"""F3 · écran d'invitation ado, version « vendeuse ».

The invitation is the pivot from « outil du parent » to « outil de la famille »,
but it was a thin single-column modal (code + copy + email/sms). This replaces
InvitationModal in the dashboard asset with a two-panel experience:

  · gauche · un APERÇU de ce que la personne invitée verra (mini maquette de
    son espace : accueil personnalisé, prochain test, comparaison à venir).
    On montre le bénéfice, on ne le décrit pas.
  · droite · le bénéfice en 3 points + le code + le partage en un geste
    (copier le lien, WhatsApp, SMS, email).

Role-aware: a parent invites the ado (FIRST_NAME); the ado invites « ton parent ».
The link/code reuses _proxxieGetLinkCode. The 2-column grid collapses to one
column on mobile via the bundle's injected mobile stylesheet.

The whole component is replaced by slicing between its signature and the next
module marker (__proxxie_mode_choice_v1__), so re-running is idempotent (the
replacement re-emits the same signature + body).
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
FILES = ["Proxxie Dashboard.html", "dashboard.html"]

START_ANCHOR = "const InvitationModal = ({ open, onClose }) => {"
END_ANCHOR = "/* __proxxie_mode_choice_v1__ */"

NEW_COMPONENT = r"""const InvitationModal = ({ open, onClose }) => { /* PROXXIE_INVITE_V2 */
  const role = useProxxieRole();
  const isEnfant = role === "enfant";
  const [code] = React.useState(_proxxieGetLinkCode);
  const [copied, setCopied] = React.useState(false);
  const [copiedLink, setCopiedLink] = React.useState(false);
  if (!open) return null;

  const invitedName = isEnfant ? "ton parent" : FIRST_NAME;
  const invitedNameCap = isEnfant ? "Ton parent" : FIRST_NAME;
  const joinUrl = "https://www.proxxie.co/connexion?code=" + code;
  const shareMsg = (isEnfant ? "Salut, rejoins-moi sur Proxxie" : "Bonjour, rejoins-moi sur Proxxie")
    + " avec mon code " + code + " · " + joinUrl;

  const copyCode = () => { try { navigator.clipboard.writeText(code); setCopied(true); setTimeout(() => setCopied(false), 1600); } catch (e) {} };
  const copyLink = () => { try { navigator.clipboard.writeText(joinUrl); setCopiedLink(true); setTimeout(() => setCopiedLink(false), 1600); } catch (e) {} };

  const benefits = isEnfant ? [
    { ic: "🧭", t: "Il découvre ton profil d'orientation", s: "Tes tests et ton rapport, expliqués de son côté." },
    { ic: "🔍", t: "Vous comparez vos visions", s: "Là où vous vous rejoignez, là où vous vous surprenez." },
    { ic: "🎓", t: "Il peut réserver un RDV coach", s: "Pour transformer tout ça en plan d'action." },
  ] : [
    { ic: "🧭", t: invitedNameCap + " passe ses propres tests", s: "Son point de vue, en plus du vôtre." },
    { ic: "🔍", t: "Vous comparez vos deux profils", s: "Là où vous vous rejoignez, là où " + invitedName + " vous surprend." },
    { ic: "💬", t: "La conversation s'ouvre", s: "Les écarts sont souvent les meilleurs sujets d'échange." },
  ];

  /* Aperçu · ce que la personne invitée verra à l'arrivée. */
  const previewGreeting = isEnfant ? "Salut 👋" : "Salut " + FIRST_NAME + " 👋";
  const previewLead = isEnfant
    ? "Voici ton espace · le profil de ton ado t'attend."
    : "Voici ton espace Proxxie. On commence ?";

  const shareBtnStyle = {
    display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
    padding: "12px 14px", borderRadius: 10, border: "1px solid rgba(10,14,44,.12)",
    fontSize: 13, fontWeight: 600, textDecoration: "none", color: "#0A0E2C",
    background: "white", cursor: "pointer", fontFamily: "inherit",
  };

  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, background: "rgba(10,14,44,.55)", display: "grid", placeItems: "center", zIndex: 200, padding: 20 }}>
      <div onClick={(e) => e.stopPropagation()} style={{ background: "white", borderRadius: 24, maxWidth: 760, width: "100%", overflow: "hidden", boxShadow: "0 20px 60px rgba(10,14,44,.25)", display: "grid", gridTemplateColumns: "1fr 1fr" }}>

        {/* ---- Aperçu (gauche) ---- */}
        <div style={{ background: "linear-gradient(160deg, #1320CE 0%, #0A0E2C 100%)", color: "white", padding: "28px 26px", position: "relative" }}>
          <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase", color: "rgba(255,255,255,.6)" }}>
            Aperçu
          </span>
          <h3 style={{ fontFamily: "var(--font-display)", fontSize: 21, fontWeight: 600, letterSpacing: "-0.01em", margin: "8px 0 18px", lineHeight: 1.2 }}>
            Ce que {invitedName} verra
          </h3>

          <div style={{ background: "white", color: "#0A0E2C", borderRadius: 14, padding: "16px 16px 14px", boxShadow: "0 10px 30px rgba(0,0,0,.25)" }}>
            <div style={{ fontFamily: "var(--font-display)", fontSize: 16, fontWeight: 600, marginBottom: 2 }}>{previewGreeting}</div>
            <div style={{ fontSize: 11, color: "rgba(10,14,44,.55)", marginBottom: 12, lineHeight: 1.35 }}>{previewLead}</div>

            <div style={{ display: "flex", alignItems: "center", gap: 9, padding: "9px 10px", borderRadius: 10, background: "rgba(253,105,54,.08)", marginBottom: 8 }}>
              <span style={{ width: 26, height: 26, borderRadius: 8, background: "rgba(253,105,54,.16)", display: "grid", placeItems: "center", fontSize: 13, flexShrink: 0 }}>🎯</span>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: "#FD6936" }}>Prochaine étape</div>
                <div style={{ fontSize: 11, color: "rgba(10,14,44,.6)" }}>Passer le Big Five · 10 min</div>
              </div>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: 9, padding: "9px 10px", borderRadius: 10, background: "rgba(72,122,255,.08)" }}>
              <span style={{ width: 26, height: 26, borderRadius: 8, background: "rgba(72,122,255,.16)", display: "grid", placeItems: "center", fontSize: 13, flexShrink: 0 }}>🔍</span>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: "#1320CE" }}>Comparaison</div>
                <div style={{ fontSize: 11, color: "rgba(10,14,44,.6)" }}>Vos deux profils, côte à côte</div>
              </div>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 7, marginTop: 16, fontSize: 11, color: "rgba(255,255,255,.7)" }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#22A06B" }} />
            Compte relié · données partagées en toute sécurité
          </div>
        </div>

        {/* ---- Inviter (droite) ---- */}
        <div style={{ padding: "26px 26px 28px" }}>
          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 6 }}>
            <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase", color: "#FD6936", display: "inline-flex", alignItems: "center", gap: 7 }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#FD6936" }} />
              {isEnfant ? "Inviter mon parent" : "Inviter mon ado"}
            </span>
            <button onClick={onClose} style={{ background: "transparent", border: "none", fontSize: 22, color: "rgba(10,14,44,.5)", cursor: "pointer", padding: 0, lineHeight: 1, fontFamily: "inherit" }} aria-label="Fermer">×</button>
          </div>
          <h3 style={{ fontFamily: "var(--font-display)", fontSize: 23, fontWeight: 600, letterSpacing: "-0.02em", margin: "0 0 16px", lineHeight: 1.15 }}>
            {isEnfant ? "Invite ton parent à te rejoindre" : "Invitez " + FIRST_NAME + " à vous rejoindre"}
          </h3>

          <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 18 }}>
            {benefits.map((b, i) => (
              <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 11 }}>
                <span style={{ fontSize: 17, lineHeight: 1.3, flexShrink: 0 }}>{b.ic}</span>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "#0A0E2C" }}>{b.t}</div>
                  <div style={{ fontSize: 12, color: "rgba(10,14,44,.55)", lineHeight: 1.4 }}>{b.s}</div>
                </div>
              </div>
            ))}
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "12px 14px", border: "1.5px dashed rgba(19,32,206,.25)", borderRadius: 12, background: "rgba(19,32,206,.03)", marginBottom: 12 }}>
            <span style={{ flex: 1, fontFamily: "var(--font-num)", fontSize: 20, fontWeight: 700, color: "#1320CE", letterSpacing: "0.08em" }}>{code}</span>
            <button onClick={copyCode} className="btn btn-orange" style={{ padding: "9px 15px", fontSize: 13, borderRadius: 10 }}>
              {copied ? "Copié ✓" : "Copier"}
            </button>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            <button onClick={copyLink} style={shareBtnStyle}>{copiedLink ? "Lien copié ✓" : "🔗 Copier le lien"}</button>
            <a href={"https://wa.me/?text=" + encodeURIComponent(shareMsg)} target="_blank" rel="noopener" style={shareBtnStyle}>🟢 WhatsApp</a>
            <a href={"sms:?body=" + encodeURIComponent(shareMsg)} style={shareBtnStyle}>💬 SMS</a>
            <a href={"mailto:?subject=" + encodeURIComponent("Rejoins-moi sur Proxxie") + "&body=" + encodeURIComponent(shareMsg)} style={shareBtnStyle}>📧 Email</a>
          </div>

          <p style={{ fontSize: 12, color: "rgba(10,14,44,.45)", margin: "14px 0 0", lineHeight: 1.4 }}>
            {isEnfant
              ? "Dès que ton parent s'inscrit avec ce code, vos comptes sont liés et la comparaison apparaît sur vos deux dashboards."
              : "Dès que " + FIRST_NAME + " s'inscrit avec ce code, vos comptes sont liés et la comparaison apparaît sur vos deux dashboards."}
          </p>
        </div>
      </div>
    </div>
  );
};


"""


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

    start = src.find(START_ANCHOR)
    end = src.find(END_ANCHOR)
    if start == -1 or end == -1 or end < start:
        return "SKIP anchors not found"

    already = "PROXXIE_INVITE_V2" in src[start:end]
    src = src[:start] + NEW_COMPONENT + END_ANCHOR + src[end + len(END_ANCHOR):]

    nd = src.encode("utf-8")
    if comp:
        nd = gzip.compress(nd)
    manifest[uuid]["data"] = base64.b64encode(nd).decode("ascii")
    new_manifest = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest + html[m.end(2):]
    target.write_text(new_html, encoding="utf-8")
    return ("re-patched" if already else "patched") + " (asset " + uuid[:8] + ")"


if __name__ == "__main__":
    for fn in FILES:
        print("  " + fn + ": " + patch_one(REPO / fn))

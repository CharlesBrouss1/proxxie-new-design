#!/usr/bin/env python3
"""F1 · « votre prochaine étape » · l'action unique du dashboard.

The dashboard opens on a wall of equally-weighted sections, so a parent who
lands doesn't know what to do first. This injects a NextBestAction hero at the
top that computes the SINGLE most important next step from the journey state
and presents it as one big, unmissable CTA. Everything else stays below.

State machine (reuses _proxxieGetOnboardingState, defined earlier in the asset):
  parent · profil → 1er document → Big Five → inviter l'ado → 1er RDV → régime
  ado    · profil → Big Five → 1er document → inviter le parent → régime
The first incomplete step wins; once everything is done it shows a steady-state
"keep the report up to date" nudge so the hero is always actionable.

It also removes a pre-existing duplicate <OnboardingChecklist /> render (two
identical checklists were stacked), which directly cuts the clutter the hero is
meant to fix.

Idempotent · component is strip-and-readd between markers; the render insertion
and the de-dup are guarded.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
FILES = ["Proxxie Dashboard.html", "dashboard.html"]

BEGIN = "/* PROXXIE_NEXT_BEST_ACTION_BEGIN */"
END = "/* PROXXIE_NEXT_BEST_ACTION_END */"

CREATE_ROOT = 'ReactDOM.createRoot(document.getElementById("root")).render(<Dashboard />);'

# Mount right under the (thin) ReengagementBanner strip, above WhatsNewFeed.
RENDER_ANCHOR = "      <ReengagementBanner />\n"
RENDER_INSERT = (
    RENDER_ANCHOR
    + "      <NextBestAction onOpenProfile={() => setProfileOpen(true)} onOpenInvite={() => setInviteOpen(true)} />\n"
)

# De-dup: remove the second, prop-light OnboardingChecklist render.
DUP_LINE = "\n      <OnboardingChecklist onOpenProfile={() => setProfileOpen(true)} />"

COMPONENT = BEGIN + r"""
/* ---------------- NextBestAction · l'action unique du moment ---------------- */
const _proxxieRdvBooked = () => {
  try { return localStorage.getItem("proxxie.rdv.booked") === "1"; } catch (e) { return false; }
};

const NextBestAction = ({ onOpenProfile, onOpenInvite }) => {
  const role = useProxxieRole();
  const isEnfant = role === "enfant";
  const [state, setState] = React.useState(_proxxieGetOnboardingState);

  // Re-lit l'état au retour sur l'onglet (test passé, doc uploadé, profil rempli).
  React.useEffect(() => {
    const refresh = () => setState(_proxxieGetOnboardingState());
    window.addEventListener("focus", refresh);
    document.addEventListener("visibilitychange", refresh);
    return () => {
      window.removeEventListener("focus", refresh);
      document.removeEventListener("visibilitychange", refresh);
    };
  }, []);
  const rdv = _proxxieRdvBooked();

  const steps = isEnfant ? [
    { done: state.profile,  title: "Complète ton profil",
      text: "Ton prénom et ta classe · 20 secondes. C'est ce qui adapte tout le reste.",
      cta: "Compléter mon profil", kind: "profile" },
    { done: state.firsttest, title: "Passe ton premier test · le Big Five",
      text: "10 minutes pour révéler tes 5 grands traits. Ton tableau de bord se remplit ensuite.",
      cta: "Lancer le test", href: "Proxxie Test.html" },
    { done: state.firstdoc, title: "Ajoute ton premier bulletin",
      text: "Pour caler les recommandations (lycées, vœux, métiers) sur tes vraies notes.",
      cta: "Ajouter un document", href: "Proxxie Documents.html" },
    { done: state.invited,  title: "Invite ton parent",
      text: "Compte relié · il compare sa vision à la tienne et te suit dans la durée.",
      cta: "Inviter mon parent", kind: "invite" },
  ] : [
    { done: state.profile,  title: "Indiquez le profil de " + FIRST_NAME,
      text: "Prénom et classe · 20 secondes. C'est ce qui personnalise lycées, vœux et métiers.",
      cta: "Compléter le profil", kind: "profile" },
    { done: state.firstdoc, title: "Ajoutez le premier bulletin de " + FIRST_NAME,
      text: "Le rapport et les conseils se calibrent sur ses vraies notes. Un bulletin suffit pour démarrer.",
      cta: "Ajouter un document", href: "Proxxie Documents.html" },
    { done: state.firsttest, title: "Passez le Big Five à la place de " + FIRST_NAME,
      text: "10 minutes. Vous répondez pour " + FIRST_NAME + ", il pourra le refaire de son côté ensuite.",
      cta: "Lancer le test", href: "Proxxie Test.html" },
    { done: state.invited,  title: "Invitez " + FIRST_NAME + " à rejoindre",
      text: "Compte relié · " + FIRST_NAME + " passe ses propres tests et vous comparez vos visions.",
      cta: "Inviter " + FIRST_NAME, kind: "invite" },
    { done: rdv,            title: "Réservez le premier RDV avec le coach",
      text: "Vous avez les tests et le rapport. Place à l'accompagnement avec Charles.",
      cta: "Prendre RDV", href: "Proxxie Coach.html" },
  ];

  const total = steps.length;
  const doneCount = steps.filter((s) => s.done).length;
  const currentIdx = steps.findIndex((s) => !s.done);
  const allDone = currentIdx === -1;

  const action = allDone
    ? {
        title: isEnfant ? "Tout est en place · continue sur ta lancée" : "Tout est en place · gardez le rapport à jour",
        text: isEnfant
          ? "Ajoute tes nouveaux bulletins dès qu'ils tombent et reviens explorer tes activités."
          : "Ajoutez les bulletins de chaque trimestre dès qu'ils arrivent · le rapport de " + FIRST_NAME + " reste vivant.",
        cta: isEnfant ? "Voir mes documents" : "Voir les documents",
        href: "Proxxie Documents.html",
      }
    : steps[currentIdx];

  const stepNo = allDone ? total : currentIdx + 1;
  const accent = allDone ? "#22A06B" : "#FD6936";
  const accentBg = allDone ? "rgba(34,160,107,.08)" : "rgba(253,105,54,.08)";

  const ctaStyle = {
    display: "inline-flex", alignItems: "center", gap: 8,
    padding: "14px 26px", borderRadius: 12, fontWeight: 700, fontSize: 15,
    fontFamily: "inherit", border: "none", cursor: "pointer", textDecoration: "none",
    background: accent, color: "white", whiteSpace: "nowrap",
    boxShadow: "0 6px 18px " + (allDone ? "rgba(34,160,107,.28)" : "rgba(253,105,54,.28)"),
  };
  const ctaLabel = action.cta + " →";
  const cta = action.kind === "profile"
    ? <button onClick={onOpenProfile} style={ctaStyle}>{ctaLabel}</button>
    : action.kind === "invite"
    ? <button onClick={() => { try { localStorage.setItem("proxxie.onboarding.invited", "1"); } catch (e) {} if (onOpenInvite) onOpenInvite(); }} style={ctaStyle}>{ctaLabel}</button>
    : <a href={action.href} style={ctaStyle}>{ctaLabel}</a>;

  return (
    <section style={{ margin: "0 auto 24px", padding: "0 24px", maxWidth: 1280 }}>
      <div style={{
        background: "white", borderRadius: 20, padding: "30px 32px",
        borderLeft: "5px solid " + accent,
        border: "1px solid var(--c-line)", borderLeftWidth: 5, borderLeftColor: accent,
        boxShadow: "0 4px 22px rgba(10,14,44,.05)",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        gap: 28, flexWrap: "wrap",
      }}>
        <div style={{ flex: 1, minWidth: 280 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12, flexWrap: "wrap" }}>
            <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase", color: accent, background: accentBg, padding: "5px 12px", borderRadius: 999 }}>
              {allDone ? (isEnfant ? "Ton parcours" : "Le parcours") : (isEnfant ? "Ta prochaine étape" : "Votre prochaine étape")}
            </span>
            {!allDone && (
              <span style={{ fontSize: 12, fontWeight: 600, color: "var(--c-muted)", fontFamily: "var(--font-num)" }}>
                Étape {stepNo} sur {total}
              </span>
            )}
          </div>
          <h2 style={{ fontFamily: "var(--font-display)", fontSize: 28, fontWeight: 600, letterSpacing: "-0.02em", margin: "0 0 8px", lineHeight: 1.15 }}>
            {action.title}
          </h2>
          <p style={{ fontSize: 15, color: "var(--c-muted)", margin: 0, lineHeight: 1.5, maxWidth: 620 }}>
            {action.text}
          </p>
          {/* progression · points */}
          <div style={{ display: "flex", alignItems: "center", gap: 7, marginTop: 18 }}>
            {steps.map((s, i) => (
              <span key={i} title={s.title} style={{
                width: i === currentIdx ? 26 : 9, height: 9, borderRadius: 999,
                background: s.done ? "#22A06B" : (i === currentIdx ? accent : "rgba(10,14,44,.12)"),
                transition: "width .2s, background .2s",
              }} />
            ))}
            <span style={{ fontSize: 12, color: "var(--c-muted)", marginLeft: 6, fontFamily: "var(--font-num)" }}>
              {doneCount}/{total} fait
            </span>
          </div>
        </div>
        <div style={{ flexShrink: 0 }}>{cta}</div>
      </div>
    </section>
  );
};
""" + END + "\n\n"


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

    # 1 · component (strip-and-readd)
    src = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n\n", "", src, flags=re.DOTALL)
    if CREATE_ROOT not in src:
        return "SKIP no createRoot anchor"
    src = src.replace(CREATE_ROOT, COMPONENT + CREATE_ROOT, 1)
    changes.append("component")

    # 2 · mount hero
    if "<NextBestAction" in src:
        changes.append("render(already)")
    elif RENDER_ANCHOR in src:
        src = src.replace(RENDER_ANCHOR, RENDER_INSERT, 1)
        changes.append("render")
    else:
        return "SKIP no <ReengagementBanner /> anchor"

    # 3 · de-dup OnboardingChecklist
    if DUP_LINE in src:
        src = src.replace(DUP_LINE, "", 1)
        changes.append("dedup-checklist")
    else:
        changes.append("dedup(already)")

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

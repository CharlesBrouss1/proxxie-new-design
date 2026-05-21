#!/usr/bin/env python3
"""Add a "Mise en route" onboarding checklist to the dashboard, plus a
reusable EditProfileModal for prénom + classe.

Three checklist items track progress in localStorage·
  - profile  · proxxie.onboarding.profile  (set by EditProfileModal save)
  - firsttest· proxxie.tests.big5 === "done" (Big Five = OCEAN-X)
  - firstdoc · ANY proxxie.docs.* set to "1"

Once all three are complete (or user clicks "Plus tard"), the card hides.

Wires into the Dashboard return between ReengagementBanner and WelcomeBanner.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
TARGETS = ["dashboard.html", "Proxxie Dashboard.html"]
DASHBOARD_ASSET = "5a278f70-3fa5-4bc0-bdb2-349143947f86"
MARKER = "/* __proxxie_onboarding_v1__ */"


COMPONENTS_JSX = r"""
/* __proxxie_onboarding_v1__ */

const _proxxieGetOnboardingState = () => {
  let profile = false, firsttest = false, firstdoc = false, invited = false, dismissed = false;
  try {
    profile   = localStorage.getItem("proxxie.onboarding.profile") === "1";
    invited   = localStorage.getItem("proxxie.onboarding.invited") === "1";
    dismissed = localStorage.getItem("proxxie.onboarding.dismissed") === "1";
    /* firsttest · viewer's own Big Five (role-scoped via _patch_tests_dual_storage) */
    const role = localStorage.getItem("proxxie.role");
    if (role === "parent" || role === "enfant") {
      firsttest = localStorage.getItem("proxxie.tests.big5." + role) === "done";
    }
    /* legacy fallback */
    if (!firsttest) firsttest = localStorage.getItem("proxxie.tests.big5") === "done";
    /* firstdoc · ANY proxxie.docs.X === "1" counts */
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (k && k.indexOf("proxxie.docs.") === 0 && localStorage.getItem(k) === "1") {
        firstdoc = true; break;
      }
    }
  } catch (e) {}
  return { profile, firsttest, firstdoc, invited, dismissed };
};

const EditProfileModal = ({ open, onClose, onSaved }) => {
  const role = useProxxieRole();
  const isEnfant = role === "enfant";
  const [name, setName] = React.useState(() => {
    try { return localStorage.getItem("proxxie_firstName") || ""; } catch (e) { return ""; }
  });
  const [grade, setGrade] = React.useState(() => {
    try { return localStorage.getItem("proxxie_grade") || "Terminale"; } catch (e) { return "Terminale"; }
  });

  if (!open) return null;

  const save = () => {
    try {
      if (name) localStorage.setItem("proxxie_firstName", name);
      if (grade) localStorage.setItem("proxxie_grade", grade);
      localStorage.setItem("proxxie.onboarding.profile", "1");
    } catch (e) {}
    if (onSaved) onSaved();
    onClose();
    /* Reload so the dashboard picks up the new FIRST_NAME / GRADE
       (they are computed at module init time, not from React state). */
    setTimeout(() => { try { window.location.reload(); } catch (e) {} }, 100);
  };

  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, background: "rgba(10,14,44,.55)", display: "grid", placeItems: "center", zIndex: 200, padding: 20 }}>
      <div onClick={(e) => e.stopPropagation()} style={{ background: "white", borderRadius: 24, maxWidth: 480, width: "100%", padding: 32, boxShadow: "0 20px 60px rgba(10,14,44,.25)" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
          <span className="eyebrow"><span className="dot"></span>{isEnfant ? "Ton profil" : "Le profil de votre ado"}</span>
          <button onClick={onClose} style={{ background: "transparent", border: "none", fontSize: 22, color: "rgba(10,14,44,.5)", cursor: "pointer", padding: 4, lineHeight: 1, fontFamily: "inherit" }} aria-label="Fermer">×</button>
        </div>
        <h3 style={{ fontFamily: "var(--font-display)", fontSize: 26, fontWeight: 600, letterSpacing: "-0.02em", margin: "0 0 10px" }}>
          {isEnfant ? "Dis-nous qui tu es" : "Indiquez le profil de votre ado"}
        </h3>
        <p style={{ fontSize: 14, color: "rgba(10,14,44,.55)", margin: "0 0 22px", lineHeight: 1.5 }}>
          {isEnfant
            ? "Ton prénom et ta classe nous servent à adapter les recommandations (lycées, vœux, métiers)."
            : "Le prénom et la classe de votre ado nous servent à adapter les recommandations (lycées, vœux, métiers)."}
        </p>

        <label style={{ display: "grid", gap: 6, marginBottom: 16 }}>
          <span style={{ fontSize: 13, fontWeight: 600 }}>{isEnfant ? "Ton prénom" : "Prénom de votre ado"}</span>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder={isEnfant ? "Arthur" : "Arthur"}
            style={{ padding: "13px 16px", borderRadius: 12, border: "1px solid rgba(10,14,44,0.12)", fontSize: 15, fontFamily: "inherit", outline: "none" }}
            onFocus={(e) => e.target.style.borderColor = "#487AFF"}
            onBlur={(e) => e.target.style.borderColor = "rgba(10,14,44,0.12)"}
          />
        </label>

        <label style={{ display: "grid", gap: 6, marginBottom: 22 }}>
          <span style={{ fontSize: 13, fontWeight: 600 }}>{isEnfant ? "Ta classe" : "Sa classe"}</span>
          <select
            value={grade}
            onChange={(e) => setGrade(e.target.value)}
            style={{ padding: "13px 16px", borderRadius: 12, border: "1px solid rgba(10,14,44,0.12)", fontSize: 15, fontFamily: "inherit", outline: "none", background: "white" }}
          >
            <option value="3ème">3ème</option>
            <option value="2nde">2nde</option>
            <option value="1ère">1ère</option>
            <option value="Terminale">Terminale</option>
            <option value="Post-Bac">Post-Bac</option>
          </select>
        </label>

        <button onClick={save} className="btn btn-orange" style={{ width: "100%", justifyContent: "center", padding: "14px 22px", fontSize: 14, borderRadius: 12 }}>
          Enregistrer
        </button>
      </div>
    </div>
  );
};

const OnboardingChecklist = ({ onOpenProfile, onOpenInvite }) => {
  const role = useProxxieRole();
  const isEnfant = role === "enfant";
  const [state, setState] = React.useState(_proxxieGetOnboardingState);

  /* Re-read state on focus/visibility so checks update when the user comes
     back from a test page or documents upload. */
  React.useEffect(() => {
    const refresh = () => setState(_proxxieGetOnboardingState());
    window.addEventListener("focus", refresh);
    document.addEventListener("visibilitychange", refresh);
    return () => {
      window.removeEventListener("focus", refresh);
      document.removeEventListener("visibilitychange", refresh);
    };
  }, []);

  /* Order matches the user's stated parent-first journey · profil →
     documents → tests → invite. For ado · profil → tests → docs → invite
     (the ado is more naturally led by tests than docs). */
  const items = isEnfant ? [
    {
      id: "profile",
      done: state.profile,
      label: "Complète ton profil",
      sub:   "Prénom + classe, 20 sec.",
      cta:   "Compléter",
      onClick: onOpenProfile,
    },
    {
      id: "firsttest",
      done: state.firsttest,
      label: "Passe ton premier test (Big Five)",
      sub:   "10 min · révèle tes 5 grands traits de personnalité.",
      cta:   "Lancer",
      href:  "Proxxie Test.html",
    },
    {
      id: "firstdoc",
      done: state.firstdoc,
      label: "Upload ton premier bulletin",
      sub:   "Permet de calibrer les recommandations sur tes vraies notes.",
      cta:   "Uploader",
      href:  "Proxxie Documents.html",
    },
    {
      id: "invite",
      done: state.invited,
      label: "Invite ton parent",
      sub:   "Pour qu'il puisse comparer son profil avec le tien et te suivre.",
      cta:   "Inviter",
      onClick: () => { try { localStorage.setItem("proxxie.onboarding.invited", "1"); } catch (e) {} if (onOpenInvite) onOpenInvite(); },
    },
  ] : [
    {
      id: "profile",
      done: state.profile,
      label: "Complétez le profil de votre ado",
      sub:   "Prénom + classe, 20 sec. Indispensable pour personnaliser les recommandations.",
      cta:   "Compléter",
      onClick: onOpenProfile,
    },
    {
      id: "firstdoc",
      done: state.firstdoc,
      label: "Uploadez un premier bulletin",
      sub:   "Le rapport et les conseils se calibrent sur les vraies notes de votre ado.",
      cta:   "Uploader",
      href:  "Proxxie Documents.html",
    },
    {
      id: "firsttest",
      done: state.firsttest,
      label: "Passez le Big Five (vous)",
      sub:   "10 min. Votre profil sert de point de comparaison quand votre ado passera le sien.",
      cta:   "Lancer",
      href:  "Proxxie Test.html",
    },
    {
      id: "invite",
      done: state.invited,
      label: "Invitez votre ado",
      sub:   "Lien sécurisé pour qu'il/elle accède à son espace et passe ses propres tests.",
      cta:   "Inviter",
      onClick: () => { try { localStorage.setItem("proxxie.onboarding.invited", "1"); } catch (e) {} if (onOpenInvite) onOpenInvite(); },
    },
  ];
  const done = items.filter((i) => i.done).length;
  const allDone = done === items.length;

  if (state.dismissed || allDone) return null;

  const dismiss = () => {
    try { localStorage.setItem("proxxie.onboarding.dismissed", "1"); } catch (e) {}
    setState({ ...state, dismissed: true });
  };

  const pct = Math.round((done / items.length) * 100);

  return (
    <section style={{ margin: "0 auto 24px", padding: "0 24px", maxWidth: 1280 }}>
      <div style={{
        background: "white",
        border: "1px solid rgba(10,14,44,0.08)",
        borderRadius: 20,
        padding: "26px 28px",
        position: "relative",
        boxShadow: "0 2px 14px rgba(10,14,44,.04)",
      }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 24, marginBottom: 20, flexWrap: "wrap" }}>
          <div style={{ maxWidth: 640, flex: 1, minWidth: 240 }}>
            <span className="eyebrow"><span className="dot"></span>Mise en route</span>
            <h2 style={{ fontFamily: "var(--font-display)", fontSize: 26, fontWeight: 600, letterSpacing: "-0.02em", marginTop: 10, marginBottom: 6, color: "#0A0E2C" }}>
              {isEnfant
                ? items.length + " actions pour démarrer ton parcours"
                : items.length + " actions pour démarrer le parcours de votre ado"}
            </h2>
            <p style={{ color: "rgba(10,14,44,.55)", fontSize: 14, margin: 0, lineHeight: 1.5 }}>
              {isEnfant
                ? "Coche ces étapes (10 min au total) pour que ton tableau de bord se remplisse avec tes vraies données et que ton parent puisse te suivre."
                : "Cochez ces étapes (10 min au total) pour que le tableau de bord se remplisse avec les vraies données de votre ado, et lancez l'accompagnement."}
            </p>
          </div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 6, minWidth: 160 }}>
            <div style={{ fontFamily: "var(--font-num)", fontSize: 26, fontWeight: 700, color: allDone ? "#22A06B" : "#1320CE" }}>
              {done}<span style={{ color: "rgba(10,14,44,.4)", fontSize: 18, fontWeight: 600 }}> / {items.length}</span>
            </div>
            <div style={{ width: 160, height: 8, borderRadius: 999, background: "rgba(10,14,44,.06)", overflow: "hidden" }}>
              <div style={{ width: pct + "%", height: "100%", background: allDone ? "#22A06B" : "linear-gradient(90deg, #FD6936 0%, #F5EB3F 100%)", transition: "width .4s ease" }} />
            </div>
            <button onClick={dismiss} style={{ background: "transparent", border: "none", fontSize: 12, color: "rgba(10,14,44,.5)", cursor: "pointer", padding: "4px 0", fontFamily: "inherit", textDecoration: "underline" }}>
              Plus tard
            </button>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 14 }}>
          {items.map((it, i) => {
            const inner = (
              <React.Fragment>
                <div style={{
                  width: 32, height: 32, borderRadius: 10,
                  background: it.done ? "rgba(34,160,107,.12)" : "rgba(72,122,255,.08)",
                  color: it.done ? "#22A06B" : "#487AFF",
                  display: "grid", placeItems: "center", flexShrink: 0,
                  fontWeight: 700, fontSize: 14,
                }}>
                  {it.done ? "✓" : (i + 1)}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 14, fontWeight: 600, color: "#0A0E2C", marginBottom: 2, textDecoration: it.done ? "line-through" : "none", textDecorationColor: "rgba(10,14,44,.3)" }}>
                    {it.label}
                  </div>
                  <div style={{ fontSize: 12, color: "rgba(10,14,44,.55)", lineHeight: 1.45 }}>
                    {it.sub}
                  </div>
                </div>
                {!it.done && (
                  <span style={{ fontSize: 13, fontWeight: 600, color: "#1320CE", whiteSpace: "nowrap" }}>{it.cta} →</span>
                )}
              </React.Fragment>
            );
            const sharedStyle = {
              display: "flex", alignItems: "center", gap: 14,
              padding: "16px 18px",
              border: "1px solid " + (it.done ? "rgba(34,160,107,.25)" : "rgba(10,14,44,.08)"),
              borderRadius: 14,
              background: it.done ? "rgba(34,160,107,.04)" : "#FAFAF6",
              textDecoration: "none", color: "inherit",
              cursor: it.done ? "default" : "pointer",
              transition: "transform .15s, border-color .15s, box-shadow .15s",
              opacity: it.done ? 0.85 : 1,
            };
            const hover = (e, on) => {
              if (it.done) return;
              e.currentTarget.style.transform = on ? "translateY(-1px)" : "translateY(0)";
              e.currentTarget.style.borderColor = on ? "#487AFF" : "rgba(10,14,44,.08)";
              e.currentTarget.style.boxShadow = on ? "0 4px 14px rgba(19,32,206,.06)" : "none";
            };
            if (it.href && !it.done) {
              return (
                <a key={it.id} href={it.href} style={sharedStyle}
                   onMouseEnter={(e) => hover(e, true)} onMouseLeave={(e) => hover(e, false)}>
                  {inner}
                </a>
              );
            }
            return (
              <div key={it.id} style={sharedStyle} role={it.done ? undefined : "button"} tabIndex={it.done ? undefined : 0}
                   onClick={it.done || !it.onClick ? undefined : it.onClick}
                   onMouseEnter={(e) => hover(e, true)} onMouseLeave={(e) => hover(e, false)}>
                {inner}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
"""

RETURN_ANCHOR = '<ReengagementBanner />'
RETURN_REPLACE = '<ReengagementBanner />\n      <OnboardingChecklist onOpenProfile={() => setProfileOpen(true)} onOpenInvite={() => setInviteOpen(true)} />'

STATE_HOOK_ANCHOR = 'const [inviteOpen, setInviteOpen] = React.useState(false);'
STATE_HOOK_INSERT = STATE_HOOK_ANCHOR + '\n  const [profileOpen, setProfileOpen] = React.useState(false);'

MODAL_ANCHOR = '<InvitationModal open={inviteOpen} onClose={() => setInviteOpen(false)} />'
MODAL_INSERT = MODAL_ANCHOR + '\n      <EditProfileModal open={profileOpen} onClose={() => setProfileOpen(false)} />'


STRIP_RE = re.compile(
    r'\n/\* __proxxie_onboarding_v1__ \*/.*?(?=\n(?:/\* __proxxie_|const Dashboard = \(\) =>))',
    flags=re.S,
)


def strip_v1(src: str) -> str:
    src = STRIP_RE.sub("", src)
    src = src.replace(RETURN_REPLACE, RETURN_ANCHOR, 1)
    src = src.replace(STATE_HOOK_INSERT, STATE_HOOK_ANCHOR, 1)
    src = src.replace(MODAL_INSERT, MODAL_ANCHOR, 1)
    return src


def patch_asset(src: str) -> str:
    if MARKER in src:
        src = strip_v1(src)
    if RETURN_ANCHOR not in src:
        raise SystemExit("ReengagementBanner anchor not found (run _patch_dashboard_v2.py first)")
    if STATE_HOOK_ANCHOR not in src:
        raise SystemExit("inviteOpen state anchor not found")
    if MODAL_ANCHOR not in src:
        raise SystemExit("InvitationModal anchor not found")
    src = src.replace("const Dashboard = () =>", COMPONENTS_JSX + "\nconst Dashboard = () =>", 1)
    src = src.replace(STATE_HOOK_ANCHOR, STATE_HOOK_INSERT, 1)
    src = src.replace(RETURN_ANCHOR, RETURN_REPLACE, 1)
    src = src.replace(MODAL_ANCHOR, MODAL_INSERT, 1)
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
    verb = "re-patched" if was_patched else "patched"
    return f"{verb} (asset {len(new_src)} chars)"


if __name__ == "__main__":
    for fn in TARGETS:
        try:
            print(f"{fn}: {patch_one(REPO / fn)}")
        except SystemExit as e:
            print(f"{fn}: ERROR · {e}")

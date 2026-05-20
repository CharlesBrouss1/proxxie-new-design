#!/usr/bin/env python3
"""Patch connexion.html to add:
  - Tabs: Se connecter / Creer un compte
  - Role selector: Parent / Ado (enfant)
  - Copy adapts: vouvoiement for parent, tutoiement for enfant
  - Signup mode adds name, confirm password, optional link code
  - On submit, persists role to localStorage and redirects with ?role=...

The page bundles a React component via <script type="text/babel"> inside
the Pretext template. We replace that whole component.

Re-runnable. Idempotent: if the new marker is found, we skip.
"""
import re, json, pathlib, sys

REPO = pathlib.Path(__file__).parent
TARGET = REPO / "connexion.html"

NEW_MARKER = "const AuthPage = () =>"

NEW_BABEL_SCRIPT = r"""
    const AuthPage = () => {
      const initialRole = (() => {
        try {
          const u = new URLSearchParams(window.location.search).get("role");
          if (u === "parent" || u === "enfant") return u;
          const s = localStorage.getItem("proxxie.role");
          if (s === "parent" || s === "enfant") return s;
        } catch (e) {}
        return "parent";
      })();
      const initialMode = (() => {
        try {
          const m = new URLSearchParams(window.location.search).get("mode");
          if (m === "signup" || m === "login") return m;
        } catch (e) {}
        return "login";
      })();

      const [mode, setMode] = React.useState(initialMode);
      const [role, setRole] = React.useState(initialRole);
      const [email, setEmail] = React.useState("");
      const [pwd, setPwd] = React.useState("");
      const [pwd2, setPwd2] = React.useState("");
      const [name, setName] = React.useState("");
      const [linkCode, setLinkCode] = React.useState("");
      const [show, setShow] = React.useState(false);
      const [remember, setRemember] = React.useState(true);
      const [error, setError] = React.useState("");
      const [loading, setLoading] = React.useState(false);

      const isEnfant = role === "enfant";
      const isSignup = mode === "signup";

      const T = isEnfant ? {
        eyebrow: "Espace ado",
        loginTitle: "Bon retour",
        loginSub: "Connecte-toi pour retrouver ton tableau de bord, ton rapport et ton coach.",
        signupTitle: "Crée ton compte",
        signupSub: "5 minutes pour démarrer ton parcours d'orientation.",
        emailLabel: "Ton email",
        emailPh: "prenom@email.com",
        nameLabel: "Ton prénom",
        namePh: "Lou",
        pwdLabel: "Ton mot de passe",
        pwd2Label: "Confirme ton mot de passe",
        linkLabel: "Code parent (optionnel)",
        linkPh: "ex. PRX-7G2F",
        linkHelp: "Si un parent t'a invité, colle son code pour relier vos comptes et comparer vos résultats.",
        ctaLogin: "Se connecter",
        ctaSignup: "Créer mon compte",
        swapToSignup: "Pas encore de compte ?",
        swapToSignupCTA: "Crée le tien en 5 min",
        swapToLogin: "Déjà un compte ?",
        swapToLoginCTA: "Connecte-toi",
        rememberLabel: "Rester connecté sur cet appareil",
        demoCTA: "Pré-remplir avec un compte démo",
        rightBadge: "Espace sécurisé",
        rightHeading: "Tout ton avenir,",
        rightHeadingHl: "en un seul endroit",
        rightSub: "Rapport OCEAN-X, vœux Parcoursup, séances coach et messagerie. Reprends où tu en étais.",
        features: [
          { t: "Ton profil OCEAN-X", d: "Personnalité, métiers compatibles, secteurs porteurs" },
          { t: "Tes tests psychométriques", d: "RIASEC, MBTI, PCM, HPI et plus, à ton rythme" },
          { t: "Ton coach dédié", d: "Messagerie, créneaux, replays de tes séances" },
        ],
      } : {
        eyebrow: "Espace parent",
        loginTitle: "Bon retour parmi nous",
        loginSub: "Connectez-vous pour retrouver le tableau de bord, le rapport et le coach de votre ado.",
        signupTitle: "Créer votre compte parent",
        signupSub: "5 minutes pour démarrer le parcours d'orientation de votre ado.",
        emailLabel: "Email parent",
        emailPh: "prenom.nom@email.com",
        nameLabel: "Votre prénom",
        namePh: "Caroline",
        pwdLabel: "Mot de passe",
        pwd2Label: "Confirmer le mot de passe",
        linkLabel: "Code de votre ado (optionnel)",
        linkPh: "ex. PRX-7G2F",
        linkHelp: "Si votre ado a déjà créé son compte, collez son code pour relier vos comptes et comparer vos résultats.",
        ctaLogin: "Se connecter",
        ctaSignup: "Créer mon compte",
        swapToSignup: "Pas encore de compte ?",
        swapToSignupCTA: "Démarrer en 5 min",
        swapToLogin: "Déjà un compte ?",
        swapToLoginCTA: "Se connecter",
        rememberLabel: "Rester connecté sur cet appareil",
        demoCTA: "Pré-remplir avec un compte démo",
        rightBadge: "Espace sécurisé",
        rightHeading: "Tout l'avenir de votre ado,",
        rightHeadingHl: "en un seul endroit",
        rightSub: "Rapport OCEAN-X, vœux Parcoursup, séances coach et messagerie sécurisée. Connectez-vous pour reprendre où vous en étiez.",
        features: [
          { t: "Profil OCEAN-X complet", d: "Personnalité, métiers compatibles, secteurs porteurs" },
          { t: "Suivi Parcoursup", d: "Vœux, statuts, lettres de motivation relues" },
          { t: "Coach dédié", d: "Messagerie, créneaux, replays de vos séances" },
        ],
      };

      const persistAndGo = () => {
        try {
          localStorage.setItem("proxxie.role", role);
          if (isSignup) localStorage.setItem("proxxie.justSignedUp", "1");
        } catch (e) {}
        setLoading(true);
        setTimeout(() => {
          window.location.href = "Proxxie Dashboard.html?role=" + role;
        }, 700);
      };

      const submit = (e) => {
        e.preventDefault();
        setError("");
        if (!email || !pwd) {
          setError(isEnfant ? "Email et mot de passe sont nécessaires." : "Email et mot de passe sont requis.");
          return;
        }
        if (isSignup) {
          if (!name) { setError(isEnfant ? "Indique ton prénom." : "Indiquez votre prénom."); return; }
          if (pwd !== pwd2) { setError(isEnfant ? "Les deux mots de passe ne correspondent pas." : "Les deux mots de passe ne correspondent pas."); return; }
        }
        persistAndGo();
      };

      const fillDemo = () => {
        if (isEnfant) {
          setEmail("lou.martin@example.com");
          setName("Lou");
        } else {
          setEmail("caroline.martin@example.com");
          setName("Caroline");
        }
        setPwd("demo1234");
        setPwd2("demo1234");
      };

      // Reusable segmented-control button style
      const segBtn = (active) => ({
        flex: 1,
        padding: "10px 14px",
        borderRadius: 10,
        border: "1px solid " + (active ? "#1320CE" : "var(--c-line)"),
        background: active ? "#1320CE" : "white",
        color: active ? "white" : "var(--c-ink-2)",
        fontWeight: 600,
        fontSize: 13,
        cursor: "pointer",
        fontFamily: "inherit",
        transition: "all .15s ease",
      });

      return (
        <div style={{ minHeight: "100vh", display: "grid", gridTemplateColumns: "1fr 1fr" }}>
          {/* Left side — form */}
          <div style={{ display: "flex", flexDirection: "column", padding: "40px 60px", background: "white" }}>
            <a href="Proxxie Home.html" style={{ display: "inline-flex", alignItems: "center", gap: 10, textDecoration: "none" }}>
              <ProxxieLogo />
            </a>

            <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", maxWidth: 460, margin: "0 auto", width: "100%" }}>
              {/* Role selector */}
              <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
                <button type="button" onClick={() => setRole("parent")} style={segBtn(!isEnfant)}>Je suis parent</button>
                <button type="button" onClick={() => setRole("enfant")} style={segBtn(isEnfant)}>Je suis ado</button>
              </div>

              <span className="eyebrow"><span className="dot"></span>{T.eyebrow}</span>
              <h1 style={{ fontFamily: "var(--font-display)", fontSize: 36, fontWeight: 600, letterSpacing: "-0.02em", marginTop: 12, marginBottom: 8 }}>
                {isSignup ? T.signupTitle : T.loginTitle}
              </h1>
              <p style={{ color: "var(--c-muted)", fontSize: 15, marginBottom: 22 }}>
                {isSignup ? T.signupSub : T.loginSub}
              </p>

              {/* Login/Signup tabs */}
              <div style={{ display: "flex", gap: 4, padding: 4, background: "var(--c-cream-light)", borderRadius: 12, marginBottom: 20 }}>
                <button type="button" onClick={() => setMode("login")} style={{
                  flex: 1, padding: "10px 12px", border: "none", borderRadius: 8,
                  background: !isSignup ? "white" : "transparent",
                  boxShadow: !isSignup ? "0 1px 3px rgba(0,0,0,.06)" : "none",
                  fontWeight: 600, fontSize: 13, cursor: "pointer", fontFamily: "inherit",
                  color: !isSignup ? "var(--c-ink)" : "var(--c-muted)",
                }}>Se connecter</button>
                <button type="button" onClick={() => setMode("signup")} style={{
                  flex: 1, padding: "10px 12px", border: "none", borderRadius: 8,
                  background: isSignup ? "white" : "transparent",
                  boxShadow: isSignup ? "0 1px 3px rgba(0,0,0,.06)" : "none",
                  fontWeight: 600, fontSize: 13, cursor: "pointer", fontFamily: "inherit",
                  color: isSignup ? "var(--c-ink)" : "var(--c-muted)",
                }}>Créer un compte</button>
              </div>

              <form onSubmit={submit} style={{ display: "grid", gap: 14 }}>
                {isSignup && (
                  <label style={{ display: "grid", gap: 6 }}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>{T.nameLabel}</span>
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder={T.namePh}
                      style={{ padding: "13px 16px", borderRadius: 12, border: "1px solid var(--c-line)", fontSize: 15, fontFamily: "inherit", outline: "none" }}
                      onFocus={(e) => e.target.style.borderColor = "#487AFF"}
                      onBlur={(e) => e.target.style.borderColor = "var(--c-line)"}
                    />
                  </label>
                )}

                <label style={{ display: "grid", gap: 6 }}>
                  <span style={{ fontSize: 13, fontWeight: 600 }}>{T.emailLabel}</span>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder={T.emailPh}
                    style={{ padding: "13px 16px", borderRadius: 12, border: "1px solid var(--c-line)", fontSize: 15, fontFamily: "inherit", outline: "none" }}
                    onFocus={(e) => e.target.style.borderColor = "#487AFF"}
                    onBlur={(e) => e.target.style.borderColor = "var(--c-line)"}
                  />
                </label>

                <label style={{ display: "grid", gap: 6 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>{T.pwdLabel}</span>
                    {!isSignup && (
                      <a href="#" style={{ fontSize: 12, color: "#487AFF", textDecoration: "none", fontWeight: 500 }}>Oublié&nbsp;?</a>
                    )}
                  </div>
                  <div style={{ position: "relative" }}>
                    <input
                      type={show ? "text" : "password"}
                      value={pwd}
                      onChange={(e) => setPwd(e.target.value)}
                      placeholder="••••••••"
                      style={{ padding: "13px 16px", paddingRight: 50, borderRadius: 12, border: "1px solid var(--c-line)", fontSize: 15, fontFamily: "inherit", outline: "none", width: "100%", boxSizing: "border-box" }}
                      onFocus={(e) => e.target.style.borderColor = "#487AFF"}
                      onBlur={(e) => e.target.style.borderColor = "var(--c-line)"}
                    />
                    <button
                      type="button"
                      onClick={() => setShow(!show)}
                      style={{ position: "absolute", right: 8, top: "50%", transform: "translateY(-50%)", background: "transparent", border: "none", color: "var(--c-muted)", fontSize: 12, fontWeight: 500, cursor: "pointer", padding: 8 }}
                    >
                      {show ? "Masquer" : "Voir"}
                    </button>
                  </div>
                </label>

                {isSignup && (
                  <label style={{ display: "grid", gap: 6 }}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>{T.pwd2Label}</span>
                    <input
                      type={show ? "text" : "password"}
                      value={pwd2}
                      onChange={(e) => setPwd2(e.target.value)}
                      placeholder="••••••••"
                      style={{ padding: "13px 16px", borderRadius: 12, border: "1px solid var(--c-line)", fontSize: 15, fontFamily: "inherit", outline: "none" }}
                      onFocus={(e) => e.target.style.borderColor = "#487AFF"}
                      onBlur={(e) => e.target.style.borderColor = "var(--c-line)"}
                    />
                  </label>
                )}

                {isSignup && (
                  <label style={{ display: "grid", gap: 6 }}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>{T.linkLabel}</span>
                    <input
                      type="text"
                      value={linkCode}
                      onChange={(e) => setLinkCode(e.target.value.toUpperCase())}
                      placeholder={T.linkPh}
                      style={{ padding: "13px 16px", borderRadius: 12, border: "1px solid var(--c-line)", fontSize: 15, fontFamily: "inherit", outline: "none", letterSpacing: "0.04em" }}
                      onFocus={(e) => e.target.style.borderColor = "#487AFF"}
                      onBlur={(e) => e.target.style.borderColor = "var(--c-line)"}
                    />
                    <span style={{ fontSize: 12, color: "var(--c-muted)", lineHeight: 1.4 }}>{T.linkHelp}</span>
                  </label>
                )}

                {!isSignup && (
                  <label style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 14, color: "var(--c-ink-2)", cursor: "pointer" }}>
                    <input
                      type="checkbox"
                      checked={remember}
                      onChange={(e) => setRemember(e.target.checked)}
                      style={{ width: 18, height: 18, accentColor: "#1320CE" }}
                    />
                    {T.rememberLabel}
                  </label>
                )}

                {error && (
                  <div style={{ padding: "10px 14px", background: "rgba(253,105,54,.08)", border: "1px solid rgba(253,105,54,.3)", borderRadius: 10, fontSize: 13, color: "#FD6936" }}>
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  className="btn btn-orange btn-lg"
                  disabled={loading}
                  style={{ width: "100%", justifyContent: "center", marginTop: 4, opacity: loading ? 0.6 : 1 }}
                >
                  {loading ? (isSignup ? "Création…" : "Connexion…") : (isSignup ? T.ctaSignup : T.ctaLogin)}
                </button>

                <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "4px 0", color: "var(--c-muted)", fontSize: 12 }}>
                  <div style={{ flex: 1, height: 1, background: "var(--c-line)" }} />
                  <span>OU</span>
                  <div style={{ flex: 1, height: 1, background: "var(--c-line)" }} />
                </div>

                <button
                  type="button"
                  onClick={fillDemo}
                  style={{ padding: "12px 16px", borderRadius: 12, border: "1px dashed var(--c-line)", background: "var(--c-cream-light)", fontSize: 14, fontWeight: 500, color: "var(--c-ink-2)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 8, fontFamily: "inherit" }}
                >
                  <Icon.spark style={{ width: 14, height: 14, color: "#FD6936" }} />
                  {T.demoCTA}
                </button>
              </form>

              <p style={{ marginTop: 24, fontSize: 14, color: "var(--c-muted)", textAlign: "center" }}>
                {isSignup ? T.swapToLogin : T.swapToSignup}{" "}
                <a href="#" onClick={(e) => { e.preventDefault(); setMode(isSignup ? "login" : "signup"); }} style={{ color: "#1320CE", fontWeight: 600, textDecoration: "none" }}>
                  {isSignup ? T.swapToLoginCTA : T.swapToSignupCTA}
                </a>
              </p>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "var(--c-muted)", paddingTop: 30 }}>
              <span>© 2026 Proxxie</span>
              <div style={{ display: "flex", gap: 18 }}>
                <a href="#" style={{ color: "inherit", textDecoration: "none" }}>Politique</a>
                <a href="#" style={{ color: "inherit", textDecoration: "none" }}>CGV</a>
                <a href="#" style={{ color: "inherit", textDecoration: "none" }}>Aide</a>
              </div>
            </div>
          </div>

          {/* Right side — illustration / value */}
          <div style={{ background: "linear-gradient(180deg, #1320CE 0%, #0A0E2C 100%)", color: "white", padding: "60px", display: "flex", flexDirection: "column", justifyContent: "center", position: "relative", overflow: "hidden" }}>
            <div style={{ position: "absolute", top: -60, right: -60, width: 240, height: 240, borderRadius: "50%", background: "rgba(72,122,255,.25)" }} />
            <div style={{ position: "absolute", bottom: -80, left: -80, width: 320, height: 320, borderRadius: "50%", background: "rgba(245,235,63,.10)" }} />
            <Pill color="#FD6936" w={120} h={36} style={{ position: "absolute", top: 80, right: 80, transform: "rotate(-12deg)" }} />

            <div style={{ position: "relative", zIndex: 1, maxWidth: 480 }}>
              <span style={{ display: "inline-flex", alignItems: "center", gap: 8, padding: "6px 12px", borderRadius: 999, background: "rgba(255,255,255,.12)", fontSize: 12, fontWeight: 600, letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 24 }}>
                <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#F5EB3F" }} />
                {T.rightBadge}
              </span>

              <h2 style={{ fontFamily: "var(--font-display)", fontSize: 44, fontWeight: 600, letterSpacing: "-0.02em", lineHeight: 1.1, marginBottom: 20 }}>
                {T.rightHeading} <span style={{ background: "linear-gradient(180deg, transparent 60%, #F5EB3F 60%)", padding: "0 4px" }}>{T.rightHeadingHl}</span>.
              </h2>
              <p style={{ fontSize: 16, color: "rgba(255,255,255,.8)", lineHeight: 1.6, marginBottom: 40 }}>
                {T.rightSub}
              </p>

              <div style={{ display: "grid", gap: 14 }}>
                {T.features.map((it, i) => (
                  <div key={i} style={{ display: "flex", gap: 14, alignItems: "flex-start", padding: "14px 16px", borderRadius: 14, background: "rgba(255,255,255,.06)", border: "1px solid rgba(255,255,255,.10)" }}>
                    <div style={{ width: 32, height: 32, borderRadius: 10, background: "#FD6936", display: "grid", placeItems: "center", flexShrink: 0 }}>
                      <Icon.check style={{ width: 16, height: 16, color: "white" }} />
                    </div>
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 2 }}>{it.t}</div>
                      <div style={{ fontSize: 13, color: "rgba(255,255,255,.65)" }}>{it.d}</div>
                    </div>
                  </div>
                ))}
              </div>

              <div style={{ marginTop: 40, paddingTop: 30, borderTop: "1px solid rgba(255,255,255,.12)", display: "flex", gap: 30 }}>
                {[
                  { n: "98%", l: isEnfant ? "Ados satisfaits" : "Parents satisfaits" },
                  { n: "+300", l: "Ados orientés" },
                  { n: "9/10", l: "Recommandent" },
                ].map((s, i) => (
                  <div key={i}>
                    <div style={{ fontFamily: "var(--font-num)", fontSize: 28, fontWeight: 700, color: "#F5EB3F" }}>{s.n}</div>
                    <div style={{ fontSize: 12, color: "rgba(255,255,255,.7)", marginTop: 2 }}>{s.l}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      );
    };

    ReactDOM.createRoot(document.getElementById("root")).render(<AuthPage />);
  """


def encode_template(tpl_str: str) -> str:
    """JSON-encode the inner template, then escape </script> so the outer
    <script type="__bundler/template">...</script> tag stays well-formed."""
    raw = json.dumps(tpl_str, ensure_ascii=False)
    return raw.replace("</script>", r"<\/script>")


def extract_template(html: str):
    """Return (start_idx, end_idx, tpl_str). Uses rfind to be tolerant of a
    previous bad patch that left literal </script> inside the JSON.
    Assumes the template tag is the LAST <script>...</script> in the file."""
    start_m = re.search(r'<script[^>]*type="__bundler/template"[^>]*>', html)
    if not start_m:
        return None
    last_close = html.rfind("</script>")
    if last_close <= start_m.end():
        return None
    raw = html[start_m.end():last_close]
    tpl = json.loads(raw.strip())
    return start_m.end(), last_close, tpl


def patch():
    html = TARGET.read_text(encoding="utf-8")

    ext = extract_template(html)
    if ext is None:
        print("ERROR: no __bundler/template script in connexion.html", file=sys.stderr)
        sys.exit(1)
    s, e, tpl = ext

    if NEW_MARKER in tpl:
        print("- already patched (AuthPage marker present); re-encoding to ensure escapes are correct")
        new_tpl = tpl
    else:
        if "const LoginPage = () =>" not in tpl:
            print("ERROR: expected LoginPage component not found", file=sys.stderr)
            sys.exit(1)

        babel_re = re.compile(r'(<script type="text/babel">)(.*?)(</script>)', flags=re.S)
        replaced = 0

        def repl(mm):
            nonlocal replaced
            body = mm.group(2)
            if "const LoginPage" in body:
                replaced += 1
                return mm.group(1) + NEW_BABEL_SCRIPT + mm.group(3)
            return mm.group(0)

        new_tpl = babel_re.sub(repl, tpl)
        if replaced != 1:
            print(f"ERROR: replaced {replaced} babel scripts, expected 1", file=sys.stderr)
            sys.exit(1)

    new_raw = encode_template(new_tpl)
    new_html = html[:s] + new_raw + html[e:]
    TARGET.write_text(new_html, encoding="utf-8")
    print(f"+ patched connexion.html (template now {len(new_tpl)} chars, encoded {len(new_raw)} bytes)")


if __name__ == "__main__":
    patch()

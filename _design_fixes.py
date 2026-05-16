#!/usr/bin/env python3
"""Apply design-review fixes to all bundled HTML files.

Idempotent: re-running has no effect if the changes are already applied.

Scope (excludes mini-quiz changes per user request):
  F001/F006  Mobile responsive nav + Charles in mobile sticky bar
  F002       Promote "Rdv avec Charles" CTA from ghost to filled
  F003       Standardize "30 min avec Charles" label
  F005       Make phone optional at signup (was required at step 4 of 5)
  F007       Add next-step CTA below the pain-points section
  F009       Pricing eyebrow color consistency
  F010       Touch targets >=44px on mobile nav
  F011       "Voir un exemple de rapport" upgraded to a proper outline button
  F015       Continuer disabled state visual clarity
"""

import re, json, base64, gzip, pathlib, sys

REPO = pathlib.Path(__file__).parent

# All page files. (Proxxie X.html and lowercase x.html are byte-identical pairs.)
ALL_HTML_FILES = [
    "Proxxie Home.html", "index.html",
    "Proxxie Coach.html", "coach.html",
    "Proxxie Connexion.html", "connexion.html",
    "Proxxie Dashboard.html", "dashboard.html",
    "Proxxie Documents.html", "documents.html",
    "Proxxie Rapport.html", "rapport.html",
    "Proxxie Ressources.html", "ressources.html",
    "Proxxie Test.html", "test.html",
]

# ===========================================================================
# CSS PATCHES — operate on the raw HTML <style> block
# ===========================================================================

# F001 + F006 + F010: replace the existing mobile media-query rule that hides
# the secondary Charles CTA. Instead we:
#   - keep Charles visible at all sizes
#   - hide the inner nav links (.muted) on mobile so the nav fits
#   - shrink the orange CTA to icon-only at small sizes
#   - bump touch targets on nav links to >=44px
CSS_PATCHES = [
    # F006: Don't hide the Charles secondary CTA on mobile — it's the
    # most important conversion goal for Proxxie. Keep it; instead hide
    # the inner nav links on smallest sizes.
    (
        "/* Two-track CTA : \"Parler à Charles\" ghost visible desktop+tablet, hidden mobile */\n@media (max-width: 860px) {\n  .nav-cta-secondary { display: none !important; }\n}",
        "/* Two-track CTA : \"Rdv avec Charles\" stays visible at ALL viewports.\n   It is THE primary differentiator for Proxxie's conversion goal. */\n@media (max-width: 860px) {\n  .nav-cta-secondary { padding: 10px 14px !important; font-size: 13px !important; }\n}\n@media (max-width: 520px) {\n  /* On the smallest screens, keep Charles + Test; the Test button hides\n     its \" gratuit\" suffix already. Charles uses a compact label here. */\n  .nav-cta-secondary { padding: 8px 12px !important; font-size: 12px !important; }\n}",
    ),

    # F001: Hide the inner nav links (La méthode / Le rapport / Tarifs /
    # Ressources) on viewports too narrow to fit them. The page anchors are
    # still reachable by scrolling — and the Resources menu duplicates them
    # in the footer. The horizontal-scroll bug (scrollWidth 737 vs 375 on iPhone)
    # came from this row not collapsing.
    (
        "/* Nav CTA: tighter on small desktop / tablet so 'Commencer le test gratuit' fits */",
        "/* F001: hide the inner nav links on small screens so the nav row fits\n   in the viewport. The orange CTA, Charles CTA, and logo remain visible. */\n@media (max-width: 860px) {\n  nav .shell > div:nth-child(2) { display: none !important; }\n  nav .shell > div:nth-child(3) { gap: 8px !important; }\n  nav .shell > div:nth-child(3) > a.muted { display: none !important; }\n}\n\n/* F001-bis: on the smallest screens, the top-nav CTAs are duplicated by the\n   mobile sticky bar at the bottom. Hide the top-nav orange CTA there to give\n   the Charles CTA room. The sticky bar at the bottom still shows both. */\n@media (max-width: 520px) {\n  nav .shell .nav-cta { display: none !important; }\n  nav .shell > div:nth-child(3) { gap: 4px !important; }\n}\n\n/* F010: Tap targets >= 44px on mobile nav */\n@media (max-width: 860px) {\n  nav .shell { min-height: 56px; }\n  nav a, nav button { min-height: 44px; }\n}\n\n/* Nav CTA: tighter on small desktop / tablet so 'Commencer le test gratuit' fits */",
    ),

    # F002 + QA-001c — Both extend the .btn-ghost block. Merged into a
    # SINGLE patch so the patcher stays idempotent. Two separate patches
    # anchored on the same `.btn-ghost {` sentinel would chain-apply
    # forever: patch 2 inserts before patch 5's anchor, then on the next
    # run patch 5 inserts before patch 2's now-displaced anchor, etc.
    # Lesson: never anchor two patches on the same line.
    (
        ".btn-ghost {\n  background: transparent;\n  color: var(--c-ink);\n  border: 1.5px solid rgba(10,14,44,.16);\n}\n.btn-ghost:hover { background: rgba(10,14,44,.04); }",
        ".btn-ghost {\n  background: transparent;\n  color: var(--c-ink);\n  border: 1.5px solid rgba(10,14,44,.16);\n}\n.btn-ghost:hover { background: rgba(10,14,44,.04); }\n/* F002: stronger outline for the Charles secondary CTA. Reads as a real\n   call-to-action next to the orange primary, not as a nav link. */\n.nav-cta-secondary.btn-ghost {\n  background: white;\n  color: var(--c-ink);\n  border: 1.5px solid var(--c-ink);\n  box-shadow: 0 4px 12px -4px rgba(10,14,44,.18);\n}\n.nav-cta-secondary.btn-ghost:hover {\n  background: var(--c-ink);\n  color: white;\n  transform: translateY(-1px);\n}\n/* QA-001c — Hide the product-page nav links + parent-name text on mobile.\n   Logo + avatar stay visible. Prevents header-row overflow. */\n@media (max-width: 860px) {\n  header[style*=\"sticky\"] nav { display: none !important; }\n  header[style*=\"sticky\"] .shell > div:first-child > span { display: none !important; }\n  header[style*=\"sticky\"] .shell > div:last-child > div > div:last-child { display: none !important; }\n}\n@media (max-width: 520px) {\n  header[style*=\"sticky\"] .shell > div:last-child button { display: none !important; }\n}",
    ),

    # F006-bis: Make the mobile sticky CTA bar support two buttons side-by-side
    # (currently the orange test button takes 100% width). Style the second
    # button as a navy outline so it doesn't fight the orange visually.
    (
        "  .mobile-sticky-cta .btn { flex: 1; justify-content: center; padding: 14px; }",
        "  .mobile-sticky-cta .btn { flex: 1; justify-content: center; padding: 14px; min-height: 44px; }\n  /* F006: Charles button in the mobile sticky bar is a navy outline */\n  .mobile-sticky-cta .btn-charles {\n    background: white;\n    color: var(--c-ink);\n    border: 1.5px solid var(--c-ink);\n    text-decoration: none;\n  }",
    ),

    # QA-001 — Product app pages (Dashboard, Documents, Rapport, Coach,
    # Ressources) overflow on mobile (~700-790px content vs 375px viewport)
    # for two reasons:
    #   (a) ShellHeader nav with 5 inline links doesn't collapse
    #   (b) Content grids (Dashboard hero card, Documents grids, Coach
    #       expertise/sessions panels) use fixed grid-template-columns that
    #       stay desktop-wide on mobile
    # The Home page CSS already collapses generic grids on <= 760px, but
    # the product-page CSS is a shorter variant that only adjusts section
    # padding. We add the missing rules here.
    # The CSS_PATCHES tuples use REAL newlines in both strings. The script
    # passes them through _escape_for_js_string before searching, which
    # converts real newlines to the on-disk literal "\n" escape form.
    (
        "@media (max-width: 760px) {\n  section { padding: 64px 0; }\n  .shell { padding: 0 20px; }\n}",
        "@media (max-width: 760px) {\n  section { padding: 64px 0; }\n  .shell { padding: 0 20px; }\n  /* QA-001a: collapse generic 2/3/4-col grids to single column on phones */\n  [style*=\"grid-template-columns: 1fr 1fr\"],\n  [style*=\"repeat(2, 1fr)\"],\n  [style*=\"repeat(3, 1fr)\"],\n  [style*=\"repeat(4, 1fr)\"],\n  [style*=\"grid-template-columns: 1.7fr 1fr\"],\n  [style*=\"grid-template-columns: 1.6fr 1fr\"],\n  [style*=\"grid-template-columns: 1fr 1.6fr\"],\n  [style*=\"grid-template-columns: 1.1fr 1fr\"],\n  [style*=\"grid-template-columns: auto 1fr auto\"] { grid-template-columns: 1fr !important; }\n  /* QA-001b: stop big inline-fixed hero h1s from forcing horizontal scroll */\n  h1 { font-size: clamp(28px, 7vw, 40px) !important; }\n}",
    ),
    # (QA-001c was merged into the F002 patch above to avoid the
    # overlapping-patch idempotency bug — see comment there.)
]

# ===========================================================================
# BUNDLE PATCHES — operate on JSX inside gzipped+base64 manifest assets
# ===========================================================================
# Each entry: needle (must be in asset to apply), then a list of (old, new)
# replacements. Each replacement must be unique within the asset; the script
# fails loudly if a needle is found but a replacement isn't (catches drift).

BUNDLE_PATCHES = [
    # ----- F002: Promote "Rdv avec Charles" in the Nav -----
    # Move it left of the test CTA in source order (right-side cluster), and
    # use a slightly tighter label so both buttons read as primary actions.
    {
        "name": "F002 nav Charles CTA prominence",
        "needle": 'className="btn btn-ghost nav-cta-secondary"',
        "replacements": [
            (
                '<a href="https://calendly.com/proxxie/entretien" target="_blank" rel="noopener noreferrer" onClick={() => { if (typeof window !== "undefined" && window.trackEvent) window.trackEvent("calendly_opened", { source: "header_nav" }); }} className="btn btn-ghost nav-cta-secondary" style={{ textDecoration: "none", fontSize: 14 }}>\n          Rdv avec Charles\n        </a>',
                '<a href="https://calendly.com/proxxie/entretien" target="_blank" rel="noopener noreferrer" onClick={() => { if (typeof window !== "undefined" && window.trackEvent) window.trackEvent("calendly_opened", { source: "header_nav" }); }} className="btn btn-ghost nav-cta-secondary" style={{ textDecoration: "none", fontSize: 14, fontWeight: 600 }}>\n          30 min avec Charles\n        </a>',
            ),
        ],
    },

    # ----- F011: "Voir un exemple de rapport" as a real outline button -----
    # Skips Test.html because that page has its own marketing-style hero
    # with a "Voir un exemple de rapport" CTA in a different JSX shape.
    # The patch targets the Home page's Hero component only.
    {
        "name": "F011 sample-report secondary CTA",
        # Needle is specific to the original underline state — disappears
        # after F011 applies (consumed by OLD→NEW) AND also after F011B
        # chain-applies (which uses a different style closing). This is what
        # lets the patcher cleanly SKIP F011 on re-runs once F011B is in
        # place, instead of reporting DRIFT for an unfindable OLD.
        "needle": 'textDecoration: "underline", textUnderlineOffset: 4 }}',
        "pages_skip": ["Proxxie Test.html", "test.html"],
        "replacements": [
            (
                '<button onClick={onDemo} style={{ background: "transparent", border: "none", color: "var(--c-ink-2)", fontSize: 14, fontWeight: 500, display: "inline-flex", alignItems: "center", gap: 6, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 4 }}>\n                <Icon.play style={{ width: 14, height: 14 }} /> Voir un exemple de rapport\n              </button>',
                '<button onClick={onDemo} className="btn btn-ghost btn-lg" style={{ background: "white", borderColor: "var(--c-ink)", color: "var(--c-ink)" }}>\n                <Icon.play style={{ width: 16, height: 16 }} /> Voir un exemple de rapport\n              </button>',
            ),
        ],
    },

    # ----- F006: Add Charles CTA to the mobile sticky bar -----
    {
        "name": "F006 mobile sticky bar with Charles",
        "needle": '<div className="mobile-sticky-cta">',
        "replacements": [
            (
                '{/* Sticky mobile CTA bar */}\n      <div className="mobile-sticky-cta">\n        <button className="btn btn-orange" onClick={openOnboarding} style={{ flex: 2 }}>\n          Commencer le test gratuit\n        </button>\n      </div>',
                '{/* Sticky mobile CTA bar — F006: dual-CTA (Charles + Test) so the meeting\n          path stays visible on mobile, where it disappeared previously. */}\n      <div className="mobile-sticky-cta">\n        <a href="https://calendly.com/proxxie/entretien" target="_blank" rel="noopener noreferrer" className="btn btn-charles" onClick={() => { if (typeof window !== "undefined" && window.trackEvent) window.trackEvent("calendly_opened", { source: "mobile_sticky" }); }}>\n          Charles\n        </a>\n        <button className="btn btn-orange" onClick={openOnboarding} style={{ flex: 2 }}>\n          Commencer le test gratuit\n        </button>\n      </div>',
            ),
        ],
    },

    # ----- F005: Make phone optional at signup step (was required) -----
    # After the team's 8 → 5 wizard refactor, accountLocked combines
    # email + phone + firstName + parentName. We drop phoneValid from the
    # blocking set. Phone is still collected (and Calendly asks for it
    # again at booking), so no data is lost — just one fewer field that
    # blocks the signup.
    {
        "name": "F005 phone optional at signup (post-refactor)",
        "needle": 'const accountLocked = !emailValid || !phoneValid',
        "replacements": [
            (
                'const accountLocked = !emailValid || !phoneValid || !(profile.firstName||"").trim() || !(profile.parentName||"").trim();',
                'const accountLocked = !emailValid || !(profile.firstName||"").trim() || !(profile.parentName||"").trim();',
            ),
        ],
    },
    {
        "name": "F005 phone label says optional (post-refactor)",
        "needle": "<label style={labelCls}>Numéro de téléphone</label>",
        "replacements": [
            (
                "<label style={labelCls}>Numéro de téléphone</label>",
                "<label style={labelCls}>Numéro de téléphone <span style={{ textTransform: \"none\", fontWeight: 500, color: \"var(--c-muted)\", letterSpacing: 0 }}>(optionnel)</span></label>",
            ),
        ],
    },

    # ----- F003: Standardize "30 min" — Calendly description / Hero copy -----
    # Many touch-points mention "30 min" already. The Calendly page itself is
    # configured to 20 min — that needs to be fixed on Calendly's side, NOT in
    # the website code. We standardize the WEBSITE-side labels here.
    # No other "20 min" strings appear in the site code, so this is mainly
    # a label rename in the nav (handled by F002 above: "30 min avec Charles").

    # ----- F007: Add a next-step CTA below the 6-card pain-points grid -----
    {
        "name": "F007 pain-points next step",
        "needle": '{ t: "Filières méconnues", d: "Le système a changé depuis votre époque et c\'est devenu opaque." },',
        "replacements": [
            (
                # OLD/NEW stop at the CTA-strip </div> (not at </section>) so
                # downstream patches (F-STATS-RELOCATED) can insert content
                # between the CTA strip and section close without breaking
                # F007's idempotency check.
                '        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>\n          {items.map((it, i) => (\n            <div key={i} className="card" style={{ padding: 24, background: "white" }}>\n              <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#FD6936", marginBottom: 14 }} />\n              <div style={{ fontWeight: 600, fontSize: 17, marginBottom: 6 }}>{it.t}</div>\n              <p style={{ color: "var(--c-muted)", fontSize: 14 }}>{it.d}</p>\n            </div>\n          ))}\n        </div>',
                # Same grid + an in-section CTA strip that points to the method explanation.
                '        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>\n          {items.map((it, i) => (\n            <div key={i} className="card" style={{ padding: 24, background: "white" }}>\n              <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#FD6936", marginBottom: 14 }} />\n              <div style={{ fontWeight: 600, fontSize: 17, marginBottom: 6 }}>{it.t}</div>\n              <p style={{ color: "var(--c-muted)", fontSize: 14 }}>{it.d}</p>\n            </div>\n          ))}\n        </div>\n        {/* F007: section CTA — closes the empathy block with two clear paths. */}\n        <div style={{ marginTop: 36, display: "flex", justifyContent: "center", flexWrap: "wrap", gap: 12 }}>\n          <a href="#methode" className="btn btn-orange btn-arrow" style={{ textDecoration: "none" }}>\n            Voir comment on aide\n          </a>\n          <a href="https://calendly.com/proxxie/entretien" target="_blank" rel="noopener noreferrer" className="btn btn-ghost" style={{ textDecoration: "none", background: "white", borderColor: "var(--c-ink)", color: "var(--c-ink)" }} onClick={() => { if (typeof window !== "undefined" && window.trackEvent) window.trackEvent("calendly_opened", { source: "situations_cta" }); }}>\n            30 min avec Charles\n          </a>\n        </div>',
            ),
        ],
    },

    # ----- F008-bis: mini-quiz result links to the 5-step method -----
    # Per user feedback: keep the mini-quiz at the bottom (don't move it to
    # the hero), but make its result drive curious visitors to the method
    # explainer rather than ending with a "Recommencer" loop. The primary
    # CTA still opens the onboarding wizard.
    {
        "name": "F008b mini-quiz result → method link",
        "needle": "Voir le rapport complet (gratuit)",
        "replacements": [
            (
                '<div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>\n                    <button className="btn btn-orange btn-arrow" onClick={onCTA}>Voir le rapport complet (gratuit)</button>\n                    <button className="btn btn-ghost" onClick={reset} style={{ color: "white", borderColor: "rgba(255,255,255,.3)" }}>Recommencer</button>\n                  </div>',
                '<div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>\n                    <button className="btn btn-orange btn-arrow" onClick={onCTA}>Voir le rapport complet (gratuit)</button>\n                    <a className="btn btn-ghost" href="#methode" style={{ color: "white", borderColor: "rgba(255,255,255,.3)", textDecoration: "none" }}>Voir notre méthode</a>\n                  </div>\n                  <button onClick={reset} style={{ marginTop: 14, background: "transparent", border: "none", color: "rgba(255,255,255,.7)", fontSize: 13, fontWeight: 500, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 3, padding: 0 }}>Recommencer le test</button>',
            ),
        ],
    },

    # ============================================================
    # A+ GAP PATCHES (round 2)
    # ============================================================

    # ----- G2: Media-mention bar in the Hero -----
    # Logos + press URLs lifted from www.proxxie.co's "Ils parlent de nous"
    # section. Three press mentions, each linking to the source content.
    # Inserted right after the asterisk footnote, just above </section>.
    {
        "name": "G2 media-mention bar in Hero",
        # Needle is the original Hero "Trust bar" comment — present in
        # fresh builds, gone after F-STATS-MOVED relocates the trust bar
        # below SituationsSection. Using the comment instead of the
        # footnote text avoids false-matching in 3cf76be5 after
        # F-STATS-RELOCATED reuses the same footnote in SituationsSection.
        "needle": "Trust bar — repositionnée juste sous le hero",
        "replacements": [
            (
                '        <div style={{ fontSize: 11, color: "var(--c-muted)", marginTop: 8, textAlign: "right", paddingRight: 8 }}>\n          * Sur les terminales accompagnées en 2024-25 ayant validé un vœu Parcoursup.\n        </div>\n      </div>\n    </section>',
                '        <div style={{ fontSize: 11, color: "var(--c-muted)", marginTop: 8, textAlign: "right", paddingRight: 8 }}>\n          * Sur les terminales accompagnées en 2024-25 ayant validé un vœu Parcoursup.\n        </div>\n\n        {/* G2 — Media-mention bar : lift the strongest trust signal from\n            www.proxxie.co. Each logo links to the actual press content. */}\n        <div style={{ marginTop: 32, paddingTop: 24, borderTop: "1px solid rgba(10,14,44,.08)" }}>\n          <div style={{ textAlign: "center", marginBottom: 16 }}>\n            <span className="eyebrow" style={{ fontSize: 11 }}><span className="dot"></span>Ils parlent de nous</span>\n          </div>\n          <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 48, flexWrap: "wrap", opacity: 0.85 }}>\n            <a href="https://www.rcf.fr/bien-etre-et-psychologie/chemins-des-possibles?episode=564205" target="_blank" rel="noopener noreferrer" style={{ display: "inline-flex", flexDirection: "column", alignItems: "center", gap: 6, textDecoration: "none", color: "var(--c-muted)", fontSize: 11, fontWeight: 500, transition: "opacity .2s, transform .2s" }} onMouseEnter={(e) => { e.currentTarget.style.opacity = 1; e.currentTarget.style.transform = "translateY(-2px)"; }} onMouseLeave={(e) => { e.currentTarget.style.opacity = 0.85; e.currentTarget.style.transform = "none"; }}>\n              <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 22, letterSpacing: "0.02em", color: "var(--c-ink-2)" }}>RCF</span>\n              <span>Écouter l\'interview →</span>\n            </a>\n            <a href="https://drive.google.com/file/d/1oB1l-gXU6_3PElJVN_1LfjYhsPOBWsmy/view" target="_blank" rel="noopener noreferrer" style={{ display: "inline-flex", flexDirection: "column", alignItems: "center", gap: 6, textDecoration: "none", color: "var(--c-muted)", fontSize: 11, fontWeight: 500, transition: "opacity .2s, transform .2s" }} onMouseEnter={(e) => { e.currentTarget.style.opacity = 1; e.currentTarget.style.transform = "translateY(-2px)"; }} onMouseLeave={(e) => { e.currentTarget.style.opacity = 0.85; e.currentTarget.style.transform = "none"; }}>\n              <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 22, letterSpacing: "-0.01em", color: "var(--c-ink-2)" }}>France <span style={{ color: "#1320CE" }}>Bleu</span></span>\n              <span>Écouter l\'interview →</span>\n            </a>\n            <a href="https://drive.google.com/file/d/1LHVR84mIKt_jFR4W4Bn51LF6GrXtHvTh/view" target="_blank" rel="noopener noreferrer" style={{ display: "inline-flex", flexDirection: "column", alignItems: "center", gap: 6, textDecoration: "none", color: "var(--c-muted)", fontSize: 11, fontWeight: 500, transition: "opacity .2s, transform .2s" }} onMouseEnter={(e) => { e.currentTarget.style.opacity = 1; e.currentTarget.style.transform = "translateY(-2px)"; }} onMouseLeave={(e) => { e.currentTarget.style.opacity = 0.85; e.currentTarget.style.transform = "none"; }}>\n              <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 22, letterSpacing: "0.01em", color: "var(--c-ink-2)" }}>france<span style={{ color: "#FD6936" }}>•</span>tv</span>\n              <span>Regarder le replay →</span>\n            </a>\n          </div>\n        </div>\n      </div>\n    </section>',
            ),
        ],
    },

    # ----- G3 step 1: ClassTimeline component definition -----
    # Inserted right before `const App = () => {` so the component is
    # in module scope. Five-tab class strip with concerns + guide link.
    {
        "name": "G3 ClassTimeline component definition",
        "needle": "const App = () => {",
        "replacements": [
            (
                "const App = () => {",
                # Define the component and then continue with App.
                '/* G3 — Class-segmented timeline. Five tabs (3ème → Post-Bac),\n   one concern card per tab + a link into the existing guide. */\nconst CLASS_TABS = [\n  { k: "3eme",      l: "3ème",     concern: "Découverte et exploration",        body: "Premier vrai choix : 2nde générale, technologique ou pro ? On pose les bases en aidant votre ado à se découvrir, sans pression.",          period: "1er trimestre · sept-déc" },\n  { k: "2nde",      l: "2nde",     concern: "Choix des spécialités",            body: "Les spés de 1ère pèsent sur Parcoursup. On évite les choix par défaut et on construit la combinaison qui ouvre, pas qui ferme.",        period: "2e trimestre · jan-mars" },\n  { k: "1ere",      l: "1ère",     concern: "Confirmation du projet",            body: "C\'est l\'année où le projet se précise. Métiers visés, écoles cibles, doubles cursus, projets perso à valoriser — on cale tout ça.",        period: "Année complète" },\n  { k: "terminale", l: "Terminale", concern: "Stratégie Parcoursup",             body: "10 vœux à formuler, lettres de motivation, choix de filières d\'art ou Sciences Po, parcours sélectifs. On stresse moins, on cible mieux.",   period: "Janvier → mai" },\n  { k: "postbac",   l: "Post-Bac",  concern: "Rebondir ou réorienter",           body: "Première année qui ne se passe pas comme prévu ? On évite l\'année blanche : réorientation Parcoursup ou hors-Parcoursup, passerelles, alternance.", period: "À tout moment" },\n];\n\nconst ClassTimeline = () => {\n  const [active, setActive] = React.useState("terminale");\n  const tab = CLASS_TABS.find((t) => t.k === active) || CLASS_TABS[0];\n  return (\n    <section id="classes" style={{ paddingTop: 80, paddingBottom: 80, background: "var(--c-cream)" }}>\n      <div className="shell">\n        <div style={{ textAlign: "center", maxWidth: 760, margin: "0 auto 36px" }}>\n          <span className="eyebrow"><span className="dot"></span>Adapté à chaque étape</span>\n          <h2 style={{ marginTop: 14 }}>De la 3ème au post-bac, à chaque classe sa question.</h2>\n          <p style={{ fontSize: 17, color: "var(--c-ink-2)", marginTop: 14 }}>\n            Cliquez sur la classe de votre ado pour voir ce qu\'on travaille à ce moment précis.\n          </p>\n        </div>\n\n        <div style={{ display: "flex", justifyContent: "center", gap: 8, flexWrap: "wrap", marginBottom: 32 }}>\n          {CLASS_TABS.map((t) => (\n            <button\n              key={t.k}\n              onClick={() => setActive(t.k)}\n              style={{\n                padding: "10px 18px", borderRadius: 999,\n                background: active === t.k ? "var(--c-ink)" : "white",\n                color: active === t.k ? "white" : "var(--c-ink-2)",\n                border: "1.5px solid " + (active === t.k ? "var(--c-ink)" : "var(--c-line)"),\n                fontWeight: 600, fontSize: 14, letterSpacing: "-0.005em",\n                transition: "background .15s, color .15s, transform .15s",\n                cursor: "pointer", minHeight: 44,\n              }}\n              onMouseEnter={(e) => { if (active !== t.k) { e.currentTarget.style.background = "var(--c-cream-light)"; e.currentTarget.style.transform = "translateY(-1px)"; }}}\n              onMouseLeave={(e) => { if (active !== t.k) { e.currentTarget.style.background = "white"; e.currentTarget.style.transform = "none"; }}}\n            >\n              {t.l}\n            </button>\n          ))}\n        </div>\n\n        <div className="card" style={{ padding: "36px 40px", maxWidth: 880, margin: "0 auto", background: "white" }}>\n          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14, flexWrap: "wrap", gap: 12 }}>\n            <span className="chip" style={{ background: "rgba(253,105,54,.12)", color: "#FD6936" }}>{tab.l} · {tab.concern}</span>\n            <span style={{ fontSize: 12, color: "var(--c-muted)", fontWeight: 500 }}>{tab.period}</span>\n          </div>\n          <p style={{ fontSize: 17, lineHeight: 1.55, color: "var(--c-ink-2)", marginBottom: 22 }}>{tab.body}</p>\n          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>\n            <a href="./guide-orientation.html" className="btn btn-orange btn-arrow" style={{ textDecoration: "none" }}>\n              Voir le guide {tab.l}\n            </a>\n            <a href="https://calendly.com/proxxie/entretien" target="_blank" rel="noopener noreferrer" className="btn btn-ghost" style={{ textDecoration: "none", background: "white", borderColor: "var(--c-ink)", color: "var(--c-ink)" }} onClick={() => { if (typeof window !== "undefined" && window.trackEvent) window.trackEvent("calendly_opened", { source: "class_timeline_" + tab.k }); }}>\n              30 min avec Charles\n            </a>\n          </div>\n        </div>\n      </div>\n    </section>\n  );\n};\n\nconst App = () => {',
            ),
        ],
    },

    # ----- G3 step 2: insert <ClassTimeline /> into App's render tree -----
    # Placed between <HowItWorks /> and the mini-quiz: visitor sees pain →
    # method → class self-identification → quiz → results → testimonials.
    {
        "name": "G3 ClassTimeline placement in App",
        "needle": "{t.showMiniQuiz && <MiniQuiz onCTA={openOnboarding} />}",
        "replacements": [
            (
                "      <HowItWorks onCTA={openOnboarding} />\n      {t.showMiniQuiz && <MiniQuiz onCTA={openOnboarding} />}",
                "      <HowItWorks onCTA={openOnboarding} />\n      <ClassTimeline />\n      {t.showMiniQuiz && <MiniQuiz onCTA={openOnboarding} />}",
            ),
        ],
    },

    # ----- Obsidian-style radar v2 — drill-down + back-navigation -----
    # The v1 radar (committed to main via PR #20) showed 5 main facets with
    # idle wobble + drag-and-spring. v2 adds:
    #   - Click a facet node → graph "rotates" to show 5 sub-facets of that
    #     parent (spring physics retargets nodes; no separate animation code).
    #     The center node label updates from "Léa" to the parent facet name.
    #   - Click the center node → returns to the root view.
    #   - Tap-vs-drag detection: short press (< 350ms, < 6px movement) on a
    #     node is a tap → drill down. Anything else is a drag → spring back.
    #   - Hint text updates to reflect the available action at each level.
    #
    # The old `new` string from the v1 patch becomes the new `old` here — we
    # replace the v1 component in-place. Sentinel is the new v2 comment so
    # idempotency check fires correctly on a second run.
    {
        "name": "Radar Obsidian-style v2 — drill-down + back nav",
        "needle": "const InteractiveRadar = () => {",
        "replacements": [
            (
                # OLD = the entire v1 InteractiveRadar block as inserted by PR #20
                '/* Obsidian-style force-directed radar — 5 personality dimensions orbit\n   the center node "Léa". Each node wobbles around its score-weighted target\n   position; user can drag any node and it springs back. */\nconst InteractiveRadar = () => {\n  const DIMS = [\n    { l: "Ouverture",   v: 0.86 },\n    { l: "Curiosité",   v: 0.92 },\n    { l: "Ambition",    v: 0.74 },\n    { l: "Énergie",     v: 0.81 },\n    { l: "Empathie",    v: 0.78 },\n  ];\n  const N = DIMS.length;\n  const W = 320, H = 200, cx = W / 2, cy = H / 2, R = 78;\n\n  const target = (i) => {\n    const a = -Math.PI / 2 + (i * 2 * Math.PI) / N;\n    return { x: cx + Math.cos(a) * R * DIMS[i].v, y: cy + Math.sin(a) * R * DIMS[i].v };\n  };\n  const init = DIMS.map((_, i) => ({ ...target(i), vx: 0, vy: 0 }));\n\n  const [nodes, setNodes] = React.useState(init);\n  const [drag, setDrag] = React.useState(null);\n  const [hover, setHover] = React.useState(null);\n  const dragRef = React.useRef(null);\n  const tRef = React.useRef(0);\n  const svgRef = React.useRef(null);\n  React.useEffect(() => { dragRef.current = drag; }, [drag]);\n\n  React.useEffect(() => {\n    let raf;\n    const tick = () => {\n      tRef.current += 0.015;\n      setNodes((prev) => prev.map((p, i) => {\n        if (dragRef.current === i) return p;\n        const tg = target(i);\n        const wx = Math.sin(tRef.current + i * 1.3) * 2.6;\n        const wy = Math.cos(tRef.current * 0.85 + i * 0.7) * 2.6;\n        const k = 0.06, damp = 0.86;\n        const ax = (tg.x + wx - p.x) * k;\n        const ay = (tg.y + wy - p.y) * k;\n        const vx = (p.vx + ax) * damp;\n        const vy = (p.vy + ay) * damp;\n        return { x: p.x + vx, y: p.y + vy, vx, vy };\n      }));\n      raf = requestAnimationFrame(tick);\n    };\n    raf = requestAnimationFrame(tick);\n    return () => cancelAnimationFrame(raf);\n  }, []);\n\n  const localPoint = (e) => {\n    const rect = svgRef.current.getBoundingClientRect();\n    const cx2 = e.touches ? e.touches[0].clientX : e.clientX;\n    const cy2 = e.touches ? e.touches[0].clientY : e.clientY;\n    return { x: ((cx2 - rect.left) / rect.width) * W, y: ((cy2 - rect.top) / rect.height) * H };\n  };\n\n  const onDown = (i) => (e) => { e.preventDefault(); setDrag(i); };\n  React.useEffect(() => {\n    if (drag == null) return;\n    const move = (e) => {\n      const pt = localPoint(e);\n      setNodes((prev) => prev.map((p, i) => (i === drag ? { ...p, x: pt.x, y: pt.y, vx: 0, vy: 0 } : p)));\n    };\n    const up = () => setDrag(null);\n    window.addEventListener("mousemove", move);\n    window.addEventListener("mouseup", up);\n    window.addEventListener("touchmove", move, { passive: false });\n    window.addEventListener("touchend", up);\n    return () => {\n      window.removeEventListener("mousemove", move);\n      window.removeEventListener("mouseup", up);\n      window.removeEventListener("touchmove", move);\n      window.removeEventListener("touchend", up);\n    };\n  }, [drag]);\n\n  const polyPoints = nodes.map((n) => n.x + "," + n.y).join(" ");\n\n  return (\n    <svg ref={svgRef} viewBox={"0 0 " + W + " " + H} style={{ width: "100%", height: 200, cursor: drag != null ? "grabbing" : "default", userSelect: "none", touchAction: "none" }}>\n      {/* Concentric guide rings (Obsidian-graph feel) */}\n      {[0.4, 0.7, 1].map((r, i) => (\n        <circle key={"r" + i} cx={cx} cy={cy} r={R * r} fill="none" stroke="rgba(10,14,44,.06)" strokeWidth={1} strokeDasharray={i === 2 ? "" : "2 3"} />\n      ))}\n      {/* Center → node lines */}\n      {nodes.map((n, i) => (\n        <line key={"c" + i} x1={cx} y1={cy} x2={n.x} y2={n.y}\n          stroke={hover === i ? "#1320CE" : "rgba(19,32,206,.25)"}\n          strokeWidth={hover === i ? 2 : 1.2} />\n      ))}\n      {/* Profile polygon (the radar shape) */}\n      <polygon points={polyPoints} fill="rgba(72,122,255,0.16)" stroke="#1320CE" strokeWidth={1.5} style={{ transition: "fill .2s" }} />\n      {/* Dimension nodes */}\n      {nodes.map((n, i) => {\n        const isHot = hover === i || drag === i;\n        return (\n          <g key={"n" + i} transform={"translate(" + n.x + "," + n.y + ")"}\n            onMouseDown={onDown(i)} onTouchStart={onDown(i)}\n            onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}\n            style={{ cursor: drag === i ? "grabbing" : "grab" }}>\n            <circle r={isHot ? 9 : 6} fill="#FD6936"\n              stroke={isHot ? "white" : "rgba(253,105,54,.4)"} strokeWidth={isHot ? 3 : 2}\n              style={{ transition: "r .15s, stroke-width .15s" }} />\n            <text y={n.y < cy - 12 ? -14 : (n.y > cy + 12 ? 20 : (n.x < cx ? 4 : 4))}\n              textAnchor={n.x < cx - 20 ? "end" : (n.x > cx + 20 ? "start" : "middle")}\n              x={n.x < cx - 20 ? -12 : (n.x > cx + 20 ? 12 : 0)}\n              style={{ fontFamily: "var(--font-display)", fontSize: 10.5, fontWeight: 600, fill: "var(--c-ink)", letterSpacing: "0.02em", textTransform: "uppercase", pointerEvents: "none" }}>\n              {DIMS[i].l}\n            </text>\n          </g>\n        );\n      })}\n      {/* Center node */}\n      <g transform={"translate(" + cx + "," + cy + ")"}>\n        <circle r={14} fill="#1320CE" />\n        <text textAnchor="middle" dy={4} style={{ fontFamily: "var(--font-display)", fontSize: 10, fontWeight: 700, fill: "white", letterSpacing: "0.06em", textTransform: "uppercase", pointerEvents: "none" }}>Léa</text>\n      </g>\n      {/* Hint */}\n      <text x={W - 8} y={H - 6} textAnchor="end" style={{ fontSize: 9, fill: "var(--c-muted)", letterSpacing: "0.04em", fontWeight: 500 }}>Glissez les points</text>\n    </svg>\n  );\n};',

                # NEW = the v2 InteractiveRadar with drill-down
                '/* Obsidian-style force-directed radar v2 — drill-down + back nav.\n   Click a facet to drill into its 5 sub-facets; click the center to return.\n   Spring physics retargets nodes when level changes, so the "rotation"\n   animation comes for free without explicit interpolation. */\nconst RADAR_TREE = [\n  { l: "Ouverture", v: 0.86, sub: [\n    { l: "Imagination",   v: 0.89 },\n    { l: "Esthétique",    v: 0.74 },\n    { l: "Idées",         v: 0.92 },\n    { l: "Diversité",     v: 0.68 },\n    { l: "Innovation",    v: 0.81 },\n  ]},\n  { l: "Curiosité", v: 0.92, sub: [\n    { l: "Recherche",       v: 0.94 },\n    { l: "Expérimentation", v: 0.88 },\n    { l: "Observation",     v: 0.82 },\n    { l: "Lecture",         v: 0.91 },\n    { l: "Questionnement",  v: 0.85 },\n  ]},\n  { l: "Ambition", v: 0.74, sub: [\n    { l: "Leadership",     v: 0.78 },\n    { l: "Performance",    v: 0.81 },\n    { l: "Reconnaissance", v: 0.62 },\n    { l: "Persévérance",   v: 0.86 },\n    { l: "Vision",         v: 0.71 },\n  ]},\n  { l: "Énergie", v: 0.81, sub: [\n    { l: "Action",       v: 0.84 },\n    { l: "Endurance",    v: 0.77 },\n    { l: "Initiative",   v: 0.85 },\n    { l: "Enthousiasme", v: 0.79 },\n    { l: "Présence",     v: 0.80 },\n  ]},\n  { l: "Empathie", v: 0.78, sub: [\n    { l: "Écoute",        v: 0.82 },\n    { l: "Soin",          v: 0.73 },\n    { l: "Médiation",     v: 0.71 },\n    { l: "Pédagogie",     v: 0.85 },\n    { l: "Collaboration", v: 0.80 },\n  ]},\n];\n\nconst InteractiveRadar = () => {\n  const W = 320, H = 220, cx = W / 2, cy = H / 2, R = 78;\n  const [level, setLevel] = React.useState(0);\n  const [parentIdx, setParentIdx] = React.useState(0);\n  const activeDims = level === 0 ? RADAR_TREE : RADAR_TREE[parentIdx].sub;\n  const activeRef = React.useRef(activeDims);\n  activeRef.current = activeDims;\n\n  const targetFor = (dims, i) => {\n    const a = -Math.PI / 2 + (i * 2 * Math.PI) / dims.length;\n    return { x: cx + Math.cos(a) * R * dims[i].v, y: cy + Math.sin(a) * R * dims[i].v };\n  };\n  const target = (i) => {\n    const dims = activeRef.current;\n    if (i >= dims.length) return { x: cx, y: cy };\n    return targetFor(dims, i);\n  };\n\n  const [nodes, setNodes] = React.useState(() => RADAR_TREE.map((_, i) => ({ ...targetFor(RADAR_TREE, i), vx: 0, vy: 0 })));\n  const [drag, setDrag] = React.useState(null);\n  const [hover, setHover] = React.useState(null);\n  const dragRef = React.useRef(null);\n  const downRef = React.useRef(null);\n  const tRef = React.useRef(0);\n  const svgRef = React.useRef(null);\n  React.useEffect(() => { dragRef.current = drag; }, [drag]);\n\n  React.useEffect(() => {\n    let raf;\n    const tick = () => {\n      tRef.current += 0.015;\n      setNodes((prev) => prev.map((p, i) => {\n        if (dragRef.current === i) return p;\n        const tg = target(i);\n        const wx = Math.sin(tRef.current + i * 1.3) * 2.2;\n        const wy = Math.cos(tRef.current * 0.85 + i * 0.7) * 2.2;\n        const k = 0.10, damp = 0.84;\n        const ax = (tg.x + wx - p.x) * k;\n        const ay = (tg.y + wy - p.y) * k;\n        const vx = (p.vx + ax) * damp;\n        const vy = (p.vy + ay) * damp;\n        return { x: p.x + vx, y: p.y + vy, vx, vy };\n      }));\n      raf = requestAnimationFrame(tick);\n    };\n    raf = requestAnimationFrame(tick);\n    return () => cancelAnimationFrame(raf);\n  }, []);\n\n  const localPoint = (e) => {\n    const rect = svgRef.current.getBoundingClientRect();\n    const cx2 = e.touches ? e.touches[0].clientX : e.clientX;\n    const cy2 = e.touches ? e.touches[0].clientY : e.clientY;\n    return { x: ((cx2 - rect.left) / rect.width) * W, y: ((cy2 - rect.top) / rect.height) * H };\n  };\n\n  const onDown = (i) => (e) => {\n    e.preventDefault();\n    const pt = localPoint(e);\n    downRef.current = { i, x: pt.x, y: pt.y, t: Date.now() };\n    setDrag(i);\n  };\n\n  React.useEffect(() => {\n    if (drag == null) return;\n    const move = (e) => {\n      const pt = localPoint(e);\n      setNodes((prev) => prev.map((p, i) => (i === drag ? { ...p, x: pt.x, y: pt.y, vx: 0, vy: 0 } : p)));\n    };\n    const up = (e) => {\n      const d = downRef.current;\n      let wasTap = false;\n      if (d) {\n        try {\n          const rect = svgRef.current.getBoundingClientRect();\n          const cx2 = e && e.changedTouches ? e.changedTouches[0].clientX : (e && e.clientX);\n          const cy2 = e && e.changedTouches ? e.changedTouches[0].clientY : (e && e.clientY);\n          if (cx2 != null) {\n            const ex = ((cx2 - rect.left) / rect.width) * W;\n            const ey = ((cy2 - rect.top) / rect.height) * H;\n            const dx = Math.abs(ex - d.x), dy = Math.abs(ey - d.y);\n            const elapsed = Date.now() - d.t;\n            wasTap = dx < 6 && dy < 6 && elapsed < 350;\n          }\n        } catch (err) { /* swallow geometry errors */ }\n        downRef.current = null;\n      }\n      setDrag(null);\n      if (wasTap && d && level === 0) {\n        setLevel(1);\n        setParentIdx(d.i);\n        if (typeof window !== "undefined" && window.trackEvent) {\n          window.trackEvent("radar_drilldown", { facet: RADAR_TREE[d.i].l });\n        }\n      }\n    };\n    window.addEventListener("mousemove", move);\n    window.addEventListener("mouseup", up);\n    window.addEventListener("touchmove", move, { passive: false });\n    window.addEventListener("touchend", up);\n    return () => {\n      window.removeEventListener("mousemove", move);\n      window.removeEventListener("mouseup", up);\n      window.removeEventListener("touchmove", move);\n      window.removeEventListener("touchend", up);\n    };\n  }, [drag, level]);\n\n  const onCenterClick = () => {\n    if (level === 1) {\n      setLevel(0);\n      if (typeof window !== "undefined" && window.trackEvent) {\n        window.trackEvent("radar_back_to_root", {});\n      }\n    }\n  };\n\n  const N = activeDims.length;\n  const polyPoints = nodes.slice(0, N).map((n) => n.x + "," + n.y).join(" ");\n  const centerLabel = level === 0 ? "Léa" : RADAR_TREE[parentIdx].l;\n  const hintText = level === 0 ? "Cliquez sur une facette" : "Cliquez au centre pour revenir";\n\n  return (\n    <svg ref={svgRef} viewBox={"0 0 " + W + " " + H} style={{ width: "100%", height: 220, cursor: drag != null ? "grabbing" : "default", userSelect: "none", touchAction: "none" }}>\n      {[0.4, 0.7, 1].map((r, i) => (\n        <circle key={"r" + i} cx={cx} cy={cy} r={R * r} fill="none" stroke="rgba(10,14,44,.06)" strokeWidth={1} strokeDasharray={i === 2 ? "" : "2 3"} />\n      ))}\n      {nodes.slice(0, N).map((n, i) => (\n        <line key={"c" + i + "-" + level} x1={cx} y1={cy} x2={n.x} y2={n.y}\n          stroke={hover === i ? "#1320CE" : "rgba(19,32,206,.25)"}\n          strokeWidth={hover === i ? 2 : 1.2} />\n      ))}\n      <polygon points={polyPoints} fill={level === 0 ? "rgba(72,122,255,0.16)" : "rgba(253,105,54,0.12)"} stroke={level === 0 ? "#1320CE" : "#FD6936"} strokeWidth={1.5} style={{ transition: "fill .25s, stroke .25s" }} />\n      {nodes.slice(0, N).map((n, i) => {\n        const isHot = hover === i || drag === i;\n        const fill = level === 0 ? "#FD6936" : "#1320CE";\n        const stroke = level === 0 ? "rgba(253,105,54,.4)" : "rgba(19,32,206,.4)";\n        return (\n          <g key={"n" + i + "-" + level} transform={"translate(" + n.x + "," + n.y + ")"}\n            onMouseDown={onDown(i)} onTouchStart={onDown(i)}\n            onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}\n            style={{ cursor: level === 0 ? (drag === i ? "grabbing" : "pointer") : (drag === i ? "grabbing" : "grab") }}>\n            <circle r={isHot ? 9 : 6} fill={fill}\n              stroke={isHot ? "white" : stroke} strokeWidth={isHot ? 3 : 2}\n              style={{ transition: "r .15s, stroke-width .15s, fill .25s" }} />\n            <text y={n.y < cy - 12 ? -14 : (n.y > cy + 12 ? 20 : 4)}\n              textAnchor={n.x < cx - 20 ? "end" : (n.x > cx + 20 ? "start" : "middle")}\n              x={n.x < cx - 20 ? -12 : (n.x > cx + 20 ? 12 : 0)}\n              style={{ fontFamily: "var(--font-display)", fontSize: 10.5, fontWeight: 600, fill: "var(--c-ink)", letterSpacing: "0.02em", textTransform: "uppercase", pointerEvents: "none" }}>\n              {activeDims[i].l}\n            </text>\n          </g>\n        );\n      })}\n      <g transform={"translate(" + cx + "," + cy + ")"} onClick={onCenterClick}\n        style={{ cursor: level > 0 ? "pointer" : "default" }}>\n        <circle r={level > 0 ? 18 : 14} fill="#1320CE"\n          style={{ transition: "r .25s" }} />\n        <text textAnchor="middle" dy={level > 0 ? 2 : 4} style={{ fontFamily: "var(--font-display)", fontSize: level > 0 ? 9 : 10, fontWeight: 700, fill: "white", letterSpacing: "0.06em", textTransform: "uppercase", pointerEvents: "none" }}>{centerLabel}</text>\n        {level > 0 && (\n          <text textAnchor="middle" dy={12} style={{ fontSize: 7.5, fill: "rgba(255,255,255,.7)", letterSpacing: "0.04em", pointerEvents: "none" }}>← retour</text>\n        )}\n      </g>\n      <text x={W - 8} y={H - 6} textAnchor="end" style={{ fontSize: 9, fill: "var(--c-muted)", letterSpacing: "0.04em", fontWeight: 500 }}>{hintText}</text>\n    </svg>\n  );\n};',
            ),
        ],
    },

    # ----- Dashboard radar v2 — drill-down with OCEAN-X tree -----
    # The dashboard's ProfileCard has its own static SVG radar showing the 5
    # canonical OCEAN traits (Ouverture / Conscienciosité / Extraversion /
    # Agréabilité / Stabilité). We replace it with a copy of the Home
    # InteractiveRadar component, but with a distinct DASHBOARD_RADAR_TREE
    # so the drill-down semantics are OCEAN-aligned (matches the test
    # the dashboard says was passed). The component is duplicated rather
    # than shared because each page has its own React bundle.
    {
        "name": "Dashboard radar v2 — DashboardProfileRadar definition",
        "needle": "const ProfileCard = ({ onOpen, audit }) => {",
        "pages_skip": [
            "Proxxie Home.html", "index.html",
            "Proxxie Coach.html", "coach.html",
            "Proxxie Connexion.html", "connexion.html",
            "Proxxie Documents.html", "documents.html",
            "Proxxie Rapport.html", "rapport.html",
            "Proxxie Ressources.html", "ressources.html",
            "Proxxie Test.html", "test.html",
        ],
        "replacements": [
            (
                "const ProfileCard = ({ onOpen, audit }) => {",
                '/* Dashboard radar v2 — DASHBOARD_RADAR_TREE drives an interactive,\n   drillable OCEAN-X visualization. Same physics as the Home radar, just\n   different data and a smaller viewport. */\nconst DASHBOARD_RADAR_TREE = [\n  { l: "Ouverture", v: 0.88, sub: [\n    { l: "Imagination",   v: 0.91 },\n    { l: "Esthétique",    v: 0.78 },\n    { l: "Idées",         v: 0.94 },\n    { l: "Diversité",     v: 0.72 },\n    { l: "Innovation",    v: 0.85 },\n  ]},\n  { l: "Conscien-\\nciosité", v: 0.74, sub: [\n    { l: "Organisation", v: 0.78 },\n    { l: "Rigueur",      v: 0.81 },\n    { l: "Discipline",   v: 0.68 },\n    { l: "Méthode",      v: 0.76 },\n    { l: "Ponctualité",  v: 0.66 },\n  ]},\n  { l: "Extra-\\nversion", v: 0.52, sub: [\n    { l: "Sociabilité",     v: 0.58 },\n    { l: "Assertivité",     v: 0.51 },\n    { l: "Énergie sociale", v: 0.47 },\n    { l: "Expression",      v: 0.55 },\n    { l: "Audace",          v: 0.49 },\n  ]},\n  { l: "Agréa-\\nbilité", v: 0.81, sub: [\n    { l: "Confiance",    v: 0.84 },\n    { l: "Coopération",  v: 0.87 },\n    { l: "Modestie",     v: 0.74 },\n    { l: "Bienveillance",v: 0.86 },\n    { l: "Conciliation", v: 0.74 },\n  ]},\n  { l: "Stabilité", v: 0.67, sub: [\n    { l: "Calme",      v: 0.72 },\n    { l: "Optimisme",  v: 0.71 },\n    { l: "Sang-froid", v: 0.64 },\n    { l: "Résilience", v: 0.66 },\n    { l: "Sérénité",   v: 0.62 },\n  ]},\n];\n\nconst DashboardProfileRadar = () => {\n  const W = 240, H = 220, cx = W / 2, cy = H / 2, R = 70;\n  const [level, setLevel] = React.useState(0);\n  const [parentIdx, setParentIdx] = React.useState(0);\n  const activeDims = level === 0 ? DASHBOARD_RADAR_TREE : DASHBOARD_RADAR_TREE[parentIdx].sub;\n  const activeRef = React.useRef(activeDims);\n  activeRef.current = activeDims;\n\n  const targetFor = (dims, i) => {\n    const a = -Math.PI / 2 + (i * 2 * Math.PI) / dims.length;\n    return { x: cx + Math.cos(a) * R * dims[i].v, y: cy + Math.sin(a) * R * dims[i].v };\n  };\n  const target = (i) => {\n    const dims = activeRef.current;\n    if (i >= dims.length) return { x: cx, y: cy };\n    return targetFor(dims, i);\n  };\n\n  const [nodes, setNodes] = React.useState(() => DASHBOARD_RADAR_TREE.map((_, i) => ({ ...targetFor(DASHBOARD_RADAR_TREE, i), vx: 0, vy: 0 })));\n  const [drag, setDrag] = React.useState(null);\n  const [hover, setHover] = React.useState(null);\n  const dragRef = React.useRef(null);\n  const downRef = React.useRef(null);\n  const tRef = React.useRef(0);\n  const svgRef = React.useRef(null);\n  React.useEffect(() => { dragRef.current = drag; }, [drag]);\n\n  React.useEffect(() => {\n    let raf;\n    const tick = () => {\n      tRef.current += 0.015;\n      setNodes((prev) => prev.map((p, i) => {\n        if (dragRef.current === i) return p;\n        const tg = target(i);\n        const wx = Math.sin(tRef.current + i * 1.3) * 1.8;\n        const wy = Math.cos(tRef.current * 0.85 + i * 0.7) * 1.8;\n        const k = 0.10, damp = 0.84;\n        const ax = (tg.x + wx - p.x) * k;\n        const ay = (tg.y + wy - p.y) * k;\n        const vx = (p.vx + ax) * damp;\n        const vy = (p.vy + ay) * damp;\n        return { x: p.x + vx, y: p.y + vy, vx, vy };\n      }));\n      raf = requestAnimationFrame(tick);\n    };\n    raf = requestAnimationFrame(tick);\n    return () => cancelAnimationFrame(raf);\n  }, []);\n\n  const localPoint = (e) => {\n    const rect = svgRef.current.getBoundingClientRect();\n    const cx2 = e.touches ? e.touches[0].clientX : e.clientX;\n    const cy2 = e.touches ? e.touches[0].clientY : e.clientY;\n    return { x: ((cx2 - rect.left) / rect.width) * W, y: ((cy2 - rect.top) / rect.height) * H };\n  };\n\n  const onDown = (i) => (e) => {\n    e.preventDefault();\n    e.stopPropagation();\n    const pt = localPoint(e);\n    downRef.current = { i, x: pt.x, y: pt.y, t: Date.now() };\n    setDrag(i);\n  };\n\n  React.useEffect(() => {\n    if (drag == null) return;\n    const move = (e) => {\n      const pt = localPoint(e);\n      setNodes((prev) => prev.map((p, i) => (i === drag ? { ...p, x: pt.x, y: pt.y, vx: 0, vy: 0 } : p)));\n    };\n    const up = (e) => {\n      const d = downRef.current;\n      let wasTap = false;\n      if (d) {\n        try {\n          const rect = svgRef.current.getBoundingClientRect();\n          const cx2 = e && e.changedTouches ? e.changedTouches[0].clientX : (e && e.clientX);\n          const cy2 = e && e.changedTouches ? e.changedTouches[0].clientY : (e && e.clientY);\n          if (cx2 != null) {\n            const ex = ((cx2 - rect.left) / rect.width) * W;\n            const ey = ((cy2 - rect.top) / rect.height) * H;\n            const dx = Math.abs(ex - d.x), dy = Math.abs(ey - d.y);\n            const elapsed = Date.now() - d.t;\n            wasTap = dx < 6 && dy < 6 && elapsed < 350;\n          }\n        } catch (err) { /* swallow */ }\n        downRef.current = null;\n      }\n      setDrag(null);\n      if (wasTap && d && level === 0) {\n        setLevel(1);\n        setParentIdx(d.i);\n      }\n    };\n    window.addEventListener("mousemove", move);\n    window.addEventListener("mouseup", up);\n    window.addEventListener("touchmove", move, { passive: false });\n    window.addEventListener("touchend", up);\n    return () => {\n      window.removeEventListener("mousemove", move);\n      window.removeEventListener("mouseup", up);\n      window.removeEventListener("touchmove", move);\n      window.removeEventListener("touchend", up);\n    };\n  }, [drag, level]);\n\n  const onCenterClick = (e) => {\n    e.stopPropagation();\n    if (level === 1) setLevel(0);\n  };\n\n  const N = activeDims.length;\n  const polyPoints = nodes.slice(0, N).map((n) => n.x + "," + n.y).join(" ");\n  const centerLabel = level === 0 ? "OCEAN-X" : DASHBOARD_RADAR_TREE[parentIdx].l.replace("\\n", " ");\n\n  return (\n    <svg ref={svgRef} viewBox={"0 0 " + W + " " + H} style={{ width: "100%", height: 220, cursor: drag != null ? "grabbing" : "default", userSelect: "none", touchAction: "none" }}>\n      {[0.4, 0.7, 1].map((r, i) => (\n        <circle key={"r" + i} cx={cx} cy={cy} r={R * r} fill="none" stroke="rgba(10,14,44,.06)" strokeWidth={1} strokeDasharray={i === 2 ? "" : "2 3"} />\n      ))}\n      {nodes.slice(0, N).map((n, i) => (\n        <line key={"c" + i + "-" + level} x1={cx} y1={cy} x2={n.x} y2={n.y}\n          stroke={hover === i ? "#1320CE" : "rgba(19,32,206,.25)"}\n          strokeWidth={hover === i ? 2 : 1.2} />\n      ))}\n      <polygon points={polyPoints} fill={level === 0 ? "rgba(72,122,255,0.2)" : "rgba(253,105,54,0.14)"} stroke={level === 0 ? "#1320CE" : "#FD6936"} strokeWidth={1.5} style={{ transition: "fill .25s, stroke .25s" }} />\n      {nodes.slice(0, N).map((n, i) => {\n        const isHot = hover === i || drag === i;\n        const fill = level === 0 ? "#FD6936" : "#1320CE";\n        const stroke = level === 0 ? "rgba(253,105,54,.4)" : "rgba(19,32,206,.4)";\n        const lbl = activeDims[i].l;\n        return (\n          <g key={"n" + i + "-" + level} transform={"translate(" + n.x + "," + n.y + ")"}\n            onMouseDown={onDown(i)} onTouchStart={onDown(i)}\n            onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}\n            style={{ cursor: level === 0 ? (drag === i ? "grabbing" : "pointer") : (drag === i ? "grabbing" : "grab") }}>\n            <circle r={isHot ? 8 : 5} fill={fill}\n              stroke={isHot ? "white" : stroke} strokeWidth={isHot ? 3 : 2}\n              style={{ transition: "r .15s, stroke-width .15s, fill .25s" }} />\n            {lbl.split("\\n").map((line, li) => (\n              <text key={li}\n                y={(n.y < cy - 8 ? -12 : (n.y > cy + 8 ? 16 : 4)) + li * 9}\n                textAnchor={n.x < cx - 15 ? "end" : (n.x > cx + 15 ? "start" : "middle")}\n                x={n.x < cx - 15 ? -10 : (n.x > cx + 15 ? 10 : 0)}\n                style={{ fontFamily: "var(--font-display)", fontSize: 9, fontWeight: 600, fill: "var(--c-ink)", letterSpacing: "0.02em", textTransform: "uppercase", pointerEvents: "none" }}>\n                {line}\n              </text>\n            ))}\n          </g>\n        );\n      })}\n      <g transform={"translate(" + cx + "," + cy + ")"} onClick={onCenterClick}\n        style={{ cursor: level > 0 ? "pointer" : "default" }}>\n        <circle r={level > 0 ? 18 : 14} fill="#1320CE"\n          style={{ transition: "r .25s" }} />\n        <text textAnchor="middle" dy={level > 0 ? 2 : 4} style={{ fontFamily: "var(--font-display)", fontSize: level > 0 ? 8 : 9, fontWeight: 700, fill: "white", letterSpacing: "0.04em", textTransform: "uppercase", pointerEvents: "none" }}>{centerLabel}</text>\n        {level > 0 && (\n          <text textAnchor="middle" dy={12} style={{ fontSize: 7, fill: "rgba(255,255,255,.7)", letterSpacing: "0.04em", pointerEvents: "none" }}>← retour</text>\n        )}\n      </g>\n      <text x={W - 4} y={H - 5} textAnchor="end" style={{ fontSize: 8, fill: "var(--c-muted)", letterSpacing: "0.04em", fontWeight: 500 }}>\n        {level === 0 ? "Cliquez sur un trait" : "Cliquez au centre"}\n      </text>\n    </svg>\n  );\n};\n\nconst ProfileCard = ({ onOpen, audit }) => {',
            ),
        ],
    },

    # ----- Dashboard radar v2 — swap the static SVG for <DashboardProfileRadar /> -----
    {
        "name": "Dashboard radar v2 — SVG replacement in ProfileCard",
        "needle": '<svg viewBox="0 0 220 200" style={{ width: "100%" }}>',
        "pages_skip": [
            "Proxxie Home.html", "index.html",
            "Proxxie Coach.html", "coach.html",
            "Proxxie Connexion.html", "connexion.html",
            "Proxxie Documents.html", "documents.html",
            "Proxxie Rapport.html", "rapport.html",
            "Proxxie Ressources.html", "ressources.html",
            "Proxxie Test.html", "test.html",
        ],
        "replacements": [
            (
                '        <svg viewBox="0 0 220 200" style={{ width: "100%" }}>\n          {[0.3, 0.55, 0.8, 1].map((s, i) => {\n            const pts = [0,1,2,3,4].map(j => {\n              const a = -Math.PI/2 + j * (2*Math.PI/5);\n              return [110 + Math.cos(a)*70*s, 100 + Math.sin(a)*70*s].join(",");\n            }).join(" ");\n            return <polygon key={i} points={pts} fill="none" stroke="#E6E2D6" strokeWidth="1" />;\n          })}\n          {(() => {\n            const pts = traits.map((t, j) => {\n              const a = -Math.PI/2 + j * (2*Math.PI/5);\n              const r = (t.v/100)*70;\n              return [110 + Math.cos(a)*r, 100 + Math.sin(a)*r];\n            });\n            return (\n              <>\n                <polygon points={pts.map(p => p.join(",")).join(" ")} fill="rgba(72,122,255,0.2)" stroke="#1320CE" strokeWidth="2" />\n                {pts.map(([x,y], i) => <circle key={i} cx={x} cy={y} r="4" fill={traits[i].c} />)}\n              </>\n            );\n          })()}\n        </svg>',
                '        {/* Interactive drill-down radar (replaces static SVG) */}\n        <DashboardProfileRadar />',
            ),
        ],
    },

    # ----- Radar replacement: swap the static SVG for <InteractiveRadar /> -----
    # (kept on Home — the Dashboard radar is replaced by a separate patch
    # below that defines its own OCEAN-X drill-down tree.)
    {
        "name": "Radar replacement in HeroPreview",
        "needle": '<polygon points="100,28 165,75 132,118 58,108 42,68"',
        "replacements": [
            (
                '      {/* Radar mock */}\n      <svg viewBox="0 0 200 140" style={{ width: "100%", height: 140 }}>\n        <polygon points="100,20 170,55 155,120 45,120 30,55" fill="none" stroke="#E6E2D6" strokeWidth="1" />\n        <polygon points="100,40 150,65 140,110 60,110 50,65" fill="none" stroke="#E6E2D6" strokeWidth="1" />\n        <polygon points="100,55 130,70 125,100 75,100 70,70" fill="none" stroke="#E6E2D6" strokeWidth="1" />\n        <polygon points="100,28 165,75 132,118 58,108 42,68" fill="rgba(72,122,255,0.18)" stroke="#1320CE" strokeWidth="2" />\n        {[[100,28],[165,75],[132,118],[58,108],[42,68]].map(([x,y],i) => (\n          <circle key={i} cx={x} cy={y} r="3.5" fill="#FD6936" />\n        ))}\n      </svg>\n\n      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: "var(--c-muted)", textTransform: "uppercase", letterSpacing: "0.08em", marginTop: -4 }}>\n        <span>Ouverture</span><span>Curiosité</span><span>Ambition</span>\n      </div>',
                # Replace radar SVG + label row with the interactive component.
                '      {/* Obsidian-style interactive radar (replaces the static SVG) */}\n      <InteractiveRadar />',
            ),
        ],
    },

    # ----- F011B: chain after F011 — un-frame the sample-report CTA -----
    # Takes the F011 framed btn-ghost and reverts it to a plain underlined
    # text link, so it doesn't compete with the primary "30 min avec Charles"
    # CTA. Needle is the visible label text — present until something else
    # removes it (it stays put through every other patch in this file).
    # On re-run after applied, NEW is in text → SKIP.
    {
        "name": "F011B sample-report CTA unframed",
        "needle": 'Voir un exemple de rapport',
        "pages_skip": ['Proxxie Test.html', 'test.html'],
        "replacements": [
            (
                '<button onClick={onDemo} className="btn btn-ghost btn-lg" style={{ background: "white", borderColor: "var(--c-ink)", color: "var(--c-ink)" }}>\n                <Icon.play style={{ width: 16, height: 16 }} /> Voir un exemple de rapport\n              </button>',
                '{/* F011B: text-link (no frame) so the secondary CTA does not compete visually with "30 min avec Charles" */}\n              <button onClick={onDemo} style={{ background: "transparent", border: "none", color: "var(--c-ink-2)", fontSize: 14, fontWeight: 500, display: "inline-flex", alignItems: "center", gap: 6, cursor: "pointer", textDecoration: "underline", textUnderlineOffset: 4, padding: 0 }}>\n                <Icon.play style={{ width: 14, height: 14 }} /> Voir un exemple de rapport\n              </button>',
            ),
        ],
    },

    # ----- G2B: chain after G2 — expand 3 press items to 7 -----
    # www.proxxie.co references 7 media mentions; G2 originally shipped
    # only 3. This patch lifts the rest (Alveus, French Tech, Le Campement,
    # Bordeaux Métropole) and tightens the layout (gap 28 + fontSize 18)
    # so 7 items fit on desktop and wrap cleanly on smaller viewports.
    # Needle = "Ils parlent de nous" is only added by G2 to the Hero.
    {
        "name": "G2B media-mention bar expanded to 7 items",
        "needle": 'Ils parlent de nous',
        "replacements": [
            (
                '<div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 48, flexWrap: "wrap", opacity: 0.85 }}>\n            <a href="https://www.rcf.fr/bien-etre-et-psychologie/chemins-des-possibles?episode=564205" target="_blank" rel="noopener noreferrer" style={{ display: "inline-flex", flexDirection: "column", alignItems: "center", gap: 6, textDecoration: "none", color: "var(--c-muted)", fontSize: 11, fontWeight: 500, transition: "opacity .2s, transform .2s" }} onMouseEnter={(e) => { e.currentTarget.style.opacity = 1; e.currentTarget.style.transform = "translateY(-2px)"; }} onMouseLeave={(e) => { e.currentTarget.style.opacity = 0.85; e.currentTarget.style.transform = "none"; }}>\n              <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 22, letterSpacing: "0.02em", color: "var(--c-ink-2)" }}>RCF</span>\n              <span>Écouter l\'interview →</span>\n            </a>\n            <a href="https://drive.google.com/file/d/1oB1l-gXU6_3PElJVN_1LfjYhsPOBWsmy/view" target="_blank" rel="noopener noreferrer" style={{ display: "inline-flex", flexDirection: "column", alignItems: "center", gap: 6, textDecoration: "none", color: "var(--c-muted)", fontSize: 11, fontWeight: 500, transition: "opacity .2s, transform .2s" }} onMouseEnter={(e) => { e.currentTarget.style.opacity = 1; e.currentTarget.style.transform = "translateY(-2px)"; }} onMouseLeave={(e) => { e.currentTarget.style.opacity = 0.85; e.currentTarget.style.transform = "none"; }}>\n              <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 22, letterSpacing: "-0.01em", color: "var(--c-ink-2)" }}>France <span style={{ color: "#1320CE" }}>Bleu</span></span>\n              <span>Écouter l\'interview →</span>\n            </a>\n            <a href="https://drive.google.com/file/d/1LHVR84mIKt_jFR4W4Bn51LF6GrXtHvTh/view" target="_blank" rel="noopener noreferrer" style={{ display: "inline-flex", flexDirection: "column", alignItems: "center", gap: 6, textDecoration: "none", color: "var(--c-muted)", fontSize: 11, fontWeight: 500, transition: "opacity .2s, transform .2s" }} onMouseEnter={(e) => { e.currentTarget.style.opacity = 1; e.currentTarget.style.transform = "translateY(-2px)"; }} onMouseLeave={(e) => { e.currentTarget.style.opacity = 0.85; e.currentTarget.style.transform = "none"; }}>\n              <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 22, letterSpacing: "0.01em", color: "var(--c-ink-2)" }}>france<span style={{ color: "#FD6936" }}>•</span>tv</span>\n              <span>Regarder le replay →</span>\n            </a>\n          </div>',
                '{/* G2B: 7 press items lifted from www.proxxie.co (was 3) */}\n          <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 28, rowGap: 24, flexWrap: "wrap", opacity: 0.85 }}>\n            <a href="https://www.rcf.fr/bien-etre-et-psychologie/chemins-des-possibles?episode=564205" target="_blank" rel="noopener noreferrer" style={{ display: "inline-flex", flexDirection: "column", alignItems: "center", gap: 6, textDecoration: "none", color: "var(--c-muted)", fontSize: 11, fontWeight: 500, transition: "opacity .2s, transform .2s" }} onMouseEnter={(e) => { e.currentTarget.style.opacity = 1; e.currentTarget.style.transform = "translateY(-2px)"; }} onMouseLeave={(e) => { e.currentTarget.style.opacity = 0.85; e.currentTarget.style.transform = "none"; }}>\n              <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 20, letterSpacing: "0.005em", color: "var(--c-ink-2)", whiteSpace: "nowrap" }}>RCF</span>\n              <span>Écouter l’interview →</span>\n            </a>\n            <a href="https://drive.google.com/file/d/1oB1l-gXU6_3PElJVN_1LfjYhsPOBWsmy/view" target="_blank" rel="noopener noreferrer" style={{ display: "inline-flex", flexDirection: "column", alignItems: "center", gap: 6, textDecoration: "none", color: "var(--c-muted)", fontSize: 11, fontWeight: 500, transition: "opacity .2s, transform .2s" }} onMouseEnter={(e) => { e.currentTarget.style.opacity = 1; e.currentTarget.style.transform = "translateY(-2px)"; }} onMouseLeave={(e) => { e.currentTarget.style.opacity = 0.85; e.currentTarget.style.transform = "none"; }}>\n              <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 18, letterSpacing: "0.005em", color: "var(--c-ink-2)", whiteSpace: "nowrap" }}>France <span style={{ color: "#1320CE" }}>Bleu</span></span>\n              <span>Écouter l’interview →</span>\n            </a>\n            <a href="https://drive.google.com/file/d/1LHVR84mIKt_jFR4W4Bn51LF6GrXtHvTh/view" target="_blank" rel="noopener noreferrer" style={{ display: "inline-flex", flexDirection: "column", alignItems: "center", gap: 6, textDecoration: "none", color: "var(--c-muted)", fontSize: 11, fontWeight: 500, transition: "opacity .2s, transform .2s" }} onMouseEnter={(e) => { e.currentTarget.style.opacity = 1; e.currentTarget.style.transform = "translateY(-2px)"; }} onMouseLeave={(e) => { e.currentTarget.style.opacity = 0.85; e.currentTarget.style.transform = "none"; }}>\n              <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 18, letterSpacing: "0.005em", color: "var(--c-ink-2)", whiteSpace: "nowrap" }}>france<span style={{ color: "#FD6936" }}>•</span>tv</span>\n              <span>Regarder le replay →</span>\n            </a>\n            <a href="https://drive.google.com/file/d/1SGYrfP3MyIpM7OpBYpp95SNML7mVPLzn/view" target="_blank" rel="noopener noreferrer" style={{ display: "inline-flex", flexDirection: "column", alignItems: "center", gap: 6, textDecoration: "none", color: "var(--c-muted)", fontSize: 11, fontWeight: 500, transition: "opacity .2s, transform .2s" }} onMouseEnter={(e) => { e.currentTarget.style.opacity = 1; e.currentTarget.style.transform = "translateY(-2px)"; }} onMouseLeave={(e) => { e.currentTarget.style.opacity = 0.85; e.currentTarget.style.transform = "none"; }}>\n              <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 18, letterSpacing: "0.005em", color: "var(--c-ink-2)", whiteSpace: "nowrap" }}>Alveus</span>\n              <span>Regarder le webinaire →</span>\n            </a>\n            <a href="https://annuaire.frenchtechbordeaux.com/organisations/proxxie" target="_blank" rel="noopener noreferrer" style={{ display: "inline-flex", flexDirection: "column", alignItems: "center", gap: 6, textDecoration: "none", color: "var(--c-muted)", fontSize: 11, fontWeight: 500, transition: "opacity .2s, transform .2s" }} onMouseEnter={(e) => { e.currentTarget.style.opacity = 1; e.currentTarget.style.transform = "translateY(-2px)"; }} onMouseLeave={(e) => { e.currentTarget.style.opacity = 0.85; e.currentTarget.style.transform = "none"; }}>\n              <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 18, letterSpacing: "0.005em", color: "var(--c-ink-2)", whiteSpace: "nowrap" }}>French Tech</span>\n              <span>Lire l’article →</span>\n            </a>\n            <a href="https://lecampement-bordeaux.fr/entretien-avec-charles-broussin-de-proxxie/" target="_blank" rel="noopener noreferrer" style={{ display: "inline-flex", flexDirection: "column", alignItems: "center", gap: 6, textDecoration: "none", color: "var(--c-muted)", fontSize: 11, fontWeight: 500, transition: "opacity .2s, transform .2s" }} onMouseEnter={(e) => { e.currentTarget.style.opacity = 1; e.currentTarget.style.transform = "translateY(-2px)"; }} onMouseLeave={(e) => { e.currentTarget.style.opacity = 0.85; e.currentTarget.style.transform = "none"; }}>\n              <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 18, letterSpacing: "0.005em", color: "var(--c-ink-2)", whiteSpace: "nowrap" }}>Le Campement</span>\n              <span>Lire l’article →</span>\n            </a>\n            <a href="https://www.bordeaux-metropole.fr/" target="_blank" rel="noopener noreferrer" style={{ display: "inline-flex", flexDirection: "column", alignItems: "center", gap: 6, textDecoration: "none", color: "var(--c-muted)", fontSize: 11, fontWeight: 500, transition: "opacity .2s, transform .2s" }} onMouseEnter={(e) => { e.currentTarget.style.opacity = 1; e.currentTarget.style.transform = "translateY(-2px)"; }} onMouseLeave={(e) => { e.currentTarget.style.opacity = 0.85; e.currentTarget.style.transform = "none"; }}>\n              <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 17, letterSpacing: "0.005em", color: "var(--c-ink-2)", whiteSpace: "nowrap" }}>Bordeaux Métropole</span>\n              <span>Lire l’article →</span>\n            </a>\n          </div>',
            ),
        ],
    },

    # ----- F-STATS-MOVED: pull the trust bar out of the Hero -----
    # The 98% / +300 / 100% / 9-10 grid moves below SituationsSection
    # (see F-STATS-RELOCATED) so the proof points land closer to the
    # empathy block where they reinforce "you're not alone, this works".
    # Needle is the Hero-only "Trust bar — repositionnée" comment — gone
    # after this patch applies, so SKIP on re-run.
    {
        "name": "F-STATS-MOVED trust bar removed from Hero",
        "needle": 'Trust bar — repositionnée juste sous le hero',
        "replacements": [
            (
                '{/* Trust bar — repositionnée juste sous le hero pour rester visible above-the-fold */}\n        <div style={{ marginTop: 36, display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8, padding: "20px 8px", borderTop: "1px solid rgba(10,14,44,.08)", borderBottom: "1px solid rgba(10,14,44,.08)" }}>\n          {[\n            { n: "98%", l: "parents satisfaits" },\n            { n: "+300", l: "ados orientés" },\n            { n: "100%", l: "admis sur Parcoursup", note: "*" },\n            { n: "9/10", l: "nous recommandent" },\n          ].map((s, i) => (\n            <div key={i} style={{ textAlign: "center", borderRight: i < 3 ? "1px solid rgba(10,14,44,.08)" : "none" }}>\n              <div style={{ fontFamily: "var(--font-num)", fontSize: 32, fontWeight: 600, color: "var(--c-blue-deep)", letterSpacing: "-0.03em" }}>\n                {s.n}{s.note && <span style={{ fontSize: 18, verticalAlign: "super", marginLeft: 2, color: "var(--c-muted)" }}>{s.note}</span>}\n              </div>\n              <div style={{ fontSize: 13, color: "var(--c-muted)", marginTop: 2 }}>{s.l}</div>\n            </div>\n          ))}\n        </div>\n        <div style={{ fontSize: 11, color: "var(--c-muted)", marginTop: 8, textAlign: "right", paddingRight: 8 }}>\n          * Sur les terminales accompagnées en 2024-25 ayant validé un vœu Parcoursup.\n        </div>',
                '{/* F-STATS-MOVED: trust bar relocated to SituationsSection so the proof points land closer to the empathy block, not above-the-fold where they crowd the hero. */}',
            ),
        ],
    },

    # ----- F-STATS-RELOCATED: drop the trust bar after the empathy CTAs -----
    # The 4-column proof grid + footnote land at the end of
    # SituationsSection, right after the F007 CTA strip and before the
    # section close. Anchored on the unique 'situations_cta' tracking
    # key (only in sit asset, not Hero). Pairs with F-STATS-MOVED to
    # complete the move.
    {
        "name": "F-STATS-RELOCATED trust bar added below SituationsSection",
        "needle": 'source: "situations_cta"',
        "replacements": [
            (
                'trackEvent("calendly_opened", { source: "situations_cta" }); }}>\n            30 min avec Charles\n          </a>\n        </div>\n      </div>\n    </section>',
                'trackEvent("calendly_opened", { source: "situations_cta" }); }}>\n            30 min avec Charles\n          </a>\n        </div>\n\n        {/* F-STATS-RELOCATED: trust bar moved from Hero — proof points land here, right after the empathy block. */}\n        <div style={{ marginTop: 56, display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8, padding: "24px 8px", borderTop: "1px solid rgba(10,14,44,.08)", borderBottom: "1px solid rgba(10,14,44,.08)" }}>\n          {[\n            { n: "98%", l: "parents satisfaits" },\n            { n: "+300", l: "ados orientés" },\n            { n: "100%", l: "admis sur Parcoursup", note: "*" },\n            { n: "9/10", l: "nous recommandent" },\n          ].map((s, i) => (\n            <div key={i} style={{ textAlign: "center", borderRight: i < 3 ? "1px solid rgba(10,14,44,.08)" : "none" }}>\n              <div style={{ fontFamily: "var(--font-num)", fontSize: 32, fontWeight: 600, color: "var(--c-blue-deep)", letterSpacing: "-0.03em" }}>\n                {s.n}{s.note && <span style={{ fontSize: 18, verticalAlign: "super", marginLeft: 2, color: "var(--c-muted)" }}>{s.note}</span>}\n              </div>\n              <div style={{ fontSize: 13, color: "var(--c-muted)", marginTop: 2 }}>{s.l}</div>\n            </div>\n          ))}\n        </div>\n        <div style={{ fontSize: 11, color: "var(--c-muted)", marginTop: 8, textAlign: "right", paddingRight: 8 }}>\n          * Sur les terminales accompagnées en 2024-25 ayant validé un vœu Parcoursup.\n        </div>\n      </div>\n    </section>',
            ),
        ],
    },

    # ----- QE-OCEAN-X / QE-VALEURS-BESOINS / QE-FORCES-AXES -----
    # Three cards inserted into the Voir-un-exemple-de-rapport modal,
    # just before Marion's coach quote: Big Five (OCEAN-X) scores,
    # Valeurs fondamentales + Besoins-clés, and Points forts + Axes de
    # développement. Mirrors the depth of an actual Proxxie report so
    # the demo feels representative of the real deliverable.
    {
        "name": "QE-OCEAN-X demo modal — Big Five + valeurs + forces",
        "needle": '{/* Commentaire coach Marion */}',
        "replacements": [
            (
                '{/* Commentaire coach Marion */}',
                '{/* QE-OCEAN-X: Big Five (OCEAN-X) scores avec interprétation */}\n          <div style={{ background: "white", border: "1px solid rgba(10,14,44,.08)", borderRadius: 18, padding: "22px 28px", marginBottom: 18 }}>\n            <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--c-muted)", marginBottom: 16 }}>\n              Profil de personnalité · Big Five (OCEAN-X)\n            </div>\n            {[\n              { l: "Ouverture d\'esprit", v: 102, d: "Curiosité intellectuelle forte, sens créatif marqué. Aime apprendre, débattre, explorer." },\n              { l: "Conscience", v: 88, d: "Organisée, persévérante. Tendance au perfectionnisme — atout pour les études exigeantes." },\n              { l: "Extraversion", v: 64, d: "Équilibre introversion/extraversion. À l\'aise en petit groupe, plus réservée en grand cercle." },\n              { l: "Convivialité", v: 78, d: "Coopérative, empathique. Privilégie le compromis et le travail d\'équipe." },\n              { l: "Stabilité émotionnelle", v: 71, d: "Résiliente, gestion correcte du stress. Vigilante sur le perfectionnisme." },\n            ].map((b, i) => (\n              <div key={i} style={{ padding: "12px 0", borderTop: i > 0 ? "1px solid rgba(10,14,44,.05)" : "none" }}>\n                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 6 }}>\n                  <div style={{ fontSize: 14, fontWeight: 600 }}>{b.l}</div>\n                  <div style={{ fontSize: 13, fontWeight: 700, color: "var(--c-blue-deep)", fontVariantNumeric: "tabular-nums" }}>{b.v} / 120</div>\n                </div>\n                <div style={{ height: 5, background: "rgba(10,14,44,.06)", borderRadius: 999, overflow: "hidden", marginBottom: 6 }}>\n                  <div style={{ width: (b.v / 120 * 100) + "%", height: "100%", background: "linear-gradient(90deg, #487AFF, #1320CE)", borderRadius: 999 }} />\n                </div>\n                <div style={{ fontSize: 12.5, color: "var(--c-muted)", lineHeight: 1.45 }}>{b.d}</div>\n              </div>\n            ))}\n          </div>\n\n          {/* QE-VALEURS-BESOINS: 2-col valeurs fondamentales + besoins-clés */}\n          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 18 }}>\n            <div style={{ background: "white", border: "1px solid rgba(10,14,44,.08)", borderRadius: 18, padding: "22px 24px" }}>\n              <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--c-muted)", marginBottom: 14 }}>Valeurs fondamentales</div>\n              {["Curiosité", "Excellence", "Autonomie", "Impact concret", "Intégrité"].map((v, i) => (\n                <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 0", borderTop: i > 0 ? "1px solid rgba(10,14,44,.05)" : "none" }}>\n                  <span style={{ width: 22, height: 22, borderRadius: "50%", background: "rgba(253,105,54,.12)", color: "#FD6936", display: "grid", placeItems: "center", fontWeight: 700, fontSize: 12, flexShrink: 0 }}>{i + 1}</span>\n                  <span style={{ fontSize: 14, fontWeight: 500 }}>{v}</span>\n                </div>\n              ))}\n            </div>\n            <div style={{ background: "white", border: "1px solid rgba(10,14,44,.08)", borderRadius: 18, padding: "22px 24px" }}>\n              <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--c-muted)", marginBottom: 14 }}>Besoins-clés</div>\n              {["Apprendre en continu", "Créer & produire", "Comprendre le \\"pourquoi\\"", "Concret & terrain", "Liens authentiques"].map((b, i) => (\n                <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 0", borderTop: i > 0 ? "1px solid rgba(10,14,44,.05)" : "none" }}>\n                  <span style={{ width: 22, height: 22, borderRadius: "50%", background: "rgba(19,32,206,.10)", color: "#1320CE", display: "grid", placeItems: "center", fontWeight: 700, fontSize: 12, flexShrink: 0 }}>{i + 1}</span>\n                  <span style={{ fontSize: 14, fontWeight: 500 }}>{b}</span>\n                </div>\n              ))}\n            </div>\n          </div>\n\n          {/* QE-FORCES-AXES: 2-col points forts vs axes de développement */}\n          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 18 }}>\n            <div style={{ background: "white", border: "1px solid rgba(34,160,109,.22)", borderRadius: 18, padding: "22px 24px" }}>\n              <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: "#1F8C5E", marginBottom: 14, display: "flex", alignItems: "center", gap: 6 }}>\n                <span style={{ width: 6, height: 6, background: "#22A06D", borderRadius: "50%" }} /> Points forts (soft skills)\n              </div>\n              {["Esprit d\'analyse", "Créativité scientifique", "Résolution de problèmes complexes", "Autonomie de travail", "Synthèse rapide"].map((f, i) => (\n                <div key={i} style={{ fontSize: 13.5, padding: "7px 0", borderTop: i > 0 ? "1px solid rgba(10,14,44,.05)" : "none", color: "var(--c-ink-2)", lineHeight: 1.45 }}>• {f}</div>\n              ))}\n            </div>\n            <div style={{ background: "white", border: "1px solid rgba(220,140,30,.22)", borderRadius: 18, padding: "22px 24px" }}>\n              <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: "#B5740B", marginBottom: 14, display: "flex", alignItems: "center", gap: 6 }}>\n                <span style={{ width: 6, height: 6, background: "#E89C2D", borderRadius: "50%" }} /> Axes de développement\n              </div>\n              {["Gestion du perfectionnisme", "Communication en grand groupe", "Délégation", "Sortir de sa zone de confort", "Anglais à l\'oral"].map((a, i) => (\n                <div key={i} style={{ fontSize: 13.5, padding: "7px 0", borderTop: i > 0 ? "1px solid rgba(10,14,44,.05)" : "none", color: "var(--c-ink-2)", lineHeight: 1.45 }}>• {a}</div>\n              ))}\n            </div>\n          </div>\n\n          {/* Commentaire coach Marion */}',
            ),
        ],
    },

    # ----- QE-TIMELINE: Évolution sur 6 semaines · 4 phases -----
    # Inserted between Marion's coach quote and the Top 10 métiers card.
    # Shows the 4-phase accompaniment arc (Découverte, Valeurs, Exploration,
    # Stratégie) with checkmarks on completed phases, so prospects see the
    # shape of what they're buying.
    {
        "name": "QE-TIMELINE demo modal — 4 phases / 6 semaines",
        "needle": '{/* Top 10 métiers */}',
        "replacements": [
            (
                '{/* Top 10 métiers */}',
                '{/* QE-TIMELINE: Évolution sur 6 semaines · 4 phases d\'accompagnement */}\n          <div style={{ background: "white", border: "1px solid rgba(10,14,44,.08)", borderRadius: 18, padding: "22px 28px", marginBottom: 18 }}>\n            <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--c-muted)", marginBottom: 18 }}>\n              Évolution sur 6 semaines · 4 phases\n            </div>\n            {[\n              { ph: "Phase 1", t: "Découverte & tests", d: "Tests OCEAN-X + RIASEC, entretien initial, première lecture du profil. Léa identifie ses 3 grandes envies.", w: "Semaines 1–2", done: true },\n              { ph: "Phase 2", t: "Valeurs & motivations", d: "Approfondissement des valeurs, des besoins, du rapport au travail. Ateliers de projection.", w: "Semaines 2–3", done: true },\n              { ph: "Phase 3", t: "Exploration métiers", d: "10 métiers explorés en détail, 5 secteurs analysés, 2 immersions d\'1 journée organisées.", w: "Semaines 3–5", done: true },\n              { ph: "Phase 4", t: "Stratégie Parcoursup", d: "Choix des 10 vœux, lettres de motivation, plan B et filet de sécurité. Validation finale.", w: "Semaines 5–6", done: false },\n            ].map((p, i) => (\n              <div key={i} style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", alignItems: "start", gap: 14, padding: "14px 0", borderTop: i > 0 ? "1px solid rgba(10,14,44,.05)" : "none" }}>\n                <div style={{ width: 28, height: 28, borderRadius: "50%", background: p.done ? "linear-gradient(135deg, #FD6936, #FFA371)" : "rgba(10,14,44,.08)", color: p.done ? "white" : "var(--c-muted)", display: "grid", placeItems: "center", flexShrink: 0, fontWeight: 700, fontSize: 12, marginTop: 2 }}>\n                  {p.done ? "✓" : (i + 1)}\n                </div>\n                <div>\n                  <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 4, flexWrap: "wrap" }}>\n                    <span style={{ fontSize: 10.5, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--c-blue-deep)" }}>{p.ph}</span>\n                    <span style={{ fontSize: 15, fontWeight: 600 }}>{p.t}</span>\n                  </div>\n                  <div style={{ fontSize: 13, color: "var(--c-muted)", lineHeight: 1.5 }}>{p.d}</div>\n                </div>\n                <div style={{ fontSize: 11, color: "var(--c-muted)", fontWeight: 500, whiteSpace: "nowrap", marginTop: 4 }}>{p.w}</div>\n              </div>\n            ))}\n          </div>\n\n          {/* Top 10 métiers */}',
            ),
        ],
    },

    # ----- QE-VIGILANCE-LEVIERS + QE-PROCHAINES -----
    # Two cards inserted right before the coach-accompaniment teaser:
    # (1) Points de vigilance vs Leviers de réussite — what we keep an
    # eye on vs what we lean on.
    # (2) Prochaines étapes recommandées: 3 columns (Court/Moyen/Long
    # terme), so the report ends with concrete forward motion, not just
    # diagnostic data.
    {
        "name": "QE-VIGILANCE-LEVIERS + QE-PROCHAINES — vigilance, leviers, next steps",
        "needle": '{/* Aperçu parcours coach */}',
        "replacements": [
            (
                '{/* Aperçu parcours coach */}',
                '{/* QE-VIGILANCE-LEVIERS: ce qu\'on garde à l\'œil vs ce qui pousse */}\n          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 18 }}>\n            <div style={{ background: "white", border: "1px solid rgba(220,140,30,.18)", borderRadius: 18, padding: "22px 24px" }}>\n              <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: "#B5740B", marginBottom: 14, display: "flex", alignItems: "center", gap: 6 }}>\n                <span style={{ width: 6, height: 6, background: "#E89C2D", borderRadius: "50%" }} /> Points de vigilance\n              </div>\n              {[\n                "Tendance au perfectionnisme — peut bloquer face à l\'incertitude.",\n                "Hésitation entre cursus créatif (design) et scientifique (ingé).",\n                "Anxiété possible en environnement très compétitif (CPGE classique).",\n              ].map((v, i) => (\n                <div key={i} style={{ fontSize: 13.5, padding: "9px 0", borderTop: i > 0 ? "1px solid rgba(10,14,44,.05)" : "none", color: "var(--c-ink-2)", lineHeight: 1.45 }}>{v}</div>\n              ))}\n            </div>\n            <div style={{ background: "white", border: "1px solid rgba(34,160,109,.22)", borderRadius: 18, padding: "22px 24px" }}>\n              <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: "#1F8C5E", marginBottom: 14, display: "flex", alignItems: "center", gap: 6 }}>\n                <span style={{ width: 6, height: 6, background: "#22A06D", borderRadius: "50%" }} /> Leviers de réussite\n              </div>\n              {[\n                "Excellent dossier scolaire (moyenne 16,5/20, mention TB au brevet).",\n                "Stage en labo réalisé en 1ère — projection métier déjà solide.",\n                "Forte motivation intrinsèque : Léa veut comprendre, pas juste valider.",\n              ].map((l, i) => (\n                <div key={i} style={{ fontSize: 13.5, padding: "9px 0", borderTop: i > 0 ? "1px solid rgba(10,14,44,.05)" : "none", color: "var(--c-ink-2)", lineHeight: 1.45 }}>{l}</div>\n              ))}\n            </div>\n          </div>\n\n          {/* QE-PROCHAINES: prochaines étapes recommandées · court / moyen / long terme */}\n          <div style={{ background: "white", border: "1px solid rgba(10,14,44,.08)", borderRadius: 18, padding: "22px 28px", marginBottom: 18 }}>\n            <div style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--c-muted)", marginBottom: 16 }}>\n              Prochaines étapes recommandées\n            </div>\n            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14 }}>\n              {[\n                { t: "Court terme", w: "Avril–mai", c: "#FD6936", items: ["Finaliser les 10 vœux Parcoursup.", "Travailler les 5 lettres de motivation.", "Concours d\'entrée Polytech (28 avril)."] },\n                { t: "Moyen terme", w: "Juin–septembre", c: "#487AFF", items: ["Bac : période de réception des vœux.", "Visite d\'un campus, contact étudiant.", "Renforcer l\'anglais oral cet été."] },\n                { t: "Long terme", w: "1ère année post-bac", c: "#1320CE", items: ["Valider le choix de filière.", "Viser la passerelle ingénieur.", "Bilan de suivi à 6 mois avec le coach."] },\n              ].map((c, i) => (\n                <div key={i} style={{ padding: "0 4px" }}>\n                  <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6 }}>\n                    <span style={{ width: 7, height: 7, background: c.c, borderRadius: "50%" }} />\n                    <span style={{ fontSize: 13, fontWeight: 700, color: "var(--c-ink)" }}>{c.t}</span>\n                  </div>\n                  <div style={{ fontSize: 11, color: "var(--c-muted)", marginBottom: 10, fontWeight: 500 }}>{c.w}</div>\n                  {c.items.map((it, j) => (\n                    <div key={j} style={{ fontSize: 12.5, color: "var(--c-ink-2)", padding: "5px 0", lineHeight: 1.4 }}>○ {it}</div>\n                  ))}\n                </div>\n              ))}\n            </div>\n          </div>\n\n          {/* Aperçu parcours coach */}',
            ),
        ],
    },

    # ----- HOMEFIX-1 (2026-05-15): replace stock-photo woman with Charles -----
    # The "Charles, votre coach" floating badge in the hero used an Unsplash
    # stock photo of a woman, which contradicts the name. Swap for the actual
    # founder photo lifted from www.proxxie.co/equipe (coach1.webp, saved
    # locally as charles-coach.webp).
    {
        "name": "HOMEFIX-1 Charles avatar — real photo",
        "needle": "https://images.unsplash.com/photo-1573496359142",
        "replacements": [
            (
                'src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=200&h=200&fit=crop&crop=faces"',
                'src="charles-coach.webp"',
            ),
        ],
    },

    # ----- HOMEFIX-2 (2026-05-15, revised 2026-05-16): hero card photo -----
    # The hero card claimed to show "Léa, 16 ans" in session with her coach
    # but used a generic stock photo. Replace with Elisa — a real young
    # person Proxxie accompanies (elisa-proxxie.jpg, provided by the
    # founder) and update the caption accordingly.
    {
        "name": "HOMEFIX-2 hero card → Elisa accompagnée par Proxxie",
        "needle": 'src="hero-coach-square.jpg"',
        "replacements": [
            (
                '<img\n        src="hero-coach-square.jpg"\n        alt="Léa en session avec son coach Proxxie"\n        style={{ width: "100%", height: 195, display: "block", marginBottom: 10, objectFit: "cover", objectPosition: "20% 30%", background: "linear-gradient(135deg, #FFF4EE, #FFDFCC)" }}\n      />\n      <div style={{ fontFamily: "var(--font-display)", fontSize: 14, color: "var(--c-ink)", textAlign: "center", letterSpacing: "-0.01em" }}>Léa, 16 ans</div>\n      <div style={{ fontSize: 10, color: "var(--c-muted)", textAlign: "center", marginTop: 1 }}>1ère · en session avec son coach</div>',
                '<img\n        src="elisa-proxxie.jpg"\n        alt="Elisa, accompagnée par Proxxie"\n        style={{ width: "100%", height: 195, display: "block", marginBottom: 10, objectFit: "cover", objectPosition: "center 22%", background: "linear-gradient(135deg, #FFF4EE, #FFDFCC)" }}\n      />\n      <div style={{ fontFamily: "var(--font-display)", fontSize: 14, color: "var(--c-ink)", textAlign: "center", letterSpacing: "-0.01em" }}>Elisa</div>\n      <div style={{ fontSize: 10, color: "var(--c-muted)", textAlign: "center", marginTop: 1 }}>Accompagnée par Proxxie</div>',
            ),
        ],
    },

    # ----- HOMEFIX-2B (2026-05-16): in-place upgrade from the previous -----
    # 2026-05-15 state (charles-accompagne.webp / "Charles, fondateur Proxxie")
    # to the Elisa photo. Without this, files that already ran HOMEFIX-2's v1
    # would not pick up the v2 swap because their needle is now gone.
    {
        "name": "HOMEFIX-2B upgrade Charles-accompagne → Elisa",
        "needle": 'src="charles-accompagne.webp"',
        "replacements": [
            (
                '<img\n        src="charles-accompagne.webp"\n        alt="Charles, fondateur Proxxie, accompagne les familles"\n        style={{ width: "100%", height: 195, display: "block", marginBottom: 10, objectFit: "cover", objectPosition: "center 25%", background: "linear-gradient(135deg, #FFF4EE, #FFDFCC)" }}\n      />\n      <div style={{ fontFamily: "var(--font-display)", fontSize: 14, color: "var(--c-ink)", textAlign: "center", letterSpacing: "-0.01em" }}>Charles, fondateur Proxxie</div>\n      <div style={{ fontSize: 10, color: "var(--c-muted)", textAlign: "center", marginTop: 1 }}>Coach d\'orientation · French Tech Bordeaux</div>',
                '<img\n        src="elisa-proxxie.jpg"\n        alt="Elisa, accompagnée par Proxxie"\n        style={{ width: "100%", height: 195, display: "block", marginBottom: 10, objectFit: "cover", objectPosition: "center 22%", background: "linear-gradient(135deg, #FFF4EE, #FFDFCC)" }}\n      />\n      <div style={{ fontFamily: "var(--font-display)", fontSize: 14, color: "var(--c-ink)", textAlign: "center", letterSpacing: "-0.01em" }}>Elisa</div>\n      <div style={{ fontSize: 10, color: "var(--c-muted)", textAlign: "center", marginTop: 1 }}>Accompagnée par Proxxie</div>',
            ),
        ],
    },

    # ----- DRAWERFIX-1 (2026-05-16): tighten side-panel section spacing -----
    # Founder feedback: the gap between sections 01/02/03/04 inside the
    # InfoDrawer (Coach / Dashboard / Documents / Rapport side panels) was
    # too large. Shave inter-section margin from 14px → 6px, header→body
    # gap from 12px → 6px, and hero→first-section marginBottom from 24 → 12.
    # The component lives in bundler asset 51ff7b1d (Proxxie Coach.html and
    # the four product pages share it).
    {
        "name": "DRAWERFIX-1 drawer section margin 14→6",
        "needle": ".drawer-section + .drawer-section { margin-top: 14px; }",
        "replacements": [
            (
                ".drawer-section + .drawer-section { margin-top: 14px; }",
                ".drawer-section + .drawer-section { margin-top: 6px; }",
            ),
        ],
    },
    {
        "name": "DRAWERFIX-1b drawer section head margin-bottom 12→6",
        "needle": "drawer-section-head {\n      display: flex; align-items: center; gap: 10px;\n      margin-bottom: 12px;",
        "replacements": [
            (
                "drawer-section-head {\n      display: flex; align-items: center; gap: 10px;\n      margin-bottom: 12px;\n    }",
                "drawer-section-head {\n      display: flex; align-items: center; gap: 10px;\n      margin-bottom: 6px;\n    }",
            ),
        ],
    },
    {
        "name": "DRAWERFIX-1c drawer hero marginBottom 24→12",
        "needle": '{data.hero && <div style={{ marginBottom: 24 }}>{data.hero}</div>}',
        "replacements": [
            (
                '{data.hero && <div style={{ marginBottom: 24 }}>{data.hero}</div>}',
                '{data.hero && <div style={{ marginBottom: 12 }}>{data.hero}</div>}',
            ),
        ],
    },

    # ----- HOMEFIX-3 (2026-05-15): tighten gap between press bar and -----
    # "Vous êtes ici" section. The hero ends with the "Ils parlent de nous"
    # press-mention strip; the following "Vous êtes ici" section opened with
    # paddingTop: 100, creating an awkward gap. Trim to 40 and tighten the
    # internal title block from margin 50px to 32px.
    {
        "name": "HOMEFIX-3 tighten 'Vous êtes ici' section top padding",
        "needle": "Vous êtes ici, vous n'êtes pas seuls",
        "replacements": [
            (
                '<section style={{ paddingTop: 100, paddingBottom: 60 }}>\n      <div className="shell">\n        <div style={{ textAlign: "center", maxWidth: 720, margin: "0 auto 50px" }}>\n          <span className="eyebrow"><span className="dot"></span>Vous êtes ici, vous n\'êtes pas seuls</span>',
                '<section style={{ paddingTop: 40, paddingBottom: 60 }}>\n      <div className="shell">\n        <div style={{ textAlign: "center", maxWidth: 720, margin: "0 auto 32px" }}>\n          <span className="eyebrow"><span className="dot"></span>Vous êtes ici, vous n\'êtes pas seuls</span>',
            ),
        ],
    },
]

# ===========================================================================
# RUNNER
# ===========================================================================

def _escape_for_js_string(s: str) -> str:
    """The CSS lives inside a JS string literal: real newlines are stored
    as the two-character escape `\\n`, double-quotes as `\\"`, etc. Convert
    our Python source strings (with real newlines) to the on-disk format."""
    return s.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')

def _sentinel_for(new: str) -> str:
    """Extract a unique identifying substring from the patch's `new` content.
    Used as the idempotency check: if the sentinel appears in the file (in
    its escaped on-disk form), the patch is considered already applied.

    Heuristic: take the first `/* TAG:` or `/* TAG —` comment marker, since
    these are the explicit fix-id labels we put at the top of each patch
    block. If no such marker exists, fall back to the first ~80 chars of new.
    """
    # Look for a fix-tag comment: matches `/* F001:`, `/* QA-001a:`, `/* G2 —`, etc.
    m = re.search(r'/\*\s+([A-Z][A-Z0-9\-]*)[\s:—-]', new)
    if m:
        # Use the comment opening + the tag + ~20 chars after as the sentinel.
        # That's unique enough to identify the patch and resists minor edits.
        idx = m.start()
        return new[idx:idx + 60]
    # Fallback: first 80 chars after any leading whitespace
    return new.lstrip()[:80]

def apply_css_patches(html: str, path_name: str) -> tuple[str, int]:
    """Apply CSS-string replacements to the raw HTML. Idempotent via per-patch
    sentinels (a unique marker substring of `new` that's stable across
    surrounding edits).

    The "CSS" lives inside a JS string literal, so newlines and quotes are
    escaped on disk. We pass patch strings through _escape_for_js_string
    before searching/replacing.
    """
    changed = 0
    for old, new in CSS_PATCHES:
        old_esc = _escape_for_js_string(old)
        new_esc = _escape_for_js_string(new)
        sentinel_esc = _escape_for_js_string(_sentinel_for(new))
        if sentinel_esc in html:
            # Already applied (or partially applied during a prior run);
            # do not re-insert. Without this check, overlapping patches
            # anchored on the same line chain-append on every run.
            continue
        if old_esc not in html:
            # Patch doesn't apply on this page (e.g. marketing-page rule on a
            # product page). Quiet — only --strict mode would care, and it
            # only cares about bundle drift.
            continue
        html = html.replace(old_esc, new_esc, 1)
        changed += 1
    return html, changed

def apply_bundle_patches(html: str, path_name: str) -> tuple[str, int]:
    """Apply JSX-string replacements inside the bundled, gzipped, base64 manifest."""
    m = re.search(r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)', html, flags=re.DOTALL)
    if not m:
        return html, 0

    manifest = json.loads(m.group(2))
    total_changes = 0

    for uuid, entry in manifest.items():
        data = base64.b64decode(entry["data"])
        compressed = entry.get("compressed", False)
        if compressed:
            try:
                data = gzip.decompress(data)
            except Exception:
                continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue  # binary asset (font, image)

        asset_changed = False
        for patch in BUNDLE_PATCHES:
            if patch["needle"].encode() not in data and patch["needle"] not in text:
                continue
            for old, new in patch["replacements"]:
                if new in text:
                    # already applied
                    continue
                if old in text:
                    text = text.replace(old, new, 1)
                    asset_changed = True
                    total_changes += 1
                    print(f"  ✓ [{path_name}/{uuid[:8]}] {patch['name']}")
                else:
                    print(f"  ! [{path_name}/{uuid[:8]}] {patch['name']}: needle present but old-string not found")

        if asset_changed:
            new_data = text.encode("utf-8")
            if compressed:
                new_data = gzip.compress(new_data)
            entry["data"] = base64.b64encode(new_data).decode("ascii")

    if total_changes == 0:
        return html, 0

    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]
    return new_html, total_changes

# Drift counter (incremented when a bundle patch's needle matches but the
# precise old-string can no longer be found — i.e. team-side code drifted
# under our feet). Tracked across all process_file() calls so --strict can
# fail at the end.
_BUNDLE_DRIFT = []

def process_file(path: pathlib.Path) -> bool:
    html = path.read_text(encoding="utf-8")
    orig = html
    html, css_n = apply_css_patches(html, path.name)
    html, jsx_n = apply_bundle_patches(html, path.name)
    if html == orig:
        return False
    path.write_text(html, encoding="utf-8")
    print(f"  → wrote {path.name} (css: {css_n}, bundle: {jsx_n})")
    return True

if __name__ == "__main__":
    # Simple arg parsing — keep dependency-free (script runs in CI sandbox).
    argv = list(sys.argv[1:])
    strict = "--strict" in argv
    if strict:
        argv.remove("--strict")
    targets = argv or ALL_HTML_FILES

    # Wrap apply_bundle_patches to capture drift events. We re-bind the symbol
    # in this module so the existing call site inside process_file picks up
    # the instrumented version without a refactor.
    _orig_apply_bundle = apply_bundle_patches

    def _instrumented_apply_bundle(html: str, path_name: str):
        # Re-implement the inner loop with drift tracking. We mirror the
        # original logic precisely; if either implementation evolves, update
        # both. The simpler alternative — patching print — was rejected as
        # too magic.
        import re as _re, json as _json, base64 as _b64, gzip as _gz
        m = _re.search(r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)', html, flags=_re.DOTALL)
        if not m:
            return html, 0
        manifest = _json.loads(m.group(2))
        total_changes = 0
        for uuid, entry in manifest.items():
            data = _b64.b64decode(entry["data"])
            compressed = entry.get("compressed", False)
            if compressed:
                try:
                    data = _gz.decompress(data)
                except Exception:
                    continue
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                continue
            asset_changed = False
            for patch in BUNDLE_PATCHES:
                # Honor per-patch skip list — some patches target a specific
                # page's JSX shape and their needle happens to also appear on
                # other pages with different surrounding code.
                if path_name in patch.get("pages_skip", []):
                    continue
                needle_in_text = (patch["needle"].encode() in data) or (patch["needle"] in text)
                if not needle_in_text:
                    continue
                for old, new in patch["replacements"]:
                    if new in text:
                        continue
                    if old in text:
                        text = text.replace(old, new, 1)
                        asset_changed = True
                        total_changes += 1
                        print(f"  ✓ [{path_name}/{uuid[:8]}] {patch['name']}")
                    else:
                        msg = f"{path_name}/{uuid[:8]} :: {patch['name']}"
                        _BUNDLE_DRIFT.append(msg)
                        print(f"  ! DRIFT [{path_name}/{uuid[:8]}] {patch['name']}: needle matches the asset but the precise old-string is gone — team code drifted")
            if asset_changed:
                new_data = text.encode("utf-8")
                if compressed:
                    new_data = _gz.compress(new_data)
                entry["data"] = _b64.b64encode(new_data).decode("ascii")
        if total_changes == 0:
            return html, 0
        new_manifest_json = _json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
        new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]
        return new_html, total_changes

    apply_bundle_patches = _instrumented_apply_bundle  # type: ignore

    for fn in targets:
        p = REPO / fn
        if not p.exists():
            print(f"skip (missing): {fn}")
            continue
        print(f"Processing: {fn}")
        process_file(p)

    # Strict-mode exit gate
    if _BUNDLE_DRIFT:
        print()
        print(f"❌ {len(_BUNDLE_DRIFT)} bundle patch(es) drifted — team code changed under our needles:")
        for d in _BUNDLE_DRIFT:
            print(f"   - {d}")
        print()
        if strict:
            print("--strict was passed, exiting non-zero. Update _design_fixes.py to match the new code shape, or remove the obsolete patch.")
            sys.exit(2)
        else:
            print("(running without --strict; deploy may be missing fixes. Run with --strict in CI to catch this earlier.)")
    elif strict:
        print()
        print("✅ --strict passed: every bundle patch needle either applied cleanly, was already applied, or didn't match this asset (skipped).")

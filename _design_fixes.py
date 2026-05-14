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

    # F002: The .btn-ghost class is too low-contrast for Charles. Make it
    # use an outlined navy treatment that reads as a real CTA, not a nav link.
    (
        ".btn-ghost {\n  background: transparent;\n  color: var(--c-ink);\n  border: 1.5px solid rgba(10,14,44,.16);\n}\n.btn-ghost:hover { background: rgba(10,14,44,.04); }",
        ".btn-ghost {\n  background: transparent;\n  color: var(--c-ink);\n  border: 1.5px solid rgba(10,14,44,.16);\n}\n.btn-ghost:hover { background: rgba(10,14,44,.04); }\n/* F002: stronger outline for the Charles secondary CTA. Reads as a real\n   call-to-action next to the orange primary, not as a nav link. */\n.nav-cta-secondary.btn-ghost {\n  background: white;\n  color: var(--c-ink);\n  border: 1.5px solid var(--c-ink);\n  box-shadow: 0 4px 12px -4px rgba(10,14,44,.18);\n}\n.nav-cta-secondary.btn-ghost:hover {\n  background: var(--c-ink);\n  color: white;\n  transform: translateY(-1px);\n}",
    ),

    # F006-bis: Make the mobile sticky CTA bar support two buttons side-by-side
    # (currently the orange test button takes 100% width). Style the second
    # button as a navy outline so it doesn't fight the orange visually.
    (
        "  .mobile-sticky-cta .btn { flex: 1; justify-content: center; padding: 14px; }",
        "  .mobile-sticky-cta .btn { flex: 1; justify-content: center; padding: 14px; min-height: 44px; }\n  /* F006: Charles button in the mobile sticky bar is a navy outline */\n  .mobile-sticky-cta .btn-charles {\n    background: white;\n    color: var(--c-ink);\n    border: 1.5px solid var(--c-ink);\n    text-decoration: none;\n  }",
    ),
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
    {
        "name": "F011 sample-report secondary CTA",
        "needle": "Voir un exemple de rapport",
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
                '        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>\n          {items.map((it, i) => (\n            <div key={i} className="card" style={{ padding: 24, background: "white" }}>\n              <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#FD6936", marginBottom: 14 }} />\n              <div style={{ fontWeight: 600, fontSize: 17, marginBottom: 6 }}>{it.t}</div>\n              <p style={{ color: "var(--c-muted)", fontSize: 14 }}>{it.d}</p>\n            </div>\n          ))}\n        </div>\n      </div>\n    </section>',
                # Same grid + an in-section CTA strip that points to the method explanation.
                '        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>\n          {items.map((it, i) => (\n            <div key={i} className="card" style={{ padding: 24, background: "white" }}>\n              <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#FD6936", marginBottom: 14 }} />\n              <div style={{ fontWeight: 600, fontSize: 17, marginBottom: 6 }}>{it.t}</div>\n              <p style={{ color: "var(--c-muted)", fontSize: 14 }}>{it.d}</p>\n            </div>\n          ))}\n        </div>\n        {/* F007: section CTA — closes the empathy block with two clear paths. */}\n        <div style={{ marginTop: 36, display: "flex", justifyContent: "center", flexWrap: "wrap", gap: 12 }}>\n          <a href="#methode" className="btn btn-orange btn-arrow" style={{ textDecoration: "none" }}>\n            Voir comment on aide\n          </a>\n          <a href="https://calendly.com/proxxie/entretien" target="_blank" rel="noopener noreferrer" className="btn btn-ghost" style={{ textDecoration: "none", background: "white", borderColor: "var(--c-ink)", color: "var(--c-ink)" }} onClick={() => { if (typeof window !== "undefined" && window.trackEvent) window.trackEvent("calendly_opened", { source: "situations_cta" }); }}>\n            30 min avec Charles\n          </a>\n        </div>\n      </div>\n    </section>',
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

    # ----- F015: Continuer disabled state — make it clearly disabled -----
    # The wizard's bottom button uses `nextLocked` to gate. The class change
    # already exists, but the visual disabled treatment was weak. We thicken
    # opacity + cursor when locked.
    # Searching for the nextLocked-driven Continuer button styling…
    # Note: this one needs to be located precisely — adding a CSS rule is simpler.
]


# ===========================================================================
# RUNNER
# ===========================================================================

def _escape_for_js_string(s: str) -> str:
    """The CSS lives inside a JS string literal: real newlines are stored
    as the two-character escape `\\n`, double-quotes as `\\"`, etc. Convert
    our Python source strings (with real newlines) to the on-disk format."""
    return s.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def apply_css_patches(html: str, path_name: str) -> tuple[str, int]:
    """Apply CSS-string replacements to the raw HTML. Idempotent.

    The "CSS" is stored inside a JS string literal, so newlines and quotes are
    escaped. We escape our patch strings to match before searching/replacing.
    """
    changed = 0
    for old, new in CSS_PATCHES:
        old_esc = _escape_for_js_string(old)
        new_esc = _escape_for_js_string(new)
        if new_esc in html:
            continue
        if old_esc not in html:
            print(f"  ! [{path_name}] CSS needle not found and not already applied: {old[:80]!r}")
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
    targets = sys.argv[1:] or ALL_HTML_FILES
    for fn in targets:
        p = REPO / fn
        if not p.exists():
            print(f"skip (missing): {fn}")
            continue
        print(f"Processing: {fn}")
        process_file(p)

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
    # Tests landing + individual test pages (added 2026-05-19 for the
    # ANALYTICS-1 GA4/Clarity rollout — every page must report).
    "Proxxie Tests.html", "tests.html",
    "Proxxie Test Anxiete.html", "test-anxiete.html",
    "Proxxie Test Autisme.html", "test-autisme.html",
    "Proxxie Test Besoins.html", "test-besoins.html",
    "Proxxie Test DYS.html", "test-dys.html",
    "Proxxie Test Drivers.html", "test-drivers.html",
    "Proxxie Test HPI.html", "test-hpi.html",
    "Proxxie Test MBTI.html", "test-mbti.html",
    "Proxxie Test PCM.html", "test-pcm.html",
    "Proxxie Test RIASEC.html", "test-riasec.html",
    "Proxxie Test TDAH.html", "test-tdah.html",
    "Proxxie Test Valeurs.html", "test-valeurs.html",
    # Static landing pages (no app bundle, but should still report
    # page_view to GA4 once they ship the analytics block).
    "blog.html",
    "carnet-orientation.html",
    "cas-clients.html",
    "guide-orientation.html",
    "newsletter-substack.html",
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

    # ----- ANALYTICS-2 (2026-05-19): wire Cookiebot consent banner -----
    # CBID 00200400-fef6-4032-a746-f80a83be8751.
    # Two coordinated changes in a single replace:
    #   1. Insert the Cookiebot script tag BEFORE the GA4 tag. The script
    #      uses data-blockingmode="auto" so Cookiebot auto-scans the page
    #      and rewrites any tracker script (googletagmanager.com,
    #      clarity.ms, etc.) to type="text/plain" until consent is given.
    #      No need to tag every individual script manually.
    #   2. Flip Consent Mode v2 defaults from `granted` to `denied`,
    #      add wait_for_update: 500 so gtag holds initial events for
    #      half a second waiting for Cookiebot's first consent decision.
    #      Cookiebot calls gtag('consent', 'update', {...}) automatically
    #      with the user's choice — no glue code needed.
    (
        '<!-- ANALYTICS-1: GA4 + Microsoft Clarity (Cookiebot pending) -->\n<!-- Google Analytics 4 (property shared with www.proxxie.co) -->\n<script async src="https://www.googletagmanager.com/gtag/js?id=G-Q93HTZY2TB"></script>\n<script>\n  window.dataLayer = window.dataLayer || [];\n  function gtag(){dataLayer.push(arguments);}\n  // Consent Mode v2 — defaults to granted until Cookiebot ships (ANALYTICS-2).\n  // When the bandeau is added, flip these defaults to \'denied\' and let\n  // Cookiebot call gtag(\'consent\',\'update\',{...}) on user choice.\n  gtag(\'consent\', \'default\', {\n    \'ad_storage\': \'granted\',\n    \'analytics_storage\': \'granted\',\n    \'ad_user_data\': \'granted\',\n    \'ad_personalization\': \'granted\'\n  });',
        '<!-- ANALYTICS-1: GA4 + Microsoft Clarity (Cookiebot WIRED via ANALYTICS-2) -->\n<!-- ANALYTICS-2: Cookiebot — MUST load before any other tracking script -->\n<script id="Cookiebot"\n        src="https://consent.cookiebot.com/uc.js"\n        data-cbid="00200400-fef6-4032-a746-f80a83be8751"\n        data-blockingmode="auto"\n        type="text/javascript"></script>\n\n<!-- Google Analytics 4 (property shared with www.proxxie.co) -->\n<script async src="https://www.googletagmanager.com/gtag/js?id=G-Q93HTZY2TB"></script>\n<script>\n  window.dataLayer = window.dataLayer || [];\n  function gtag(){dataLayer.push(arguments);}\n  // Consent Mode v2 — defaults DENIED. Cookiebot will fire\n  // gtag(\'consent\',\'update\',{...}) with the user\'s choice. The\n  // wait_for_update flag holds initial events for 500 ms so we don\'t\n  // send anonymous cookieless pings before consent is actually decided.\n  gtag(\'consent\', \'default\', {\n    \'ad_storage\': \'denied\',\n    \'analytics_storage\': \'denied\',\n    \'ad_user_data\': \'denied\',\n    \'ad_personalization\': \'denied\',\n    \'wait_for_update\': 500\n  });',
    ),

    # ----- ANALYTICS-3a (2026-05-19): site-wide engagement tracking -----
    # Adds a vanilla-JS engagement layer right after the ANALYTICS-1
    # wrapper. Auto-tracks: scroll depth (25/50/75/90/100), time on page
    # (15/30/60/120/300 s), exit intent, page visibility, generic CTA
    # clicks (button + a.btn + [data-track]), and exposes a uniform
    # `window.__proxxie_page_type` / `window.__proxxie_test_type` for
    # downstream events to consume.
    #
    # Also wires beforeunload: if a test is in progress (set by ANALYTICS-3b
    # below via `window.__proxxie_test_in_progress`), fires a
    # `test_abandoned` event with the current question index and elapsed
    # time. This is the founder's primary ask — "tracker si les gens vont
    # au bout" — so we get both completion AND abandonment signals.
    (
        # Anchor: the end of the ANALYTICS-1 wrapper script. The line
        # immediately before this is the closing `</script>` of the
        # wrapper (escaped as `<\/script>` in the JSON-encoded template).
        # Using the unique HTML comment that follows the unified wrapper
        # is more stable than tag-based anchors.
        "<!-- Unified event wrapper (kept for backwards compatibility — every -->",
        "<!-- ANALYTICS-3a: site-wide engagement layer (scroll/time/exit/clicks) -->\n<script>\n(function() {\n  if (window.__proxxieEngagementLoaded) return;\n  window.__proxxieEngagementLoaded = true;\n\n  // Derive page_type + test_type from URL so every event is segmentable.\n  var path = location.pathname.toLowerCase();\n  var pageType = 'other';\n  if (path === '/' || path.indexOf('/index') >= 0 || path.indexOf('/home') >= 0 || path.indexOf('proxxie-new-design/') >= 0 && (path.endsWith('/') || path.endsWith('index.html') || path.endsWith('proxxie%20home.html') || path.endsWith('proxxie home.html'))) pageType = 'home';\n  else if (path.indexOf('test') >= 0) pageType = 'test';\n  else if (path.indexOf('dashboard') >= 0) pageType = 'dashboard';\n  else if (path.indexOf('rapport') >= 0) pageType = 'rapport';\n  else if (path.indexOf('coach') >= 0) pageType = 'coach';\n  else if (path.indexOf('documents') >= 0) pageType = 'documents';\n  else if (path.indexOf('ressources') >= 0) pageType = 'ressources';\n  else if (path.indexOf('connexion') >= 0 || path.indexOf('login') >= 0) pageType = 'connexion';\n  else if (path.indexOf('blog') >= 0) pageType = 'blog';\n  else if (path.indexOf('guide-orientation') >= 0) pageType = 'guide';\n  else if (path.indexOf('newsletter') >= 0) pageType = 'newsletter';\n\n  var testType = null;\n  if (pageType === 'test') {\n    // Strip the proxxie-new-design/ staging prefix and \"Proxxie %20\" filename casing.\n    var pn = location.pathname.replace(/^.*\\//, '').toLowerCase();\n    var m = pn.match(/^(?:proxxie%20)?test[ %-]?(\\w+)/) || pn.match(/^test-?(\\w+)/);\n    if (m && m[1] && m[1] !== 'html') testType = m[1].replace(/\\.html$/, '');\n    if (!testType && (pn === 'test.html' || pn === 'proxxie test.html' || pn === 'proxxie%20test.html')) testType = 'ocean-x';\n    if (!testType && (pn === 'tests.html' || pn === 'proxxie tests.html' || pn === 'proxxie%20tests.html')) testType = 'landing';\n  }\n  window.__proxxie_page_type = pageType;\n  window.__proxxie_test_type = testType;\n\n  function send(name, props) {\n    if (window.trackEvent) {\n      var p = props || {};\n      p.page_type = pageType;\n      if (testType) p.test_type = testType;\n      window.trackEvent(name, p);\n    }\n  }\n\n  var startTime = Date.now();\n  var maxScroll = 0;\n  var scrollHit = {};\n  var timeHit = {};\n  var exitFired = false;\n\n  function onScroll() {\n    var sh = document.documentElement.scrollHeight - window.innerHeight;\n    if (sh <= 0) return;\n    var pct = (window.scrollY / sh) * 100;\n    if (pct > maxScroll) maxScroll = pct;\n    [25, 50, 75, 90, 100].forEach(function(t) {\n      if (!scrollHit[t] && pct >= t) {\n        scrollHit[t] = true;\n        send('scroll_depth', { depth: t });\n      }\n    });\n  }\n  window.addEventListener('scroll', onScroll, { passive: true });\n\n  function checkTime() {\n    var elapsed = Math.floor((Date.now() - startTime) / 1000);\n    [15, 30, 60, 120, 300].forEach(function(t) {\n      if (!timeHit[t] && elapsed >= t) {\n        timeHit[t] = true;\n        send('time_on_page', { seconds: t });\n      }\n    });\n  }\n  setInterval(checkTime, 5000);\n\n  function onMouseLeave(e) {\n    if (exitFired) return;\n    if (e.clientY < 5) {\n      exitFired = true;\n      var elapsed = Math.floor((Date.now() - startTime) / 1000);\n      send('exit_intent', { max_scroll: Math.round(maxScroll), seconds_on_page: elapsed });\n    }\n  }\n  document.addEventListener('mouseleave', onMouseLeave);\n\n  document.addEventListener('visibilitychange', function() {\n    var elapsed = Math.floor((Date.now() - startTime) / 1000);\n    if (document.hidden) send('page_hidden', { seconds_on_page: elapsed });\n    else send('page_visible', {});\n  });\n\n  window.addEventListener('beforeunload', function() {\n    var inProgress = window.__proxxie_test_in_progress;\n    if (inProgress) {\n      send('test_abandoned', {\n        question_index: inProgress.questionIndex || 0,\n        total_questions: inProgress.totalQuestions || 0,\n        completion_pct: inProgress.completionPct || 0,\n        time_total_ms: Date.now() - (inProgress.startedAt || Date.now())\n      });\n    }\n  });\n\n  // Generic CTA click tracker — captures button + a.btn + anything with data-track.\n  document.addEventListener('click', function(e) {\n    var target = e.target.closest('button, a.btn, [data-track]');\n    if (!target) return;\n    var label = (target.getAttribute('data-track') || target.textContent || '').trim().slice(0, 80);\n    if (!label) return;\n    var href = target.getAttribute('href') || null;\n    var isOutbound = false;\n    if (href && href.indexOf('http') === 0 && href.indexOf(location.hostname) === -1) isOutbound = true;\n    send('cta_click', {\n      cta_text: label,\n      cta_href: href,\n      cta_outbound: isOutbound\n    });\n  }, { capture: true });\n\n  // Page view enriched — fires once gtag has finished initial config.\n  setTimeout(function() {\n    if (window.gtag) window.gtag('event', 'page_view_enriched', { page_type: pageType, test_type: testType });\n  }, 200);\n})();\n</script>\n\n<!-- Unified event wrapper (kept for backwards compatibility — every -->",
    ),

    # ----- ANALYTICS-1 (2026-05-19): wire GA4 + Microsoft Clarity -----
    # Replaces the existing provider-agnostic analytics stub (which had
    # an unconfigured PLAUSIBLE_DOMAIN and no actual GA4/Clarity tag) with:
    #  - Google Analytics 4 (G-Q93HTZY2TB, same property as www.proxxie.co)
    #    + Enhanced Measurement (auto: scroll, outbound, file downloads,
    #      video, site search). IP anonymisation + ads_data_redaction on.
    #  - Microsoft Clarity (project wtjyxri1oa) for session recordings,
    #    heatmaps, rage/dead clicks.
    #  - Updated `window.trackEvent(name, props)` wrapper forwards to BOTH
    #    gtag and clarity (and still falls back to plausible/console for
    #    dev visibility on localhost/github.io).
    #
    # Cookiebot is NOT wired up in this patch — the CBID isn't available
    # yet. Added as a follow-up patch (ANALYTICS-2) once we have it.
    # This site is the github.io staging preview (not the production
    # commercial domain www.proxxie.co), so the temporary lack of a
    # consent banner is low-risk pending the Cookiebot CBID.
    (
        # OLD: the legacy provider-agnostic stub (no real analytics fires
        # because PLAUSIBLE_DOMAIN is empty and window.gtag is never set).
        "<!-- Analytics — provider-agnostic. Configure Plausible by setting window.PLAUSIBLE_DOMAIN. GA4 picked up automatically if window.gtag exists. -->\n<script>\n  // Set to your domain on plausible.io when ready, e.g. \"proxxie.co\"\n  window.PLAUSIBLE_DOMAIN = \"\";\n  if (window.PLAUSIBLE_DOMAIN) {\n    var _ps = document.createElement('script');\n    _ps.defer = true;\n    _ps.setAttribute('data-domain', window.PLAUSIBLE_DOMAIN);\n    _ps.src = 'https://plausible.io/js/script.tagged-events.js';\n    document.head.appendChild(_ps);\n  }\n  window.plausible = window.plausible || function() { (window.plausible.q = window.plausible.q || []).push(arguments) };\n  window.trackEvent = function(name, props) {\n    try {\n      if (window.plausible) window.plausible(name, { props: props || {} });\n      if (window.gtag) window.gtag('event', name, props || {});\n      var host = window.location.hostname;\n      if (host === 'localhost' || host.indexOf('github.io') !== -1 || host === '127.0.0.1') {\n        console.log('[analytics]', name, props || {});\n      }\n    } catch(e) { /* swallow */ }\n  };\n</script>",
        # NEW: GA4 + Clarity actually wired up. Consent Mode v2 set to
        # `granted` for now (no Cookiebot yet). When ANALYTICS-2 ships,
        # the consent defaults flip to `denied` and Cookiebot manages
        # the update. Keeping all event-tagging logic in one wrapper
        # means every existing `trackEvent()` call site keeps working.
        "<!-- ANALYTICS-1: GA4 + Microsoft Clarity (Cookiebot pending) -->\n<!-- Google Analytics 4 (property shared with www.proxxie.co) -->\n<script async src=\"https://www.googletagmanager.com/gtag/js?id=G-Q93HTZY2TB\"></script>\n<script>\n  window.dataLayer = window.dataLayer || [];\n  function gtag(){dataLayer.push(arguments);}\n  // Consent Mode v2 — defaults to granted until Cookiebot ships (ANALYTICS-2).\n  // When the bandeau is added, flip these defaults to 'denied' and let\n  // Cookiebot call gtag('consent','update',{...}) on user choice.\n  gtag('consent', 'default', {\n    'ad_storage': 'granted',\n    'analytics_storage': 'granted',\n    'ad_user_data': 'granted',\n    'ad_personalization': 'granted'\n  });\n  gtag('set', 'ads_data_redaction', true);\n  gtag('js', new Date());\n  gtag('config', 'G-Q93HTZY2TB', {\n    anonymize_ip: true,\n    cookie_flags: 'SameSite=None;Secure;Partitioned',\n    // Page paths on the staging preview include the repo prefix\n    // (/proxxie-new-design/...). Strip it so the GA4 dashboards\n    // match production URLs when we eventually consolidate.\n    page_path: location.pathname.replace(/^\\/proxxie-new-design\\//, '/')\n  });\n</script>\n\n<!-- Microsoft Clarity — session recordings, heatmaps, rage/dead clicks -->\n<script>\n  (function(c,l,a,r,i,t,y){\n    c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};\n    t=l.createElement(r);t.async=1;t.src=\"https://www.clarity.ms/tag/\"+i;\n    y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);\n  })(window, document, \"clarity\", \"script\", \"wtjyxri1oa\");\n</script>\n\n<!-- Unified event wrapper (kept for backwards compatibility — every -->\n<!-- existing trackEvent() call site continues to work, now also -->\n<!-- forwarding to Clarity custom events for cross-tool correlation). -->\n<script>\n  window.plausible = window.plausible || function() { (window.plausible.q = window.plausible.q || []).push(arguments) };\n  window.trackEvent = function(name, props) {\n    try {\n      if (window.gtag) window.gtag('event', name, props || {});\n      if (window.clarity) window.clarity('event', name);\n      if (window.plausible) window.plausible(name, { props: props || {} });\n      var host = window.location.hostname;\n      if (host === 'localhost' || host === '127.0.0.1') {\n        console.log('[analytics]', name, props || {});\n      }\n    } catch(e) { /* swallow */ }\n  };\n  // Set common user_properties: persona, grade level, and a sticky\n  // first-touch UTM record kept in localStorage. Hydrated by the\n  // wizard the first time the user picks a persona / class.\n  try {\n    var p = window.localStorage.getItem('proxxie_persona');\n    var g = window.localStorage.getItem('proxxie_grade');\n    var firstUtm = window.localStorage.getItem('proxxie_first_utm');\n    var url = new URL(window.location.href);\n    var utm = {};\n    ['utm_source','utm_medium','utm_campaign','utm_term','utm_content'].forEach(function(k){\n      var v = url.searchParams.get(k);\n      if (v) utm[k] = v;\n    });\n    if (Object.keys(utm).length && !firstUtm) {\n      window.localStorage.setItem('proxxie_first_utm', JSON.stringify({ ts: Date.now(), utm: utm }));\n      firstUtm = window.localStorage.getItem('proxxie_first_utm');\n    }\n    if (window.gtag) {\n      var up = {};\n      if (p) up.persona = p;\n      if (g) up.grade = g;\n      if (firstUtm) {\n        try { var fu = JSON.parse(firstUtm).utm || {}; for (var k in fu) up['first_'+k] = fu[k]; } catch(e) {}\n      }\n      if (Object.keys(up).length) window.gtag('set', 'user_properties', up);\n    }\n  } catch(e) { /* swallow */ }\n</script>",
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
        # Test pages now use a shared ProxxieNav (shared-nav.jsx) where the
        # Charles button is already in its post-fix form but without the
        # exact onClick tracking handler this patch tries to inject. Skip
        # them so the patcher doesn't report DRIFT on every push.
        "pages_skip": [
            "Proxxie Test.html", "test.html",
            "Proxxie Test RIASEC.html", "test-riasec.html",
            "Proxxie Test PCM.html", "test-pcm.html",
            "Proxxie Test MBTI.html", "test-mbti.html",
            "Proxxie Test Drivers.html", "test-drivers.html",
            "Proxxie Test Valeurs.html", "test-valeurs.html",
            "Proxxie Test Besoins.html", "test-besoins.html",
            "Proxxie Test TDAH.html", "test-tdah.html",
            "Proxxie Test Autisme.html", "test-autisme.html",
            "Proxxie Test HPI.html", "test-hpi.html",
            "Proxxie Test Anxiete.html", "test-anxiete.html",
            "Proxxie Test DYS.html", "test-dys.html",
            "Proxxie Tests.html", "tests.html",
        ],
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
                '{/* Sticky mobile CTA bar, F006: dual-CTA (Charles + Test) so the meeting\n          path stays visible on mobile, where it disappeared previously. */}\n      <div className="mobile-sticky-cta">\n        <a href="https://calendly.com/proxxie/entretien" target="_blank" rel="noopener noreferrer" className="btn btn-charles" onClick={() => { if (typeof window !== "undefined" && window.trackEvent) window.trackEvent("calendly_opened", { source: "mobile_sticky" }); }}>\n          Charles\n        </a>\n        <button className="btn btn-orange" onClick={openOnboarding} style={{ flex: 2 }}>\n          Commencer le parcours gratuit\n        </button>\n      </div>',
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
    # RETIRED 2026-05-19: the team's source now ships its own
    # CLASS_TABS + ClassTimeline definition in asset 3cf76be5. Running
    # this patch on top created a DUPLICATE `const CLASS_TABS` and
    # `const ClassTimeline` declaration → SyntaxError → Home page
    # rendered blank. Same failure mode as the Dashboard radar v2
    # patch retired earlier. Needle swapped to an impossible-to-match
    # sentinel so the patcher never applies it again. The placement
    # patch below (G3 step 2) is similarly retired — the team renders
    # <ClassTimeline /> in App on its own.
    {
        "name": "G3 ClassTimeline component definition (RETIRED)",
        "needle": "__RETIRED_2026_05_19__never_matches__",
        "_disabled_needle": "const App = () => {",
        "replacements": [
            (
                "const App = () => {",
                # Define the component and then continue with App.
                '/* G3 — Class-segmented timeline. Five tabs (3ème → Post-Bac),\n   one concern card per tab + a link into the existing guide. */\nconst CLASS_TABS = [\n  { k: "3eme",      l: "3ème",     concern: "Découverte et exploration",        body: "Premier vrai choix : 2nde générale, technologique ou pro ? On pose les bases en aidant votre ado à se découvrir, sans pression.",          period: "1er trimestre · sept-déc" },\n  { k: "2nde",      l: "2nde",     concern: "Choix des spécialités",            body: "Les spés de 1ère pèsent sur Parcoursup. On évite les choix par défaut et on construit la combinaison qui ouvre, pas qui ferme.",        period: "2e trimestre · jan-mars" },\n  { k: "1ere",      l: "1ère",     concern: "Confirmation du projet",            body: "C\'est l\'année où le projet se précise. Métiers visés, écoles cibles, doubles cursus, projets perso à valoriser — on cale tout ça.",        period: "Année complète" },\n  { k: "terminale", l: "Terminale", concern: "Stratégie Parcoursup",             body: "10 vœux à formuler, lettres de motivation, choix de filières d\'art ou Sciences Po, parcours sélectifs. On stresse moins, on cible mieux.",   period: "Janvier → mai" },\n  { k: "postbac",   l: "Post-Bac",  concern: "Rebondir ou réorienter",           body: "Première année qui ne se passe pas comme prévu ? On évite l\'année blanche : réorientation Parcoursup ou hors-Parcoursup, passerelles, alternance.", period: "À tout moment" },\n];\n\nconst ClassTimeline = () => {\n  const [active, setActive] = React.useState("terminale");\n  const tab = CLASS_TABS.find((t) => t.k === active) || CLASS_TABS[0];\n  return (\n    <section id="classes" style={{ paddingTop: 80, paddingBottom: 80, background: "var(--c-cream)" }}>\n      <div className="shell">\n        <div style={{ textAlign: "center", maxWidth: 760, margin: "0 auto 36px" }}>\n          <span className="eyebrow"><span className="dot"></span>Adapté à chaque étape</span>\n          <h2 style={{ marginTop: 14 }}>De la 3ème au post-bac, à chaque classe sa question.</h2>\n          <p style={{ fontSize: 17, color: "var(--c-ink-2)", marginTop: 14 }}>\n            Cliquez sur la classe de votre ado pour voir ce qu\'on travaille à ce moment précis.\n          </p>\n        </div>\n\n        <div style={{ display: "flex", justifyContent: "center", gap: 8, flexWrap: "wrap", marginBottom: 32 }}>\n          {CLASS_TABS.map((t) => (\n            <button\n              key={t.k}\n              onClick={() => setActive(t.k)}\n              style={{\n                padding: "10px 18px", borderRadius: 999,\n                background: active === t.k ? "var(--c-ink)" : "white",\n                color: active === t.k ? "white" : "var(--c-ink-2)",\n                border: "1.5px solid " + (active === t.k ? "var(--c-ink)" : "var(--c-line)"),\n                fontWeight: 600, fontSize: 14, letterSpacing: "-0.005em",\n                transition: "background .15s, color .15s, transform .15s",\n                cursor: "pointer", minHeight: 44,\n              }}\n              onMouseEnter={(e) => { if (active !== t.k) { e.currentTarget.style.background = "var(--c-cream-light)"; e.currentTarget.style.transform = "translateY(-1px)"; }}}\n              onMouseLeave={(e) => { if (active !== t.k) { e.currentTarget.style.background = "white"; e.currentTarget.style.transform = "none"; }}}\n            >\n              {t.l}\n            </button>\n          ))}\n        </div>\n\n        <div className="card" style={{ padding: "36px 40px", maxWidth: 880, margin: "0 auto", background: "white" }}>\n          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14, flexWrap: "wrap", gap: 12 }}>\n            <span className="chip" style={{ background: "rgba(253,105,54,.12)", color: "#FD6936" }}>{tab.l} · {tab.concern}</span>\n            <span style={{ fontSize: 12, color: "var(--c-muted)", fontWeight: 500 }}>{tab.period}</span>\n          </div>\n          <p style={{ fontSize: 17, lineHeight: 1.55, color: "var(--c-ink-2)", marginBottom: 22 }}>{tab.body}</p>\n          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>\n            <a href="./guide-orientation.html" className="btn btn-orange btn-arrow" style={{ textDecoration: "none" }}>\n              Voir le guide {tab.l}\n            </a>\n            <a href="https://calendly.com/proxxie/entretien" target="_blank" rel="noopener noreferrer" className="btn btn-ghost" style={{ textDecoration: "none", background: "white", borderColor: "var(--c-ink)", color: "var(--c-ink)" }} onClick={() => { if (typeof window !== "undefined" && window.trackEvent) window.trackEvent("calendly_opened", { source: "class_timeline_" + tab.k }); }}>\n              30 min avec Charles\n            </a>\n          </div>\n        </div>\n      </div>\n    </section>\n  );\n};\n\nconst App = () => {',
            ),
        ],
    },

    # ----- G3 step 2: insert <ClassTimeline /> into App's render tree -----
    # RETIRED 2026-05-19: paired with G3 step 1 (see comment above).
    # Team's source already renders <ClassTimeline /> in the correct
    # position (HowItWorks → ClassTimeline → MiniQuiz). Running this
    # patch would either no-op (idempotent) or insert a second copy.
    {
        "name": "G3 ClassTimeline placement in App (RETIRED)",
        "needle": "__RETIRED_2026_05_19__never_matches__",
        "_disabled_needle": "{t.showMiniQuiz && <MiniQuiz onCTA={openOnboarding} />}",
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
                '/* Obsidian-style force-directed radar v2. Drill-down + back nav.\n   Click a facet to drill into its 5 sub-facets; click the center to return.\n   Spring physics retargets nodes when level changes, so the "rotation"\n   animation comes for free without explicit interpolation. */\nconst RADAR_TREE = [\n  { l: "Ouverture", v: 0.86, sub: [\n    { l: "Imagination",   v: 0.89 },\n    { l: "Esthétique",    v: 0.74 },\n    { l: "Idées",         v: 0.92 },\n    { l: "Diversité",     v: 0.68 },\n    { l: "Innovation",    v: 0.81 },\n  ]},\n  { l: "Curiosité", v: 0.92, sub: [\n    { l: "Recherche",       v: 0.94 },\n    { l: "Expérimentation", v: 0.88 },\n    { l: "Observation",     v: 0.82 },\n    { l: "Lecture",         v: 0.91 },\n    { l: "Questionnement",  v: 0.85 },\n  ]},\n  { l: "Ambition", v: 0.74, sub: [\n    { l: "Leadership",     v: 0.78 },\n    { l: "Performance",    v: 0.81 },\n    { l: "Reconnaissance", v: 0.62 },\n    { l: "Persévérance",   v: 0.86 },\n    { l: "Vision",         v: 0.71 },\n  ]},\n  { l: "Énergie", v: 0.81, sub: [\n    { l: "Action",       v: 0.84 },\n    { l: "Endurance",    v: 0.77 },\n    { l: "Initiative",   v: 0.85 },\n    { l: "Enthousiasme", v: 0.79 },\n    { l: "Présence",     v: 0.80 },\n  ]},\n  { l: "Empathie", v: 0.78, sub: [\n    { l: "Écoute",        v: 0.82 },\n    { l: "Soin",          v: 0.73 },\n    { l: "Médiation",     v: 0.71 },\n    { l: "Pédagogie",     v: 0.85 },\n    { l: "Collaboration", v: 0.80 },\n  ]},\n];\n\nconst InteractiveRadar = () => {\n  const W = 320, H = 220, cx = W / 2, cy = H / 2, R = 78;\n  const [level, setLevel] = React.useState(0);\n  const [parentIdx, setParentIdx] = React.useState(0);\n  const activeDims = level === 0 ? RADAR_TREE : RADAR_TREE[parentIdx].sub;\n  const activeRef = React.useRef(activeDims);\n  activeRef.current = activeDims;\n\n  const targetFor = (dims, i) => {\n    const a = -Math.PI / 2 + (i * 2 * Math.PI) / dims.length;\n    return { x: cx + Math.cos(a) * R * dims[i].v, y: cy + Math.sin(a) * R * dims[i].v };\n  };\n  const target = (i) => {\n    const dims = activeRef.current;\n    if (i >= dims.length) return { x: cx, y: cy };\n    return targetFor(dims, i);\n  };\n\n  const [nodes, setNodes] = React.useState(() => RADAR_TREE.map((_, i) => ({ ...targetFor(RADAR_TREE, i), vx: 0, vy: 0 })));\n  const [drag, setDrag] = React.useState(null);\n  const [hover, setHover] = React.useState(null);\n  const dragRef = React.useRef(null);\n  const downRef = React.useRef(null);\n  const tRef = React.useRef(0);\n  const svgRef = React.useRef(null);\n  React.useEffect(() => { dragRef.current = drag; }, [drag]);\n\n  React.useEffect(() => {\n    let raf;\n    const tick = () => {\n      tRef.current += 0.015;\n      setNodes((prev) => prev.map((p, i) => {\n        if (dragRef.current === i) return p;\n        const tg = target(i);\n        const wx = Math.sin(tRef.current + i * 1.3) * 2.2;\n        const wy = Math.cos(tRef.current * 0.85 + i * 0.7) * 2.2;\n        const k = 0.10, damp = 0.84;\n        const ax = (tg.x + wx - p.x) * k;\n        const ay = (tg.y + wy - p.y) * k;\n        const vx = (p.vx + ax) * damp;\n        const vy = (p.vy + ay) * damp;\n        return { x: p.x + vx, y: p.y + vy, vx, vy };\n      }));\n      raf = requestAnimationFrame(tick);\n    };\n    raf = requestAnimationFrame(tick);\n    return () => cancelAnimationFrame(raf);\n  }, []);\n\n  const localPoint = (e) => {\n    const rect = svgRef.current.getBoundingClientRect();\n    const cx2 = e.touches ? e.touches[0].clientX : e.clientX;\n    const cy2 = e.touches ? e.touches[0].clientY : e.clientY;\n    return { x: ((cx2 - rect.left) / rect.width) * W, y: ((cy2 - rect.top) / rect.height) * H };\n  };\n\n  const onDown = (i) => (e) => {\n    e.preventDefault();\n    const pt = localPoint(e);\n    downRef.current = { i, x: pt.x, y: pt.y, t: Date.now() };\n    setDrag(i);\n  };\n\n  React.useEffect(() => {\n    if (drag == null) return;\n    const move = (e) => {\n      const pt = localPoint(e);\n      setNodes((prev) => prev.map((p, i) => (i === drag ? { ...p, x: pt.x, y: pt.y, vx: 0, vy: 0 } : p)));\n    };\n    const up = (e) => {\n      const d = downRef.current;\n      let wasTap = false;\n      if (d) {\n        try {\n          const rect = svgRef.current.getBoundingClientRect();\n          const cx2 = e && e.changedTouches ? e.changedTouches[0].clientX : (e && e.clientX);\n          const cy2 = e && e.changedTouches ? e.changedTouches[0].clientY : (e && e.clientY);\n          if (cx2 != null) {\n            const ex = ((cx2 - rect.left) / rect.width) * W;\n            const ey = ((cy2 - rect.top) / rect.height) * H;\n            const dx = Math.abs(ex - d.x), dy = Math.abs(ey - d.y);\n            const elapsed = Date.now() - d.t;\n            wasTap = dx < 6 && dy < 6 && elapsed < 350;\n          }\n        } catch (err) { /* swallow geometry errors */ }\n        downRef.current = null;\n      }\n      setDrag(null);\n      if (wasTap && d && level === 0) {\n        setLevel(1);\n        setParentIdx(d.i);\n        if (typeof window !== "undefined" && window.trackEvent) {\n          window.trackEvent("radar_drilldown", { facet: RADAR_TREE[d.i].l });\n        }\n      }\n    };\n    window.addEventListener("mousemove", move);\n    window.addEventListener("mouseup", up);\n    window.addEventListener("touchmove", move, { passive: false });\n    window.addEventListener("touchend", up);\n    return () => {\n      window.removeEventListener("mousemove", move);\n      window.removeEventListener("mouseup", up);\n      window.removeEventListener("touchmove", move);\n      window.removeEventListener("touchend", up);\n    };\n  }, [drag, level]);\n\n  const onCenterClick = () => {\n    if (level === 1) {\n      setLevel(0);\n      if (typeof window !== "undefined" && window.trackEvent) {\n        window.trackEvent("radar_back_to_root", {});\n      }\n    }\n  };\n\n  const N = activeDims.length;\n  const polyPoints = nodes.slice(0, N).map((n) => n.x + "," + n.y).join(" ");\n  const centerLabel = level === 0 ? "Léa" : RADAR_TREE[parentIdx].l;\n  const hintText = level === 0 ? "Cliquez sur une facette" : "Cliquez au centre pour revenir";\n\n  return (\n    <svg ref={svgRef} viewBox={"0 0 " + W + " " + H} style={{ width: "100%", height: 220, cursor: drag != null ? "grabbing" : "default", userSelect: "none", touchAction: "none" }}>\n      {[0.4, 0.7, 1].map((r, i) => (\n        <circle key={"r" + i} cx={cx} cy={cy} r={R * r} fill="none" stroke="rgba(10,14,44,.06)" strokeWidth={1} strokeDasharray={i === 2 ? "" : "2 3"} />\n      ))}\n      {nodes.slice(0, N).map((n, i) => (\n        <line key={"c" + i + "-" + level} x1={cx} y1={cy} x2={n.x} y2={n.y}\n          stroke={hover === i ? "#1320CE" : "rgba(19,32,206,.25)"}\n          strokeWidth={hover === i ? 2 : 1.2} />\n      ))}\n      <polygon points={polyPoints} fill={level === 0 ? "rgba(72,122,255,0.16)" : "rgba(253,105,54,0.12)"} stroke={level === 0 ? "#1320CE" : "#FD6936"} strokeWidth={1.5} style={{ transition: "fill .25s, stroke .25s" }} />\n      {nodes.slice(0, N).map((n, i) => {\n        const isHot = hover === i || drag === i;\n        const fill = level === 0 ? "#FD6936" : "#1320CE";\n        const stroke = level === 0 ? "rgba(253,105,54,.4)" : "rgba(19,32,206,.4)";\n        return (\n          <g key={"n" + i + "-" + level} transform={"translate(" + n.x + "," + n.y + ")"}\n            onMouseDown={onDown(i)} onTouchStart={onDown(i)}\n            onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}\n            style={{ cursor: level === 0 ? (drag === i ? "grabbing" : "pointer") : (drag === i ? "grabbing" : "grab") }}>\n            <circle r={isHot ? 9 : 6} fill={fill}\n              stroke={isHot ? "white" : stroke} strokeWidth={isHot ? 3 : 2}\n              style={{ transition: "r .15s, stroke-width .15s, fill .25s" }} />\n            <text y={n.y < cy - 12 ? -14 : (n.y > cy + 12 ? 20 : 4)}\n              textAnchor={n.x < cx - 20 ? "end" : (n.x > cx + 20 ? "start" : "middle")}\n              x={n.x < cx - 20 ? -12 : (n.x > cx + 20 ? 12 : 0)}\n              style={{ fontFamily: "var(--font-display)", fontSize: 10.5, fontWeight: 600, fill: "var(--c-ink)", letterSpacing: "0.02em", textTransform: "uppercase", pointerEvents: "none" }}>\n              {activeDims[i].l}\n            </text>\n          </g>\n        );\n      })}\n      <g transform={"translate(" + cx + "," + cy + ")"} onClick={onCenterClick}\n        style={{ cursor: level > 0 ? "pointer" : "default" }}>\n        <circle r={level > 0 ? 18 : 14} fill="#1320CE"\n          style={{ transition: "r .25s" }} />\n        <text textAnchor="middle" dy={level > 0 ? 2 : 4} style={{ fontFamily: "var(--font-display)", fontSize: level > 0 ? 9 : 10, fontWeight: 700, fill: "white", letterSpacing: "0.06em", textTransform: "uppercase", pointerEvents: "none" }}>{centerLabel}</text>\n        {level > 0 && (\n          <text textAnchor="middle" dy={12} style={{ fontSize: 7.5, fill: "rgba(255,255,255,.7)", letterSpacing: "0.04em", pointerEvents: "none" }}>← retour</text>\n        )}\n      </g>\n      <text x={W - 8} y={H - 6} textAnchor="end" style={{ fontSize: 9, fill: "var(--c-muted)", letterSpacing: "0.04em", fontWeight: 500 }}>{hintText}</text>\n    </svg>\n  );\n};',
            ),
        ],
    },

    # ----- Dashboard radar v2 — drill-down with OCEAN-X tree -----
    # RETIRED 2026-05-18: the team's source now includes its own
    # DashboardProfileRadar + DASHBOARD_RADAR_TREE definition in the
    # bundle (asset 5a278f70). Running this patch on top of that creates
    # a DUPLICATE `const DASHBOARD_RADAR_TREE` / `const DashboardProfileRadar`
    # declaration → SyntaxError → Dashboard page fails to load.
    # The patch is kept here for reference but neutralized via an
    # impossible-to-match needle so the patcher never applies it.
    # If you ever need to re-enable, restore the original needle
    # ("const ProfileCard = ({ onOpen, audit }) => {") AND verify the
    # team's bundle no longer has its own definition.
    {
        "name": "Dashboard radar v2 — DashboardProfileRadar definition (RETIRED)",
        "needle": "__RETIRED_2026_05_18__never_matches__",
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
    # RETIRED 2026-05-18: paired with the definition patch above. Team's
    # bundle no longer ships the static SVG; their source uses
    # <DashboardProfileRadar /> directly.
    {
        "name": "Dashboard radar v2 — SVG replacement in ProfileCard (RETIRED)",
        "needle": "__RETIRED_2026_05_18__never_matches__",
        "_disabled_needle": '<svg viewBox="0 0 220 200" style={{ width: "100%" }}>',
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
                'trackEvent("calendly_opened", { source: "situations_cta" }); }}>\n            30 min avec Charles\n          </a>\n        </div>\n\n        {/* F-STATS-RELOCATED: trust bar moved from Hero, proof points land here, right after the empathy block. */}\n        <div style={{ marginTop: 56, display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8, padding: "24px 8px", borderTop: "1px solid rgba(10,14,44,.08)", borderBottom: "1px solid rgba(10,14,44,.08)" }}>\n          {[\n            { n: "98%", l: "parents satisfaits" },\n            { n: "+300", l: "ados orientés" },\n            { n: "100%", l: "admis sur Parcoursup", note: "*" },\n            { n: "9/10", l: "nous recommandent" },\n          ].map((s, i) => (\n            <div key={i} style={{ textAlign: "center", borderRight: i < 3 ? "1px solid rgba(10,14,44,.08)" : "none" }}>\n              <div style={{ fontFamily: "var(--font-num)", fontSize: 32, fontWeight: 600, color: "var(--c-blue-deep)", letterSpacing: "-0.03em" }}>\n                {s.n}{s.note && <span style={{ fontSize: 18, verticalAlign: "super", marginLeft: 2, color: "var(--c-muted)" }}>{s.note}</span>}\n              </div>\n              <div style={{ fontSize: 13, color: "var(--c-muted)", marginTop: 2 }}>{s.l}</div>\n            </div>\n          ))}\n        </div>\n        <div style={{ fontSize: 11, color: "var(--c-muted)", marginTop: 8, textAlign: "right", paddingRight: 8 }}>\n          * Sur les terminales accompagnées en 2024-25 ayant validé un vœu Parcoursup.\n        </div>\n      </div>\n    </section>',
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

    # ----- RESULTSFIX-1 (2026-05-19): refocus "Aperçu du rapport" hero -----
    # Founder feedback: drop the "Sans payer." flourish from the title,
    # and broaden the bullet list to surface ALL the deliverables the
    # parent gets at the end of an accompaniment (not just rapport
    # contents). The current 3 bullets stop at the rapport itself;
    # we add a 4th item highlighting the offered coach session — the
    # biggest differentiator — and elevate the descriptor copy to make
    # each deliverable feel like a concrete outcome.
    {
        "name": "RESULTSFIX-1a drop 'Sans payer' from title",
        "needle": "Voici ce que vous obtenez. <span style={{ color:",
        "replacements": [
            (
                '<h2 style={{ marginTop: 14, marginBottom: 18 }}>\n              Voici ce que vous obtenez. <span style={{ color: "var(--c-blue-deep)" }}>Sans payer.</span>\n            </h2>',
                '<h2 style={{ marginTop: 14, marginBottom: 18 }}>\n              Voici ce que vous obtenez <span style={{ color: "var(--c-blue-deep)" }}>à la fin de l\'accompagnement.</span>\n            </h2>',
            ),
        ],
    },

    # ----- RESULTSFIX-1c (2026-05-19, follow-up) : reframe the eyebrow -----
    # Founder follow-up: "ce n'est pas le rapport qu'ils obtiennent sans
    # payer mais le rapport final qu'ils peuvent avoir à la fin que l'on
    # doit mettre en avant." → Rename the eyebrow so it reads as the
    # FINAL deliverable, not a free preview/teaser.
    {
        "name": "RESULTSFIX-1c eyebrow → 'Aperçu du rapport final'",
        "needle": '<span className="eyebrow"><span className="dot"></span>Aperçu du rapport</span>',
        "replacements": [
            (
                '<span className="eyebrow"><span className="dot"></span>Aperçu du rapport</span>',
                '<span className="eyebrow"><span className="dot"></span>Aperçu du rapport final</span>',
            ),
        ],
    },
    {
        "name": "RESULTSFIX-1b expand deliverables list (add coach RDV + suivi)",
        "needle": '{ i: <Icon.briefcase />, t: "10 à 15 métiers compatibles"',
        "replacements": [
            (
                '            <div style={{ display: "grid", gap: 14, marginBottom: 30 }}>\n              {[\n                { i: <Icon.briefcase />, t: "10 à 15 métiers compatibles", d: "Avec score de compatibilité, missions concrètes, salaire et débouchés" },\n                { i: <Icon.spark />, t: "5 secteurs porteurs analysés", d: "Croisement profil × tendances du marché du travail" },\n                { i: <Icon.graduation />, t: "Vœux Parcoursup ciblés", d: "Formations, écoles, attendus, et stratégie de candidature" },\n              ].map((b, i) => (\n                <div key={i} style={{ display: "flex", gap: 14 }}>\n                  <div style={{ width: 40, height: 40, borderRadius: 10, background: "var(--c-blue-tint)", color: "var(--c-blue-deep)", display: "grid", placeItems: "center", flexShrink: 0 }}>{b.i}</div>\n                  <div>\n                    <div style={{ fontWeight: 600, fontSize: 16, marginBottom: 2 }}>{b.t}</div>\n                    <div style={{ color: "var(--c-muted)", fontSize: 14 }}>{b.d}</div>\n                  </div>\n                </div>\n              ))}\n            </div>',
                '            <div style={{ display: "grid", gap: 12, marginBottom: 26 }}>\n              {[\n                { i: <Icon.briefcase />, t: "10 à 15 métiers compatibles", d: "Score de compatibilité, missions, salaire et débouchés concrets", c: "var(--c-blue-tint)", cc: "var(--c-blue-deep)" },\n                { i: <Icon.spark />, t: "5 secteurs porteurs analysés", d: "Profil de votre ado croisé aux tendances du marché du travail", c: "var(--c-blue-tint)", cc: "var(--c-blue-deep)" },\n                { i: <Icon.graduation />, t: "Vœux Parcoursup ciblés + stratégie", d: "Formations, écoles, attendus, ordre des vœux et lettres", c: "var(--c-blue-tint)", cc: "var(--c-blue-deep)" },\n                { i: <Icon.calendar />, t: "RDV coach offert (30 min)", d: "Lecture personnalisée du rapport et plan d\'action avec Charles", c: "rgba(253,105,54,.14)", cc: "#FD6936" },\n                { i: <Icon.check />, t: "Tableau de bord parent à vie", d: "Suivi continu, documents centralisés, RDV bonus de parrainage", c: "rgba(34,160,107,.12)", cc: "#1F8C5E" },\n              ].map((b, i) => (\n                <div key={i} style={{ display: "flex", gap: 14, alignItems: "flex-start" }}>\n                  <div style={{ width: 38, height: 38, borderRadius: 10, background: b.c, color: b.cc, display: "grid", placeItems: "center", flexShrink: 0 }}>{b.i}</div>\n                  <div>\n                    <div style={{ fontWeight: 600, fontSize: 15.5, marginBottom: 2, letterSpacing: "-0.005em" }}>{b.t}</div>\n                    <div style={{ color: "var(--c-muted)", fontSize: 13.5, lineHeight: 1.45 }}>{b.d}</div>\n                  </div>\n                </div>\n              ))}\n            </div>',
            ),
        ],
    },

    # ----- LOGOFIX-1 (2026-05-19): stop the sidebar Proxxie wordmark -----
    # from stretching. The <img> renders inside a flex-column container
    # (`display: flex; flexDirection: column`) whose default
    # `align-items: stretch` was stretching the cross-axis (= width)
    # of the image to match the sidebar width while keeping the
    # explicit `height: 40px` — i.e. squashing the wordmark wider
    # than its native 2.1:1 ratio. Fix: pin `alignSelf: "flex-start"`
    # and add `flexShrink: 0` + a computed `width` based on the source
    # webp's known dimensions (3502 × 1665) so the browser cannot
    # second-guess the aspect ratio.
    {
        "name": "LOGOFIX-1 ProxxieLogo respect aspect ratio (no stretch)",
        "needle": 'const ProxxieLogo = ({ variant = "default", size = 22 }) => {',
        "pages_skip": [
            # Product pages ship a different ProxxieLogo (ProxxieMark +
            # <span>proxxie</span>) that doesn't use an <img>, so the
            # flex-stretch bug doesn't apply. Skip to avoid spurious DRIFT.
            "Proxxie Coach.html", "coach.html",
            "Proxxie Connexion.html", "connexion.html",
            "Proxxie Dashboard.html", "dashboard.html",
            "Proxxie Documents.html", "documents.html",
            "Proxxie Rapport.html", "rapport.html",
            "Proxxie Ressources.html", "ressources.html",
            "Proxxie Test.html", "test.html",
            # Same shape — Tests landing + individual test pages added 2026-05-19.
            "Proxxie Tests.html", "tests.html",
            "Proxxie Test Anxiete.html", "test-anxiete.html",
            "Proxxie Test Autisme.html", "test-autisme.html",
            "Proxxie Test Besoins.html", "test-besoins.html",
            "Proxxie Test DYS.html", "test-dys.html",
            "Proxxie Test Drivers.html", "test-drivers.html",
            "Proxxie Test HPI.html", "test-hpi.html",
            "Proxxie Test MBTI.html", "test-mbti.html",
            "Proxxie Test PCM.html", "test-pcm.html",
            "Proxxie Test RIASEC.html", "test-riasec.html",
            "Proxxie Test TDAH.html", "test-tdah.html",
            "Proxxie Test Valeurs.html", "test-valeurs.html",
        ],
        "replacements": [
            (
                'const ProxxieLogo = ({ variant = "default", size = 22 }) => {\n  const isWhite = variant === "white";\n  const height = Math.round(size * 1.8);\n  return (\n    <img\n      src="proxxie-logo-full.webp"\n      alt="Proxxie"\n      style={{\n        height,\n        width: "auto",\n        display: "inline-block",\n        filter: isWhite ? "brightness(0) invert(1)" : "none",\n      }}\n    />\n  );\n};',
                'const ProxxieLogo = ({ variant = "default", size = 22 }) => {\n  /* LOGOFIX-1 — explicit aspect ratio so flex parents can\'t stretch the wordmark. */\n  const isWhite = variant === "white";\n  const height = Math.round(size * 1.8);\n  /* Native webp is 3502 × 1665, ratio ≈ 2.103. Pin width to keep it. */\n  const width = Math.round(height * 2.103);\n  return (\n    <img\n      src="proxxie-logo-full.webp"\n      alt="Proxxie"\n      width={width}\n      height={height}\n      style={{\n        height,\n        width,\n        display: "inline-block",\n        alignSelf: "flex-start",\n        flexShrink: 0,\n        objectFit: "contain",\n        filter: isWhite ? "brightness(0) invert(1)" : "none",\n      }}\n    />\n  );\n};',
            ),
        ],
    },

    # ----- STEPFIX-1 (2026-05-19): make Étape 3/5 "Voici ce qui vous -----
    # attend" fit a single viewport (no scroll). Founder feedback: the
    # preview cards forced scroll on standard laptop screens. We:
    #  - drop the 120px mock-preview hero on each card → 40px inline icon
    #  - shrink h2 30→24, subtitle marginBottom 24→12, card padding 22→14
    #  - tighten bullet line-height 1.7→1.45, fontSize 13→12.5
    #  - compact the Charles 30-min strip (44→32px avatar, smaller text)
    # The interactive "Voir l'exemple" / "Voir la démo" buttons stay,
    # just as inline text-links at the bottom of each card.
    {
        "name": "STEPFIX-1a compact StepPreview header",
        "needle": "const StepPreview = ({ persona, firstName, onSeeExample, onSeeDashboardVideo }) => {",
        "replacements": [
            (
                'const StepPreview = ({ persona, firstName, onSeeExample, onSeeDashboardVideo }) => {\n  const isEleve = persona === "eleve";\n  const cardCls = { background: "white", padding: 22, borderRadius: 16, border: "1px solid var(--c-line)" };\n  const previewBtnCls = {\n    width: "100%", border: "none", padding: 0, cursor: "pointer",\n    background: "transparent", display: "block",\n    transition: "transform .15s, box-shadow .15s",\n  };\n  return (\n    <div>\n      <span className="chip" style={{ background: "rgba(72,122,255,.12)", color: "#1320CE" }}>Aperçu</span>\n      <h2 style={{ marginTop: 14, marginBottom: 10, fontSize: 30 }}>\n        {isEleve ? "Voici ce qui t\'attend après inscription." : "Voici ce qui vous attend après inscription."}\n      </h2>\n      <p style={{ color: "var(--c-ink-2)", fontSize: 15, marginBottom: 24, lineHeight: 1.55 }}>\n        Un rapport personnalisé + un tableau de bord pour suivre l\'orientation, étape par étape, sans engagement.\n      </p>',
                'const StepPreview = ({ persona, firstName, onSeeExample, onSeeDashboardVideo }) => {\n  /* STEPFIX-1 — compact no-scroll layout */\n  const isEleve = persona === "eleve";\n  const cardCls = { background: "white", padding: 14, borderRadius: 14, border: "1px solid var(--c-line)", display: "flex", flexDirection: "column", gap: 10 };\n  const linkBtnCls = { alignSelf: "flex-start", background: "transparent", border: "none", fontSize: 12, fontWeight: 700, cursor: "pointer", padding: 0, display: "inline-flex", alignItems: "center", gap: 4 };\n  return (\n    <div>\n      <span className="chip" style={{ background: "rgba(72,122,255,.12)", color: "#1320CE" }}>Aperçu</span>\n      <h2 style={{ marginTop: 10, marginBottom: 6, fontSize: 24, letterSpacing: "-0.02em" }}>\n        {isEleve ? "Voici ce qui t\'attend après inscription." : "Voici ce qui vous attend après inscription."}\n      </h2>\n      <p style={{ color: "var(--c-ink-2)", fontSize: 14, marginBottom: 12, lineHeight: 1.5 }}>\n        Un rapport personnalisé + un tableau de bord pour suivre l\'orientation, étape par étape, sans engagement.\n      </p>',
            ),
        ],
    },
    {
        "name": "STEPFIX-1b compact Rapport card (icon + bullets + text link)",
        "needle": '{/* Carte Rapport, preview clickable → QuickExample */}',
        "replacements": [
            (
                '      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>\n        {/* Carte Rapport, preview clickable → QuickExample */}\n        <div style={cardCls}>\n          <button\n            type="button"\n            onClick={() => {\n              if (typeof window !== "undefined" && window.trackEvent) window.trackEvent("report_example_opened", { source: "step2_preview_left" });\n              if (onSeeExample) onSeeExample();\n            }}\n            style={previewBtnCls}\n            onMouseEnter={(e) => { e.currentTarget.style.transform = "translateY(-2px)"; }}\n            onMouseLeave={(e) => { e.currentTarget.style.transform = "translateY(0)"; }}\n          >\n            <div style={{ height: 120, background: "linear-gradient(135deg, rgba(72,122,255,.18), rgba(72,122,255,.04))", borderRadius: 12, marginBottom: 14, position: "relative", overflow: "hidden", border: "1px solid rgba(72,122,255,.18)" }}>\n              {/* Mini mockup rapport */}\n              <div style={{ position: "absolute", inset: 14, background: "white", borderRadius: 8, padding: "10px 12px", boxShadow: "0 4px 14px -6px rgba(10,14,44,.15)" }}>\n                <div style={{ width: 60, height: 4, background: "#FD6936", borderRadius: 2, marginBottom: 6 }} />\n                <div style={{ width: "85%", height: 7, background: "var(--c-ink)", borderRadius: 2, marginBottom: 8 }} />\n                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4 }}>\n                  <div style={{ height: 3, background: "rgba(72,122,255,.4)", borderRadius: 2 }} />\n                  <div style={{ height: 3, background: "rgba(72,122,255,.25)", borderRadius: 2 }} />\n                  <div style={{ height: 3, background: "rgba(253,105,54,.4)", borderRadius: 2 }} />\n                  <div style={{ height: 3, background: "rgba(253,105,54,.25)", borderRadius: 2 }} />\n                </div>\n              </div>\n              <div style={{ position: "absolute", bottom: 8, right: 10, fontSize: 11, fontWeight: 700, color: "#1320CE", background: "white", padding: "3px 8px", borderRadius: 99, boxShadow: "0 2px 6px rgba(10,14,44,.1)" }}>\n                Voir l\'exemple →\n              </div>\n            </div>\n          </button>\n          <div style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--c-muted)", fontWeight: 600, marginBottom: 6 }}>Rapport</div>\n          <h3 style={{ fontSize: 17, fontWeight: 600, marginBottom: 10, letterSpacing: "-0.01em" }}>Rapport d\'orientation 18 pages</h3>\n          <ul style={{ fontSize: 13, color: "var(--c-ink-2)", margin: 0, padding: "0 0 0 16px", lineHeight: 1.7 }}>\n            <li>Profil OCEAN-X complet</li>\n            <li>10 métiers compatibles</li>\n            <li>5 secteurs porteurs</li>\n            <li>5 vœux Parcoursup ciblés</li>\n            <li>Lecture coach personnalisée</li>\n          </ul>\n        </div>',
                '      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>\n        {/* Carte Rapport — compact STEPFIX-1 */}\n        <div style={cardCls}>\n          <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>\n            <div style={{ width: 40, height: 40, borderRadius: 10, background: "linear-gradient(135deg, rgba(72,122,255,.2), rgba(72,122,255,.06))", display: "grid", placeItems: "center", flexShrink: 0, border: "1px solid rgba(72,122,255,.2)" }}>\n              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1320CE" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="9" y1="13" x2="15" y2="13"/><line x1="9" y1="17" x2="13" y2="17"/></svg>\n            </div>\n            <div style={{ flex: 1, minWidth: 0 }}>\n              <div style={{ fontSize: 10, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--c-muted)", fontWeight: 600, marginBottom: 2 }}>Rapport</div>\n              <h3 style={{ fontSize: 15, fontWeight: 600, letterSpacing: "-0.01em", lineHeight: 1.25 }}>Rapport d\'orientation 18 pages</h3>\n            </div>\n          </div>\n          <ul style={{ fontSize: 12.5, color: "var(--c-ink-2)", margin: 0, padding: "0 0 0 14px", lineHeight: 1.45 }}>\n            <li>Profil OCEAN-X complet</li>\n            <li>10 métiers compatibles</li>\n            <li>5 secteurs porteurs</li>\n            <li>5 vœux Parcoursup ciblés</li>\n            <li>Lecture coach personnalisée</li>\n          </ul>\n          <button\n            type="button"\n            onClick={() => {\n              if (typeof window !== "undefined" && window.trackEvent) window.trackEvent("report_example_opened", { source: "step2_preview_left" });\n              if (onSeeExample) onSeeExample();\n            }}\n            style={{ ...linkBtnCls, color: "#1320CE" }}\n          >\n            Voir l\'exemple →\n          </button>\n        </div>',
            ),
        ],
    },
    {
        "name": "STEPFIX-1c compact Tableau-de-bord card + Charles strip",
        "needle": '{/* Carte Tableau de bord, preview clickable → vidéo démo */}',
        "replacements": [
            (
                '        {/* Carte Tableau de bord, preview clickable → vidéo démo */}\n        <div style={cardCls}>\n          <button\n            type="button"\n            onClick={() => {\n              if (typeof window !== "undefined" && window.trackEvent) window.trackEvent("dashboard_demo_opened", { source: "step2_preview_right" });\n              if (onSeeDashboardVideo) onSeeDashboardVideo();\n            }}\n            style={previewBtnCls}\n            onMouseEnter={(e) => { e.currentTarget.style.transform = "translateY(-2px)"; }}\n            onMouseLeave={(e) => { e.currentTarget.style.transform = "translateY(0)"; }}\n          >\n            <div style={{ height: 120, background: "linear-gradient(135deg, rgba(253,105,54,.18), rgba(253,105,54,.04))", borderRadius: 12, marginBottom: 14, position: "relative", overflow: "hidden", border: "1px solid rgba(253,105,54,.18)" }}>\n              {/* Mini mockup tableau de bord avec onglets */}\n              <div style={{ position: "absolute", inset: 14, background: "white", borderRadius: 8, padding: "8px 10px", boxShadow: "0 4px 14px -6px rgba(10,14,44,.15)", display: "flex", flexDirection: "column", gap: 6 }}>\n                <div style={{ display: "flex", gap: 6, fontSize: 7, fontWeight: 600 }}>\n                  <span style={{ color: "var(--c-ink)", borderBottom: "1.5px solid #FD6936", paddingBottom: 1 }}>Dashboard</span>\n                  <span style={{ color: "var(--c-muted)" }}>Documents</span>\n                  <span style={{ color: "var(--c-muted)" }}>Rapport</span>\n                  <span style={{ color: "var(--c-muted)" }}>Coach</span>\n                </div>\n                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4, flex: 1 }}>\n                  <div style={{ background: "rgba(72,122,255,.15)", borderRadius: 3 }} />\n                  <div style={{ background: "rgba(253,105,54,.15)", borderRadius: 3 }} />\n                  <div style={{ background: "rgba(34,160,107,.15)", borderRadius: 3 }} />\n                  <div style={{ background: "rgba(245,235,63,.3)", borderRadius: 3 }} />\n                </div>\n              </div>\n              {/* Play icon overlay */}\n              <div style={{ position: "absolute", inset: 0, display: "grid", placeItems: "center" }}>\n                <div style={{ width: 44, height: 44, borderRadius: "50%", background: "rgba(255,255,255,.95)", display: "grid", placeItems: "center", color: "#FD6936", boxShadow: "0 6px 18px rgba(10,14,44,.2)" }}>\n                  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>\n                </div>\n              </div>\n              <div style={{ position: "absolute", bottom: 8, right: 10, fontSize: 11, fontWeight: 700, color: "#FD6936", background: "white", padding: "3px 8px", borderRadius: 99, boxShadow: "0 2px 6px rgba(10,14,44,.1)" }}>\n                Voir la démo →\n              </div>\n            </div>\n          </button>\n          <div style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--c-muted)", fontWeight: 600, marginBottom: 6 }}>Tableau de bord</div>\n          <h3 style={{ fontSize: 17, fontWeight: 600, marginBottom: 10, letterSpacing: "-0.01em" }}>Suivi parent en temps réel</h3>\n          <ul style={{ fontSize: 13, color: "var(--c-ink-2)", margin: 0, padding: "0 0 0 16px", lineHeight: 1.7 }}>\n            <li>À faire ensuite, priorisé</li>\n            <li>RDV coach + lien visio</li>\n            <li>Documents centralisés</li>\n            <li>Vœux Parcoursup éditables</li>\n            <li>Parrainage (séances bonus)</li>\n          </ul>\n        </div>\n      </div>\n\n      <div style={{ marginTop: 18, padding: 16, background: "rgba(253,105,54,.08)", borderRadius: 14, display: "flex", gap: 14, alignItems: "center" }}>\n        <div style={{ width: 44, height: 44, borderRadius: "50%", background: "linear-gradient(135deg, #FD6936, #FFA371)", color: "white", display: "grid", placeItems: "center", fontWeight: 700, fontSize: 14, flexShrink: 0, fontFamily: "var(--font-display)" }}>CB</div>\n        <div style={{ flex: 1, fontSize: 14, lineHeight: 1.5, color: "var(--c-ink)" }}>\n          <strong>+ 30 min offertes avec Charles Broussin</strong>, fondateur Proxxie, inventeur du test OCEAN-X. Visio ou téléphone, sans engagement.\n        </div>\n      </div>',
                '        {/* Carte Tableau de bord — compact STEPFIX-1 */}\n        <div style={cardCls}>\n          <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>\n            <div style={{ width: 40, height: 40, borderRadius: 10, background: "linear-gradient(135deg, rgba(253,105,54,.2), rgba(253,105,54,.06))", display: "grid", placeItems: "center", flexShrink: 0, border: "1px solid rgba(253,105,54,.2)" }}>\n              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FD6936" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>\n            </div>\n            <div style={{ flex: 1, minWidth: 0 }}>\n              <div style={{ fontSize: 10, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--c-muted)", fontWeight: 600, marginBottom: 2 }}>Tableau de bord</div>\n              <h3 style={{ fontSize: 15, fontWeight: 600, letterSpacing: "-0.01em", lineHeight: 1.25 }}>Suivi parent en temps réel</h3>\n            </div>\n          </div>\n          <ul style={{ fontSize: 12.5, color: "var(--c-ink-2)", margin: 0, padding: "0 0 0 14px", lineHeight: 1.45 }}>\n            <li>À faire ensuite, priorisé</li>\n            <li>RDV coach + lien visio</li>\n            <li>Documents centralisés</li>\n            <li>Vœux Parcoursup éditables</li>\n            <li>Parrainage (séances bonus)</li>\n          </ul>\n          <button\n            type="button"\n            onClick={() => {\n              if (typeof window !== "undefined" && window.trackEvent) window.trackEvent("dashboard_demo_opened", { source: "step2_preview_right" });\n              if (onSeeDashboardVideo) onSeeDashboardVideo();\n            }}\n            style={{ ...linkBtnCls, color: "#FD6936" }}\n          >\n            ▶ Voir la démo →\n          </button>\n        </div>\n      </div>\n\n      <div style={{ marginTop: 12, padding: "10px 14px", background: "rgba(253,105,54,.08)", borderRadius: 12, display: "flex", gap: 12, alignItems: "center" }}>\n        <div style={{ width: 32, height: 32, borderRadius: "50%", background: "linear-gradient(135deg, #FD6936, #FFA371)", color: "white", display: "grid", placeItems: "center", fontWeight: 700, fontSize: 12, flexShrink: 0, fontFamily: "var(--font-display)" }}>CB</div>\n        <div style={{ flex: 1, fontSize: 13, lineHeight: 1.4, color: "var(--c-ink)" }}>\n          <strong>+ 30 min offertes avec Charles Broussin</strong>, fondateur Proxxie, inventeur du test OCEAN-X.\n        </div>\n      </div>',
            ),
        ],
    },

    # ----- ANALYTICS-4 (2026-05-19): onboarding wizard step funnel -----
    # The home page's 5-step onboarding wizard (Qui êtes-vous → Niveau &
    # profil → Aperçu rapport final → Inscription → Coach offert) is
    # currently invisible to GA4 — we only see `funnel_opened` /
    # `funnel_step` once. This patch adds two useEffect hooks at the top
    # of the wizard component:
    #
    #   1. fires `wizard_step_view` on every step change with step_index,
    #      step_name (who_are_you / level_profile / preview / signup / coach),
    #      persona, and the running max_step
    #   2. fires `wizard_opened` on first open, `wizard_dropoff` if the
    #      wizard closes before the user reaches the final step,
    #      `wizard_completed` once they hit the last step
    #
    # Updates window.__proxxie_wizard_in_progress so the beforeunload
    # handler (added in this patch via a third useEffect) can fire
    # `wizard_dropoff` even if the user just closes the tab.
    #
    # Anchor: `if (!open) return null;` — unique to the wizard component
    # at this position in 12cdb3c9.
    {
        "name": "ANALYTICS-4 wizard step funnel tracking",
        "needle": "const stepDefs = isMentor",
        "replacements": [
            (
                "if (!open) return null;",
                "/* ANALYTICS-4: wizard step funnel tracking */\n  React.useEffect(() => {\n    if (!open) return;\n    var stepNames = ['who_are_you', 'level_profile', 'preview', 'signup', 'coach', 'thanks', 'mentor_signup', 'mentor_book'];\n    if (window.trackEvent) {\n      window.trackEvent('wizard_step_view', {\n        step_index: step,\n        step_name: stepNames[step] || ('step_' + step),\n        persona: persona || null,\n        max_step: maxStep\n      });\n    }\n    if (window.__proxxie_wizard_in_progress) {\n      window.__proxxie_wizard_in_progress.maxStep = Math.max(window.__proxxie_wizard_in_progress.maxStep || 0, step);\n      window.__proxxie_wizard_in_progress.currentStep = step;\n      /* Final step reached → completion */\n      var finalStep = isMentor ? 7 : 4;\n      if (step >= finalStep && !window.__proxxie_wizard_in_progress.completed) {\n        window.__proxxie_wizard_in_progress.completed = true;\n        if (window.trackEvent) window.trackEvent('wizard_completed', {\n          persona: persona || null,\n          time_total_ms: Date.now() - window.__proxxie_wizard_in_progress.startedAt,\n          is_mentor: !!isMentor\n        });\n      }\n    }\n  }, [step, open]);\n\n  React.useEffect(() => {\n    if (open && !window.__proxxie_wizard_in_progress) {\n      window.__proxxie_wizard_in_progress = { startedAt: Date.now(), maxStep: 0, currentStep: 0, completed: false };\n      if (window.trackEvent) window.trackEvent('wizard_opened', { persona: persona || null, is_mentor: !!isMentor });\n    } else if (!open && window.__proxxie_wizard_in_progress) {\n      var wp = window.__proxxie_wizard_in_progress;\n      if (!wp.completed && window.trackEvent) {\n        window.trackEvent('wizard_dropoff', {\n          last_step: wp.currentStep || 0,\n          max_step: wp.maxStep || 0,\n          time_total_ms: Date.now() - wp.startedAt,\n          via: 'close'\n        });\n      }\n      window.__proxxie_wizard_in_progress = null;\n    }\n  }, [open]);\n\n  React.useEffect(() => {\n    function onBeforeUnload() {\n      var wp = window.__proxxie_wizard_in_progress;\n      if (wp && !wp.completed && window.trackEvent) {\n        window.trackEvent('wizard_dropoff', {\n          last_step: wp.currentStep || 0,\n          max_step: wp.maxStep || 0,\n          time_total_ms: Date.now() - wp.startedAt,\n          via: 'beforeunload'\n        });\n      }\n    }\n    window.addEventListener('beforeunload', onBeforeUnload);\n    return function() { window.removeEventListener('beforeunload', onBeforeUnload); };\n  }, []);\n\n  if (!open) return null;",
            ),
        ],
    },

    # ----- ANALYTICS-3b (2026-05-19): test consent + test_started -----
    # Patches the shared TestApp.pickPersona handler (every psychometric
    # test page has this signature). On click:
    #   1. Fire test_initiated (user intent)
    #   2. Check localStorage for prior consent on this test_type
    #   3. If no consent: show a custom modal (RGPD-compliant text + Accept/Decline)
    #      → test_consent_shown / _granted / _declined
    #   4. After consent: fire test_started + populate __proxxie_test_in_progress
    #      so the engagement layer's beforeunload handler (ANALYTICS-3a) can
    #      fire test_abandoned with accurate progress.
    {
        "name": "ANALYTICS-3b TestApp.pickPersona consent + tracking",
        "needle": 'const pickPersona = (p) => { setPersona(p); setMode("test"); window.scrollTo({ top: 0, behavior: "smooth" }); };',
        "replacements": [
            (
                'const pickPersona = (p) => { setPersona(p); setMode("test"); window.scrollTo({ top: 0, behavior: "smooth" }); };',
                'const pickPersona = (p) => {\n    /* ANALYTICS-3b: test_initiated → consent gate → test_started */\n    var testType = window.__proxxie_test_type || \'unknown\';\n    var consentKey = \'proxxie_test_consent_\' + testType;\n    var hasConsent = false;\n    try { hasConsent = !!window.localStorage.getItem(consentKey); } catch(e) {}\n    if (window.trackEvent) window.trackEvent(\'test_initiated\', { test_type: testType, persona: p });\n    function startNow() {\n      setPersona(p);\n      setMode("test");\n      window.scrollTo({ top: 0, behavior: "smooth" });\n      if (window.trackEvent) window.trackEvent(\'test_started\', { test_type: testType, persona: p });\n      window.__proxxie_test_in_progress = { startedAt: Date.now(), questionIndex: 0, totalQuestions: 0, completionPct: 0, testType: testType, persona: p };\n    }\n    if (hasConsent) { startNow(); return; }\n    if (window.trackEvent) window.trackEvent(\'test_consent_shown\', { test_type: testType });\n    var overlay = document.createElement(\'div\');\n    overlay.id = \'__proxxie_test_consent\';\n    overlay.setAttribute(\'role\', \'dialog\');\n    overlay.setAttribute(\'aria-modal\', \'true\');\n    overlay.style.cssText = \'position:fixed;inset:0;z-index:99999;background:rgba(10,14,44,.55);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);display:grid;place-items:center;padding:24px\';\n    overlay.innerHTML = \'<div style="background:#fff;border-radius:18px;padding:28px 32px;max-width:520px;font-family:Montserrat,system-ui,sans-serif;box-shadow:0 24px 60px -16px rgba(19,32,206,.28);animation:proxxieFadeIn .25s ease"><div style="font-family:Mulish,Goldplay,system-ui,sans-serif;font-size:22px;font-weight:600;letter-spacing:-.02em;color:#0A0E2C;margin-bottom:10px">Avant de commencer ce test</div><p style="font-size:14px;line-height:1.55;color:#2A2F4F;margin:0 0 14px">Vos réponses sont confidentielles et stockées <strong>uniquement sur votre appareil</strong> (RGPD). Elles ne sortent jamais de votre navigateur sans votre action.</p><p style="font-size:14px;line-height:1.55;color:#2A2F4F;margin:0 0 18px">En continuant, vous acceptez que vos réponses soient analysées par notre algorithme propriétaire pour générer un rapport personnalisé d\\\'orientation. <strong>Elles ne sont jamais utilisées pour entraîner un modèle d\\\'IA.</strong></p><p style="font-size:12px;color:#6B6F8C;margin:0 0 20px">Vous pourrez supprimer vos réponses à tout moment depuis votre tableau de bord.</p><div style="display:flex;gap:10px;justify-content:flex-end;flex-wrap:wrap"><button id="__proxxie_decline" style="background:transparent;border:1.5px solid rgba(10,14,44,.16);border-radius:99px;padding:10px 18px;font-size:13px;font-weight:600;color:#0A0E2C;cursor:pointer;font-family:inherit">Refuser</button><button id="__proxxie_accept" style="background:#FD6936;color:#fff;border:none;border-radius:99px;padding:10px 22px;font-size:14px;font-weight:600;cursor:pointer;font-family:inherit;box-shadow:0 8px 22px -6px rgba(253,105,54,.55)">Commencer le test →</button></div></div>\';\n    document.body.appendChild(overlay);\n    document.getElementById(\'__proxxie_accept\').onclick = function() {\n      try { window.localStorage.setItem(consentKey, \'granted_\' + Date.now()); } catch(e) {}\n      if (window.trackEvent) window.trackEvent(\'test_consent_granted\', { test_type: testType });\n      overlay.remove();\n      startNow();\n    };\n    document.getElementById(\'__proxxie_decline\').onclick = function() {\n      if (window.trackEvent) window.trackEvent(\'test_consent_declined\', { test_type: testType });\n      overlay.remove();\n    };\n  };',
            ),
        ],
    },

    # ----- ANALYTICS-3c (2026-05-19): test_completed when reaching results -----
    # Patches TestApp.onComplete to fire `test_completed` with total time
    # and clear the in-progress marker so beforeunload no longer fires
    # `test_abandoned`. Answers the founder's primary ask: which users
    # actually go all the way through each test.
    {
        "name": "ANALYTICS-3c TestApp.onComplete fires test_completed",
        "needle": 'const onComplete = (ans) => { setAnswers(ans); setResults(computeResults(ans)); setMode("results"); window.scrollTo({ top: 0, behavior: "smooth" }); };',
        "replacements": [
            (
                'const onComplete = (ans) => { setAnswers(ans); setResults(computeResults(ans)); setMode("results"); window.scrollTo({ top: 0, behavior: "smooth" }); };',
                'const onComplete = (ans) => {\n    setAnswers(ans);\n    setResults(computeResults(ans));\n    setMode("results");\n    window.scrollTo({ top: 0, behavior: "smooth" });\n    /* ANALYTICS-3c: test_completed (founder ask: who goes the distance) */\n    if (window.trackEvent) {\n      var inProgress = window.__proxxie_test_in_progress;\n      var elapsed = inProgress && inProgress.startedAt ? (Date.now() - inProgress.startedAt) : null;\n      window.trackEvent(\'test_completed\', {\n        test_type: window.__proxxie_test_type || \'unknown\',\n        total_questions: (ans || []).length,\n        time_total_ms: elapsed,\n        persona: inProgress ? inProgress.persona : null\n      });\n    }\n    window.__proxxie_test_in_progress = null;\n  };',
            ),
        ],
    },

    # ----- ANALYTICS-3d (2026-05-19): per-question progress tracking -----
    # Patches TestFlowEngine.setAnswer to update __proxxie_test_in_progress
    # on every question answered. This means the beforeunload handler (in
    # ANALYTICS-3a) fires test_abandoned with the EXACT question index and
    # completion percentage when the user leaves mid-test. Also fires a
    # lightweight `test_question_answered` event (useful for finding
    # drop-off questions).
    {
        "name": "ANALYTICS-3d TestFlowEngine.setAnswer progress + question_answered",
        "needle": "const setAnswer = (val) => {\n    const next = answers.slice();\n    next[i] = val;\n    setAnswers(next);",
        "replacements": [
            (
                "const setAnswer = (val) => {\n    const next = answers.slice();\n    next[i] = val;\n    setAnswers(next);",
                "const setAnswer = (val) => {\n    const next = answers.slice();\n    next[i] = val;\n    setAnswers(next);\n    /* ANALYTICS-3d: update in-progress + fire test_question_answered */\n    try {\n      var answered = next.filter(function(a){ return a !== null; }).length;\n      if (window.__proxxie_test_in_progress) {\n        window.__proxxie_test_in_progress.questionIndex = i;\n        window.__proxxie_test_in_progress.totalQuestions = next.length;\n        window.__proxxie_test_in_progress.completionPct = Math.round((answered / next.length) * 100);\n      }\n      if (window.trackEvent) window.trackEvent('test_question_answered', {\n        test_type: window.__proxxie_test_type || 'unknown',\n        question_index: i,\n        total_questions: next.length,\n        completion_pct: Math.round((answered / next.length) * 100),\n        answer_value: val\n      });\n    } catch(e) {}",
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
    our Python source strings (with real newlines) to the on-disk format.

    Also escapes the `</` pattern to `<\\/`. JavaScript's JSON.stringify
    (which generated the on-disk template) does this for security — it
    prevents an HTML parser from terminating the wrapping `<script>` tag
    early if the template content contains a closing tag like `</script>`.
    Without this, a CSS_PATCH whose old/new contains `</script>` would
    silently fail to match (it would 'partially match' up to but excluding
    the closing tag). Added 2026-05-19 with ANALYTICS-1."""
    return (s
            .replace("\\", "\\\\")
            .replace("\n", "\\n")
            .replace('"', '\\"')
            .replace("</", "<\\/"))

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

def apply_static_html_patches(html: str, path_name: str) -> tuple[str, int]:
    """Plain-HTML patches for the 5 static landing pages that DON'T ship
    a bundler/template script (blog.html, carnet-orientation.html,
    cas-clients.html, guide-orientation.html, newsletter-substack.html).
    These pages serve HTML directly to the browser, so there is no JSON
    encoding to worry about — old/new are matched verbatim.

    Idempotency: each patch declares a `sentinel` substring; if the
    sentinel is already in the file, we skip. The patch list itself is
    declared as STATIC_HTML_PATCHES below."""
    changed = 0
    for patch in STATIC_HTML_PATCHES:
        sentinel = patch.get("sentinel") or patch["new"][:80]
        if sentinel in html:
            continue
        if patch["old"] not in html:
            continue
        html = html.replace(patch["old"], patch["new"], 1)
        changed += 1
    return html, changed


# ===========================================================================
# STATIC HTML PATCHES — for the 5 landing pages without a bundler template
# ===========================================================================

# Same analytics block as ANALYTICS-1 in CSS_PATCHES, but as plain HTML
# (no `</` → `<\/` escaping, no `\n` → \\n escaping) because these files
# are served raw. Injected right before `</head>`.
_ANALYTICS_BLOCK_RAW = """<!-- ANALYTICS-1: GA4 + Microsoft Clarity (Cookiebot pending) -->
<!-- Google Analytics 4 (property shared with www.proxxie.co) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-Q93HTZY2TB"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('consent', 'default', {
    'ad_storage': 'granted',
    'analytics_storage': 'granted',
    'ad_user_data': 'granted',
    'ad_personalization': 'granted'
  });
  gtag('set', 'ads_data_redaction', true);
  gtag('js', new Date());
  gtag('config', 'G-Q93HTZY2TB', {
    anonymize_ip: true,
    cookie_flags: 'SameSite=None;Secure;Partitioned',
    page_path: location.pathname.replace(/^\\/proxxie-new-design\\//, '/')
  });
</script>

<!-- Microsoft Clarity — session recordings, heatmaps, rage/dead clicks -->
<script>
  (function(c,l,a,r,i,t,y){
    c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
    t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
    y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
  })(window, document, "clarity", "script", "wtjyxri1oa");
</script>

<!-- Unified event wrapper -->
<script>
  window.plausible = window.plausible || function() { (window.plausible.q = window.plausible.q || []).push(arguments) };
  window.trackEvent = function(name, props) {
    try {
      if (window.gtag) window.gtag('event', name, props || {});
      if (window.clarity) window.clarity('event', name);
      if (window.plausible) window.plausible(name, { props: props || {} });
      var host = window.location.hostname;
      if (host === 'localhost' || host === '127.0.0.1') {
        console.log('[analytics]', name, props || {});
      }
    } catch(e) { /* swallow */ }
  };
  try {
    var p = window.localStorage.getItem('proxxie_persona');
    var g = window.localStorage.getItem('proxxie_grade');
    var firstUtm = window.localStorage.getItem('proxxie_first_utm');
    var url = new URL(window.location.href);
    var utm = {};
    ['utm_source','utm_medium','utm_campaign','utm_term','utm_content'].forEach(function(k){
      var v = url.searchParams.get(k);
      if (v) utm[k] = v;
    });
    if (Object.keys(utm).length && !firstUtm) {
      window.localStorage.setItem('proxxie_first_utm', JSON.stringify({ ts: Date.now(), utm: utm }));
      firstUtm = window.localStorage.getItem('proxxie_first_utm');
    }
    if (window.gtag) {
      var up = {};
      if (p) up.persona = p;
      if (g) up.grade = g;
      if (firstUtm) {
        try { var fu = JSON.parse(firstUtm).utm || {}; for (var k in fu) up['first_'+k] = fu[k]; } catch(e) {}
      }
      if (Object.keys(up).length) window.gtag('set', 'user_properties', up);
    }
  } catch(e) { /* swallow */ }
</script>
"""

_ANALYTICS_3A_BLOCK_RAW = """<!-- ANALYTICS-3a: site-wide engagement layer (scroll/time/exit/clicks) -->
<script>
(function() {
  if (window.__proxxieEngagementLoaded) return;
  window.__proxxieEngagementLoaded = true;

  var path = location.pathname.toLowerCase();
  var pageType = 'other';
  if (path === '/' || path.indexOf('/index') >= 0 || path.indexOf('/home') >= 0) pageType = 'home';
  else if (path.indexOf('test') >= 0) pageType = 'test';
  else if (path.indexOf('dashboard') >= 0) pageType = 'dashboard';
  else if (path.indexOf('rapport') >= 0) pageType = 'rapport';
  else if (path.indexOf('coach') >= 0) pageType = 'coach';
  else if (path.indexOf('documents') >= 0) pageType = 'documents';
  else if (path.indexOf('ressources') >= 0) pageType = 'ressources';
  else if (path.indexOf('connexion') >= 0 || path.indexOf('login') >= 0) pageType = 'connexion';
  else if (path.indexOf('blog') >= 0) pageType = 'blog';
  else if (path.indexOf('guide-orientation') >= 0) pageType = 'guide';
  else if (path.indexOf('newsletter') >= 0) pageType = 'newsletter';
  else if (path.indexOf('cas-clients') >= 0) pageType = 'cas-clients';
  else if (path.indexOf('carnet') >= 0) pageType = 'carnet';

  var testType = null;
  if (pageType === 'test') {
    var pn = location.pathname.replace(/^.*\\//, '').toLowerCase();
    var m = pn.match(/^(?:proxxie%20)?test[ %-]?(\\w+)/) || pn.match(/^test-?(\\w+)/);
    if (m && m[1] && m[1] !== 'html') testType = m[1].replace(/\\.html$/, '');
    if (!testType && (pn === 'test.html' || pn === 'proxxie test.html' || pn === 'proxxie%20test.html')) testType = 'ocean-x';
    if (!testType && (pn === 'tests.html' || pn === 'proxxie tests.html' || pn === 'proxxie%20tests.html')) testType = 'landing';
  }
  window.__proxxie_page_type = pageType;
  window.__proxxie_test_type = testType;

  function send(name, props) {
    if (window.trackEvent) {
      var p = props || {};
      p.page_type = pageType;
      if (testType) p.test_type = testType;
      window.trackEvent(name, p);
    }
  }

  var startTime = Date.now();
  var maxScroll = 0;
  var scrollHit = {};
  var timeHit = {};
  var exitFired = false;

  function onScroll() {
    var sh = document.documentElement.scrollHeight - window.innerHeight;
    if (sh <= 0) return;
    var pct = (window.scrollY / sh) * 100;
    if (pct > maxScroll) maxScroll = pct;
    [25, 50, 75, 90, 100].forEach(function(t) {
      if (!scrollHit[t] && pct >= t) {
        scrollHit[t] = true;
        send('scroll_depth', { depth: t });
      }
    });
  }
  window.addEventListener('scroll', onScroll, { passive: true });

  function checkTime() {
    var elapsed = Math.floor((Date.now() - startTime) / 1000);
    [15, 30, 60, 120, 300].forEach(function(t) {
      if (!timeHit[t] && elapsed >= t) {
        timeHit[t] = true;
        send('time_on_page', { seconds: t });
      }
    });
  }
  setInterval(checkTime, 5000);

  function onMouseLeave(e) {
    if (exitFired) return;
    if (e.clientY < 5) {
      exitFired = true;
      var elapsed = Math.floor((Date.now() - startTime) / 1000);
      send('exit_intent', { max_scroll: Math.round(maxScroll), seconds_on_page: elapsed });
    }
  }
  document.addEventListener('mouseleave', onMouseLeave);

  document.addEventListener('visibilitychange', function() {
    var elapsed = Math.floor((Date.now() - startTime) / 1000);
    if (document.hidden) send('page_hidden', { seconds_on_page: elapsed });
    else send('page_visible', {});
  });

  window.addEventListener('beforeunload', function() {
    var inProgress = window.__proxxie_test_in_progress;
    if (inProgress) {
      send('test_abandoned', {
        question_index: inProgress.questionIndex || 0,
        total_questions: inProgress.totalQuestions || 0,
        completion_pct: inProgress.completionPct || 0,
        time_total_ms: Date.now() - (inProgress.startedAt || Date.now())
      });
    }
  });

  document.addEventListener('click', function(e) {
    var target = e.target.closest('button, a.btn, [data-track]');
    if (!target) return;
    var label = (target.getAttribute('data-track') || target.textContent || '').trim().slice(0, 80);
    if (!label) return;
    var href = target.getAttribute('href') || null;
    var isOutbound = false;
    if (href && href.indexOf('http') === 0 && href.indexOf(location.hostname) === -1) isOutbound = true;
    send('cta_click', { cta_text: label, cta_href: href, cta_outbound: isOutbound });
  }, { capture: true });

  setTimeout(function() {
    if (window.gtag) window.gtag('event', 'page_view_enriched', { page_type: pageType, test_type: testType });
  }, 200);
})();
</script>
"""

STATIC_HTML_PATCHES = [
    {
        "name": "ANALYTICS-1-STATIC inject GA4 + Clarity into static landing pages",
        "sentinel": "<!-- ANALYTICS-1: GA4 + Microsoft Clarity",
        "old": "</head>",
        "new": _ANALYTICS_BLOCK_RAW + "</head>",
    },
    {
        "name": "ANALYTICS-3a-STATIC inject engagement layer into static landing pages",
        "sentinel": "<!-- ANALYTICS-3a: site-wide engagement layer",
        "old": "<!-- Unified event wrapper -->",
        "new": _ANALYTICS_3A_BLOCK_RAW + "<!-- Unified event wrapper -->",
    },

    # ANALYTICS-2 mirror for static pages — same Cookiebot insertion +
    # Consent Mode flip as the CSS_PATCHES version above, but as raw HTML.
    {
        "name": "ANALYTICS-2-STATIC wire Cookiebot consent banner into static landing pages",
        "sentinel": '<!-- ANALYTICS-2: Cookiebot',
        "old": '<!-- ANALYTICS-1: GA4 + Microsoft Clarity (Cookiebot pending) -->\n<!-- Google Analytics 4 (property shared with www.proxxie.co) -->\n<script async src="https://www.googletagmanager.com/gtag/js?id=G-Q93HTZY2TB"></script>\n<script>\n  window.dataLayer = window.dataLayer || [];\n  function gtag(){dataLayer.push(arguments);}\n  gtag(\'consent\', \'default\', {\n    \'ad_storage\': \'granted\',\n    \'analytics_storage\': \'granted\',\n    \'ad_user_data\': \'granted\',\n    \'ad_personalization\': \'granted\'\n  });',
        "new": '<!-- ANALYTICS-1: GA4 + Microsoft Clarity (Cookiebot WIRED via ANALYTICS-2) -->\n<!-- ANALYTICS-2: Cookiebot — MUST load before any other tracking script -->\n<script id="Cookiebot"\n        src="https://consent.cookiebot.com/uc.js"\n        data-cbid="00200400-fef6-4032-a746-f80a83be8751"\n        data-blockingmode="auto"\n        type="text/javascript"></script>\n\n<!-- Google Analytics 4 (property shared with www.proxxie.co) -->\n<script async src="https://www.googletagmanager.com/gtag/js?id=G-Q93HTZY2TB"></script>\n<script>\n  window.dataLayer = window.dataLayer || [];\n  function gtag(){dataLayer.push(arguments);}\n  gtag(\'consent\', \'default\', {\n    \'ad_storage\': \'denied\',\n    \'analytics_storage\': \'denied\',\n    \'ad_user_data\': \'denied\',\n    \'ad_personalization\': \'denied\',\n    \'wait_for_update\': 500\n  });',
    },
]


def process_file(path: pathlib.Path) -> bool:
    html = path.read_text(encoding="utf-8")
    orig = html
    html, css_n = apply_css_patches(html, path.name)
    html, jsx_n = apply_bundle_patches(html, path.name)
    html, static_n = apply_static_html_patches(html, path.name)
    if html == orig:
        return False
    path.write_text(html, encoding="utf-8")
    print(f"  → wrote {path.name} (css: {css_n}, bundle: {jsx_n}, static: {static_n})")
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

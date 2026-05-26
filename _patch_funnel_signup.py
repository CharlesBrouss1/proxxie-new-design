#!/usr/bin/env python3
"""Wire le funnel OnboardingFlow du proto sur l'API prod proxxie-app.

À la fin de l'étape "Inscription" du funnel (le user clique "Créer mon
compte" et passe au step 4 "Coach offert"), POST les données collectées
vers https://proxxie-app-seven.vercel.app/api/funnel/signup. L'API ·
  - crée User + Family + Child + Profile + Consent en DB Supabase EU
  - envoie un magic link via Resend à l'email saisi
  - le parent reçoit le mail, clique, atterrit /dashboard authentifié
    avec ses infos déjà saisies

Le funnel actuel reste fonctionnel · il continue d'afficher les étapes 4
(Coach offert) et 5 (final) avec ses comportements existants (book RDV,
voir dashboard). Le seul changement · un appel fetch en background quand
l'user atteint step >= 4.

Idempotent côté serveur (upsert User sur email, Child sur familyId+prenom).
Idempotent côté client (`window.__proxxie_funnel_submitted` empêche les
re-POST sur re-render). Cf BACKEND_SPEC.md du proto pour le contrat data.

Modifications ·
1. `const SIGNUP_ENDPOINT = "";` → URL prod (constante déjà déclarée,
   jamais consommée jusque-là).
2. Injection d'un useEffect dans OnboardingFlow qui POST.

Idempotent · marker `__proxxie_funnel_signup_v1__`, strip-and-readd.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
FILES = ["Proxxie Home.html", "index.html"]

PROD_ENDPOINT = "https://proxxie-app-seven.vercel.app/api/funnel/signup"
MARKER = "/* __proxxie_funnel_signup_v1__ */"

OLD_ENDPOINT_LINE = 'const SIGNUP_ENDPOINT = "";'
NEW_ENDPOINT_LINE = f'const SIGNUP_ENDPOINT = "{PROD_ENDPOINT}";'

# Anchor stable dans OnboardingFlow · avant le useEffect d'analytics
# wizard tracking. On insère NOTRE useEffect juste avant.
INJECT_ANCHOR = "/* ANALYTICS-4: wizard step funnel tracking */"

INJECT = MARKER + r"""
  /* Funnel signup · POST une fois quand l'user atteint step 4 (post-Inscription)
     avec email rempli. Idempotent · une seule submission par session navigateur
     grâce à window.__proxxie_funnel_submitted + upsert côté serveur. */
  React.useEffect(() => {
    if (step >= 4 && persona === "parent" && account && account.email && account.email.indexOf("@") > 0 && !window.__proxxie_funnel_submitted) {
      window.__proxxie_funnel_submitted = true;
      var payload = {
        email: account.email,
        phone: account.phone || undefined,
        parentName: profile && profile.parentName ? profile.parentName : undefined,
        firstName: profile && profile.firstName ? profile.firstName : undefined,
        grade: profile && profile.grade ? profile.grade : undefined,
        persona: persona,
        funnelMeta: {
          schoolGroup: typeof schoolGroup !== "undefined" ? schoolGroup : null,
          testChoice: typeof testChoice !== "undefined" ? testChoice : null,
          bookedCoach: typeof bookCoach !== "undefined" ? !!bookCoach : false,
          skippedBooking: typeof skippedBooking !== "undefined" ? !!skippedBooking : false,
          source: "proxxie-new-design-home"
        }
      };
      try {
        fetch(SIGNUP_ENDPOINT, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        }).then(function(r){ return r.json(); }).then(function(j){
          if (window.trackEvent) window.trackEvent("funnel_signup_submitted", { ok: !!(j && j.ok), magic: !!(j && j.magicLinkSent) });
        }).catch(function(e){
          window.__proxxie_funnel_submitted = false;
          if (window.trackEvent) window.trackEvent("funnel_signup_error", { msg: String(e && e.message || e) });
        });
      } catch (e) {}
    }
  }, [step, persona, account]);
"""

STRIP_RE = re.compile(
    r"\n  /\* __proxxie_funnel_signup_v1__ \*/.*?(?=\n\s*/\* ANALYTICS-4)",
    flags=re.S,
)


def patch_asset(src: str) -> tuple[str, list[str]]:
    changes = []
    if MARKER in src:
        src = STRIP_RE.sub("", src)
        src = src.replace(NEW_ENDPOINT_LINE, OLD_ENDPOINT_LINE, 1)
        changes.append("re-patch")

    if OLD_ENDPOINT_LINE not in src:
        raise SystemExit(
            "anchor introuvable · const SIGNUP_ENDPOINT = \"\" (le code source du proto a changé?)"
        )
    if INJECT_ANCHOR not in src:
        raise SystemExit("anchor analytics-4 introuvable · /* ANALYTICS-4 ... */")

    src = src.replace(OLD_ENDPOINT_LINE, NEW_ENDPOINT_LINE, 1)
    changes.append("endpoint URL")
    # Inject AVANT l'anchor analytics-4
    src = src.replace(INJECT_ANCHOR, INJECT + "\n  " + INJECT_ANCHOR, 1)
    changes.append("useEffect signup")
    return src, changes


def patch_one(target: pathlib.Path) -> str:
    if not target.exists():
        return "SKIP missing"
    html = target.read_text(encoding="utf-8")
    m = re.search(r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)', html, re.DOTALL)
    if not m:
        return "no manifest"
    manifest = json.loads(m.group(2))

    target_uuid = None
    for uuid, entry in manifest.items():
        data = base64.b64decode(entry["data"])
        if entry.get("compressed", False):
            try:
                data = gzip.decompress(data)
            except OSError:
                continue
        try:
            s = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if "const OnboardingFlow" in s and OLD_ENDPOINT_LINE in s:
            target_uuid = uuid
            break
        if "const OnboardingFlow" in s and MARKER in s:
            target_uuid = uuid  # déjà patché, on re-patch
            break
    if target_uuid is None:
        return "asset OnboardingFlow introuvable"

    entry = manifest[target_uuid]
    data = base64.b64decode(entry["data"])
    comp = entry.get("compressed", False)
    if comp:
        data = gzip.decompress(data)
    src = data.decode("utf-8")
    new_src, changes = patch_asset(src)
    nd = new_src.encode("utf-8")
    if comp:
        nd = gzip.compress(nd)
    entry["data"] = base64.b64encode(nd).decode("ascii")
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]
    target.write_text(new_html, encoding="utf-8")
    return f"patched (asset {target_uuid[:8]}, {', '.join(changes)})"


if __name__ == "__main__":
    for fn in FILES:
        try:
            print(f"{fn}: {patch_one(REPO / fn)}")
        except SystemExit as e:
            print(f"{fn}: ERROR · {e}")

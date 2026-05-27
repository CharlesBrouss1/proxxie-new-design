#!/usr/bin/env python3
"""Quota-gating : 2 tests gratuits avant inscription.

Remplace le système requiresAuth: true par-test par un quota d'usage global.
Tous les tests sont accessibles, mais après 2 tests complétés (mesurés via
localStorage proxxie.tests.* = "done"), le clic redirige vers signup
SAUF si l'utilisateur est déjà connecté (_proxxieIsConnected()).

Modifications :
1. Bascule tous les `requiresAuth: true` à `false` (les cartes affichent
   toutes « Démarrer »).
2. Injecte un helper `_proxxieCountCompletedTests` dans le JS de TestCard.
3. Ajoute un onClick sur le <a> qui vérifie le quota.
4. Banner d'info en haut de la liste : « 2 tests gratuits sans inscription ».
5. Modifie le TestCard pour utiliser le quota au lieu de requiresAuth.

Idempotent · sentinelles BEGIN/END.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
ASSET_UUID_PREFIX = "61feca88"

TARGETS = ["Proxxie Tests.html", "tests.html"]

BEGIN_HELPER = "/* PROXXIE_QUOTA_HELPER_BEGIN */"
END_HELPER   = "/* PROXXIE_QUOTA_HELPER_END */"

# Composant React banner · doit être défini AVANT HELPER_JS qui le concatène
QUOTA_BANNER_COMPONENT = r'''
const ProxxieQuotaBanner = () => {
  const [show, setShow] = React.useState(false);
  React.useEffect(() => {
    try {
      const connected = _proxxieIsConnectedLocal();
      const count = _proxxieCountCompletedTests();
      setShow(!connected && count >= PROXXIE_FREE_TESTS);
    } catch (e) { /* ignore */ }
  }, []);
  if (!show) return null;
  return (
    <div style={{
      maxWidth: 760, margin: "0 auto 36px", padding: "22px 26px",
      background: "white", border: "1px solid rgba(10,14,44,.08)",
      borderRadius: 18, position: "relative",
      boxShadow: "0 4px 14px -8px rgba(10,14,44,.08)",
      display: "flex", alignItems: "center", gap: 20, flexWrap: "wrap",
    }}>
      <div style={{
        position: "absolute", top: 18, bottom: 18, left: 0,
        width: 3, borderRadius: 3, background: "#FD6936",
      }} />
      <div style={{ flex: "1 1 280px", paddingLeft: 14 }}>
        <div style={{ fontSize: 13, color: "#FD6936", fontWeight: 600, marginBottom: 4 }}>
          Tu as déjà passé 2 tests
        </div>
        <div style={{ fontSize: 15, color: "var(--c-ink, #0A0E2C)", lineHeight: 1.5 }}>
          Crée un compte gratuit pour passer les autres et retrouver tes résultats à tout moment.
        </div>
      </div>
      <a href="connexion.html?signup=1" style={{
        background: "#FD6936", color: "white",
        padding: "11px 20px", borderRadius: 99, fontWeight: 600, fontSize: 14,
        textDecoration: "none", whiteSpace: "nowrap",
        display: "inline-flex", alignItems: "center", gap: 6,
        boxShadow: "0 10px 24px -10px rgba(253,105,54,.6)",
        flexShrink: 0,
      }}>
        Créer mon compte
        <span style={{ fontSize: 14 }}>&rarr;</span>
      </a>
    </div>
  );
};
'''

# Helper injecté avant TestCard, dispo dans le scope du composant
HELPER_JS = BEGIN_HELPER + r'''
const PROXXIE_FREE_TESTS = 2;
const _proxxieCountCompletedTests = () => {
  try {
    if (typeof window === "undefined" || !window.localStorage) return 0;
    let count = 0;
    for (let i = 0; i < window.localStorage.length; i++) {
      const k = window.localStorage.key(i);
      if (k && k.indexOf("proxxie.tests.") === 0 && window.localStorage.getItem(k) === "done") {
        count++;
      }
    }
    return count;
  } catch (e) { return 0; }
};
const _proxxieIsConnectedLocal = () => {
  try {
    if (typeof window === "undefined" || !window.localStorage) return false;
    const r = window.localStorage.getItem("proxxie.role");
    return r === "parent" || r === "enfant";
  } catch (e) { return false; }
};
const _proxxieCheckQuota = (e, href) => {
  if (_proxxieIsConnectedLocal()) return; // connecté = pas de limite
  const count = _proxxieCountCompletedTests();
  if (count >= PROXXIE_FREE_TESTS) {
    e.preventDefault();
    window.location.href = "Proxxie Home.html#signup";
  }
};
''' + QUOTA_BANNER_COMPONENT + END_HELPER

ANCHOR_HELPER = "const TestCard = ({ t }) =>"

# Modifs TestCard : ajout onClick quota + suppression du fallback href requiresAuth
# Variante simple (tests.html legacy)
TESTCARD_OLD_HREF = '  <a href={t.requiresAuth ? "Proxxie Home.html#signup" : t.href} style={{'
TESTCARD_NEW_HREF = '  <a href={t.href} onClick={(e) => _proxxieCheckQuota(e, t.href)} style={{'

# Variante élargie qui gère aussi `bientot` (Proxxie Tests.html)
TESTCARD_OLD_HREF_BIENTOT = '  <a href={t.bientot ? "#" : (t.requiresAuth ? "Proxxie Home.html#signup" : t.href)} onClick={t.bientot ? (e) => e.preventDefault() : undefined} style={{'
TESTCARD_NEW_HREF_BIENTOT = '  <a href={t.bientot ? "#" : t.href} onClick={(e) => { if (t.bientot) { e.preventDefault(); return; } _proxxieCheckQuota(e, t.href); }} style={{'

# CTA : ne plus dépendre de requiresAuth (qui sera false partout)
TESTCARD_OLD_CTA = '        {t.requiresAuth ? "Inscription requise" : "Démarrer"} <Icon.arrow style={{ width: 14, height: 14 }} />'
TESTCARD_NEW_CTA = '        Démarrer <Icon.arrow style={{ width: 14, height: 14 }} />'

# Badge "Inscription" sur la carte : on garde le bloc {t.requiresAuth && (...)}
# mais comme requiresAuth devient false partout, il ne s'affiche plus jamais. Pas besoin de toucher.

# Banner quota · conditionnel, rendu uniquement si count>=2 ET non connecté.
# Avant : bandeau jaune permanent en haut de la liste (laid + bruit pour les
# nouveaux visiteurs). Après : composant React qui apparaît UNIQUEMENT pour les
# utilisateurs qui ont atteint le quota (= ceux pour qui le message est utile).
# Idempotence : détection par présence du nom de composant.
# Le marker doit identifier le RENDER call (pas la définition du composant qui
# est aussi dans le helper). On cherche "<ProxxieQuotaBanner" qui est le JSX call.
QUOTA_BANNER_MARKER = "<ProxxieQuotaBanner"
QUOTA_BANNER_JSX = r'''        <ProxxieQuotaBanner />
        '''

ANCHOR_BANNER = '{TESTS_ORIENTATION.map('


def strip_between(src: str, begin: str, end: str) -> str:
    pat = re.compile(r'\s*' + re.escape(begin) + r'.*?' + re.escape(end), re.DOTALL)
    return pat.sub('', src)


def patch_src(src: str) -> tuple[str, list[str]]:
    changes = []
    # 0. Cleanup d'idempotence
    src = strip_between(src, BEGIN_HELPER, END_HELPER)
    # Cleanup banner v1 · variante avec sentinelles JSX qui se rendaient comme texte
    src = strip_between(src, "/* PROXXIE_QUOTA_BANNER_BEGIN */", "/* PROXXIE_QUOTA_BANNER_END */")
    # Cleanup banner v2 · static "2 tests gratuits sans inscription" (toujours-visible)
    # Pattern : div avec background jaune + emoji 🎁 + texte specifique
    old_banner_pattern = re.compile(
        r'\s*<div style=\{\{\s*maxWidth: 720[^<]*background: "rgba\(245,235,63,0\.18\)"[^<]*\}\}>\s*'
        r'<span style=\{\{[^}]+\}\}>🎁</span>\s*'
        r'<span><strong>2 tests gratuits[^<]*</strong>[^<]*</span>\s*'
        r'</div>',
        re.DOTALL,
    )
    src = old_banner_pattern.sub('', src)
    # Cleanup banner v3 · render call précédent <ProxxieQuotaBanner /> (pour réinsertion)
    src = re.sub(r'\n\s*<ProxxieQuotaBanner\s*/>\s*', '\n', src)

    # 1. Tous les requiresAuth: true → false
    n_flips = src.count('requiresAuth: true')
    if n_flips > 0:
        src = src.replace('requiresAuth: true', 'requiresAuth: false')
        changes.append(f"{n_flips} requiresAuth bascule à false")

    # 2. Injection helper avant TestCard
    if ANCHOR_HELPER not in src:
        return src, changes + ["WARN: ancre TestCard introuvable"]
    src = src.replace(ANCHOR_HELPER, HELPER_JS + "\n\n" + ANCHOR_HELPER, 1)
    changes.append("+ helper _proxxieCheckQuota")

    # 3. Modif TestCard href · 2 variantes possibles
    if TESTCARD_OLD_HREF_BIENTOT in src:
        src = src.replace(TESTCARD_OLD_HREF_BIENTOT, TESTCARD_NEW_HREF_BIENTOT, 1)
        changes.append("TestCard href + onClick quota (variante bientot)")
    elif TESTCARD_OLD_HREF in src:
        src = src.replace(TESTCARD_OLD_HREF, TESTCARD_NEW_HREF, 1)
        changes.append("TestCard href + onClick quota")
    elif TESTCARD_NEW_HREF in src or TESTCARD_NEW_HREF_BIENTOT in src:
        pass  # déjà patché
    else:
        changes.append("WARN: ancre href TestCard introuvable")

    # 4. Modif TestCard CTA
    if TESTCARD_OLD_CTA in src:
        src = src.replace(TESTCARD_OLD_CTA, TESTCARD_NEW_CTA, 1)
        changes.append("TestCard CTA simplifié")

    # 5. Banner info quota (idempotent par détection de présence)
    if QUOTA_BANNER_MARKER in src:
        # Déjà inséré · skip
        changes.append("banner déjà présent")
    elif ANCHOR_BANNER in src:
        # Insère le banner juste avant la ligne `{TESTS_ORIENTATION.map(`
        idx = src.find(ANCHOR_BANNER)
        line_start = src.rfind('\n', 0, idx) + 1
        src = src[:line_start] + QUOTA_BANNER_JSX + src[line_start:]
        changes.append("+ banner info 2 tests gratuits")
    else:
        changes.append("WARN: ancre banner TESTS_ORIENTATION.map introuvable")

    return src, changes


def patch_one(target: pathlib.Path) -> str:
    if not target.exists():
        return f"{target.name}: file not found"
    html = target.read_text(encoding="utf-8")
    m = re.search(r'(<script type="__bundler/manifest">)(.*?)(</script>)', html, re.DOTALL)
    if not m:
        return f"{target.name}: pas de manifest"
    manifest = json.loads(m.group(2))
    uuid = next((k for k in manifest if k.startswith(ASSET_UUID_PREFIX)), None)
    if uuid is None:
        return f"{target.name}: asset {ASSET_UUID_PREFIX} introuvable"
    entry = manifest[uuid]
    raw = base64.b64decode(entry['data'])
    comp = entry.get('compressed', False)
    src = gzip.decompress(raw).decode('utf-8') if comp else raw.decode('utf-8')
    new_src, changes = patch_src(src)
    if new_src == src or not changes:
        return f"{target.name}: aucun changement"
    nd = new_src.encode('utf-8')
    if comp:
        nd = gzip.compress(nd)
    entry['data'] = base64.b64encode(nd).decode('ascii')
    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]
    target.write_text(new_html, encoding='utf-8')
    return f"{target.name}: [{', '.join(changes)}]"


if __name__ == "__main__":
    for fn in TARGETS:
        print(patch_one(REPO / fn))

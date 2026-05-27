#!/usr/bin/env python3
"""Masque le panneau legacy « Allez plus loin avec Proxxie » présent dans la
Results component des 3 premiers tests (OCEAN-X, PCM, RIASEC).

Pourquoi :
- Charles a fait une critique UX : trop de CTA en bas de page (panneau natif
  bleu gradient + bandeau AI + signup callout). On a refondu la hiérarchie :
  un seul CTA primaire = RDV Charles. Le panneau bleu legacy fait redondance
  avec le nouveau bloc (mêmes liens "Voir tous les tests" + "Refaire le test"
  qu'on a dégradés en liens texte secondaires) et concurrence visuellement
  le CTA Charles.

Stratégie :
- Le panneau JSX est imbriqué dans la fonction Results, intra-bundle. Plutôt
  que d'éditer chaque variante du JSX (3 tests, structures légèrement
  différentes), on injecte un mini script dans le template head qui :
  - cherche tout h2 dont le texte commence par "Allez plus loin avec Proxxie"
  - remonte 1 à 4 parents pour trouver le div avec radial-gradient
  - masque (display: none)
- MutationObserver pour gérer le render React asynchrone.

Cible : 3 tests seulement (OCEAN-X, PCM, RIASEC) mais on l'applique à tous
les tests · le script no-op s'il ne trouve rien.
Idempotent · sentinelles HTML BEGIN/END dans le head du template.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent

BEGIN = "<!-- PROXXIE_HIDE_LEGACY_OUTRO_BEGIN -->"
END   = "<!-- PROXXIE_HIDE_LEGACY_OUTRO_END -->"

SCRIPT_BLOCK = BEGIN + """
<script>
(function(){
  var hideLegacyOutro = function(){
    var hs = document.querySelectorAll('h2');
    for (var i = 0; i < hs.length; i++) {
      var h = hs[i];
      var txt = (h.textContent || '').trim();
      if (txt.indexOf('Allez plus loin avec Proxxie') === 0) {
        // Remonte jusqu'à 5 parents pour trouver le div radial-gradient
        var el = h.parentElement;
        for (var d = 0; d < 5 && el; d++) {
          var bg = el.style && el.style.background;
          if (bg && bg.indexOf('radial-gradient') !== -1) {
            el.style.display = 'none';
            return true;
          }
          el = el.parentElement;
        }
      }
    }
    return false;
  };
  // Première passe au DOMContentLoaded
  var run = function(){ try { hideLegacyOutro(); } catch(e){} };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
  // Re-run à chaque mutation du DOM (React monte asynchrone, navigation entre modes)
  if (typeof MutationObserver !== 'undefined') {
    var obs = new MutationObserver(function(){
      // Throttle : requestAnimationFrame suffit, on n'a pas besoin d'un appel par mutation
      if (obs._raf) return;
      obs._raf = requestAnimationFrame(function(){ obs._raf = null; run(); });
    });
    var startObs = function(){
      if (document.body) obs.observe(document.body, { childList: true, subtree: true });
      else setTimeout(startObs, 50);
    };
    startObs();
  } else {
    // Fallback : quelques re-runs espacés
    setTimeout(run, 300);
    setTimeout(run, 1000);
    setTimeout(run, 2500);
  }
})();
</script>
""" + END

# Toutes les pages test (le script no-op sur les autres pages)
TARGETS = sorted([p.name for p in REPO.glob("Proxxie Test*.html")] +
                 [p.name for p in REPO.glob("test-*.html")])


def strip_between(html: str, begin: str, end: str) -> str:
    pat = re.compile(re.escape(begin) + r'.*?' + re.escape(end), re.DOTALL)
    return pat.sub('', html)


def patch_template(template: str) -> tuple[str, bool]:
    template = strip_between(template, BEGIN, END)
    if '</head>' in template:
        template = template.replace('</head>', SCRIPT_BLOCK + '\n</head>', 1)
        return template, True
    if '<head>' in template:
        template = template.replace('<head>', '<head>\n' + SCRIPT_BLOCK, 1)
        return template, True
    return template, False


def patch_one(target: pathlib.Path) -> str:
    if not target.exists():
        return f"{target.name}: file not found"
    html = target.read_text(encoding="utf-8")
    m = re.search(r'(<script type="__bundler/template">)(.*?)("\s*</script>)', html, re.DOTALL)
    if not m:
        return f"{target.name}: pas de template bundler"
    template_json = m.group(2) + '"'
    try:
        template = json.loads(template_json)
    except Exception as e:
        return f"{target.name}: JSON parse error {e}"
    new_template, changed = patch_template(template)
    if not changed:
        return f"{target.name}: ni <head> ni </head>, skip"
    new_template_json = json.dumps(new_template, ensure_ascii=False)
    assert new_template_json.endswith('"')
    new_template_json = new_template_json[:-1]
    # Escape `</` en `<\/` pour préserver l'encodage original (gotcha bundler)
    new_template_json = new_template_json.replace('</', '<\\/')
    new_html = html[:m.start(2)] + new_template_json + html[m.end(2):]
    target.write_text(new_html, encoding='utf-8')
    return f"{target.name}: script hide-legacy-outro injecté"


if __name__ == "__main__":
    for fn in TARGETS:
        print(patch_one(REPO / fn))

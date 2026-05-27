#!/usr/bin/env python3
"""Fix responsive · force les grids inline (gridTemplateColumns) à stacker sur mobile.

Le prototype utilise massivement des inline styles React avec `gridTemplateColumns`
qui ne contiennent pas de media query (impossible en inline). Sur mobile (<= 768px),
ça crée des overlaps visibles (colonnes qui ne stackent pas).

Stratégie : injecter une `<style>` global dans le template bundler qui cible les
patterns d'inline styles les plus fréquents via attribute selectors :
   div[style*="grid-template-columns: 1fr 1fr"]
   div[style*="grid-template-columns: 1fr 1.1fr"]
   ...
Et les force à `1fr !important` sous 768px.

Cible toutes les pages bundlées (homepage + tests + dashboard + autres).
Idempotent · sentinelles `<!-- PROXXIE_RESPONSIVE_GRIDS_BEGIN -->`.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent

BEGIN = "<!-- PROXXIE_RESPONSIVE_GRIDS_BEGIN -->"
END   = "<!-- PROXXIE_RESPONSIVE_GRIDS_END -->"

# Bloc CSS à injecter dans le <head> du template bundler.
# Le sélecteur cible les patterns de gridTemplateColumns les plus courants.
# `!important` est nécessaire car les inline styles JSX ont une spécificité maximale.
CSS_BLOCK = BEGIN + """
<style>
@media (max-width: 768px) {
  /* 2-column grids : stacker en single column */
  div[style*="grid-template-columns: 1fr 1fr"],
  div[style*="grid-template-columns: 1.1fr 1fr"],
  div[style*="grid-template-columns: 1fr 1.1fr"],
  div[style*="grid-template-columns: 1.2fr 1fr"],
  div[style*="grid-template-columns: 1fr 1.2fr"],
  div[style*="grid-template-columns: 1.5fr 1fr"],
  div[style*="grid-template-columns: 1fr 1.5fr"],
  div[style*="grid-template-columns: 2fr 1fr"],
  div[style*="grid-template-columns: 1fr 2fr"],
  div[style*="grid-template-columns: repeat(2, 1fr)"],
  section[style*="grid-template-columns: 1fr 1fr"],
  section[style*="grid-template-columns: repeat(2, 1fr)"] {
    grid-template-columns: 1fr !important;
    gap: 20px !important;
  }
  /* 3-column grids : stacker en single column */
  div[style*="grid-template-columns: repeat(3, 1fr)"],
  div[style*="grid-template-columns: 1fr 1fr 1fr"],
  section[style*="grid-template-columns: repeat(3, 1fr)"] {
    grid-template-columns: 1fr !important;
    gap: 16px !important;
  }
  /* 4-column grids : passer en 2 colonnes */
  div[style*="grid-template-columns: repeat(4, 1fr)"],
  div[style*="grid-template-columns: 1fr 1fr 1fr 1fr"] {
    grid-template-columns: 1fr 1fr !important;
    gap: 12px !important;
  }
  /* Sticky disabled sur mobile : un sticky 540px de hauteur déborde toujours */
  div[style*="position: sticky"] {
    position: static !important;
    height: auto !important;
  }
  /* Padding latéral minimum sur les shells (cas où marges écran trop minces) */
  .shell {
    padding-left: 18px !important;
    padding-right: 18px !important;
  }
}
@media (max-width: 480px) {
  /* Très petits écrans : ajuster les tailles de heros énormes */
  h1 {
    font-size: clamp(28px, 8vw, 38px) !important;
    line-height: 1.15 !important;
  }
  h2 {
    font-size: clamp(22px, 6vw, 30px) !important;
    line-height: 1.2 !important;
  }
}
</style>
""" + END

# Cibles : toutes les pages HTML bundlées Proxxie
TARGETS = sorted(p.name for p in REPO.glob("*.html"))


def strip_between(html: str, begin: str, end: str) -> str:
    pat = re.compile(re.escape(begin) + r'.*?' + re.escape(end), re.DOTALL)
    return pat.sub('', html)


def patch_template(template: str) -> tuple[str, bool]:
    """Injecte le bloc CSS dans le <head> du template. Idempotent."""
    template = strip_between(template, BEGIN, END)
    # Le template est une string JSON-escaped (échappée pour <script type="__bundler/template">)
    # Mais ici on travaille sur le template décodé (string JSON.parse), donc directement HTML.
    # Insérer juste après <head> ou avant </head>.
    if '</head>' in template:
        template = template.replace('</head>', CSS_BLOCK + '\n</head>', 1)
        return template, True
    elif '<head>' in template:
        template = template.replace('<head>', '<head>\n' + CSS_BLOCK, 1)
        return template, True
    return template, False


def patch_one(target: pathlib.Path) -> str:
    if not target.exists():
        return f"{target.name}: file not found"
    html = target.read_text(encoding="utf-8")
    # Le template bundler vit dans <script type="__bundler/template">"escaped HTML"</script>.
    # Attention : le template peut contenir des <script type="application/ld+json">...</script>
    # imbriqués pour SEO. Le close du template est unique : la JSON string ferme par `"` non
    # échappé suivi de whitespace + </script>. Les `"` à l'intérieur sont `\"`.
    # Pattern : `"` + (\s+) + `</script>`. Les ld+json scripts ferment sur `}` + \s + </script>.
    m = re.search(r'(<script type="__bundler/template">)(.*?)("\s*</script>)', html, re.DOTALL)
    if not m:
        return f"{target.name}: pas de template bundler"
    # group(2) contient le contenu SANS le `"` final (puisque `"</script>` est dans group(3))
    # On reconstruit la JSON string en remettant le `"` pour le parse.
    # Remet le `"` de fin (capturé dans group(3) avec `</script>`) pour reparser comme JSON
    template_json = m.group(2) + '"'
    try:
        template = json.loads(template_json)
    except Exception as e:
        return f"{target.name}: JSON parse error {e}"
    new_template, changed = patch_template(template)
    if not changed:
        return f"{target.name}: ni <head> ni </head> trouvé, skip"
    # Re-sérialise. json.dumps inclut les `"` ouvrant et fermant. On retire le `"` fermant
    # pour le rendre cohérent avec le template/close `"</script>` du fichier (le `"` reste
    # dans group(3) qu'on conserve).
    new_template_json = json.dumps(new_template, ensure_ascii=False)
    assert new_template_json.endswith('"'), "json.dumps doit fermer par un quote"
    new_template_json = new_template_json[:-1]  # retire le `"` fermant
    # CRITIQUE : escape les `</` en `<\/` pour préserver l'encodage original. Le bundler
    # JS et notre regex matchent `</script>` littéral. Sans escape, le PREMIER `</script>`
    # interne (du <script type="application/ld+json"> imbriqué) tronque l'extraction.
    new_template_json = new_template_json.replace('</', '<\\/')
    new_html = html[:m.start(2)] + new_template_json + html[m.end(2):]
    # NOTE : on ne touche pas au <head> statique pré-bundle. Le bundler remplace
    # le document complet à l'unpack via documentElement.replaceWith, donc le
    # <head> du template (où on a injecté la CSS) prend le pas dès le 1er render
    # post-unpack. Patcher aussi le head statique briserait le JSON template
    # (le marker BEGIN/END existerait à deux endroits, strip_between non-greedy
    # toucherait à la fois la zone statique ET le template JSON).
    target.write_text(new_html, encoding='utf-8')
    return f"{target.name}: patched (template only)"


if __name__ == "__main__":
    for fn in TARGETS:
        # Skip non-Proxxie HTML files
        if fn.startswith('_') or fn == "DESIGN_CRITIQUE.md":
            continue
        result = patch_one(REPO / fn)
        print(result)

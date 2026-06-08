"""Rewrite Future-Proof's per-pillar comparison copy from rhetorical questions
to explicit, interpretive statements (direction + meaning + magnitude).

The user complaint: comparison prompts like
  "Charles se place plus haut que toi ici. D'ou vient la difference ?"
leave the difference to interpretation. The approved registry is INTERPRETIVE:
state who sees the dimension higher, what the dimension measures, and the gap
magnitude, with no dangling question.

Idempotent: skips a file that already carries INTERP_MARKER.
In-place on the gzip+base64 bundle embedded in each HTML, matching the
convention of _patch_results_layout.py.
"""
from __future__ import annotations

import base64
import gzip
import json
import pathlib
import re

ASSET_UUID_PREFIX = "61feca88"
INTERP_MARKER = "se voit nettement plus fort ici"

TARGETS = ("test-futureproof.html", "Proxxie Test FuturProof.html")

# New helper: takes (row, gap) so it can name the dimension and its meaning.
NEW_HELPER = """  const pillarPrompt = (row, gap) => {
    const g = Math.abs(gap);
    const m = row.meta;
    const inside = m.short.match(/\\(([^)]+)\\)/);
    const lead = m.short.replace(/\\s*\\([^)]*\\)\\s*/, "").trim();
    const meaning = inside ? (inside[1] + ", " + lead.charAt(0).toLowerCase() + lead.slice(1)) : lead;
    if (g <= 8) {
      return "Perception quasi identique sur " + m.l + " (" + meaning + ") : " + g + " points d'écart seulement. Vous lisez cette dimension de la même façon.";
    }
    const intensity = g > 12 ? "c'est un vrai contraste de perception sur cette dimension" : "c'est un écart net de perception sur cette dimension";
    const Intensity = intensity.charAt(0).toUpperCase() + intensity.slice(1);
    if (isPredict) {
      if (gap > 0) return who + " t'a sous-estimé ici : tu te places " + g + " points au-dessus de sa prédiction sur " + meaning + ". " + Intensity + ".";
      return who + " t'a vu plus fort que tu ne te places : " + g + " points entre sa prédiction et ta réponse sur " + meaning + ". " + Intensity + ".";
    }
    if (gap > 0) return "Tu te vois nettement plus fort ici : " + meaning + ". " + g + " points d'écart, " + intensity + ".";
    return who + " se voit nettement plus fort ici : " + meaning + ". " + g + " points d'écart, " + intensity + ".";
  };"""

OLD_HELPER_RE = re.compile(
    r"  const pillarPrompt = \(gap\) => \{.*?\n  \};",
    re.DOTALL,
)
CALLSITE_RE = re.compile(r"pillarPrompt\(gap\)")


def _patch_src(src: str) -> str:
    if INTERP_MARKER in src:
        return src  # already interpretive
    if not OLD_HELPER_RE.search(src):
        raise RuntimeError("pillarPrompt helper not found, bundle changed?")
    src = OLD_HELPER_RE.sub(lambda _m: NEW_HELPER, src, count=1)
    src = CALLSITE_RE.sub("pillarPrompt(row, gap)", src)
    return src


def patch_file(path: pathlib.Path) -> str:
    html = path.read_text(encoding="utf-8")
    m = re.search(
        r'(<script type="__bundler/manifest">)(.*?)(</script>)', html, re.DOTALL
    )
    if not m:
        return f"{path.name}: pas de manifest"
    manifest = json.loads(m.group(2))
    uuid = next((k for k in manifest if k.startswith(ASSET_UUID_PREFIX)), None)
    if uuid is None:
        return f"{path.name}: asset introuvable"
    entry = manifest[uuid]
    raw = base64.b64decode(entry["data"])
    comp = bool(entry.get("compressed"))
    src = gzip.decompress(raw).decode("utf-8") if comp else raw.decode("utf-8")

    if INTERP_MARKER in src:
        return f"{path.name}: deja interpretatif (skip)"

    new_src = _patch_src(src)
    if new_src == src:
        return f"{path.name}: aucun changement"

    nd = new_src.encode("utf-8")
    if comp:
        nd = gzip.compress(nd)
    entry["data"] = base64.b64encode(nd).decode("ascii")
    new_manifest = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[: m.start(2)] + new_manifest + html[m.end(2):]
    path.write_text(new_html, encoding="utf-8")
    return f"{path.name}: PATCHED"


def main() -> None:
    root = pathlib.Path(".")
    for name in TARGETS:
        p = root / name
        if not p.exists():
            print(f"{name}: absent")
            continue
        print(patch_file(p))


if __name__ == "__main__":
    main()

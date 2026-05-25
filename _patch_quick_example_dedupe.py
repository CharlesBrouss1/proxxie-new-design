#!/usr/bin/env python3
"""Dedupe duplicated blocks in the Proxxie Home bundle.

The bundled React component had several blocks rendered twice:
  - QuickExample modal sections (OCEAN-X, VALEURS-BESOINS, FORCES-AXES,
    VIGILANCE-LEVIERS, PROCHAINES).
  - Section CTA F007 («Voir comment on aide» / «30 min avec Charles»)
    rendered twice right after the empathy block.

For QuickExample sections, the second copy was an em-dash-flavored
duplicate, we keep the first (comma-flavored). For F007, the first copy is
the em-dash one and the second is the comma one, we drop the em-dash copy
to honor the «no em-dash» preference.

We also rename the 3rd hero trust-bar badge from a duplicate
«Données privées (RGPD)» (shield icon) to «Sans CB ni engagement» so each
badge carries a distinct trust signal.

Re-runnable. Idempotent. Touches the React asset bundles inside
Proxxie Home.html and index.html.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent

# Each pair: marker that opens the duplicate, marker that opens the next
# legitimate section right after the duplicated block. We delete everything
# between (inclusive of the duplicate start, exclusive of the next marker).
# Used for cases where the duplicate is the SECOND occurrence of start_marker.
DUPLICATE_RANGES = [
    # 2nd copy of: OCEAN-X + VALEURS-BESOINS + FORCES-AXES
    ("{/* QE-OCEAN-X: Big Five (OCEAN-X) scores avec interprétation */}",
     "{/* Commentaire coach Marion */}"),
    # 2nd copy of: VIGILANCE-LEVIERS + PROCHAINES
    ("{/* QE-VIGILANCE-LEVIERS: ce qu'on garde à l'œil vs ce qui pousse */}",
     "{/* Aperçu parcours coach */}"),
]

# Each pair: (start_marker, end_marker) — both UNIQUE in the bundle.
# We delete the slice [start_marker_pos, end_marker_pos[. Use when the
# duplicate is the FIRST occurrence and the surviving copy is identified
# by a different (unique) marker.
REMOVE_BETWEEN = [
    # F007 CTA block rendered twice; the em-dash variant precedes the comma
    # variant. Drop the em-dash one.
    ("{/* F007: section CTA — closes the empathy block with two clear paths. */}",
     "{/* F007: section CTA, closes the empathy block with two clear paths. */}"),
]

# Each entry: (old, new). Performed verbatim. Idempotent because once `old`
# is gone the replace becomes a no-op.
LITERAL_REPLACEMENTS = [
    # Hero trust-bar: third badge was a duplicate label of the first one.
    # The <Icon.shield /> anchor is unique to this exact occurrence, so we
    # rename it to a distinct trust signal aligned with the meta description
    # («Sans CB, sans engagement»).
    ("<Icon.shield /> Données privées (RGPD)",
     "<Icon.shield /> Sans CB ni engagement"),
]


def dedupe(text: str) -> tuple[str, int]:
    """Returns (new_text, removed_blocks)."""
    removed = 0
    for start_marker, end_marker in DUPLICATE_RANGES:
        # The duplicate is the SECOND occurrence of start_marker.
        first = text.find(start_marker)
        if first < 0:
            continue
        second = text.find(start_marker, first + len(start_marker))
        if second < 0:
            continue  # already deduped
        end = text.find(end_marker, second)
        if end < 0:
            continue  # malformed, skip rather than corrupt
        # Trim the trailing whitespace before the next section comment
        # so we don't leave a double blank line in the JSX.
        cut_end = end
        while cut_end > second and text[cut_end - 1] in " \t":
            cut_end -= 1
        text = text[:second] + text[cut_end:]
        removed += 1

    for start_marker, end_marker in REMOVE_BETWEEN:
        start = text.find(start_marker)
        if start < 0:
            continue  # already removed
        end = text.find(end_marker, start + len(start_marker))
        if end < 0:
            continue
        cut_end = end
        while cut_end > start and text[cut_end - 1] in " \t":
            cut_end -= 1
        text = text[:start] + text[cut_end:]
        removed += 1

    for old, new in LITERAL_REPLACEMENTS:
        if old in text:
            text = text.replace(old, new)
            removed += 1
    return text, removed


def patch_file(path: pathlib.Path) -> bool:
    html = path.read_text(encoding="utf-8")
    m = re.search(r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)', html, re.DOTALL)
    if not m:
        print(f"  no manifest in {path.name}")
        return False

    manifest = json.loads(m.group(2))
    changed = False
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
            continue

        # Skip assets that contain none of our markers, cheap upfront filter.
        markers = (
            [pair[0] for pair in DUPLICATE_RANGES]
            + [pair[0] for pair in REMOVE_BETWEEN]
            + [old for old, _ in LITERAL_REPLACEMENTS]
        )
        if not any(mk in text for mk in markers):
            continue

        new_text, removed = dedupe(text)
        if removed == 0:
            print(f"  asset {uuid} in {path.name}: already deduped")
            continue

        new_data = new_text.encode("utf-8")
        if compressed:
            new_data = gzip.compress(new_data)
        entry["data"] = base64.b64encode(new_data).decode("ascii")
        changed = True
        print(f"  patched asset {uuid} in {path.name} (removed {removed} duplicate block(s))")

    if not changed:
        return False

    new_manifest_json = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest_json + html[m.end(2):]
    path.write_text(new_html, encoding="utf-8")
    return True


if __name__ == "__main__":
    files = ["Proxxie Home.html", "index.html"]
    for fn in files:
        p = REPO / fn
        if not p.exists():
            print(f"skip (missing): {fn}")
            continue
        print(f"Processing: {fn}")
        if patch_file(p):
            print(f"  ✓ modified {fn}")
        else:
            print(f"  - no change to {fn}")

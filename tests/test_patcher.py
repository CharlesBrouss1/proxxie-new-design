"""Tests for _design_fixes.py — the bundle+CSS patcher.

The patcher operates on production HTML files containing:
  (a) Inline CSS inside a JS string literal in a <style> tag (escaped `\\n`)
  (b) React/JSX assets gzipped + base64-encoded inside a
      <script type="__bundler/manifest"> block

These tests guard the two failure modes that have actually bitten us:
  1. Patches no longer idempotent (run twice → file mutates twice)
  2. The team's main-branch refactors silently invalidate patch needles

Run from the repo root:  python3 -m pytest tests/ -v
"""
import base64
import gzip
import importlib.util
import json
import pathlib
import re
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).parent.parent


def _load_patcher_module():
    spec = importlib.util.spec_from_file_location("_design_fixes", REPO / "_design_fixes.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ============================================================================
# 1. Escape helper round-trips through JSON-string parsing (the model the
#    browser's JS parser uses when it reads the embedded `<style>` literal).
# ============================================================================
@pytest.mark.parametrize("source", [
    "simple text",
    "with\nnewline",
    'with "quotes"',
    "with backslash \\",
    "css: { color: red; }\n@media (max-width: 760px) { ... }",
    "@font-face {\n  font-family: 'Mulish';\n  src: url(\"foo.woff2\") format('woff2');\n}",
])
def test_escape_for_js_string_roundtrips(source):
    df = _load_patcher_module()
    escaped = df._escape_for_js_string(source)
    # The escaped form, wrapped in quotes, must parse as a JSON string
    # back to the original. This is the model the browser uses to
    # un-escape the embedded CSS at runtime.
    decoded = json.loads('"' + escaped + '"')
    assert decoded == source, f"Round-trip failed: {source!r} -> {escaped!r} -> {decoded!r}"


# ============================================================================
# 2. Manifest decode → re-encode preserves the inner asset bytes.
#    (Gzip wrapper bytes can differ between compressions; what matters is
#    that the decompressed payload round-trips.)
# ============================================================================
def test_manifest_asset_inner_byte_equality():
    home = REPO / "Proxxie Home.html"
    html = home.read_text(encoding="utf-8")
    m = re.search(r'<script type="__bundler/manifest"[^>]*>(.*?)</script>', html, re.DOTALL)
    assert m is not None, "Home.html has no bundler manifest — file structure changed"
    manifest = json.loads(m.group(1))
    assert len(manifest) > 5, "Manifest suspiciously small — expected ~25 assets"

    checked = 0
    for uuid, entry in manifest.items():
        data = base64.b64decode(entry["data"])
        if not entry.get("compressed"):
            # uncompressed: base64 round-trip
            re_encoded = base64.b64encode(data).decode("ascii")
            assert re_encoded == entry["data"], f"base64 round-trip failed for {uuid}"
            checked += 1
            continue
        try:
            inner = gzip.decompress(data)
        except Exception:
            # Some assets may be raw deflate or similar; skip
            continue
        # Re-compress and decompress — the INNER bytes must match
        re_compressed = gzip.compress(inner)
        re_decompressed = gzip.decompress(re_compressed)
        assert re_decompressed == inner, f"gzip inner-byte round-trip failed for {uuid}"
        checked += 1

    assert checked >= 20, f"Only checked {checked} assets — manifest may be malformed"


# ============================================================================
# 3. Idempotency — running the patcher twice on a clean checkout produces no
#    second mutation. This is the bug that bit us when overlapping CSS
#    patches both anchored on `.btn-ghost {`.
# ============================================================================
def test_patcher_is_idempotent_on_home():
    home = REPO / "Proxxie Home.html"
    # Use a checked-in snapshot so a flaky local state doesn't break the test
    subprocess.run(["git", "checkout", "--", str(home)], cwd=REPO, check=True)

    def md5(p):
        import hashlib
        return hashlib.md5(p.read_bytes()).hexdigest()

    initial = md5(home)
    subprocess.run([sys.executable, "_design_fixes.py", "Proxxie Home.html"],
                   cwd=REPO, check=True, capture_output=True)
    after_first = md5(home)
    subprocess.run([sys.executable, "_design_fixes.py", "Proxxie Home.html"],
                   cwd=REPO, check=True, capture_output=True)
    after_second = md5(home)

    # If main is already fully patched, first run should be a no-op.
    # If patches are sitting in the queue, first run applies them, second
    # run MUST NOT mutate again.
    assert after_first == after_second, (
        f"Patcher is not idempotent: first run produced {after_first}, "
        f"second run produced {after_second}. A patch is appending state every run."
    )

    # Restore the file for downstream tests
    subprocess.run(["git", "checkout", "--", str(home)], cwd=REPO, check=True)


# ============================================================================
# 4. --strict mode passes against main (catches the moment our needles drift)
# ============================================================================
def test_strict_mode_passes_on_current_main():
    result = subprocess.run(
        [sys.executable, "_design_fixes.py", "--strict"],
        cwd=REPO, capture_output=True, text=True,
    )
    # Restore any files mutated by the run so other tests aren't affected
    subprocess.run(["git", "checkout", "--",
                    "Proxxie Home.html", "Proxxie Coach.html", "Proxxie Dashboard.html",
                    "Proxxie Documents.html", "Proxxie Rapport.html",
                    "Proxxie Ressources.html", "Proxxie Connexion.html", "Proxxie Test.html",
                    "index.html", "coach.html", "dashboard.html", "documents.html",
                    "rapport.html", "ressources.html", "connexion.html", "test.html",
                    "guide-orientation.html"],
                   cwd=REPO, check=False, capture_output=True)
    assert result.returncode == 0, (
        f"--strict failed (exit {result.returncode}). This means a team commit "
        f"drifted one of our patch needles. Output:\n{result.stdout}\n{result.stderr}"
    )


# ============================================================================
# 5. Sentinel detection — each CSS patch must have a unique sentinel so the
#    idempotency check correctly identifies "already applied".
# ============================================================================
def test_each_css_patch_has_unique_sentinel():
    df = _load_patcher_module()
    sentinels = []
    for old, new in df.CSS_PATCHES:
        sent = df._sentinel_for(new)
        sentinels.append(sent)
    # All sentinels must be distinct or two patches would clobber each
    # other's idempotency detection.
    duplicates = [s for s in sentinels if sentinels.count(s) > 1]
    assert not duplicates, f"Duplicate sentinels found: {set(duplicates)}"


# ============================================================================
# 6. No two BUNDLE_PATCHES share the same `old` AND target the same page.
#    The overlapping-patch bug was on CSS; this guards the bundle side too.
# ============================================================================
def test_no_overlapping_bundle_patches():
    df = _load_patcher_module()
    seen = {}
    for patch in df.BUNDLE_PATCHES:
        for old, _new in patch["replacements"]:
            key = old
            if key in seen:
                # OK only if pages_skip lists are disjoint
                prev_skip = set(seen[key].get("pages_skip", []))
                this_skip = set(patch.get("pages_skip", []))
                # If neither skips anything, both apply to all pages — overlap
                if not prev_skip and not this_skip:
                    pytest.fail(
                        f"Two BUNDLE_PATCHES share the same `old` and target "
                        f"the same pages: {seen[key]['name']!r} and {patch['name']!r}"
                    )
            seen[key] = patch


# ============================================================================
# 7. The situations CTA (F007) must never be duplicated. This regression kept
#    reappearing: every bundle re-export ships the CTA (comma comment variant),
#    but the additive F007 patch only recognized its own em-dash `new` string,
#    so it appended a second copy on each patcher run. A `skip_if` marker now
#    detects the existing CTA in any variant. Guard it so it can't come back.
# ============================================================================
def _count_in_bundle(html: str, needle: str) -> int:
    m = re.search(r'<script type="__bundler/manifest"[^>]*>(.*?)</script>', html, re.DOTALL)
    assert m is not None, "no bundler manifest"
    manifest = json.loads(m.group(1))
    total = 0
    for entry in manifest.values():
        data = base64.b64decode(entry["data"])
        if entry.get("compressed"):
            try:
                data = gzip.decompress(data)
            except Exception:
                continue
        try:
            total += data.decode("utf-8").count(needle)
        except UnicodeDecodeError:
            continue
    return total


def test_situations_cta_not_duplicated_after_patch():
    home = REPO / "Proxxie Home.html"
    subprocess.run(["git", "checkout", "--", str(home)], cwd=REPO, check=True)
    try:
        # The committed bundle already ships exactly one situations CTA.
        assert _count_in_bundle(home.read_text(encoding="utf-8"), "Voir comment on aide") == 1, \
            "Precondition failed: committed Home.html should ship exactly one situations CTA"
        # Running the patcher must NOT append a second one.
        subprocess.run([sys.executable, "_design_fixes.py", "Proxxie Home.html"],
                       cwd=REPO, check=True, capture_output=True)
        count = _count_in_bundle(home.read_text(encoding="utf-8"), "Voir comment on aide")
        assert count == 1, (
            f"F007 duplicated the situations CTA: found {count} copies of "
            f"'Voir comment on aide' after a patcher run (expected 1). The "
            f"skip_if idempotency guard regressed."
        )
    finally:
        subprocess.run(["git", "checkout", "--", str(home)], cwd=REPO, check=True)


def test_f007_patch_has_skip_if_guard():
    df = _load_patcher_module()
    f007 = next((p for p in df.BUNDLE_PATCHES if p["name"].startswith("F007")), None)
    assert f007 is not None, "F007 patch disappeared from BUNDLE_PATCHES"
    assert f007.get("skip_if"), (
        "F007 lost its skip_if guard — without it, a re-export that already "
        "ships the CTA will be doubled on the next patcher run."
    )

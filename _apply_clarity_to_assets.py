#!/usr/bin/env python3
"""Apply the clarity edits (results-screen scale legends / verdicts / framing)
directly to the decoded 61feca88 bundler asset of each already-fully-patched
test HTML.

Rationale: running the _patch_build_<test>.py scripts in isolation rebuilds the
test block from the base file and DROPS every post-build patch (CompareHub,
ResultsTopActions, SaveResultsCallout, etc). Instead we diff the test's
<NAME>_BLOCK raw string (HEAD vs working tree) to recover exactly the localized
clarity hunks, then splice those same hunks into the live asset. This keeps all
post-build work intact and only adds the clarity changes.

Read-only on .py sources; writes the HTML files in place. Idempotent: a hunk
whose "after" text is already present is skipped.
"""
import re, json, base64, gzip, subprocess, sys, difflib, pathlib

ASSET_PREFIX = "61feca88"

# test -> (py script, BLOCK var name, [html variants])
TESTS = {
    "caas":        ("_patch_build_caas.py",        "CAAS_BLOCK",        ["Proxxie Test CAAS.html", "test-caas.html"]),
    "brief":       ("_patch_build_brief.py",       "BRIEF_BLOCK",       ["Proxxie Test BRIEF.html", "test-brief.html"]),
    "phq9":        ("_patch_build_phq9.py",        "PHQ9_BLOCK",        ["Proxxie Test PHQ9.html", "test-phq9.html"]),
    "grit":        ("_patch_build_grit.py",        "GRIT_BLOCK",        ["Proxxie Test Grit.html", "test-grit.html"]),
    "futureproof": ("_patch_build_futureproof.py", "FUTUREPROOF_BLOCK", ["Proxxie Test FuturProof.html", "test-futureproof.html"]),
    "dweck":       ("_patch_build_dweck.py",       "DWECK_BLOCK",       ["Proxxie Test Dweck.html", "test-dweck.html"]),
    "via":         ("_patch_build_via.py",         "VIA_BLOCK",         ["Proxxie Test VIA.html", "test-via.html"]),
}


def extract_block(src: str, var: str) -> str:
    m = re.search(rf"{var}\s*=\s*r'''(.*?)'''", src, re.DOTALL)
    if not m:
        raise SystemExit(f"BLOCK var {var} not found")
    return m.group(1)


def head_file(path: str) -> str:
    return subprocess.check_output(["git", "show", f"HEAD:{path}"], text=True)


def compute_hunks(old: str, new: str, ctx: int = 3):
    """Return list of (before, after) line-block pairs.

    Change-runs that sit closer than the combined padding are merged into one
    hunk so the emitted before-texts never overlap (overlap would let one
    replacement clobber the anchor of the next when applied sequentially).
    Each before-text is padded just enough to be unique within `old`.
    """
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    sm = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False)
    changes = [(i1, i2, j1, j2) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal"]
    if not changes:
        return []
    # Merge change-runs whose old-line gap is small enough that padded context
    # would overlap.
    merged = [list(changes[0])]
    for i1, i2, j1, j2 in changes[1:]:
        if i1 - merged[-1][1] <= 2 * ctx:
            merged[-1][1] = i2
            merged[-1][3] = j2
        else:
            merged.append([i1, i2, j1, j2])
    hunks = []
    for i1, i2, j1, j2 in merged:
        for pad in range(ctx, 14):
            a, b = max(0, i1 - pad), min(len(old_lines), i2 + pad)
            c, d = max(0, j1 - pad), min(len(new_lines), j2 + pad)
            before = "".join(old_lines[a:b])
            after = "".join(new_lines[c:d])
            if old.count(before) == 1:
                hunks.append((before, after))
                break
        else:
            hunks.append((None, None))
            print(f"  !! could not isolate hunk old[{i1}:{i2}] new[{j1}:{j2}]")
    return hunks


def decode_asset(html: str):
    m = re.search(r'<script type="__bundler/manifest">(.*?)</script>', html, re.DOTALL)
    man = json.loads(m.group(1))
    uuid = next(k for k in man if k.startswith(ASSET_PREFIX))
    e = man[uuid]
    raw = base64.b64decode(e["data"])
    src = gzip.decompress(raw).decode("utf-8") if e.get("compressed") else raw.decode("utf-8")
    return man, uuid, e, src, m


def reencode(html: str, man, uuid, entry, new_src, mmatch):
    if entry.get("compressed"):
        entry["data"] = base64.b64encode(gzip.compress(new_src.encode("utf-8"))).decode("ascii")
    else:
        entry["data"] = base64.b64encode(new_src.encode("utf-8")).decode("ascii")
    new_manifest = json.dumps(man, ensure_ascii=False)
    return html[:mmatch.start(1)] + new_manifest + html[mmatch.end(1):]


def main():
    only = sys.argv[1:]
    for test, (py, var, files) in TESTS.items():
        if only and test not in only:
            continue
        cur_block = extract_block(open(py, encoding="utf-8").read(), var)
        head_block = extract_block(head_file(py), var)
        if cur_block == head_block:
            print(f"=== {test}: no BLOCK changes, skipping ===")
            continue
        hunks = compute_hunks(head_block, cur_block)
        print(f"=== {test}: {len(hunks)} hunk(s) ===")
        for fname in files:
            html = open(fname, encoding="utf-8").read()
            man, uuid, entry, src, mmatch = decode_asset(html)
            applied = skipped = failed = 0
            for before, after in hunks:
                if before is None:
                    failed += 1
                    continue
                n = src.count(before)
                if n == 1:
                    src = src.replace(before, after, 1)
                    applied += 1
                elif after.strip() and src.count(after) >= 1:
                    skipped += 1  # already applied
                else:
                    failed += 1
                    print(f"  !! {fname}: hunk before-text count={n} (expected 1); not applied")
            new_html = reencode(html, man, uuid, entry, src, mmatch)
            pathlib.Path(fname).write_text(new_html, encoding="utf-8")
            print(f"  {fname}: applied={applied} skipped={skipped} failed={failed}")


if __name__ == "__main__":
    main()

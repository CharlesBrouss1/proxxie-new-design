#!/usr/bin/env python3
"""CompareHub slotCard: when a local "déjà passé" pill is clicked, the PXC input
box stays empty (only the pill highlights), so it feels like nothing happened.
This swaps the input for a filled confirmation box when a local result is picked:
shows ✓ + test label + "ton résultat" + a "Changer" link to revert.

Local results have no PXC code (the code is created server-side only at compare
time), so we confirm the selection by name rather than faking a code.

Idempotent: skipped if marker already present. Direct-asset patch on 61feca88.
"""
import re, json, base64, gzip, glob, pathlib

ASSET_PREFIX = "61feca88"
MARKER = "· ton résultat"

ANCHOR = (
    '<input\n'
    '        value={code}\n'
    '        onChange={(e) => { setCode(e.target.value); setSlot(null); }}\n'
    '        placeholder="PXC-XXXX"\n'
    '        style={{ width: "100%", padding: "12px 14px", borderRadius: 12, '
    'border: "1.5px solid " + ((slot == null && code) ? accent : "var(--c-line)"), '
    'fontSize: 15, fontFamily: "var(--font-mono, monospace)", letterSpacing: "0.08em", '
    'textTransform: "uppercase", outline: "none", boxSizing: "border-box" }}\n'
    '      />'
)

REPLACEMENT = (
    '{slot && slot.kind === "local" ? (\n'
    '        <div style={{ width: "100%", padding: "12px 14px", borderRadius: 12, '
    'border: "1.5px solid " + accent, background: accent + "12", display: "flex", '
    'alignItems: "center", justifyContent: "space-between", gap: 10, boxSizing: "border-box" }}>\n'
    '          <span style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 15, '
    'fontWeight: 700, color: "var(--c-ink)" }}>\n'
    '            <span style={{ color: accent, fontWeight: 800 }}>✓</span>'
    '{(_HUB_LABELS[slot.slug] || slot.slug) + " · ton résultat"}\n'
    '          </span>\n'
    '          <button type="button" onClick={() => setSlot(null)} '
    'style={{ background: "transparent", border: "none", color: "var(--c-muted)", '
    'fontSize: 13, cursor: "pointer", padding: 0, textDecoration: "underline" }}>Changer</button>\n'
    '        </div>\n'
    '      ) : (\n'
    '        ' + ANCHOR + '\n'
    '      )}'
)


def decode_asset(html):
    m = re.search(r'<script type="__bundler/manifest">(.*?)</script>', html, re.DOTALL)
    man = json.loads(m.group(1))
    uuid = next(k for k in man if k.startswith(ASSET_PREFIX))
    e = man[uuid]
    raw = base64.b64decode(e["data"])
    src = gzip.decompress(raw).decode("utf-8") if e.get("compressed") else raw.decode("utf-8")
    return man, uuid, e, src, m


def reencode(html, man, uuid, entry, new_src, mmatch):
    if entry.get("compressed"):
        entry["data"] = base64.b64encode(gzip.compress(new_src.encode("utf-8"))).decode("ascii")
    else:
        entry["data"] = base64.b64encode(new_src.encode("utf-8")).decode("ascii")
    return html[:mmatch.start(1)] + json.dumps(man, ensure_ascii=False) + html[mmatch.end(1):]


def main():
    files = [f for f in glob.glob("*.html") if ("Test" in f or f.startswith("test-"))]
    for fname in sorted(files):
        html = open(fname, encoding="utf-8").read()
        man, uuid, entry, src, mmatch = decode_asset(html)
        if "const slotCard" not in src:
            print(f"  -- {fname}: no slotCard (skip)")
            continue
        if MARKER in src:
            print(f"  == {fname}: already applied (skip)")
            continue
        if src.count(ANCHOR) != 1:
            print(f"  !! {fname}: anchor count={src.count(ANCHOR)} (expected 1); NOT applied")
            continue
        src = src.replace(ANCHOR, REPLACEMENT, 1)
        new_html = reencode(html, man, uuid, entry, src, mmatch)
        pathlib.Path(fname).write_text(new_html, encoding="utf-8")
        print(f"  ++ {fname}: applied")


if __name__ == "__main__":
    main()

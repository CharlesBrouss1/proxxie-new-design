#!/usr/bin/env python3
"""Show the PXC code itself inside the "Compare avec quelqu'un" share modal
(ApiShareLinkPanel, done state). Today only the full link is shown; this adds a
prominent code card above it, with its own copy button. Applies to every test
asset that has ApiShareLinkPanel (Anxiete/PHQ9 have no peer-share panel).

Idempotent: skips a file whose insertion marker is already present.
Direct-asset patch on the 61feca88 bundle. Writes HTML in place.
"""
import re, json, base64, gzip, glob, pathlib

ASSET_PREFIX = "61feca88"

ANCHOR = '{status === "done" && (\n        <div style={{ display: "grid", gap: 16 }}>'

MARKER = "Ton code de partage"

INSERT = (
    '\n          {code && ('
    '\n            <div style={{ display: "grid", gap: 8 }}>'
    '\n              <div style={{ fontSize: 13, fontWeight: 700, color: accent }}>'
    '{isPredict ? "Ton code à transmettre" : "Ton code de partage"}</div>'
    '\n              <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>'
    '\n                <span style={{ flex: 1, minWidth: 180, padding: "11px 14px", borderRadius: 10, '
    'border: "1.5px solid " + accent + "55", background: accent + "0F", fontSize: 22, fontWeight: 800, '
    'fontFamily: "var(--font-mono, monospace)", letterSpacing: "0.12em", color: "var(--c-ink)" }}>{code}</span>'
    '\n                <button className="btn btn-ghost" onClick={() => { try { navigator.clipboard.writeText(code); } '
    'catch (e) { window.prompt("Copiez le code :", code); } }}>Copier le code</button>'
    '\n              </div>'
    '\n              <p style={{ fontSize: 12.5, color: "var(--c-muted)", margin: 0, lineHeight: 1.5 }}>'
    '{isPredict ? "L\'autre colle ce code dans « Comparer deux résultats »." '
    ': "L\'autre peut coller ce code dans « Comparer deux résultats », ou ouvrir le lien."}</p>'
    '\n            </div>'
    '\n          )}'
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
        if "const ApiShareLinkPanel" not in src:
            print(f"  -- {fname}: no ApiShareLinkPanel (skip)")
            continue
        if MARKER in src:
            print(f"  == {fname}: already applied (skip)")
            continue
        if src.count(ANCHOR) != 1:
            print(f"  !! {fname}: anchor count={src.count(ANCHOR)} (expected 1); NOT applied")
            continue
        src = src.replace(ANCHOR, ANCHOR + INSERT, 1)
        new_html = reencode(html, man, uuid, entry, src, mmatch)
        pathlib.Path(fname).write_text(new_html, encoding="utf-8")
        print(f"  ++ {fname}: applied")


if __name__ == "__main__":
    main()

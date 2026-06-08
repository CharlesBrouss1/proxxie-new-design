#!/usr/bin/env python3
"""Decode the 61feca88 bundler asset of a test HTML to a .txt file for inspection.

Usage: python3 _decode_asset.py "Proxxie Test HPI.html" [out.txt]
Read-only on the HTML; writes the decoded JS source to out.txt
(default: _decoded_<slug>.txt).
"""
import re, json, base64, gzip, sys, pathlib

ASSET_PREFIX = "61feca88"


def decode_asset(html: str) -> str:
    m = re.search(r'<script type="__bundler/manifest">(.*?)</script>', html, re.DOTALL)
    man = json.loads(m.group(1))
    uuid = next(k for k in man if k.startswith(ASSET_PREFIX))
    e = man[uuid]
    raw = base64.b64decode(e["data"])
    return gzip.decompress(raw).decode("utf-8") if e.get("compressed") else raw.decode("utf-8")


def main() -> None:
    src_file = sys.argv[1]
    html = open(src_file, encoding="utf-8").read()
    code = decode_asset(html)
    slug = re.sub(r"[^a-z0-9]+", "-", src_file.lower()).strip("-")
    out = sys.argv[2] if len(sys.argv) > 2 else f"_decoded_{slug}.txt"
    pathlib.Path(out).write_text(code, encoding="utf-8")
    print(f"{out}: {len(code)} chars")


if __name__ == "__main__":
    main()

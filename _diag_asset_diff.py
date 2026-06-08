#!/usr/bin/env python3
"""Diagnostic: decode the bundler asset from HEAD vs working tree for a test HTML,
and report which top-level component/const definitions exist in HEAD but are
missing from the working-tree (freshly rebuilt) version. Read-only."""
import re, json, base64, gzip, subprocess, sys

ASSET_PREFIX = "61feca88"

def decode_asset(html: str) -> str:
    m = re.search(r'<script type="__bundler/manifest">(.*?)</script>', html, re.DOTALL)
    manifest = json.loads(m.group(1))
    uuid = next(k for k in manifest if k.startswith(ASSET_PREFIX))
    entry = manifest[uuid]
    raw = base64.b64decode(entry["data"])
    return gzip.decompress(raw).decode("utf-8") if entry.get("compressed") else raw.decode("utf-8")

def defs(src: str):
    names = set(re.findall(r'const\s+([A-Z][A-Za-z0-9_]+)\s*=', src))
    names |= set(re.findall(r'function\s+([A-Z][A-Za-z0-9_]+)\s*\(', src))
    return names

def head_version(path: str) -> str:
    return subprocess.check_output(["git", "show", f"HEAD:{path}"], text=True)

for fname in sys.argv[1:]:
    work = open(fname, encoding="utf-8").read()
    head = head_version(fname)
    ws, hs = decode_asset(work), decode_asset(head)
    wd, hd = defs(ws), defs(hs)
    missing = sorted(hd - wd)
    print(f"=== {fname} ===")
    print(f"  asset chars: HEAD={len(hs)}  work={len(ws)}  delta={len(ws)-len(hs)}")
    print(f"  defs in HEAD not in work: {missing}")
    print(f"  SaveResultsCallout def in HEAD={'SaveResultsCallout' in hs}  work={'SaveResultsCallout' in ws}")

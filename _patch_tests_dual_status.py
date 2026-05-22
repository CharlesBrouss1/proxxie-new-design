#!/usr/bin/env python3
"""F2 (volet liste) · double statut parent/ado sur les cartes de test.

The dashboard TestsPanel showed a single status pill per test, so you couldn't
tell who had answered: the parent (who fills tests on the ado's behalf) or the
ado. This is the heart of the product model, and it was invisible.

This patches TestStatusCard in the dashboard asset to replace the single pill
with a two-line indicator · the viewer's own status and the other person's,
read from the role-scoped keys written by _patch_tests_dual_storage:
  proxxie.tests.{id}.parent  and  proxxie.tests.{id}.enfant
(parent falls back to the legacy proxxie.tests.{id} / def so the demo still
reads sensibly; the ado defaults to « à passer » until they answer, which is
exactly the nudge to invite them).

Labels are role-aware: a parent sees « Vous » + the ado's first name; the ado
sees « Toi » + « Ton parent ». A ✓ marks a passed test, « … » an in-progress one.

Idempotent · the helper is strip-and-readd between markers; the pill swap is
guarded by the PROXXIE_DUAL_STATUS marker.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
FILES = ["Proxxie Dashboard.html", "dashboard.html"]

BEGIN = "/* PROXXIE_DUAL_STATUS_BEGIN */"
END = "/* PROXXIE_DUAL_STATUS_END */"

HELPER_ANCHOR = "const TestStatusCard = ({ t, role, suggested }) => {"

HELPER = BEGIN + r"""
/* Statut par rôle · lit les clés dual-storage, avec repli legacy/def pour le
   parent et « à passer » par défaut pour l'ado. */
const _proxxieDualStatus = (t) => {
  const get = (who) => {
    try { return localStorage.getItem("proxxie.tests." + t.id + "." + who); } catch (e) { return null; }
  };
  let legacy = null;
  try { legacy = localStorage.getItem("proxxie.tests." + t.id); } catch (e) {}
  return {
    parent: get("parent") || legacy || t.def,
    enfant: get("enfant") || "todo",
  };
};

/* Mini-ligne « qui · statut » pour l'en-tête de carte. */
const ProxxieStatusMini = ({ who, status }) => {
  const m = TESTS_STATUS_MAP[status] || TESTS_STATUS_MAP.todo;
  const glyph = status === "done" ? " ✓" : status === "wip" ? " …" : "";
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 5, fontSize: 10, fontWeight: 600, color: "rgba(10,14,44,.6)", whiteSpace: "nowrap" }}>
      <span style={{ width: 7, height: 7, borderRadius: "50%", background: m.color, flexShrink: 0 }} />
      {who}<span style={{ color: m.color, fontWeight: 700 }}>{glyph}</span>
    </span>
  );
};

/* Bloc double statut · ordre = le viewer d'abord, puis l'autre personne. */
const ProxxieDualStatus = ({ t, role }) => {
  const isEnfant = role === "enfant";
  const ds = _proxxieDualStatus(t);
  const viewer = isEnfant
    ? { who: "Toi", status: ds.enfant }
    : { who: "Vous", status: ds.parent };
  const other = isEnfant
    ? { who: "Ton parent", status: ds.parent }
    : { who: FIRST_NAME, status: ds.enfant };
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 3, alignItems: "flex-end", flexShrink: 0 }}>
      <ProxxieStatusMini who={viewer.who} status={viewer.status} />
      <ProxxieStatusMini who={other.who} status={other.status} />
    </div>
  );
};

""" + END + "\n\n" + HELPER_ANCHOR

# The single pill currently rendered in the card header (exact line).
PILL_OLD = '<span style={{ fontSize: 11, fontWeight: 600, padding: "3px 9px", borderRadius: 999, background: sb.bg, color: sb.color }}>{sb.label}</span>'
PILL_NEW = '{/* PROXXIE_DUAL_STATUS */}<ProxxieDualStatus t={t} role={role} />'


def find_dash_asset(manifest):
    for uuid, entry in manifest.items():
        data = base64.b64decode(entry["data"])
        comp = entry.get("compressed", False)
        if comp:
            try: data = gzip.decompress(data)
            except Exception: continue
        try: src = data.decode("utf-8")
        except UnicodeDecodeError: continue
        if 'render(<Dashboard />)' in src:
            return uuid, src, comp
    return None, None, False


def patch_one(target: pathlib.Path) -> str:
    if not target.exists():
        return "SKIP missing"
    html = target.read_text(encoding="utf-8")
    m = re.search(r'(<script type="__bundler/manifest"[^>]*>)(.*?)(</script>)', html, re.DOTALL)
    if not m:
        return "no manifest"
    manifest = json.loads(m.group(2))
    uuid, src, comp = find_dash_asset(manifest)
    if not uuid:
        return "SKIP no dashboard asset"

    changes = []

    # 1 · helper (strip-and-readd; the readd re-attaches HELPER_ANCHOR)
    src = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n\n", "", src, flags=re.DOTALL)
    if HELPER_ANCHOR not in src:
        return "SKIP no TestStatusCard anchor"
    src = src.replace(HELPER_ANCHOR, HELPER, 1)
    changes.append("helper")

    # 2 · swap the single pill for the dual indicator
    if PILL_NEW in src:
        changes.append("pill(already)")
    elif PILL_OLD in src:
        src = src.replace(PILL_OLD, PILL_NEW, 1)
        changes.append("pill")
    else:
        return "SKIP no status pill anchor (after helper)"

    nd = src.encode("utf-8")
    if comp:
        nd = gzip.compress(nd)
    manifest[uuid]["data"] = base64.b64encode(nd).decode("ascii")
    new_manifest = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[:m.start(2)] + new_manifest + html[m.end(2):]
    target.write_text(new_html, encoding="utf-8")
    return "patched [" + ", ".join(changes) + "] (asset " + uuid[:8] + ")"


if __name__ == "__main__":
    for fn in FILES:
        print("  " + fn + ": " + patch_one(REPO / fn))

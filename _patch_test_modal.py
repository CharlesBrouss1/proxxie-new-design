#!/usr/bin/env python3
"""Dashboard · ouvrir les tests dans une modale (rester dans l'espace connecté).

Bug : cliquer « Passer le test » depuis le dashboard ouvrait la page de test
publique (Proxxie Test*.html · « 100% offert · sans inscription »), sans le shell
connecté · l'utilisateur a l'impression de sortir de son espace (et le flux de
fin renvoie vers le funnel/home).

Correctif : ProxxieTestModal intercepte les clics sur tout lien vers une page de
test (Proxxie Test*.html) et l'ouvre dans une iframe en modale · le dashboard
reste derrière, un bouton ✕ ferme et ramène à l'espace connecté.

Idempotent · composant strip-and-readd entre marqueurs ; rendu gardé par sentinelle.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
FILES = ["Proxxie Dashboard.html", "dashboard.html"]

BEGIN = "/* PROXXIE_TEST_MODAL_BEGIN */"
END = "/* PROXXIE_TEST_MODAL_END */"
CREATE_ROOT = 'ReactDOM.createRoot(document.getElementById("root")).render(<Dashboard />);'

COMPONENT = BEGIN + r"""
/* ---------------- ProxxieTestModal · tests en modale (reste connecté) ---------------- */
const ProxxieTestModal = () => {
  const [open, setOpen] = React.useState(false);
  const [src, setSrc] = React.useState("");
  const [title, setTitle] = React.useState("Test");

  React.useEffect(() => {
    const onClick = (e) => {
      const a = e.target && e.target.closest ? e.target.closest("a") : null;
      if (!a) return;
      const href = a.getAttribute("href") || "";
      // pages de test : "Proxxie Test.html", "Proxxie Test RIASEC.html", etc.
      if (/^Proxxie Test.*\.html/.test(href) || /Proxxie%20Test[^"']*\.html/.test(href)) {
        e.preventDefault();
        e.stopPropagation();
        setSrc(a.href);
        setTitle((a.textContent || "Test").replace(/→.*/, "").replace(/Passer\s*/i, "").trim().slice(0, 46) || "Test");
        setOpen(true);
      }
    };
    document.addEventListener("click", onClick, true);
    return () => document.removeEventListener("click", onClick, true);
  }, []);

  if (!open) return null;
  return (
    <div onClick={() => setOpen(false)} style={{ position: "fixed", inset: 0, background: "rgba(10,14,44,.6)", zIndex: 500, display: "grid", placeItems: "center", padding: 20 }}>
      <div onClick={(e) => e.stopPropagation()} style={{ width: "100%", maxWidth: 1000, height: "92vh", background: "white", borderRadius: 18, overflow: "hidden", display: "flex", flexDirection: "column", boxShadow: "0 24px 70px rgba(10,14,44,.4)" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 18px", borderBottom: "1px solid var(--c-line)", flexShrink: 0 }}>
          <span style={{ display: "inline-flex", alignItems: "center", gap: 9, fontWeight: 600, fontSize: 14 }}>
            <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#FD6936" }} />
            {title}
          </span>
          <button onClick={() => setOpen(false)} style={{ display: "inline-flex", alignItems: "center", gap: 6, background: "rgba(10,14,44,.05)", border: "none", borderRadius: 10, padding: "8px 14px", fontSize: 13, fontWeight: 600, cursor: "pointer", fontFamily: "inherit", color: "var(--c-ink)" }}>
            Fermer ✕
          </button>
        </div>
        <iframe title={title} src={src} style={{ flex: 1, border: "none", width: "100%" }} />
      </div>
    </div>
  );
};
""" + END + "\n\n" + CREATE_ROOT

RENDER_ANCHOR = "      <Footer />\n"
RENDER_INSERT = "      <ProxxieTestModal />\n" + RENDER_ANCHOR


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
    src = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n\n", "", src, flags=re.DOTALL)
    if CREATE_ROOT not in src:
        return "SKIP no createRoot anchor"
    src = src.replace(CREATE_ROOT, COMPONENT, 1)
    changes.append("component")

    if "<ProxxieTestModal />" not in src and RENDER_ANCHOR in src:
        src = src.replace(RENDER_ANCHOR, RENDER_INSERT, 1); changes.append("render")
    elif "<ProxxieTestModal />" in src:
        changes.append("render(already)")

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

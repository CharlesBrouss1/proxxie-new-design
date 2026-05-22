#!/usr/bin/env python3
"""P3 · vraie UX d'upload de documents sur la page Documents.

The Documents page looked rich but the upload was fake: clicking « Glissez vos
fichiers ici » or « + Ajouter un document » just opened an info drawer. No real
file handling, no list of expected documents, no accusé de réception · yet
adding documents is a core promise of the product.

This patches the Documents asset (the one rendering <DocsApp />) to add:
  · DocsUploader · a real <input type=file> + drag-and-drop zone. Dropped /
    chosen files are listed with name, size and date, persisted to
    localStorage (proxxie.docs.uploads), and each upload marks the next missing
    expected document as received + shows an « accusé de réception » banner.
  · DocsExpected · a « Documents attendus » checklist (bulletins, lettre, CV…)
    with a progress bar and a « + Ajouter » action on each missing item that
    triggers the uploader.
The hero « + Ajouter un document » button now triggers the real uploader.

Files aren't sent anywhere (static mock) · we store metadata only. Idempotent:
component block is strip-and-readd between markers; the two in-place edits are
sentinel-guarded.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
FILES = ["Proxxie Documents.html", "documents.html"]

BEGIN = "/* PROXXIE_DOCS_UPLOAD_BEGIN */"
END = "/* PROXXIE_DOCS_UPLOAD_END */"
APP_ANCHOR = "const DocsApp = () => {"

COMPONENT = BEGIN + r"""
/* ---------- Upload réel (mock · métadonnées seulement) ---------- */
const _PROXXIE_UPLOADS_KEY = "proxxie.docs.uploads";
const _proxxieGetUploads = () => {
  try { return JSON.parse(localStorage.getItem(_PROXXIE_UPLOADS_KEY) || "[]"); } catch (e) { return []; }
};
const _proxxieSaveUploads = (list) => {
  try { localStorage.setItem(_PROXXIE_UPLOADS_KEY, JSON.stringify(list)); } catch (e) {}
};
const _proxxieFmtSize = (b) => {
  if (!b && b !== 0) return "";
  if (b < 1024) return b + " o";
  if (b < 1048576) return Math.round(b / 1024) + " Ko";
  return (b / 1048576).toFixed(1) + " Mo";
};

const _PROXXIE_EXPECTED = [
  { id: "bull_t1", l: "Bulletin T1 (année en cours)", def: true  },
  { id: "bull_t2", l: "Bulletin T2 (année en cours)", def: true  },
  { id: "bull_t3", l: "Bulletin T3 (année en cours)", def: false },
  { id: "lm",      l: "Lettre de motivation Parcoursup", def: true },
  { id: "cv",      l: "CV / activités extra-scolaires",  def: true },
  { id: "maths",   l: "Dernier devoir de maths",         def: false },
];
const _proxxieDocGot = (d) => {
  try { const v = localStorage.getItem("proxxie.docs." + d.id); if (v != null) return v === "1"; } catch (e) {}
  return d.def;
};
const _proxxieMarkNextMissing = () => {
  const d = _PROXXIE_EXPECTED.find((x) => !_proxxieDocGot(x));
  if (d) { try { localStorage.setItem("proxxie.docs." + d.id, "1"); } catch (e) {} }
};

const DocsUploader = () => {
  const [uploads, setUploads] = React.useState(_proxxieGetUploads);
  const [drag, setDrag] = React.useState(false);
  const [toast, setToast] = React.useState(null);
  const inputRef = React.useRef(null);

  React.useEffect(() => {
    window.__proxxieOpenUpload = () => { if (inputRef.current) inputRef.current.click(); };
    return () => { try { delete window.__proxxieOpenUpload; } catch (e) {} };
  }, []);

  const addFiles = (fileList) => {
    const arr = Array.prototype.slice.call(fileList || []);
    if (!arr.length) return;
    const now = new Date().toLocaleDateString("fr-FR", { day: "numeric", month: "short" });
    const added = arr.map((f) => ({ n: f.name, size: f.size, date: now }));
    const next = added.concat(uploads);
    setUploads(next);
    _proxxieSaveUploads(next);
    _proxxieMarkNextMissing();
    try { window.dispatchEvent(new Event("proxxie-docs-changed")); } catch (e) {}
    setToast(added.length + " document" + (added.length > 1 ? "s" : "") + " reçu" + (added.length > 1 ? "s" : "") + " · analyse en cours");
    setTimeout(() => setToast(null), 4500);
  };

  const removeOne = (idx) => {
    const next = uploads.filter((_, i) => i !== idx);
    setUploads(next);
    _proxxieSaveUploads(next);
    try { window.dispatchEvent(new Event("proxxie-docs-changed")); } catch (e) {}
  };

  const onDrop = (e) => {
    e.preventDefault(); setDrag(false);
    if (e.dataTransfer && e.dataTransfer.files) addFiles(e.dataTransfer.files);
  };

  return (
    <div className="card" style={{ padding: 18 }}>
      <input ref={inputRef} type="file" multiple accept=".pdf,.jpg,.jpeg,.png" style={{ display: "none" }}
        onChange={(e) => { addFiles(e.target.files); e.target.value = ""; }} />

      <div
        onClick={() => inputRef.current && inputRef.current.click()}
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={onDrop}
        style={{
          padding: 22, borderRadius: 14, textAlign: "center", cursor: "pointer",
          border: "2px dashed " + (drag ? "var(--c-blue)" : "var(--c-line)"),
          background: drag ? "rgba(72,122,255,.06)" : "transparent",
          transition: "border-color .15s, background .15s",
        }}
      >
        <div style={{ width: 46, height: 46, borderRadius: 12, background: "var(--c-blue)", color: "white", display: "grid", placeItems: "center", margin: "0 auto 10px" }}>
          <Icon.upload style={{ width: 21, height: 21 }} />
        </div>
        <h4 style={{ fontSize: 16, marginBottom: 4 }}>Glissez vos fichiers ici</h4>
        <p style={{ fontSize: 12, color: "var(--c-muted)", marginBottom: 12 }}>PDF, JPG, PNG · 20 Mo max</p>
        <button className="btn btn-blue" style={{ fontSize: 12 }} onClick={(e) => { e.stopPropagation(); inputRef.current && inputRef.current.click(); }}>Parcourir mes fichiers</button>
      </div>

      {toast && (
        <div style={{ marginTop: 12, display: "flex", alignItems: "center", gap: 10, padding: "12px 14px", borderRadius: 12, background: "rgba(34,160,107,.10)", border: "1px solid rgba(34,160,107,.28)" }}>
          <div style={{ width: 26, height: 26, borderRadius: "50%", background: "#22A06B", color: "white", display: "grid", placeItems: "center", flexShrink: 0 }}>
            <Icon.check style={{ width: 13, height: 13 }} />
          </div>
          <div style={{ fontSize: 13, fontWeight: 600, color: "#1d7a52" }}>{toast}</div>
        </div>
      )}

      {uploads.length > 0 && (
        <div style={{ marginTop: 14 }}>
          <div style={{ fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--c-muted)", marginBottom: 8 }}>
            Vos ajouts ({uploads.length})
          </div>
          <div style={{ display: "grid", gap: 8 }}>
            {uploads.map((u, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, padding: "9px 12px", background: "var(--c-cream)", borderRadius: 10 }}>
                <div style={{ width: 30, height: 30, borderRadius: 7, background: "white", color: "var(--c-blue)", display: "grid", placeItems: "center", border: "1px solid var(--c-line)", flexShrink: 0 }}>
                  <Icon.doc style={{ width: 14, height: 14 }} />
                </div>
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{u.n}</div>
                  <div style={{ fontSize: 11, color: "var(--c-muted)" }}>{_proxxieFmtSize(u.size)} · {u.date} · reçu</div>
                </div>
                <span className="chip" style={{ background: "rgba(34,160,107,.12)", color: "#22A06B", fontSize: 11 }}>● Reçu</span>
                <button onClick={() => removeOne(i)} title="Retirer" style={{ background: "transparent", border: "none", color: "var(--c-muted)", cursor: "pointer", fontSize: 16, lineHeight: 1, padding: 2 }}>×</button>
              </div>
            ))}
          </div>
        </div>
      )}

      {uploads.length === 0 && !toast && (
        <div style={{ marginTop: 12, padding: "12px 14px", borderRadius: 10, background: "var(--c-cream)", textAlign: "center", fontSize: 12, color: "var(--c-muted)", lineHeight: 1.45 }}>
          Vos documents ajoutés apparaîtront ici · commencez par un bulletin récent.
        </div>
      )}
    </div>
  );
};

const DocsExpected = () => {
  const [, force] = React.useReducer((x) => x + 1, 0);
  React.useEffect(() => {
    const r = () => force();
    window.addEventListener("proxxie-docs-changed", r);
    window.addEventListener("focus", r);
    return () => { window.removeEventListener("proxxie-docs-changed", r); window.removeEventListener("focus", r); };
  }, []);
  const got = _PROXXIE_EXPECTED.filter(_proxxieDocGot).length;
  const total = _PROXXIE_EXPECTED.length;
  const pct = Math.round((got / total) * 100);
  return (
    <div className="card" style={{ padding: 22 }}>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 12 }}>
        <h4 style={{ fontSize: 15, margin: 0 }}>Documents attendus</h4>
        <span style={{ fontSize: 12, color: "var(--c-muted)", fontFamily: "var(--font-num)" }}>{got}/{total}</span>
      </div>
      <div style={{ height: 8, borderRadius: 999, background: "rgba(10,14,44,.06)", overflow: "hidden", marginBottom: 14 }}>
        <div style={{ width: pct + "%", height: "100%", background: got === total ? "#22A06B" : "linear-gradient(90deg, #FD6936, #F5EB3F)", transition: "width .4s ease" }} />
      </div>
      <div style={{ display: "grid", gap: 9 }}>
        {_PROXXIE_EXPECTED.map((d, i) => {
          const ok = _proxxieDocGot(d);
          return (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 13 }}>
              <div style={{ width: 18, height: 18, borderRadius: "50%", flexShrink: 0, display: "grid", placeItems: "center",
                background: ok ? "rgba(34,160,107,.15)" : "rgba(10,14,44,.06)", color: ok ? "#22A06B" : "var(--c-muted)" }}>
                {ok ? <Icon.check style={{ width: 11, height: 11 }} /> : <span style={{ fontSize: 11 }}>·</span>}
              </div>
              <span style={{ flex: 1, color: ok ? "var(--c-ink)" : "var(--c-muted)", textDecoration: ok ? "none" : "none" }}>{d.l}</span>
              {!ok && (
                <button onClick={() => { if (window.__proxxieOpenUpload) window.__proxxieOpenUpload(); }}
                  style={{ background: "transparent", border: "none", color: "var(--c-blue)", fontWeight: 600, fontSize: 12, cursor: "pointer", whiteSpace: "nowrap", padding: 0 }}>
                  + Ajouter
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

""" + END + "\n\n" + APP_ANCHOR

# Hero button · trigger the real uploader (unique via the data-click-key context)
HERO_OLD = (
    '          data-click-key={t.audit ? "docs-upload" : undefined}\n'
    '          onClick={() => openDrawer("docs-upload")}\n'
    "        >+ Ajouter un document</button>}"
)
HERO_NEW = (
    '          data-click-key={t.audit ? "docs-upload" : undefined}\n'
    '          onClick={() => { if (window.__proxxieOpenUpload) { window.__proxxieOpenUpload(); } else { openDrawer("docs-upload"); } }}\n'
    "        >+ Ajouter un document</button>}"
)

# Right-column fake dashed card · replace with the real uploader + expected list
DASH_OLD = '''              <div
                className="card"
                data-click-key={t.audit ? "docs-upload" : undefined}
                onClick={() => openDrawer("docs-upload")}
                style={{ padding: 24, border: "2px dashed var(--c-line)", background: "transparent", textAlign: "center", cursor: "pointer", transition: "border-color .15s, background .15s" }}
                onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--c-blue)"; e.currentTarget.style.background = "rgba(72,122,255,.04)"; }}
                onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--c-line)"; e.currentTarget.style.background = "transparent"; }}
              >
                <div style={{ width: 48, height: 48, borderRadius: 12, background: "var(--c-blue)", color: "white", display: "grid", placeItems: "center", margin: "0 auto 12px" }}>
                  <Icon.upload style={{ width: 22, height: 22 }} />
                </div>
                <h4 style={{ fontSize: 16, marginBottom: 6 }}>Glissez vos fichiers ici</h4>
                <p style={{ fontSize: 12, color: "var(--c-muted)", marginBottom: 14 }}>PDF, JPG, PNG · 20 Mo max</p>
                <button className="btn btn-blue" style={{ fontSize: 12 }}>Parcourir mes fichiers</button>
              </div>'''
DASH_NEW = "              <DocsUploader />\n              <DocsExpected />"


def find_docs_asset(manifest):
    for uuid, entry in manifest.items():
        data = base64.b64decode(entry["data"])
        comp = entry.get("compressed", False)
        if comp:
            try: data = gzip.decompress(data)
            except Exception: continue
        try: src = data.decode("utf-8")
        except UnicodeDecodeError: continue
        if "render(<DocsApp />)" in src:
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
    uuid, src, comp = find_docs_asset(manifest)
    if not uuid:
        return "SKIP no DocsApp asset"

    changes = []

    # component (strip-and-readd; readd re-attaches APP_ANCHOR)
    src = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n\n", "", src, flags=re.DOTALL)
    if APP_ANCHOR not in src:
        return "SKIP no DocsApp anchor"
    src = src.replace(APP_ANCHOR, COMPONENT, 1)
    changes.append("component")

    # hero button
    if "__proxxieOpenUpload" in src and HERO_OLD not in src and "{ if (window.__proxxieOpenUpload) { window.__proxxieOpenUpload(); } else { openDrawer" in src:
        changes.append("hero(already)")
    elif HERO_OLD in src:
        src = src.replace(HERO_OLD, HERO_NEW, 1); changes.append("hero")
    else:
        return "SKIP hero button anchor not found"

    # dashed card → uploader + expected
    if "<DocsUploader />" in src:
        changes.append("dropzone(already)")
    elif DASH_OLD in src:
        src = src.replace(DASH_OLD, DASH_NEW, 1); changes.append("dropzone")
    else:
        return "SKIP dashed-card anchor not found"

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

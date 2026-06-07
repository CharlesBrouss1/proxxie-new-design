#!/usr/bin/env python3
"""Ajoute le hub de comparaison (3e carte + écran CompareHub) à tous les tests câblés.

Modèle « hub 2 coordonnées, multi-tests » : sur l'écran « Vous prenez ce test
pour qui ? », une 3e carte « Comparer deux résultats » ouvre un écran où l'on
fournit deux coordonnées (un code PXC collé, ou un test déjà passé proposé
depuis le localStorage). Le hub appaire les deux côtés via l'API existante
(create + child) puis redirige vers test-<id>.html?code=...&role=parent, qui
affiche le ComparePanel bespoke du test. Aucun changement backend ni du pont.

Transform en place sur le bundle gzip+base64. Auto-détection : on ne touche
qu'aux fichiers déjà câblés (ApiShareLinkPanel présent) et pas encore équipés
du hub (CompareHub absent). Idempotent.

Usage:
  python3 _patch_add_compare_hub.py                 # tous les tests câblés
  python3 _patch_add_compare_hub.py test-valeurs.html  # un seul fichier
"""
import re
import json
import base64
import gzip
import pathlib
import sys

REPO = pathlib.Path(__file__).parent
ASSET_UUID_PREFIX = "61feca88"

# ---------------------------------------------------------------------------
# Bloc JS injecté · composant CompareHub (agnostique du test).
# Référence apiPost / API_BASE / readSavedProfile, tous définis avant TestApp.
# ---------------------------------------------------------------------------
COMPARE_HUB_JS = r"""
/* __proxxie_compare_hub_v1__ · hub de comparaison 2 coordonnées, multi-tests */
const _HUB_LABELS = {
  valeurs: "Valeurs", mbti: "MBTI", riasec: "RIASEC", hpi: "HPI", tdah: "TDAH",
  autisme: "Autisme", dys: "DYS", pcm: "PCM", drivers: "Drivers", besoins: "Besoins",
  brief: "BRIEF", caas: "CAAS", dweck: "Mindset", grit: "Grit", via: "VIA",
  futureproof: "Future-Proof", anxiete: "Anxiété", phq9: "PHQ-9",
};

const _hubLocalTaken = () => {
  const out = [];
  try {
    for (let i = 0; i < window.localStorage.length; i++) {
      const k = window.localStorage.key(i);
      const mm = k && k.match(/^proxxie-(.+?)-x-answers$/);
      if (!mm) continue;
      const slug = mm[1];
      let parsed;
      try { parsed = JSON.parse(window.localStorage.getItem(k)); } catch (e) { continue; }
      const a = parsed && parsed.answers;
      if (!Array.isArray(a) || !a.length) continue;
      if (a.some((x) => x == null)) continue;
      out.push({ slug, a });
    }
  } catch (e) {}
  return out;
};

const _hubResolveCode = (codeRaw) => {
  const code = (codeRaw || "").trim().toUpperCase();
  if (!code) return Promise.reject(new Error("Colle un code PXC."));
  return fetch(API_BASE + "/api/comparison/" + encodeURIComponent(code))
    .then((r) => r.json())
    .then((data) => {
      if (!data || !data.ok) throw new Error("Code introuvable : " + code);
      const tid = (data.tests && data.tests[0]) ||
        (data.parentResults && Object.keys(data.parentResults)[0]);
      const pr = data.parentResults && data.parentResults[tid];
      if (!tid || !pr || !pr.a) throw new Error("Ce code n'a pas encore de résultat.");
      return { testId: tid, a: pr.a, n: pr.n || "Quelqu'un", code };
    });
};

const CompareHub = ({ accent, onBack }) => {
  const profile = (typeof readSavedProfile === "function") ? (readSavedProfile() || {}) : {};
  const myName = profile.firstName || profile.name || profile.prenom || "Moi";
  const taken = React.useMemo(_hubLocalTaken, []);
  const [codeA, setCodeA] = React.useState("");
  const [codeB, setCodeB] = React.useState("");
  const [slotA, setSlotA] = React.useState(null);
  const [slotB, setSlotB] = React.useState(null);
  const [status, setStatus] = React.useState("idle");
  const [err, setErr] = React.useState("");

  const pickLocal = (setSlot, setCode, item) => {
    setSlot({ kind: "local", slug: item.slug, a: item.a, n: myName });
    setCode("");
  };

  const go = () => {
    setErr("");
    setStatus("loading");
    const resolve = (slot, code) =>
      (slot && slot.kind === "local")
        ? Promise.resolve({ testId: slot.slug, a: slot.a, n: slot.n })
        : _hubResolveCode(code);
    Promise.all([resolve(slotA, codeA), resolve(slotB, codeB)])
      .then(([A, B]) => {
        if (A.testId !== B.testId) {
          throw new Error("Ces deux résultats ne portent pas sur le même test.");
        }
        const T = A.testId;
        return apiPost("/api/comparison", { parentResults: { [T]: { a: A.a, n: A.n } }, tests: [T] })
          .then((c) => {
            if (!c || !c.ok || !c.code) throw new Error("Création de la comparaison impossible.");
            return apiPost("/api/comparison/" + encodeURIComponent(c.code) + "/child", {
              childResults: { [T]: { a: B.a } }, consent: true,
            }).then(() => {
              window.location.href = "./test-" + T + ".html?code=" + encodeURIComponent(c.code) + "&role=parent";
            });
          });
      })
      .catch((e) => { setErr(e.message || "Une erreur est survenue."); setStatus("idle"); });
  };

  const slotCard = (idx, title, hint, slot, setSlot, code, setCode) => (
    <div style={{ background: "white", borderRadius: 20, padding: 24, border: "1.5px solid var(--c-line)" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
        <span style={{ width: 26, height: 26, borderRadius: 99, background: accent + "22", color: accent, display: "grid", placeItems: "center", fontSize: 13, fontWeight: 700 }}>{idx}</span>
        <span style={{ fontSize: 17, fontWeight: 700 }}>{title}</span>
      </div>
      <p style={{ fontSize: 13, color: "var(--c-muted)", lineHeight: 1.5, margin: "0 0 14px 36px" }}>{hint}</p>
      <input
        value={code}
        onChange={(e) => { setCode(e.target.value); setSlot(null); }}
        placeholder="PXC-XXXX"
        style={{ width: "100%", padding: "12px 14px", borderRadius: 12, border: "1.5px solid " + ((slot == null && code) ? accent : "var(--c-line)"), fontSize: 15, fontFamily: "var(--font-mono, monospace)", letterSpacing: "0.08em", textTransform: "uppercase", outline: "none", boxSizing: "border-box" }}
      />
      {taken.length > 0 && (
        <div style={{ marginTop: 14 }}>
          <div style={{ fontSize: 12, color: "var(--c-muted)", marginBottom: 8 }}>ou un test que tu as déjà passé :</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {taken.map((t) => {
              const active = slot && slot.kind === "local" && slot.slug === t.slug;
              return (
                <button key={t.slug} type="button" onClick={() => pickLocal(setSlot, setCode, t)}
                  style={{ padding: "7px 13px", borderRadius: 99, fontSize: 13, fontWeight: 600, cursor: "pointer", border: "1.5px solid " + (active ? accent : "var(--c-line)"), background: active ? accent + "18" : "white", color: active ? accent : "var(--c-ink-2)", transition: "all .12s" }}>
                  {_HUB_LABELS[t.slug] || t.slug}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );

  const ready = ((slotA && slotA.kind === "local") || codeA.trim()) &&
                ((slotB && slotB.kind === "local") || codeB.trim());

  return (
    <section style={{ paddingTop: 80, paddingBottom: 80 }}>
      <div className="shell" style={{ maxWidth: 640 }}>
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <span className="eyebrow"><span className="dot"></span>Comparer</span>
          <h1 style={{ marginTop: 14, fontSize: 34 }}>Comparer deux résultats</h1>
          <p style={{ fontSize: 16, color: "var(--c-ink-2)", lineHeight: 1.6, maxWidth: 460, margin: "12px auto 0" }}>
            Fournis deux coordonnées qui portent sur le même test. On affiche les deux profils côte à côte.
          </p>
        </div>
        <div style={{ display: "grid", gap: 16 }}>
          {slotCard("1", "L'autre personne", "Colle le code PXC qu'on t'a envoyé.", slotA, setSlotA, codeA, setCodeA)}
          {slotCard("2", "Toi", "Choisis un test déjà passé, ou colle ton propre code.", slotB, setSlotB, codeB, setCodeB)}
        </div>
        {err && (
          <div style={{ marginTop: 18, padding: "12px 16px", borderRadius: 12, background: "#FDECEC", color: "#B23B3B", fontSize: 14, textAlign: "center" }}>{err}</div>
        )}
        <button onClick={go} disabled={!ready || status === "loading"} className="btn btn-orange btn-lg btn-arrow"
          style={{ marginTop: 24, width: "100%", justifyContent: "center", opacity: (!ready || status === "loading") ? 0.5 : 1, cursor: (!ready || status === "loading") ? "not-allowed" : "pointer" }}>
          {status === "loading" ? "Comparaison en cours…" : "Comparer les deux"}
        </button>
        <div style={{ textAlign: "center", marginTop: 18 }}>
          <button onClick={onBack} type="button" style={{ background: "none", border: "none", color: "var(--c-muted)", fontSize: 14, cursor: "pointer", textDecoration: "underline" }}>
            Retour
          </button>
        </div>
      </div>
    </section>
  );
};
"""

# 3e carte injectée dans la grille PersonaIntro (pleine largeur, style pointillé).
CARD3_JS = r"""<button onClick={() => onPick("compare_hub")} style={{
            gridColumn: "1 / -1", background: "white", borderRadius: 20, padding: 24,
            border: "1.5px dashed var(--c-line)", cursor: "pointer", textAlign: "left",
            transition: "all .15s", display: "flex", alignItems: "center", gap: 18,
          }}
            onMouseEnter={(e) => { e.currentTarget.style.borderColor = accent; e.currentTarget.style.transform = "translateY(-2px)"; e.currentTarget.style.boxShadow = "0 16px 36px -16px " + accent + "44"; }}
            onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--c-line)"; e.currentTarget.style.transform = "none"; e.currentTarget.style.boxShadow = "none"; }}
          >
            <div style={{ width: 48, height: 48, borderRadius: 12, background: accent + "22", color: accent, display: "grid", placeItems: "center", flexShrink: 0 }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M16 3h5v5"/><path d="M21 3l-7 7"/><path d="M8 21H3v-5"/><path d="M3 21l7-7"/></svg>
            </div>
            <div>
              <div style={{ fontSize: 19, fontWeight: 700, marginBottom: 4 }}>Comparer deux résultats</div>
              <p style={{ fontSize: 14, color: "var(--c-muted)", lineHeight: 1.55 }}>J'ai déjà passé des tests, ou j'ai un code PXC. Je compare deux profils côte à côte.</p>
            </div>
          </button>
          """


def _patch_src(src: str) -> str:
    # 1 · garde dans pickPersona : compare_hub ne lance pas le test.
    _hub_guard = ('if (p === "compare_hub") { setMode("compare_hub"); '
                  'window.scrollTo({ top: 0, behavior: "smooth" }); return; }')
    anchor1a = "const pickPersona = (p) => {\n    /* ANALYTICS-3b:"
    anchor1b = "const pickPersona = (p) => { setPersona(p);"
    if anchor1a in src:
        guard = ('const pickPersona = (p) => {\n'
                 '    ' + _hub_guard + '\n'
                 '    /* ANALYTICS-3b:')
        src = src.replace(anchor1a, guard, 1)
    elif anchor1b in src:
        guard = 'const pickPersona = (p) => { ' + _hub_guard + ' setPersona(p);'
        src = src.replace(anchor1b, guard, 1)
    elif "const pickPersona = (p) => {\n" in src:
        # variante générique : insère la garde comme 1re instruction du corps.
        anchor1c = "const pickPersona = (p) => {\n"
        guard = anchor1c + "    " + _hub_guard + "\n"
        src = src.replace(anchor1c, guard, 1)
    else:
        raise ValueError("anchor pickPersona introuvable")

    # 2 · 3e carte dans la grille PersonaIntro.
    anchor2 = ("Vais-je le surprendre ?\n            </p>\n"
               "          </button>\n        </div>")
    if anchor2 not in src:
        raise ValueError("anchor carte predict introuvable")
    repl2 = ("Vais-je le surprendre ?\n            </p>\n"
             "          </button>\n          " + CARD3_JS.strip() + "\n        </div>")
    src = src.replace(anchor2, repl2, 1)

    # 3 · composant CompareHub juste avant TestApp (API_BASE/apiPost en scope).
    anchor3 = "const TestApp = () => {"
    if anchor3 not in src:
        raise ValueError("anchor TestApp introuvable")
    src = src.replace(anchor3, COMPARE_HUB_JS + "\nconst TestApp = () => {", 1)

    # 4 · branche de rendu mode compare_hub. Accent récupéré du picker.
    mm = re.search(r'accent="(#[0-9A-Fa-f]{3,8})"', src)
    accent = mm.group(1) if mm else "#F5EB3F"
    anchor4 = '{mode === "test" && ('
    if anchor4 not in src:
        raise ValueError("anchor render test introuvable")
    branch = ('{mode === "compare_hub" && <CompareHub accent="' + accent +
              '" onBack={goPicker} />}\n      {mode === "test" && (')
    src = src.replace(anchor4, branch, 1)
    return src


def patch_file(path: pathlib.Path) -> str:
    html = path.read_text(encoding="utf-8")
    m = re.search(r'(<script type="__bundler/manifest">)(.*?)(</script>)', html, re.DOTALL)
    if not m:
        return f"{path.name}: pas de manifest"
    manifest = json.loads(m.group(2))
    uuid = next((k for k in manifest if k.startswith(ASSET_UUID_PREFIX)), None)
    if uuid is None:
        return f"{path.name}: asset introuvable"
    entry = manifest[uuid]
    raw = base64.b64decode(entry["data"])
    comp = entry.get("compressed", False)
    src = gzip.decompress(raw).decode("utf-8") if comp else raw.decode("utf-8")

    if "ApiShareLinkPanel" not in src:
        return f"{path.name}: non câblé, sauté"
    if "CompareHub" in src:
        return f"{path.name}: hub déjà présent, sauté"

    try:
        new_src = _patch_src(src)
    except ValueError as e:
        return f"{path.name}: ÉCHEC ({e})"
    nd = new_src.encode("utf-8")
    if comp:
        nd = gzip.compress(nd)
    entry["data"] = base64.b64encode(nd).decode("ascii")
    new_manifest = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False)
    new_html = html[: m.start(2)] + new_manifest + html[m.end(2):]
    path.write_text(new_html, encoding="utf-8")
    return f"{path.name}: hub ajouté ({len(src)} → {len(new_src)})"


def main() -> None:
    if len(sys.argv) > 1:
        targets = [REPO / a for a in sys.argv[1:]]
    else:
        targets = sorted(REPO.glob("test-*.html")) + sorted(REPO.glob("Proxxie Test *.html"))
    for p in targets:
        if not p.exists():
            print(f"  {p.name}: absent")
            continue
        print(" ", patch_file(p))


if __name__ == "__main__":
    main()

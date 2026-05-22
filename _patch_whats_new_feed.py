#!/usr/bin/env python3
"""« Depuis ta dernière visite » · returning-user feed on the dashboard.

The product must become the parent's go-to tool, which means giving them a
reason to come back. This injects a `WhatsNewFeed` React component into the
dashboard asset (the same gzip+base64 asset that holds DashHeader / Dashboard).
For a returning user it shows, near the top:

  1. Échéance · the nearest Parcoursup / orientation milestone for the ado's
     grade, with a live day countdown computed from today's real date.
  2. Coach · the next RDV (kept evergreen: now + 4 days) with a countdown.
  3. Nouveauté · a fresh resource in the hub.
  4. Rappel · the next recommended test (reuses _proxxieNextTest / TESTS_LIST).

It is gated on `localStorage["proxxie.lastVisit"]`: on a true first visit it
renders nothing (onboarding covers new users) and just records the timestamp;
on every later visit it greets with a relative time ("il y a 6 jours") and the
feed. Role-aware (tu for the ado, vous for the parent) via useProxxieRole().

All globals it relies on (FIRST_NAME, GRADE, useProxxieRole, _proxxieNextTest,
TESTS_LIST) are defined earlier in the asset, so the component is injected just
before the ReactDOM.createRoot render call and mounted right after
<ReengagementBanner /> in the Dashboard tree.

Idempotent · strip-and-readd between the BEGIN/END markers, render insertion is
skipped if already present.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
FILES = ["Proxxie Dashboard.html", "dashboard.html"]

BEGIN = "/* PROXXIE_WHATS_NEW_BEGIN */"
END = "/* PROXXIE_WHATS_NEW_END */"

RENDER_ANCHOR = "      <ReengagementBanner />\n"
RENDER_INSERT = RENDER_ANCHOR + "      <WhatsNewFeed />\n"

CREATE_ROOT = "ReactDOM.createRoot(document.getElementById(\"root\")).render(<Dashboard />);"

COMPONENT = BEGIN + r"""
/* ---------------- WhatsNewFeed · « depuis ta dernière visite » ---------------- */
/* Orientation / Parcoursup calendar, keyed by grade. Months are 0-indexed.
   Picks the soonest milestone whose date is today or later (current year). */
const _PROXXIE_CALENDAR = {
  "3ème": [
    { m: 2, d: 16, t: "Intentions d'orientation au conseil de classe", x: "Le 2e trimestre, vous indiquez les voies envisagées (générale, techno, pro)." },
    { m: 4, d: 11, t: "Choix définitifs d'orientation", x: "Saisie des vœux d'affectation au lycée avant le conseil de fin d'année." },
    { m: 5, d: 30, t: "Résultats d'affectation au lycée (Affelnet)", x: "Les affectations tombent fin juin. Préparez les inscriptions." },
  ],
  "2nde": [
    { m: 1, d: 9, t: "Choix des 3 spécialités pour la 1ère", x: "Le 2e trimestre, on affine les enseignements de spécialité à demander." },
    { m: 4, d: 25, t: "Validation des spés au conseil de classe", x: "Le conseil de classe se prononce sur les spécialités demandées." },
  ],
  "1ère": [
    { m: 2, d: 20, t: "Choix de la spé à abandonner en Terminale", x: "On garde 2 spés sur 3. Le moment de trancher en cohérence avec les vœux." },
    { m: 5, d: 15, t: "Épreuves anticipées de français", x: "Écrit + oral de français. Le rapport aide à viser les bons attendus." },
  ],
  "Terminale": [
    { m: 0, d: 21, t: "Ouverture · formulation des vœux Parcoursup", x: "Jusqu'à 10 vœux. On part du rapport pour bâtir une liste cohérente." },
    { m: 2, d: 13, t: "Date limite pour formuler les vœux", x: "Dernier jour pour ajouter des vœux sur Parcoursup." },
    { m: 3, d: 3, t: "Finalisation du dossier + confirmation des vœux", x: "Confirmez chaque vœu et complétez le projet de formation motivé." },
    { m: 5, d: 2, t: "Phase d'admission · les premières réponses arrivent", x: "Les propositions tombent. On vous aide à arbitrer sereinement." },
    { m: 6, d: 10, t: "Fin de la phase principale d'admission", x: "Pensez à la phase complémentaire si besoin d'options." },
  ],
  "Post-Bac": [
    { m: 2, d: 13, t: "Vœux Parcoursup pour une réorientation", x: "Une passerelle est possible. On cible les formations qui recrutent à bac+1." },
  ],
};
const _proxxieNextMilestone = (now) => {
  const grade = (typeof GRADE !== "undefined" && GRADE) || "Terminale";
  const list = _PROXXIE_CALENDAR[grade] || _PROXXIE_CALENDAR["Terminale"];
  const y = now.getFullYear();
  let best = null;
  for (const it of list) {
    const dt = new Date(y, it.m, it.d);
    if (dt >= new Date(now.getFullYear(), now.getMonth(), now.getDate()) && (!best || dt < best.dt)) {
      best = { dt, t: it.t, x: it.x };
    }
  }
  if (!best) {
    // tout est passé cette année · vise la prochaine étape symbolique à +2 semaines
    const dt = new Date(now.getTime() + 14 * 86400000);
    best = { dt, t: list[list.length - 1].t, x: list[list.length - 1].x };
  }
  return best;
};

const _proxxieFmtDate = (dt) => {
  const mois = ["jan", "fév", "mars", "avr", "mai", "juin", "juil", "août", "sep", "oct", "nov", "déc"];
  return dt.getDate() + " " + mois[dt.getMonth()];
};
const _proxxieDaysTo = (dt, now) => {
  const a = new Date(dt.getFullYear(), dt.getMonth(), dt.getDate());
  const b = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  return Math.round((a - b) / 86400000);
};
const _proxxieCountdownLabel = (days) => {
  if (days <= 0) return "aujourd'hui";
  if (days === 1) return "demain";
  if (days < 7) return "dans " + days + " jours";
  if (days < 31) {
    const w = Math.round(days / 7);
    return w <= 1 ? "dans 1 semaine" : "dans " + w + " semaines";
  }
  const mo = Math.round(days / 30);
  return mo <= 1 ? "dans 1 mois" : "dans " + mo + " mois";
};

/* Capture la dernière visite UNE seule fois, avant tout render React, puis
   on horodate maintenant. Deux pièges contournés :
   1. lire dans un useState initializer échoue car notre propre écriture + le
      double-mount de React.StrictMode font relire la valeur fraîche.
   2. l'asset du bundler s'exécute DEUX fois par chargement de page · une const
      de module est donc évaluée 2x et le 2e passage réécrit « maintenant »
      avant de lire. On mémorise sur window pour ne capturer/horodater qu'une
      seule fois par session de page. */
const _PROXXIE_LAST_VISIT = (() => {
  try {
    if (window.__PROXXIE_LAST_VISIT !== undefined) return window.__PROXXIE_LAST_VISIT;
    const raw = localStorage.getItem("proxxie.lastVisit");
    const v = raw ? parseInt(raw, 10) : null;
    window.__PROXXIE_LAST_VISIT = v;
    localStorage.setItem("proxxie.lastVisit", String(Date.now()));
    return v;
  } catch (e) { return null; }
})();

const WhatsNewFeed = () => {
  const role = useProxxieRole();
  const isEnfant = role === "enfant";
  const now = new Date();

  const lastVisit = _PROXXIE_LAST_VISIT;

  // Première visite · on laisse l'onboarding faire le travail.
  if (!lastVisit) return null;

  const daysSince = Math.max(0, Math.round((now.getTime() - lastVisit) / 86400000));
  const sinceLabel = daysSince === 0 ? "aujourd'hui"
    : daysSince === 1 ? "hier"
    : "il y a " + daysSince + " jours";

  // ---- Build feed items ----
  const items = [];

  // 1 · Échéance calendaire (réelle, countdown vivant)
  const ms = _proxxieNextMilestone(now);
  const msDays = _proxxieDaysTo(ms.dt, now);
  items.push({
    cat: "Échéance", color: "#FD6936", bg: "rgba(253,105,54,.10)", icon: "📅",
    title: ms.t,
    text: ms.x,
    when: _proxxieFmtDate(ms.dt) + " · " + _proxxieCountdownLabel(msDays),
    href: "Proxxie Parcours.html", action: "Voir le parcours",
  });

  // 2 · Prochain RDV coach (evergreen : maintenant + 4 jours)
  const rdv = new Date(now.getTime() + 4 * 86400000);
  const rdvDays = _proxxieDaysTo(rdv, now);
  items.push({
    cat: "Coach", color: "#1320CE", bg: "rgba(19,32,206,.08)", icon: "🎓",
    title: isEnfant ? "Ton prochain RDV avec Charles" : "Prochain RDV de votre ado avec le coach",
    text: isEnfant
      ? "Stratégie réception des vœux Parcoursup · visio de 30 min. Prépare tes questions."
      : "Stratégie réception des vœux Parcoursup · visio de 30 min. Le coach a relu le rapport.",
    when: _proxxieFmtDate(rdv) + " 14h · " + _proxxieCountdownLabel(rdvDays),
    href: "Proxxie Coach.html", action: "Préparer le RDV",
  });

  // 3 · Nouveauté contenu
  items.push({
    cat: "Nouveauté", color: "#22A06B", bg: "rgba(34,160,107,.10)", icon: "✨",
    title: isEnfant ? "Un nouveau guide est en ligne" : "Un nouveau guide pour les parents",
    text: isEnfant
      ? "« Décrypter les réponses Parcoursup » · 6 min de lecture, ajouté au centre de ressources."
      : "« Accompagner son ado pendant la phase d'admission » · à lire avant le prochain RDV.",
    when: "ajouté " + sinceLabel,
    href: "Proxxie Ressources Hub.html", action: "Lire",
  });

  // 4 · Rappel · prochain test recommandé (état réel)
  let nt = null;
  try { nt = (typeof _proxxieNextTest === "function") ? _proxxieNextTest() : null; } catch (e) {}
  if (nt) {
    items.push({
      cat: "Rappel", color: "#487AFF", bg: "rgba(72,122,255,.10)", icon: "🎯",
      title: isEnfant ? ("Il te reste à passer · " + nt.title) : ("Test à compléter · " + nt.title),
      text: isEnfant
        ? (nt.desc + " · +50 XP à la clé.")
        : (nt.desc + " Vous pouvez y répondre pour " + FIRST_NAME + ", puis l'inviter à le refaire."),
      when: "≈ 10 min",
      href: nt.href || "Proxxie Tests.html", action: isEnfant ? "Passer le test" : "Lancer le test",
    });
  }

  const heading = isEnfant ? "Depuis ta dernière visite" : "Depuis votre dernière visite";

  return (
    <section className="shell" style={{ maxWidth: 1280, margin: "0 auto 24px", padding: "0 24px" }}>
      <div style={{ background: "white", border: "1px solid var(--c-line)", borderRadius: 20, padding: "24px 26px" }}>
        <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
          <h2 style={{ fontFamily: "var(--font-display)", fontSize: 22, fontWeight: 600, letterSpacing: "-0.02em", margin: 0 }}>
            {heading}
          </h2>
          <span style={{ fontSize: 12, fontWeight: 600, color: "var(--c-muted)", fontFamily: "var(--font-num)" }}>
            dernière connexion {sinceLabel}
          </span>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {items.map((it, i) => (
            <a key={i} href={it.href} style={{
              display: "flex", alignItems: "flex-start", gap: 14, padding: "14px 0",
              textDecoration: "none", color: "inherit",
              borderTop: i === 0 ? "none" : "1px solid var(--c-line)",
            }}>
              <div style={{ width: 40, height: 40, borderRadius: 11, background: it.bg, display: "grid", placeItems: "center", fontSize: 19, flexShrink: 0 }}>
                {it.icon}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 3, flexWrap: "wrap" }}>
                  <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase", color: it.color, background: it.bg, padding: "3px 9px", borderRadius: 999 }}>
                    {it.cat}
                  </span>
                  <span style={{ fontSize: 11, color: "var(--c-muted)", fontFamily: "var(--font-num)" }}>{it.when}</span>
                </div>
                <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 2, lineHeight: 1.25 }}>{it.title}</div>
                <div style={{ fontSize: 13, color: "var(--c-muted)", lineHeight: 1.4 }}>{it.text}</div>
              </div>
              <span style={{ fontSize: 13, fontWeight: 600, color: it.color, whiteSpace: "nowrap", alignSelf: "center", flexShrink: 0 }}>
                {it.action} →
              </span>
            </a>
          ))}
        </div>
      </div>
    </section>
  );
};
""" + END + "\n\n"


def find_dash_asset(manifest):
    for uuid, entry in manifest.items():
        data = base64.b64decode(entry["data"])
        comp = entry.get("compressed", False)
        if comp:
            try: data = gzip.decompress(data)
            except Exception: continue
        try: src = data.decode("utf-8")
        except UnicodeDecodeError: continue
        if "ReactDOM.createRoot(document.getElementById(\"root\")).render(<Dashboard />)" in src:
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

    # 1 · component definition (strip-and-readd between markers)
    src = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n\n", "", src, flags=re.DOTALL)
    if CREATE_ROOT not in src:
        return "SKIP no createRoot anchor"
    src = src.replace(CREATE_ROOT, COMPONENT + CREATE_ROOT, 1)
    changes.append("component")

    # 2 · mount in render tree (idempotent)
    if "<WhatsNewFeed />" in src:
        changes.append("render(already)")
    elif RENDER_ANCHOR in src:
        src = src.replace(RENDER_ANCHOR, RENDER_INSERT, 1)
        changes.append("render")
    else:
        return "SKIP no <ReengagementBanner /> anchor"

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

#!/usr/bin/env python3
"""Dashboard · intégrer « votre prochaine étape » dans le fil, flaggée orange.

Demande : plutôt qu'un gros héros séparé, intégrer la prochaine étape dans la
carte « Depuis votre dernière visite », flaggée en orange (CTA fond orange) pour
qu'elle tire l'œil.

  · réécrit WhatsNewFeed (en place, en conservant ses helpers) pour : accepter
    onOpenProfile / onOpenInvite, calculer la prochaine étape via
    _proxxieGetOnboardingState, et la rendre en PREMIER item de la carte, sur un
    fond orange avec un bouton CTA. La carte s'affiche aussi en première visite
    (le fil temporel n'apparaît que pour les visiteurs de retour),
  · retire le rendu autonome <NextBestAction .../>,
  · passe les handlers de modale à <WhatsNewFeed .../>.

Réutilise _PROXXIE_LAST_VISIT / _proxxieNextMilestone / _proxxieDaysTo /
_proxxieFmtDate / _proxxieCountdownLabel / _proxxieNextTest /
_proxxieGetOnboardingState / FIRST_NAME / useProxxieRole.

Idempotent · remplacement de fonction par index ; rendu gardé par sentinelles.
"""
import re, json, base64, gzip, pathlib

REPO = pathlib.Path(__file__).parent
FILES = ["Proxxie Dashboard.html", "dashboard.html"]

FN_START = "const WhatsNewFeed = "
FN_END = "\n/* PROXXIE_WHATS_NEW_END */"

NEW_FN = r"""const WhatsNewFeed = ({ onOpenProfile, onOpenInvite }) => {
  const role = useProxxieRole();
  const isEnfant = role === "enfant";
  const now = new Date();
  const lastVisit = _PROXXIE_LAST_VISIT;

  /* ---- Prochaine étape (intégrée, flaggée orange) ---- */
  let st = { profile: false, firsttest: false, firstdoc: false, invited: false };
  try { st = _proxxieGetOnboardingState(); } catch (e) {}
  let rdvBooked = false;
  try { rdvBooked = localStorage.getItem("proxxie.rdv.booked") === "1"; } catch (e) {}
  /* OCEAN-X (Big Five) puis RIASEC · les deux tests en autonomie du parcours */
  const oceanDone = st.firsttest;
  let riasecDone = false;
  try { riasecDone = (localStorage.getItem("proxxie.tests.riasec." + role) || localStorage.getItem("proxxie.tests.riasec")) === "done"; } catch (e) {}
  const steps = isEnfant ? [
    { done: st.profile,  title: "Complète ton profil", cta: "Compléter mon profil", kind: "profile" },
    { done: oceanDone,  title: "Passe le test OCEAN-X (Big Five)", cta: "Passer l'OCEAN-X", href: "Proxxie Test.html" },
    { done: riasecDone, title: "Passe le test RIASEC", cta: "Passer le RIASEC", href: "Proxxie Test RIASEC.html" },
    { done: st.firstdoc, title: "Ajoute ton premier bulletin", cta: "Ajouter un document", href: "Proxxie Documents.html" },
    { done: st.invited,  title: "Invite ton parent", cta: "Inviter mon parent", kind: "invite" },
  ] : [
    { done: st.profile,  title: "Indiquez le profil de " + FIRST_NAME, cta: "Compléter le profil", kind: "profile" },
    { done: oceanDone,  title: "Passez le test OCEAN-X (Big Five) pour " + FIRST_NAME, cta: "Passer l'OCEAN-X", href: "Proxxie Test.html" },
    { done: riasecDone, title: "Passez le test RIASEC pour " + FIRST_NAME, cta: "Passer le RIASEC", href: "Proxxie Test RIASEC.html" },
    { done: st.firstdoc, title: "Ajoutez le premier bulletin de " + FIRST_NAME, cta: "Ajouter un document", href: "Proxxie Documents.html" },
    { done: st.invited,  title: "Invitez " + FIRST_NAME + " à rejoindre", cta: "Inviter " + FIRST_NAME, kind: "invite" },
    { done: rdvBooked,   title: "Réservez le premier RDV avec le coach", cta: "Prendre RDV", href: "https://calendly.com/proxxie/cadrage" },
  ];
  const total = steps.length;
  const doneCount = steps.filter((s) => s.done).length;
  const curIdx = steps.findIndex((s) => !s.done);
  const allDone = curIdx === -1;
  const step = allDone
    ? { title: isEnfant ? "Tout est en place · continue sur ta lancée" : "Tout est en place · gardez le rapport à jour", cta: isEnfant ? "Voir mes documents" : "Voir les documents", href: "Proxxie Documents.html" }
    : steps[curIdx];
  const stepNo = allDone ? total : curIdx + 1;
  const accent = allDone ? "#22A06B" : "#FD6936";

  const ctaStyle = { display: "inline-flex", alignItems: "center", gap: 8, padding: "12px 22px", borderRadius: 11, background: accent, color: "white", fontWeight: 700, fontSize: 14, fontFamily: "inherit", border: "none", cursor: "pointer", textDecoration: "none", whiteSpace: "nowrap", boxShadow: "0 6px 16px " + (allDone ? "rgba(34,160,107,.26)" : "rgba(253,105,54,.28)") };
  const ctaLabel = step.cta + " →";
  const stepCta = step.kind === "profile"
    ? <button onClick={onOpenProfile} style={ctaStyle}>{ctaLabel}</button>
    : step.kind === "invite"
    ? <button onClick={() => { try { localStorage.setItem("proxxie.onboarding.invited", "1"); } catch (e) {} if (onOpenInvite) onOpenInvite(); }} style={ctaStyle}>{ctaLabel}</button>
    : (step.href && step.href.indexOf("http") === 0
        ? <a href={step.href} target="_blank" rel="noopener noreferrer" style={ctaStyle}>{ctaLabel}</a>
        : <a href={step.href} style={ctaStyle}>{ctaLabel}</a>);

  /* ---- Article de la semaine · choisi selon la classe de l'ado ---- */
  let grade = "Terminale";
  try { grade = (typeof GRADE !== "undefined" && GRADE) || localStorage.getItem("proxxie_grade") || "Terminale"; } catch (e) {}
  const _ARTICLES = {
    "3ème": "Bien choisir son lycée et ses options",
    "2nde": "Choisir ses 3 spécialités de 1ère sans se tromper",
    "1ère": "Quelles spécialités garder en Terminale ?",
    "Terminale": "Phase d'admission Parcoursup · décrypter les réponses",
    "Post-Bac": "Réorientation · les passerelles après une 1re année",
  };
  const article = _ARTICLES[grade] || _ARTICLES["Terminale"];

  /* ---- Items du fil ---- */
  const items = [];
  if (lastVisit) {
    const ms = _proxxieNextMilestone(now);
    const msDays = _proxxieDaysTo(ms.dt, now);
    items.push({ cat: "Échéance", color: "#FD6936", bg: "rgba(253,105,54,.10)", icon: "📅", title: ms.t, text: ms.x, when: _proxxieFmtDate(ms.dt) + " · " + _proxxieCountdownLabel(msDays), href: "Proxxie Parcours.html", action: "Voir le parcours" });
  }
  /* Article de la semaine · adapté à la classe */
  items.push({ cat: "Article de la semaine", color: "#22A06B", bg: "rgba(34,160,107,.10)", icon: "📰", title: article, text: isEnfant ? "Sélectionné pour ta classe (" + grade + ") · guide de l'orientation." : "Sélectionné pour la classe de " + FIRST_NAME + " (" + grade + ") · guide de l'orientation.", when: "cette semaine", href: "guide-orientation.html", action: "Lire l'article" });
  /* Push upload de documents */
  items.push({ cat: "Documents", color: "#487AFF", bg: "rgba(72,122,255,.10)", icon: "📄", title: isEnfant ? "Ajoute tes bulletins" : "Ajoutez les bulletins de " + FIRST_NAME, text: isEnfant ? "Plus on a de données, plus ton rapport est précis. Glisse-les en 30 sec." : "Plus on a de données, plus le rapport est précis. Glissez-les en 30 sec.", when: "recommandé", href: "Proxxie Documents.html", action: "Ajouter un document" });

  const daysSince = lastVisit ? Math.max(0, Math.round((now.getTime() - lastVisit) / 86400000)) : 0;
  const sinceLabel = daysSince === 0 ? "aujourd'hui" : daysSince === 1 ? "hier" : "il y a " + daysSince + " jours";
  const heading = lastVisit ? (isEnfant ? "Depuis ta dernière visite" : "Depuis votre dernière visite") : "Pour bien démarrer";

  return (
    <section className="shell" style={{ maxWidth: 1280, margin: "0 auto 24px", padding: "0 24px" }}>
      <div style={{ background: "white", border: "1px solid var(--c-line)", borderRadius: 20, padding: "24px 26px" }}>
        <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
          <h2 style={{ fontFamily: "var(--font-display)", fontSize: 22, fontWeight: 600, letterSpacing: "-0.02em", margin: 0 }}>{heading}</h2>
          {lastVisit && <span style={{ fontSize: 12, fontWeight: 600, color: "var(--c-muted)", fontFamily: "var(--font-num)" }}>dernière connexion {sinceLabel}</span>}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 16, padding: "16px 18px", borderRadius: 14, background: allDone ? "rgba(34,160,107,.08)" : "rgba(253,105,54,.08)", border: "1px solid " + (allDone ? "rgba(34,160,107,.25)" : "rgba(253,105,54,.30)"), marginBottom: items.length ? 14 : 0, flexWrap: "wrap" }}>
          <div style={{ flex: 1, minWidth: 240 }}>
            <span style={{ display: "inline-flex", alignItems: "center", gap: 8, fontSize: 10, fontWeight: 700, letterSpacing: "0.06em", textTransform: "uppercase", color: accent }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: accent }} />
              {isEnfant ? "Ta prochaine étape" : "Votre prochaine étape"}{allDone ? "" : " · Étape " + stepNo + "/" + total}
            </span>
            <div style={{ fontSize: 16, fontWeight: 600, margin: "5px 0 7px", lineHeight: 1.25 }}>{step.title}</div>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              {steps.map((s, i) => (
                <span key={i} style={{ width: i === curIdx ? 22 : 8, height: 8, borderRadius: 999, background: s.done ? "#22A06B" : (i === curIdx ? accent : "rgba(10,14,44,.12)") }} />
              ))}
              <span style={{ fontSize: 11, color: "var(--c-muted)", marginLeft: 5, fontFamily: "var(--font-num)" }}>{doneCount}/{total} fait</span>
            </div>
          </div>
          {stepCta}
        </div>

        {items.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
            {items.map((it, i) => (
              <a key={i} href={it.href} style={{ display: "flex", alignItems: "flex-start", gap: 14, padding: "14px 0", textDecoration: "none", color: "inherit", borderTop: "1px solid var(--c-line)" }}>
                <div style={{ width: 40, height: 40, borderRadius: 11, background: it.bg, display: "grid", placeItems: "center", fontSize: 19, flexShrink: 0 }}>{it.icon}</div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 3, flexWrap: "wrap" }}>
                    <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase", color: it.color, background: it.bg, padding: "3px 9px", borderRadius: 999 }}>{it.cat}</span>
                    <span style={{ fontSize: 11, color: "var(--c-muted)", fontFamily: "var(--font-num)" }}>{it.when}</span>
                  </div>
                  <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 2, lineHeight: 1.25 }}>{it.title}</div>
                  <div style={{ fontSize: 13, color: "var(--c-muted)", lineHeight: 1.4 }}>{it.text}</div>
                </div>
                <span style={{ fontSize: 13, fontWeight: 600, color: it.color, whiteSpace: "nowrap", alignSelf: "center", flexShrink: 0 }}>{it.action} →</span>
              </a>
            ))}
          </div>
        )}
      </div>
    </section>
  );
};"""

DROP_HERO = "      <NextBestAction onOpenProfile={() => setProfileOpen(true)} onOpenInvite={() => setInviteOpen(true)} />\n"
FEED_OLD = "      <WhatsNewFeed />\n"
FEED_NEW = "      <WhatsNewFeed onOpenProfile={() => setProfileOpen(true)} onOpenInvite={() => setInviteOpen(true)} />\n"


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

    # 1 · replace WhatsNewFeed function in place (keep helpers + END marker)
    fs = src.find(FN_START)
    fe = src.find(FN_END, fs)
    if fs == -1 or fe == -1:
        return "SKIP WhatsNewFeed not found"
    src = src[:fs] + NEW_FN + src[fe:]
    changes.append("feed-rewritten")

    # 2 · remove standalone hero
    if DROP_HERO in src:
        src = src.replace(DROP_HERO, "", 1); changes.append("-hero")

    # 3 · pass handlers to WhatsNewFeed
    if FEED_OLD in src:
        src = src.replace(FEED_OLD, FEED_NEW, 1); changes.append("feed+props")
    elif FEED_NEW in src:
        changes.append("feed+props(already)")

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

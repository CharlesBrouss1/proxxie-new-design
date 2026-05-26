/* ─── QuickExample : exemple de rapport Proxxie complet (Léa, Terminale) ─── */
/* Rédigé dans le ton et la profondeur du rapport-modèle Benjamin Lindeboom.
   12 sections, narratif coach + voix de l'élève, arbitrages explicites,
   échanges avec le coach mis en avant. Aucune dépendance externe (inline
   SVG, inline styles, CSS variables globales uniquement).                 */
const QuickExample = ({ open, onClose, onPersonalize }) => {
  if (!open) return null;

  const BLUE = "#1320CE";
  const ORANGE = "#FD6936";
  const GREEN = "#22A06B";

  const oceanX = [
    { dim: "Ouverture d'esprit", score: 102, max: 120, color: BLUE,
      detail: "Curiosité intellectuelle forte, goût pour les idées et la création. Léa aime apprendre, débattre, explorer des domaines variés. Score le plus haut du profil." },
    { dim: "Conscience", score: 88, max: 120, color: BLUE,
      detail: "Organisée, persévérante. Tendance au perfectionnisme, atout pour les études exigeantes. Le revers : Léa peut se mettre une pression excessive et procrastiner par peur de mal faire." },
    { dim: "Extraversion", score: 64, max: 120, color: BLUE,
      detail: "Équilibre intro/extra. À l'aise en petit groupe, plus réservée en grand collectif. Préfère écouter avant de prendre la parole, mais s'engage clairement une fois en confiance." },
    { dim: "Convivialité", score: 81, max: 120, color: BLUE,
      detail: "Coopérative, empathique. Bonne lectrice des émotions des autres. Évite la confrontation, peut négliger ses propres besoins pour préserver le groupe." },
    { dim: "Stabilité émotionnelle", score: 58, max: 120, color: BLUE,
      detail: "Sensibilité émotionnelle marquée. Léa ressent fortement, ce qui nourrit sa créativité, mais la rend plus vulnérable au stress en période d'examen." },
  ];

  const valeurs = [
    { n: "Sens", d: "Avoir un impact concret, ne pas faire que par obligation." },
    { n: "Apprentissage", d: "Comprendre comment fonctionnent les choses, monter en compétence en continu." },
    { n: "Autonomie", d: "Pouvoir organiser son travail et ses décisions sans micro-management." },
    { n: "Honnêteté", d: "Intégrité dans les relations, transparence des intentions." },
    { n: "Beauté", d: "Sensibilité esthétique forte, attirée par les objets et idées bien conçus." },
  ];

  const besoins = [
    { n: "Sécurité", d: "Cadre clair, échéances visibles, environnement bienveillant." },
    { n: "Relations", d: "Lien fort avec famille proche et amis ; petit cercle plutôt que foule." },
    { n: "Reconnaissance", d: "Besoin que ses efforts soient vus et nommés, pas forcément applaudis." },
    { n: "Création", d: "Avoir des temps où elle construit quelque chose de tangible." },
    { n: "Liberté", d: "Espaces où elle décide elle-même, partiellement satisfait aujourd'hui." },
  ];

  const competencesForts = [
    "Analyse · capable de décomposer un problème, identifier les variables, prioriser.",
    "Sens du détail · repère vite les incohérences dans un raisonnement ou un visuel.",
    "Écoute · pose des questions précises avant de répondre, n'interrompt pas.",
    "Créativité appliquée · aime mêler science et design (UX, bio-éthique, design produit).",
    "Travail autonome · n'a pas besoin d'un cadre rigide pour avancer si l'objectif est clair.",
  ];

  const competencesAxes = [
    "Prise de parole · gagne à oser exprimer ses opinions plus tôt en réunion ou en cours.",
    "Gestion du stress · épisodes d'anxiété en période de contrôle, à canaliser via routine de préparation.",
    "Demande d'aide · tendance à vouloir tout résoudre seule, à apprendre à solliciter les pairs et profs.",
    "Anglais oral · niveau écrit solide (B2), oral à renforcer pour les cursus internationaux.",
  ];

  const interets = [
    { n: "Sciences du vivant", d: "Bio, génétique, neurosciences. A lu Sapiens et regarde régulièrement des contenus de vulgarisation." },
    { n: "Design & UX", d: "Sensibilité graphique forte, fait du lettering, suit des designers sur Instagram." },
    { n: "Sport individuel", d: "Course à pied (10km), escalade en salle, escalade extérieure découverte en 2025." },
    { n: "Lecture", d: "Romans contemporains (Despentes, Adichie), 1 à 2 livres par mois." },
    { n: "Engagement", d: "Bénévole dans une asso d'aide aux devoirs, sensible aux enjeux climat." },
  ];

  const phases = [
    {
      date: "Septembre 2025 — Premier contact",
      title: "« Je ne sais vraiment pas ce que je veux faire »",
      body: "Léa arrive avec deux parents inquiets et une moyenne solide (15/20) mais aucune direction claire. Trois pistes en vrac : médecine (parce que les profs lui ont dit qu'elle « pouvait »), école d'ingénieur (parce qu'elle aime les maths), Sciences-Po (parce qu'elle aime débattre). Aucune n'est nourrie par un projet. Marion observe une jeune fille polie, structurée, mais bridée par la peur de mal choisir. Première décision : on respire, on commence par mieux se connaître avant de regarder les écoles.",
      coach: "Marion · « Le piège classique : choisir une voie pour les bonnes raisons des autres. On va d'abord donner à Léa son propre langage avant de regarder les options. »",
    },
    {
      date: "Octobre 2025 — Tests et connaissance de soi",
      title: "Le miroir OCEAN-X + RIASEC",
      body: "OCEAN-X complété à la maison, RIASEC en séance. Léa découvre son profil Investigateur/Artistique dominant. Surprise : elle ne se voyait pas du tout « créative », elle pensait l'être uniquement en cours d'arts pla. Marion remet le mot à sa place : créativité = créer des solutions originales, pas seulement dessiner. Léa relit ses bulletins avec ce filtre et comprend pourquoi elle s'ennuyait en HGGSP malgré de bonnes notes. Sa mère, présente au debrief, dit textuellement : « C'est exactement elle, on n'avait jamais réussi à le formuler. »",
      coach: "Marion · « Le test ne décide rien, il donne du vocabulaire. Et là pour la première fois Léa peut nommer ce qui la met en mouvement. »",
    },
    {
      date: "Novembre — Décembre 2025 — Exploration sectorielle",
      title: "On élargit avant de resserrer",
      body: "Trois ateliers d'exploration sur la plateforme : secteurs porteurs, métiers méconnus, métiers du futur. Léa identifie cinq familles qui résonnent : santé/recherche, ingénierie biomédicale, design produit, conseil stratégie, métiers du climat. Marion l'invite à interviewer trois pros (une chercheuse en bio, un designer chez Doctolib, une ingénieure aérospatiale ex-Centrale). Léa revient transformée de l'entretien avec la chercheuse : « Je n'avais pas réalisé qu'on pouvait être en blouse ET inventer des trucs. »",
      coach: "Marion · « Le passage à l'acte change tout. Trois cafés réels valent dix vidéos YouTube. »",
    },
    {
      date: "Janvier — Février 2026 — Construction Parcoursup",
      title: "L'arbitrage : médecine, ingé bio, ou double cursus ?",
      body: "Léa est tentée par la médecine après son interview chercheuse, mais hésite : 10 ans d'études et un format PASS qu'elle redoute. Marion l'aide à modéliser les trois scénarios (médecine, ingé bio, Sciences-Po + master spécialisé). Léa tranche pour l'ingénierie biomédicale : même intérêt scientifique, format école qu'elle vit mieux, débouchés concrets. Construction des 10 vœux Parcoursup avec stratégie en triple filet : ambitieux (Polytechnique, Centrale Lyon biomed), cohérents (INSA, Polytech), filet de sécurité (université Paris-Saclay).",
      coach: "Marion · « On a posé chaque scénario sur la table avec les pour, les contre, et surtout le rythme de vie au quotidien. Léa a tranché elle-même. Mon rôle s'arrête là. »",
    },
    {
      date: "Mars — Avril 2026 — Lettres et finalisation",
      title: "Écriture des lettres et préparation aux oraux",
      body: "Six lettres de motivation rédigées, chacune relue par Marion avec annotations Loom (vidéo). Léa apprend à structurer en entonnoir : son histoire personnelle → la formation → la projection. Préparation aux oraux INSA et Polytech : trois simulations enregistrées, écoute critique entre Léa et Marion. Le père de Léa, présent à un point d'étape, dit : « J'ai vu ma fille devenir adulte sur ce sujet. » Dossier déposé le 28 mars.",
      coach: "Marion · « Le geste d'écrire ses motivations clarifie le projet autant qu'il le présente. C'est l'étape qui fait grandir le plus. »",
    },
    {
      date: "Mai 2026 — Réception des vœux et suite",
      title: "Stratégie d'acceptation et projection",
      body: "Trois admissions confirmées au 25 mai : Polytech Lyon Bio, INSA Lyon Bioingénierie, université Paris-Saclay (sécurité). Marion et Léa rebriefent les trois pour décider en conscience : confort de vie, projet pédagogique, opportunité d'alternance en M1. Léa choisit Polytech Lyon. Suivi prévu jusqu'à la rentrée pour gérer logement et inscription administrative, puis check-in semestriel pendant les deux premières années.",
      coach: "Marion · « L'orientation ne s'arrête pas à Parcoursup. On reste en lien pour la transition, et au cas où elle veut bifurquer en cours de route. »",
    },
  ];

  const voies = [
    {
      voie: "Médecine (PASS / LAS)",
      verdict: "Écartée",
      verdictColor: "#B72C4A",
      pour: "Intérêt vrai pour le vivant, vocation à aider, profil scolaire compatible (15/20).",
      contre: "10 ans d'études, format PASS très compétitif et anxiogène, perte de la dimension création/design qui nourrit Léa.",
      decision: "Léa choisit de ne pas sacrifier 10 ans à un format qui ne lui correspond pas alors que l'ingénierie biomédicale offre les mêmes débouchés santé en 5 ans.",
    },
    {
      voie: "Sciences-Po + master spécialisé santé/climat",
      verdict: "Écartée",
      verdictColor: "#B72C4A",
      pour: "Léa adore débattre, profil analytique, intérêt pour les politiques publiques (climat, santé).",
      contre: "Trop loin des sciences dures qui la nourrissent. Risque de regret en milieu de cursus.",
      decision: "Sciences-Po reste une option pour un éventuel master complémentaire après l'école d'ingénieur, mais pas comme voie principale.",
    },
    {
      voie: "École d'ingénieur biomédicale (prépa intégrée)",
      verdict: "Choix principal",
      verdictColor: GREEN,
      pour: "Croisement sciences + impact santé, format école rassurant et structuré, 5 ans, alternance possible en M1, débouchés concrets (R&D, dispositifs médicaux, e-santé).",
      contre: "Sélectivité élevée sur les écoles cibles (Polytech Lyon, INSA, Centrale).",
      decision: "Voie principale. Stratégie de candidature : 3 écoles ambitieuses, 4 cohérentes, 3 filets.",
    },
    {
      voie: "Université Paris-Saclay (Licence Bio-info)",
      verdict: "Filet de sécurité",
      verdictColor: "#7A6C2F",
      pour: "Très grand acteur de la recherche biomed en France. Passerelle possible vers Magistère ou Master sélectif.",
      contre: "Format universitaire plus autonome, demande d'auto-discipline qui n'est pas le point fort de Léa en première année.",
      decision: "Maintenu en filet ultime. Si admission Polytech ou INSA confirmée, vœu activé puis renoncé.",
    },
  ];

  const secteurs = [
    { n: "Ingénierie biomédicale", stars: 5, fit: "Très forte", note: "Croisement sciences dures + impact santé. Marché en forte croissance (e-santé, dispositifs médicaux, IA médicale)." },
    { n: "Recherche en sciences du vivant", stars: 4, fit: "Forte", note: "Bio, génétique, neurosciences. Voie longue (doctorat) mais cohérente avec l'intérêt fondamental." },
    { n: "Design produit & UX", stars: 4, fit: "Forte", note: "Sensibilité esthétique réelle. Pourrait croiser avec santé en UX médicale ou design de dispositifs." },
    { n: "Conseil stratégie (santé, climat)", stars: 3, fit: "Moyenne-forte", note: "Compatible avec profil analytique, mais perd la dimension création. Plutôt après école d'ingé." },
    { n: "Métiers du climat & énergie", stars: 3, fit: "Moyenne-forte", note: "Sensibilité climat vraie. À explorer comme spécialisation post-ingé (ingénierie environnementale)." },
    { n: "Politique & affaires publiques", stars: 2, fit: "Moyenne", note: "Léa aime débattre mais ne se projette pas dans un parcours pur Sciences-Po. Option master complémentaire." },
  ];

  const metiers = [
    { n: "Ingénieure biomédicale R&D", m: 94, s: "42-60 k€", t: "+22% emplois", d: "Conception de dispositifs médicaux (prothèses, imagerie, monitoring). Postes en startup e-santé, en hôpital, ou en industrie (Medtronic, Philips Healthcare, Stryker)." },
    { n: "Architecte UX en santé", m: 91, s: "38-55 k€", t: "+18% emplois", d: "Conception des interfaces des dispositifs médicaux ou plateformes patient. Croisement design + médical. Doctolib, Alan, Lifen recrutent." },
    { n: "Chercheuse en données de santé", m: 86, s: "45-70 k€", t: "+31% emplois", d: "Analyse de cohortes patients, IA médicale, recherche clinique computationnelle. Inserm, Owkin, hôpitaux universitaires." },
    { n: "Designer produit", m: 88, s: "36-52 k€", t: "+14% emplois", d: "Conception produit grand public ou B2B. Postes en agences ou en interne (Decathlon, Withings, Salomon)." },
    { n: "Manager innovation santé", m: 79, s: "55-85 k€", t: "+12% emplois", d: "Pilotage de projets d'innovation en clinique, lab, ou industrie. Plutôt à 3-5 ans d'expérience." },
    { n: "Consultante stratégie biotech", m: 74, s: "48-90 k€", t: "+11% emplois", d: "Conseil aux laboratoires et startups bio. Compatible avec profil analytique, à viser post-école d'ingé + master." },
  ];

  const formations = [
    { n: "Polytech Lyon — Biomédical", v: "5 ans · prépa intégrée · Lyon", m: 91, d: "Cycle ingénieur en 5 ans, spécialisation biomédicale en cycle ingé. Alternance possible en M1-M2. Réseau Polytech (15 écoles). Candidature : dossier + entretien." },
    { n: "INSA Lyon — Bioingénierie", v: "5 ans · prépa intégrée · Lyon", m: 89, d: "Cycle Préparatoire Intégré (2 ans) puis Bioingénierie & Nanobiotechnologies. Recherche forte, parcours international possible." },
    { n: "Centrale Lyon — Biomed", v: "5 ans · post-bac concours · Lyon", m: 86, d: "Voie sélective via concours post-bac. Tronc commun puis spécialisation biomed en 4ème année. Très grosse école, opportunités internationales." },
    { n: "Université Paris-Saclay — Licence Bio-info", v: "3 ans · licence · Orsay", m: 84, d: "Licence sélective Bio-informatique. Forte intensité recherche. Passerelle vers masters spécialisés ou écoles d'ingé par admission parallèle." },
    { n: "INSA Rouen — Maîtrise des Risques Industriels", v: "5 ans · prépa intégrée · Rouen", m: 78, d: "Filet géographique. Spécialisation moins ciblée santé mais bonne école, peut basculer en biomed via mobilité interne INSA." },
  ];

  const vigilance = [
    { t: "Anxiété pré-examen", d: "Léa décompense parfois sur les semaines de contrôle (sommeil dégradé, perte d'appétit). Routine de préparation à installer dès le bac (sport régulier, sommeil cadré, exposition graduée aux conditions d'examen)." },
    { t: "Perfectionnisme paralysant", d: "Conscience à 88/120 + sensibilité émotionnelle : tendance à repousser une tâche jusqu'à pouvoir la faire « parfaitement ». Travailler sur le « bon assez tôt vaut mieux que parfait jamais »." },
    { t: "Pression parentale implicite", d: "Parents bienveillants mais valorisent fortement la réussite scolaire. Léa peut s'auto-censurer pour ne pas décevoir. Marion a déjà tenu un point parental sur ce sujet, à refaire si besoin en S1." },
    { t: "Anglais oral", d: "Écrit B2 solide, oral plus hésitant. À renforcer pour les modules internationaux Polytech et INSA, et pour les stages possibles à l'étranger en M1-M2." },
  ];

  const leviers = [
    { t: "Profil analytique + créatif", d: "Combinaison rare et précieuse pour l'ingénierie biomed. Atout différenciant pour décrocher des stages chez les acteurs e-santé." },
    { t: "Maturité de réflexion", d: "Léa pèse, modélise, arbitre. Sa décision médecine/ingé a été prise à l'issue d'un raisonnement structuré qu'elle peut réutiliser pour les choix M1, stages, mobilités." },
    { t: "Sport régulier", d: "10km hebdo + escalade : régulateur émotionnel et discipline transférable. À maintenir pendant les premières années post-bac (souvent abandonné, à grand tort)." },
    { t: "Soutien parental engagé", d: "Parents présents aux points d'étape, ouverts à l'arbitrage de Léa. Excellent contexte pour la transition vers l'autonomie de l'enseignement sup." },
    { t: "Réseau Proxxie", d: "Trois pros interviewés pendant le parcours (chercheuse bio, designer Doctolib, ingé aérospatiale) restent joignables pour suivi de carrière. Première brique d'un réseau personnel." },
  ];

  const echangesStats = [
    { label: "Séances visio en 1·1", value: "12" },
    { label: "Messages WhatsApp coach", value: "47" },
    { label: "Documents annotés", value: "9" },
    { label: "Points parentaux", value: "3" },
    { label: "Interviews pros facilités", value: "3" },
  ];

  const citationsLea = [
    "« Au début je pensais que je devais choisir entre être scientifique ET être créative. Marion m'a montré que c'est exactement le contraire qui se passe en ingénierie biomed. »",
    "« Le truc qui a changé, c'est l'interview avec la chercheuse. J'ai vu une vraie personne qui aime son métier, plus une fiche ONISEP. »",
    "« J'avais tellement peur de me tromper que je n'osais rien choisir. Maintenant je sais que même si je bifurque dans deux ans, ce ne sera pas perdu. »",
    "« Mes parents me poussaient médecine. Le rapport leur a donné les arguments pour comprendre mon choix d'ingé bio. »",
  ];

  const prochainesCT = [
    "Bac : focus 100% révisions jusqu'au 24 juin, pas de nouvelle activité d'orientation.",
    "Confirmer le vœu Polytech Lyon sur Parcoursup dès réception (déjà 3 admissions sécurisées).",
    "Inscription administrative + logement Lyon (Marion partage check-list).",
    "Renforcer l'anglais oral : 15 min/jour en juillet (podcast + journal vocal).",
  ];
  const prochainesMT = [
    "Premier semestre Polytech : poser un rituel de travail hebdo (organisation = point d'attention).",
    "Reprendre contact avec la chercheuse bio interviewée pour un café à Lyon en novembre.",
    "Identifier 2 assos étudiantes (1 sportive, 1 engagée santé/climat).",
    "Point d'étape Marion mi-décembre : bilan S1, ajustements méthode.",
  ];
  const prochainesLT = [
    "Cycle ingénieur Polytech : cap sur la spé biomed en 4ème année.",
    "Viser une alternance en M1 chez un acteur e-santé (Doctolib, Withings, Alan).",
    "Explorer un semestre international en M2 (Canada, Allemagne — pôles biomed reconnus).",
    "Garder la porte du master Sciences-Po santé ouverte si l'intérêt politique se confirme.",
  ];

  // Petites helpers visuelles inline
  const sectionTitle = (eyebrow, big, sub) => (
    <div style={{ marginTop: 18, marginBottom: 14 }}>
      <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: BLUE, display: "flex", alignItems: "center", gap: 6 }}>
        <span style={{ width: 6, height: 6, background: ORANGE, borderRadius: "50%" }} /> {eyebrow}
      </div>
      <div style={{ fontFamily: "var(--font-display)", fontSize: 22, fontWeight: 600, letterSpacing: "-0.02em", marginTop: 6, color: "var(--c-ink)" }}>{big}</div>
      {sub ? <div style={{ fontSize: 14, color: "var(--c-ink-2)", marginTop: 6, lineHeight: 1.5 }}>{sub}</div> : null}
    </div>
  );

  const card = (children, extra) => (
    <div style={{ background: "white", border: "1px solid rgba(10,14,44,.08)", borderRadius: 18, padding: "22px 26px", marginBottom: 14, boxShadow: "0 8px 24px -14px rgba(10,14,44,.08)", ...(extra || {}) }}>
      {children}
    </div>
  );

  const stars = (n) => (
    <span style={{ color: ORANGE, letterSpacing: 1 }}>{"★".repeat(n)}<span style={{ color: "rgba(10,14,44,.18)" }}>{"★".repeat(5 - n)}</span></span>
  );

  return (
    <div
      style={{
        position: "fixed", inset: 0, zIndex: 110,
        background: "rgba(10,14,44,.55)",
        backdropFilter: "blur(8px)",
        display: "flex", alignItems: "stretch",
        animation: "fadeIn .25s ease",
      }}
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          margin: "auto",
          width: "min(960px, 95vw)",
          maxHeight: "94vh",
          background: "var(--c-cream-light, #FBF8F1)",
          borderRadius: 28,
          overflow: "hidden",
          boxShadow: "0 50px 100px -30px rgba(10,14,44,.6)",
          display: "flex", flexDirection: "column",
          animation: "slideIn .35s cubic-bezier(.2,.8,.2,1)",
        }}
      >
        {/* ── Header ── */}
        <div
          style={{
            padding: "22px 36px",
            background: "linear-gradient(180deg, white 0%, var(--c-cream-light) 100%)",
            borderBottom: "1px solid rgba(10,14,44,.06)",
            display: "flex", alignItems: "center", justifyContent: "space-between",
            flexShrink: 0,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <img
              src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=200&h=200&fit=crop&crop=faces&q=80"
              alt="Léa"
              style={{ width: 52, height: 52, borderRadius: "50%", objectFit: "cover", border: "2px solid white", boxShadow: "0 4px 10px -2px rgba(10,14,44,.15)" }}
            />
            <div>
              <div style={{ fontSize: 11, fontWeight: 600, color: BLUE, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 2, display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{ width: 6, height: 6, background: ORANGE, borderRadius: "50%" }} /> Rapport d'orientation Proxxie
              </div>
              <div style={{ fontSize: 18, fontWeight: 600, fontFamily: "var(--font-display)", letterSpacing: "-0.01em" }}>
                Léa, 17 ans · Terminale générale
              </div>
              <div style={{ fontSize: 12, color: "var(--c-muted)", marginTop: 2 }}>
                Coach référente : Marion · Période : sept 2025 — mai 2026
              </div>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Fermer"
            style={{
              width: 36, height: 36, borderRadius: "50%",
              background: "rgba(10,14,44,.04)", border: "none",
              cursor: "pointer", display: "grid", placeItems: "center",
              color: "var(--c-muted)",
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>

        {/* ── Body scrollable ── */}
        <div style={{ flex: 1, overflowY: "auto", padding: "28px 36px 32px" }}>

          {/* Préambule */}
          {card(
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: BLUE, marginBottom: 8 }}>
                <span style={{ display: "inline-block", width: 6, height: 6, background: ORANGE, borderRadius: "50%", marginRight: 6 }} /> Synthèse en une phrase
              </div>
              <div style={{ fontFamily: "var(--font-display)", fontSize: 24, fontWeight: 600, letterSpacing: "-0.02em", lineHeight: 1.25, color: "var(--c-ink)", marginBottom: 10 }}>
                Léa est passée d'« aucune idée » à un projet d'ingénierie biomédicale assumé, avec trois admissions sécurisées et une stratégie claire pour Polytech Lyon.
              </div>
              <div style={{ fontSize: 14, color: "var(--c-ink-2)", lineHeight: 1.55 }}>
                Ce rapport restitue 8 mois d'accompagnement : 12 séances en 1·1, 3 points parentaux, 3 interviews de pros facilitées, 9 documents annotés. Il s'appuie sur les tests Big Five OCEAN-X et RIASEC complétés par Léa, sur les arbitrages structurés faits en séance avec Marion, et sur l'observation directe de l'évolution de Léa au fil des mois.
              </div>
            </div>
          )}

          {/* Sommaire visuel */}
          {card(
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: BLUE, marginBottom: 10 }}>
                Sommaire
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "6px 24px", fontSize: 13.5, color: "var(--c-ink-2)" }}>
                {[
                  "1. Profil de personnalité",
                  "2. Valeurs & besoins",
                  "3. Forces & axes de progrès",
                  "4. Centres d'intérêt",
                  "5. Évolution au fil de l'accompagnement",
                  "6. Question centrale arbitrée",
                  "7. Secteurs explorés",
                  "8. Métiers recommandés",
                  "9. Parcours académiques (scénarios A/B/C)",
                  "10. Points de vigilance & leviers",
                  "11. Échanges avec le coach",
                  "12. Prochaines étapes",
                ].map((t, i) => (
                  <div key={i} style={{ padding: "4px 0", borderBottom: i < 10 ? "1px dashed rgba(10,14,44,.08)" : "none" }}>{t}</div>
                ))}
              </div>
            </div>,
            { background: "rgba(72,122,255,.05)", border: "1px solid rgba(72,122,255,.18)" }
          )}

          {/* 1. Profil dominant + Big Five */}
          {sectionTitle("Profil dominant · OCEAN-X + RIASEC", "Exploratrice analytique", "Forte capacité d'analyse, curiosité scientifique, sensibilité créative. Motivée par la résolution de problèmes complexes ayant un impact concret. Profil RIASEC dominant : Investigateur + Artistique.")}
          {card(
            <div>
              <div style={{ fontSize: 12, color: "var(--c-muted)", marginBottom: 10, display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{ width: 6, height: 6, background: BLUE, borderRadius: "50%" }} /> Big Five OCEAN-X — score sur 120
              </div>
              {oceanX.map((d, i) => (
                <div key={i} style={{ marginBottom: 14, paddingBottom: 14, borderBottom: i < oceanX.length - 1 ? "1px solid rgba(10,14,44,.06)" : "none" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 6 }}>
                    <div style={{ fontSize: 14, fontWeight: 600, color: "var(--c-ink)" }}>{d.dim}</div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: d.color }}>{d.score} / {d.max}</div>
                  </div>
                  <div style={{ height: 6, background: "rgba(10,14,44,.06)", borderRadius: 99, overflow: "hidden", marginBottom: 8 }}>
                    <div style={{ height: "100%", width: `${(d.score / d.max) * 100}%`, background: `linear-gradient(90deg, ${BLUE}, ${ORANGE})`, borderRadius: 99 }} />
                  </div>
                  <div style={{ fontSize: 13, color: "var(--c-ink-2)", lineHeight: 1.5 }}>{d.detail}</div>
                </div>
              ))}
            </div>
          )}

          {/* 2. Valeurs & besoins */}
          {sectionTitle("Valeurs & besoins", "Ce qui fait sens et ce qui sécurise", "Les valeurs sont les boussoles. Les besoins sont les conditions minimales pour qu'un environnement soit tenable dans la durée.")}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 14 }}>
            {card(
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: BLUE, marginBottom: 10 }}>Valeurs fondamentales</div>
                {valeurs.map((v, i) => (
                  <div key={i} style={{ marginBottom: 10 }}>
                    <div style={{ fontSize: 13.5, fontWeight: 600, color: "var(--c-ink)" }}>{v.n}</div>
                    <div style={{ fontSize: 12.5, color: "var(--c-ink-2)", lineHeight: 1.45 }}>{v.d}</div>
                  </div>
                ))}
              </div>, { marginBottom: 0 }
            )}
            {card(
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: BLUE, marginBottom: 10 }}>Besoins clés</div>
                {besoins.map((b, i) => (
                  <div key={i} style={{ marginBottom: 10 }}>
                    <div style={{ fontSize: 13.5, fontWeight: 600, color: "var(--c-ink)" }}>{b.n}</div>
                    <div style={{ fontSize: 12.5, color: "var(--c-ink-2)", lineHeight: 1.45 }}>{b.d}</div>
                  </div>
                ))}
              </div>, { marginBottom: 0 }
            )}
          </div>

          {/* 3. Forces & axes de progrès */}
          {sectionTitle("Forces & axes de progrès", "Sur quoi on s'appuie, sur quoi on bosse", "Les forces sont des atouts à activer dans le choix de formation. Les axes ne sont pas des faiblesses : ce sont des leviers à travailler dans les deux premières années post-bac.")}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 14 }}>
            {card(
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: GREEN, marginBottom: 10 }}>Points forts</div>
                {competencesForts.map((c, i) => (
                  <div key={i} style={{ fontSize: 13, color: "var(--c-ink-2)", lineHeight: 1.5, padding: "6px 0", borderTop: i > 0 ? "1px solid rgba(10,14,44,.05)" : "none" }}>• {c}</div>
                ))}
              </div>, { marginBottom: 0 }
            )}
            {card(
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: ORANGE, marginBottom: 10 }}>Axes de développement</div>
                {competencesAxes.map((c, i) => (
                  <div key={i} style={{ fontSize: 13, color: "var(--c-ink-2)", lineHeight: 1.5, padding: "6px 0", borderTop: i > 0 ? "1px solid rgba(10,14,44,.05)" : "none" }}>→ {c}</div>
                ))}
              </div>, { marginBottom: 0 }
            )}
          </div>

          {/* 4. Centres d'intérêt */}
          {sectionTitle("Centres d'intérêt", "Ce qui nourrit en dehors des cours", "Les centres d'intérêt révèlent souvent autant qu'un test. Ils sont aussi un terrain pour repérer les premiers signes d'une vocation cachée.")}
          {card(
            <div>
              {interets.map((it, i) => (
                <div key={i} style={{ padding: "10px 0", borderTop: i > 0 ? "1px solid rgba(10,14,44,.06)" : "none" }}>
                  <div style={{ fontSize: 14, fontWeight: 600, color: "var(--c-ink)", marginBottom: 3 }}>{it.n}</div>
                  <div style={{ fontSize: 13, color: "var(--c-ink-2)", lineHeight: 1.5 }}>{it.d}</div>
                </div>
              ))}
            </div>
          )}

          {/* 5. Évolution au fil de l'accompagnement */}
          {sectionTitle("Évolution au fil de l'accompagnement", "8 mois, 12 séances, une transformation", "Les phases ci-dessous restituent les moments-clés observés par Marion. Chaque phase est suivie d'une lecture coach explicite.")}
          {phases.map((p, i) => (
            <div key={i} style={{ marginBottom: 14 }}>
              {card(
                <div>
                  <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: BLUE, marginBottom: 6 }}>{p.date}</div>
                  <div style={{ fontFamily: "var(--font-display)", fontSize: 18, fontWeight: 600, letterSpacing: "-0.015em", color: "var(--c-ink)", marginBottom: 8 }}>{p.title}</div>
                  <div style={{ fontSize: 13.5, color: "var(--c-ink-2)", lineHeight: 1.6, marginBottom: 12 }}>{p.body}</div>
                  <div style={{ background: "rgba(72,122,255,.06)", border: "1px solid rgba(72,122,255,.18)", borderLeft: `3px solid ${BLUE}`, borderRadius: 10, padding: "10px 14px", fontSize: 12.5, color: "var(--c-ink-2)", lineHeight: 1.55, fontStyle: "italic" }}>
                    {p.coach}
                  </div>
                </div>, { marginBottom: 0 }
              )}
            </div>
          ))}

          {/* 6. Question centrale arbitrée */}
          {sectionTitle("Question centrale arbitrée", "Médecine, Sciences-Po, ingé bio ?", "Plutôt que de choisir une voie par défaut, on a posé les 4 hypothèses sérieuses, leurs pour, leurs contre, et la décision prise par Léa elle-même.")}
          {voies.map((v, i) => (
            <div key={i} style={{ marginBottom: 12 }}>
              {card(
                <div>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
                    <div style={{ fontFamily: "var(--font-display)", fontSize: 16, fontWeight: 600, color: "var(--c-ink)" }}>{v.voie}</div>
                    <span style={{ padding: "4px 10px", borderRadius: 99, fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", background: `${v.verdictColor}1A`, color: v.verdictColor }}>{v.verdict}</span>
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 10 }}>
                    <div>
                      <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: GREEN, marginBottom: 4 }}>Pour</div>
                      <div style={{ fontSize: 12.5, color: "var(--c-ink-2)", lineHeight: 1.5 }}>{v.pour}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "#B72C4A", marginBottom: 4 }}>Contre</div>
                      <div style={{ fontSize: 12.5, color: "var(--c-ink-2)", lineHeight: 1.5 }}>{v.contre}</div>
                    </div>
                  </div>
                  <div style={{ fontSize: 12.5, color: "var(--c-ink)", background: "rgba(10,14,44,.03)", borderRadius: 8, padding: "8px 12px", lineHeight: 1.5 }}>
                    <strong style={{ color: BLUE }}>Décision : </strong>{v.decision}
                  </div>
                </div>, { marginBottom: 0 }
              )}
            </div>
          ))}

          {/* 7. Secteurs explorés */}
          {sectionTitle("Secteurs explorés", "Le terrain de jeu réaliste", "Compatibilité = adéquation profil OCEAN-X + RIASEC + valeurs + besoins. Les étoiles reflètent l'intérêt exprimé par Léa en séance.")}
          {card(
            <div>
              {secteurs.map((s, i) => (
                <div key={i} style={{ display: "grid", gridTemplateColumns: "1.4fr auto auto 2.4fr", gap: 14, alignItems: "start", padding: "10px 0", borderTop: i > 0 ? "1px solid rgba(10,14,44,.06)" : "none" }}>
                  <div style={{ fontSize: 13.5, fontWeight: 600, color: "var(--c-ink)" }}>{s.n}</div>
                  <div style={{ fontSize: 12, color: "var(--c-muted)" }}>{stars(s.stars)}</div>
                  <div style={{ fontSize: 11, fontWeight: 700, color: BLUE, textTransform: "uppercase", letterSpacing: "0.06em" }}>{s.fit}</div>
                  <div style={{ fontSize: 12.5, color: "var(--c-ink-2)", lineHeight: 1.5 }}>{s.note}</div>
                </div>
              ))}
            </div>
          )}

          {/* 8. Métiers recommandés */}
          {sectionTitle("Métiers recommandés", "6 cibles classées par compatibilité", "Compatibilité = score profil ramené sur 100. Salaire = fourchette junior France. Croissance = perspective d'emploi 5 ans (source : France Travail, Glassdoor).")}
          {card(
            <div>
              {metiers.map((m, i) => (
                <div key={i} style={{ padding: "12px 0", borderTop: i > 0 ? "1px solid rgba(10,14,44,.06)" : "none" }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 4 }}>
                    <div style={{ fontSize: 14, fontWeight: 600, color: "var(--c-ink)" }}>{m.n}</div>
                    <div style={{ fontSize: 12, fontWeight: 700, color: BLUE }}>{m.m}% compat.</div>
                  </div>
                  <div style={{ display: "flex", gap: 12, fontSize: 11.5, color: "var(--c-muted)", marginBottom: 6 }}>
                    <span>💶 {m.s}</span>
                    <span style={{ color: GREEN, fontWeight: 600 }}>{m.t}</span>
                  </div>
                  <div style={{ fontSize: 12.5, color: "var(--c-ink-2)", lineHeight: 1.5 }}>{m.d}</div>
                </div>
              ))}
            </div>
          )}

          {/* 9. Parcours académiques */}
          {sectionTitle("Parcours académiques", "Stratégie en triple filet", "Ambitieux (Polytechnique, Centrale), cohérents (INSA, Polytech), filet (université). Trois admissions sécurisées au 25 mai.")}
          {card(
            <div>
              {formations.map((f, i) => (
                <div key={i} style={{ padding: "12px 0", borderTop: i > 0 ? "1px solid rgba(10,14,44,.06)" : "none" }}>
                  <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 4 }}>
                    <div style={{ fontSize: 14, fontWeight: 600, color: "var(--c-ink)" }}>{f.n}</div>
                    <div style={{ fontSize: 12, fontWeight: 700, color: BLUE }}>compat. {f.m}%</div>
                  </div>
                  <div style={{ fontSize: 12, color: "var(--c-muted)", marginBottom: 6 }}>{f.v}</div>
                  <div style={{ fontSize: 12.5, color: "var(--c-ink-2)", lineHeight: 1.5 }}>{f.d}</div>
                </div>
              ))}
            </div>
          )}

          {/* 10. Vigilance / leviers */}
          {sectionTitle("Vigilance & leviers", "Ce qu'on garde à l'œil et ce qui pousse", "Les points de vigilance ne sont pas des verdicts : ce sont des sujets à travailler explicitement. Les leviers sont des forces à activer dans le choix de formation et la transition post-bac.")}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 14 }}>
            {card(
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: ORANGE, marginBottom: 10 }}>⚠️ Vigilance</div>
                {vigilance.map((v, i) => (
                  <div key={i} style={{ padding: "8px 0", borderTop: i > 0 ? "1px solid rgba(10,14,44,.05)" : "none" }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: "var(--c-ink)", marginBottom: 3 }}>{v.t}</div>
                    <div style={{ fontSize: 12.5, color: "var(--c-ink-2)", lineHeight: 1.5 }}>{v.d}</div>
                  </div>
                ))}
              </div>, { marginBottom: 0 }
            )}
            {card(
              <div>
                <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: GREEN, marginBottom: 10 }}>✅ Leviers</div>
                {leviers.map((l, i) => (
                  <div key={i} style={{ padding: "8px 0", borderTop: i > 0 ? "1px solid rgba(10,14,44,.05)" : "none" }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: "var(--c-ink)", marginBottom: 3 }}>{l.t}</div>
                    <div style={{ fontSize: 12.5, color: "var(--c-ink-2)", lineHeight: 1.5 }}>{l.d}</div>
                  </div>
                ))}
              </div>, { marginBottom: 0 }
            )}
          </div>

          {/* 11. Échanges avec le coach (mis en avant) */}
          {sectionTitle("Échanges avec le coach", "Marion, présente sur les 8 mois", "L'accompagnement Proxxie n'est pas une plateforme avec un PDF à la fin. C'est un coach disponible à chaque étape, avec un volume d'échanges qui dépasse de loin les séances officielles.")}
          {card(
            <div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 10, marginBottom: 20 }}>
                {echangesStats.map((s, i) => (
                  <div key={i} style={{ textAlign: "center", padding: "14px 8px", background: "rgba(72,122,255,.06)", border: "1px solid rgba(72,122,255,.18)", borderRadius: 14 }}>
                    <div style={{ fontFamily: "var(--font-display)", fontSize: 26, fontWeight: 600, color: BLUE, letterSpacing: "-0.02em" }}>{s.value}</div>
                    <div style={{ fontSize: 11, color: "var(--c-ink-2)", marginTop: 2, lineHeight: 1.3 }}>{s.label}</div>
                  </div>
                ))}
              </div>

              <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: BLUE, marginBottom: 10 }}>Ce que Léa a dit</div>
              <div style={{ display: "grid", gap: 10 }}>
                {citationsLea.map((c, i) => (
                  <div key={i} style={{ background: "rgba(253,105,54,.06)", border: "1px solid rgba(253,105,54,.18)", borderLeft: `3px solid ${ORANGE}`, borderRadius: 10, padding: "12px 14px", fontSize: 13, color: "var(--c-ink-2)", lineHeight: 1.55, fontStyle: "italic" }}>
                    {c}
                  </div>
                ))}
              </div>

              <div style={{ marginTop: 22, padding: 16, background: "linear-gradient(135deg, rgba(72,122,255,.08), rgba(253,105,54,.06))", borderRadius: 14, display: "flex", alignItems: "center", gap: 14 }}>
                <img
                  src="coach-marion.jpg"
                  alt="Marion"
                  style={{ width: 56, height: 56, borderRadius: "50%", objectFit: "cover", border: "2px solid white", boxShadow: "0 4px 10px -2px rgba(10,14,44,.15)" }}
                />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13.5, fontWeight: 700, color: "var(--c-ink)" }}>Marion · coach Proxxie</div>
                  <div style={{ fontSize: 12.5, color: "var(--c-ink-2)", lineHeight: 1.5, marginTop: 2 }}>
                    « Léa avait tout pour réussir : profil scolaire solide, parents engagés, vraie curiosité. Ce qui lui manquait, c'était un cadre pour transformer cette matière brute en projet. Mon rôle n'est pas de décider à sa place, c'est de l'aider à voir clair, à oser, puis à arbitrer en connaissance de cause. »
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 12. Prochaines étapes */}
          {sectionTitle("Prochaines étapes", "Court, moyen, long terme", "Le rapport ne s'arrête pas à la rentrée. Voici les actions concrètes par horizon, avec les jalons coach prévus.")}
          {[
            { titre: "Court terme — Mai à août 2026", color: BLUE, items: prochainesCT },
            { titre: "Moyen terme — Septembre à décembre 2026", color: ORANGE, items: prochainesMT },
            { titre: "Long terme — 2 à 5 ans", color: GREEN, items: prochainesLT },
          ].map((h, hi) => (
            <div key={hi} style={{ marginBottom: 12 }}>
              {card(
                <div>
                  <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: h.color, marginBottom: 10 }}>{h.titre}</div>
                  {h.items.map((it, i) => (
                    <div key={i} style={{ display: "flex", alignItems: "start", gap: 10, padding: "6px 0", fontSize: 13, color: "var(--c-ink-2)", lineHeight: 1.5 }}>
                      <span style={{ width: 16, height: 16, marginTop: 2, borderRadius: 4, border: `1.5px solid ${h.color}`, flexShrink: 0, background: "white" }} />
                      <span>{it}</span>
                    </div>
                  ))}
                </div>, { marginBottom: 0 }
              )}
            </div>
          ))}

          {/* Synthèse finale */}
          <div style={{ marginTop: 20, padding: 22, borderRadius: 18, background: "linear-gradient(135deg, #1320CE 0%, #487AFF 100%)", color: "white", boxShadow: "0 20px 40px -16px rgba(19,32,206,.4)" }}>
            <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", opacity: 0.85, marginBottom: 8 }}>Synthèse</div>
            <div style={{ fontFamily: "var(--font-display)", fontSize: 20, fontWeight: 600, letterSpacing: "-0.02em", lineHeight: 1.35, marginBottom: 10 }}>
              Léa entre à Polytech Lyon Biomédical en septembre 2026 avec un projet construit, un coach toujours en lien, et une stratégie claire pour les 5 ans à venir.
            </div>
            <div style={{ fontSize: 13.5, lineHeight: 1.55, opacity: 0.92 }}>
              Le rapport montre une trajectoire qu'on ne pouvait pas deviner en septembre 2025. C'est exactement ce que vise un accompagnement Proxxie : créer les conditions pour qu'un jeune puisse choisir lui-même, en pleine conscience, plutôt que par défaut ou sous pression. Et continuer à l'accompagner après le choix, pas juste avant.
            </div>
          </div>

          {/* Note méthodologique */}
          <div style={{ marginTop: 18, padding: "14px 18px", borderRadius: 12, background: "rgba(10,14,44,.04)", fontSize: 11.5, color: "var(--c-muted)", lineHeight: 1.55 }}>
            <strong style={{ color: "var(--c-ink-2)" }}>Note méthodologique · </strong>
            Ce rapport est un exemple fictif basé sur des profils réels accompagnés par Proxxie. Toutes les sections (profil, tests, phases, arbitrages, échanges) reflètent la structure et la profondeur d'un rapport Proxxie effectif. Le rapport de votre ado sera entièrement personnalisé à partir de ses tests, ses bulletins, ses interviews et de ses échanges avec son coach.
          </div>

        </div>

        {/* ── Footer fixe avec CTA ── */}
        <div
          style={{
            padding: "18px 36px",
            background: "white",
            borderTop: "1px solid rgba(10,14,44,.08)",
            display: "flex", alignItems: "center", justifyContent: "space-between", gap: 18,
            flexShrink: 0,
          }}
        >
          <div style={{ fontSize: 13, color: "var(--c-muted)", lineHeight: 1.4, maxWidth: 380 }}>
            Cet exemple est générique. <strong style={{ color: "var(--c-ink)" }}>Le rapport de votre ado sera personnalisé</strong> avec ses bulletins, ses tests et ses échanges avec son coach.
          </div>
          <button
            type="button"
            onClick={() => { onClose(); onPersonalize(); }}
            className="btn btn-orange btn-arrow"
            style={{ padding: "14px 24px", fontSize: 15, fontWeight: 600 }}
          >
            Personnaliser pour mon ado →
          </button>
        </div>
      </div>
    </div>
  );
};

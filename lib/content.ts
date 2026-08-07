// Contenu éditorial de la landing page, isolé du JSX pour préparer une future
// extraction i18n (multi-langues fait partie de la vision produit de l'AMD).

export const nav = [
  { label: "Fonctionnalités", href: "#modules" },
  { label: "Rôles", href: "#roles" },
  { label: "Commission", href: "#commission" },
  { label: "Comment ça marche", href: "#comment-ca-marche" },
  { label: "FAQ", href: "#faq" },
];

export const hero = {
  eyebrow: "Multi-pays · Multi-langues · Multi-devises",
  title: "La plateforme tout-en-un pour la restauration africaine",
  subtitle:
    "Point de vente, cuisine, livraison, marketplace et intelligence artificielle : RestauHub Africa réunit tout ce dont un restaurant, un maquis, un hôtel ou une pâtisserie a besoin pour grandir — sans jongler entre dix outils différents.",
  primaryCta: "Essayer gratuitement",
  secondaryCta: "Voir les fonctionnalités",
  stats: [
    { value: "1%", label: "de commission, après paiement confirmé" },
    { value: "12", label: "rôles utilisateurs dédiés" },
    { value: "8", label: "domaines métier couverts" },
  ],
};

export const modules = [
  {
    icon: "UtensilsCrossed",
    title: "Catalogue & menus",
    description:
      "Produits, catégories, menus et recettes centralisés, synchronisés sur toutes vos succursales.",
  },
  {
    icon: "ClipboardList",
    title: "Commandes & cuisine",
    description:
      "Suivi en temps réel des commandes, statuts de préparation et gestion des tables et QR codes.",
  },
  {
    icon: "Truck",
    title: "Livraison",
    description:
      "Livraison intégrée avec suivi client en direct, sans dépendre d'une plateforme tierce.",
  },
  {
    icon: "Store",
    title: "Marketplace fournisseurs",
    description:
      "Commandez viandes, boissons, gaz, légumes, équipements et emballages directement depuis la plateforme.",
  },
  {
    icon: "Gift",
    title: "Fidélité & coupons",
    description:
      "Programmes de points, promotions et campagnes publicitaires pour fidéliser et attirer de nouveaux clients.",
  },
  {
    icon: "BarChart3",
    title: "Business Intelligence",
    description:
      "Rapports consolidés, prévisions de ventes et détection d'anomalies assistées par l'IA — jamais décisionnelle sur les actions critiques.",
  },
];

export const roles = [
  {
    key: "client",
    label: "Client",
    headline: "Commander, réserver, cumuler des points — en quelques secondes",
    bullets: [
      "Commander sur place, à emporter ou en livraison",
      "Réserver une table et suivre sa commande en direct",
      "Cumuler des points de fidélité et profiter des promotions",
    ],
  },
  {
    key: "gerant",
    label: "Gérant",
    headline: "Piloter un établissement sans y passer ses journées",
    bullets: [
      "Gestion du personnel, des stocks et des produits",
      "Création de promotions et suivi des ventes",
      "Rapports d'établissement générés automatiquement",
    ],
  },
  {
    key: "pdg",
    label: "PDG",
    headline: "Une vue consolidée sur tous les établissements",
    bullets: [
      "Tableau de bord multi-établissements en un coup d'œil",
      "Analyse financière et statistiques consolidées",
      "Décisions basées sur des rapports fiables, pas sur des estimations",
    ],
  },
  {
    key: "livreur",
    label: "Livreur",
    headline: "Une logistique claire, du restaurant au client",
    bullets: [
      "Liste de livraisons optimisée en temps réel",
      "Statuts de course synchronisés avec le client et le restaurant",
      "Historique et suivi des gains",
    ],
  },
] as const;

export const commission = {
  title: "Une commission transparente, pas une taxe cachée",
  description:
    "La plupart des plateformes de livraison prélèvent 20 à 30% sur chaque commande. RestauHub Africa applique un taux par défaut de 1%, configurable, prélevé uniquement après confirmation définitive du paiement — et chaque calcul est historisé pour votre comptabilité.",
  points: [
    { value: "1%", label: "Taux par défaut, configurable" },
    { value: "0", label: "Commission avant paiement confirmé" },
    { value: "100%", label: "Des calculs historisés et traçables" },
  ],
};

export const howItWorks = [
  {
    step: "01",
    title: "Créez votre compte",
    description: "Inscrivez votre établissement et configurez vos succursales en quelques minutes.",
  },
  {
    step: "02",
    title: "Configurez votre menu",
    description: "Ajoutez vos produits, catégories et recettes — modifiables à tout moment.",
  },
  {
    step: "03",
    title: "Recevez vos commandes",
    description: "Sur place, à emporter ou en livraison : tout arrive au même endroit, en temps réel.",
  },
  {
    step: "04",
    title: "Suivez vos revenus",
    description: "Rapports, statistiques et prévisions générés automatiquement, jour après jour.",
  },
];

export const faq = [
  {
    question: "Mes données sont-elles isolées de celles des autres restaurants ?",
    answer:
      "Oui. RestauHub Africa est une plateforme multi-tenant : chaque établissement dispose de ses propres utilisateurs, menus, commandes, clients et rapports. Aucune donnée n'est jamais visible entre deux tenants — c'est une règle absolue de l'architecture, appliquée à chaque requête.",
  },
  {
    question: "La plateforme fonctionne-t-elle sans connexion internet stable ?",
    answer:
      "L'application mobile est conçue en mode « offline first » : la prise de commande et les opérations essentielles continuent de fonctionner en cas de réseau dégradé, puis se synchronisent automatiquement.",
  },
  {
    question: "Quels pays, langues et devises sont supportés ?",
    answer:
      "RestauHub Africa est pensée dès l'origine pour un usage multi-pays, multi-langues et multi-devises, afin de s'adapter aux réalités du marché africain sans refonte majeure.",
  },
  {
    question: "Comment la sécurité des paiements et des comptes est-elle assurée ?",
    answer:
      "Authentification JWT, contrôle d'accès basé sur les rôles, authentification à deux facteurs, chiffrement des données sensibles et journalisation d'audit complète, conformes aux bonnes pratiques OWASP.",
  },
  {
    question: "L'intelligence artificielle peut-elle agir seule sur mon restaurant ?",
    answer:
      "Non. L'IA a un rôle strictement assistif : prévisions de ventes, détection d'anomalies, recommandations et génération de rapports. Aucune action critique n'est jamais prise de façon autonome par l'IA.",
  },
];

export const finalCta = {
  title: "Prêt à faire grandir votre établissement ?",
  subtitle:
    "Rejoignez les restaurants, maquis, hôtels et boulangeries qui gèrent déjà leur activité sur une seule plateforme.",
  primaryCta: "Essayer gratuitement",
  secondaryCta: "Parler à un conseiller",
};

export const footer = {
  description:
    "La plateforme SaaS tout-en-un pour la restauration africaine — point de vente, livraison, marketplace et intelligence artificielle.",
  columns: [
    {
      title: "Produit",
      links: [
        { label: "Fonctionnalités", href: "#modules" },
        { label: "Rôles utilisateurs", href: "#roles" },
        { label: "Commission", href: "#commission" },
      ],
    },
    {
      title: "Ressources",
      links: [
        { label: "Comment ça marche", href: "#comment-ca-marche" },
        { label: "FAQ", href: "#faq" },
      ],
    },
  ],
};

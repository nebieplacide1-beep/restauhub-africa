# RestauHub Africa — Site vitrine

Landing page de RestauHub Africa, plateforme SaaS tout-en-un pour la restauration africaine. Voir [`RESTAUHUB_AFRICA_AMD.md`](./RESTAUHUB_AFRICA_AMD.md) pour la vision produit et l'architecture globale du projet.

## Stack

- **Next.js 16** (App Router, Turbopack) + TypeScript
- **Tailwind CSS v4** avec un système de tokens dérivé du logo (teal / orange / or — voir `app/globals.css`)
- **shadcn/ui** (Radix) pour les primitives d'interface
- **lucide-react** pour les icônes, **motion** pour les micro-animations

## Développement local

Prérequis : Node.js 20+.

```bash
npm install
npm run dev
```

Ouvrir [http://localhost:3000](http://localhost:3000).

```bash
npm run build   # build de production (celui utilisé par Vercel)
npm run lint    # ESLint
```

## Structure

```
app/                 pages, layout, styles globaux, favicon
components/ui/        primitives shadcn/ui
components/sections/  sections de la landing page (Hero, Modules, Rôles, ...)
lib/content.ts        contenu éditorial (FR), isolé du JSX
public/                assets statiques (logo)
```

## Déploiement — GitHub → Vercel

Ce projet est prêt pour un déploiement Vercel sans configuration additionnelle (`vercel.json` n'est pas nécessaire pour un projet Next.js standard).

1. **Créer le dépôt GitHub** (si ce n'est pas déjà fait) et y pousser ce projet :
   ```bash
   git init
   git add .
   git commit -m "Initial commit — landing page RestauHub Africa"
   git branch -M main
   git remote add origin <URL_DU_DEPOT_GITHUB>
   git push -u origin main
   ```
2. Sur [vercel.com](https://vercel.com), **New Project → Import Git Repository**, sélectionner ce dépôt GitHub.
3. Vercel détecte automatiquement Next.js (build command `next build`, output géré automatiquement) — cliquer **Deploy**.
4. Chaque `git push` sur `main` déclenche ensuite un déploiement de production automatique ; chaque pull request obtient une URL de preview dédiée.

Aucune variable d'environnement n'est requise pour cette landing page statique.

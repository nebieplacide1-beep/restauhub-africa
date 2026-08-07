import type { Metadata } from "next";
import { Inter, Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin"],
  display: "swap",
});

const plusJakarta = Plus_Jakarta_Sans({
  variable: "--font-heading",
  subsets: ["latin"],
  weight: ["500", "600", "700", "800"],
  display: "swap",
});

const siteUrl = "https://restauhub.africa";
const title = "RestauHub Africa — La plateforme tout-en-un pour la restauration africaine";
const description =
  "Point de vente, commandes, livraison, marketplace et intelligence artificielle : RestauHub Africa réunit tout ce dont un restaurant, un maquis ou un hôtel a besoin pour grandir, en une seule plateforme pensée pour l'Afrique.";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title,
  description,
  keywords: [
    "RestauHub Africa",
    "logiciel restaurant Afrique",
    "point de vente restaurant",
    "livraison restaurant",
    "gestion restaurant SaaS",
  ],
  openGraph: {
    title,
    description,
    url: siteUrl,
    siteName: "RestauHub Africa",
    images: ["/logo-full.png"],
    locale: "fr_FR",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title,
    description,
    images: ["/logo-full.png"],
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="fr"
      className={`${inter.variable} ${plusJakarta.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}

import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BilanLab · Laboratoire d’extraction de bilans",
  description: "Déposer un bilan, comparer sept méthodes d’extraction, mesurer les durées et comprendre les contrôles.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}

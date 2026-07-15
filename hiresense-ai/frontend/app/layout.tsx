import type { Metadata } from "next";
import "./globals.css";

// Font strategy: this project intentionally uses a self-hosted/system font stack (defined in
// tailwind.config.js + globals.css) rather than `next/font/google`, so `npm run build` succeeds
// in offline or network-restricted environments (CI, air-gapped dev machines, etc.) without
// depending on fonts.googleapis.com at build time. If you want branded Google Fonts, install
// them via next/font/google and wire the resulting CSS variables into tailwind.config.js.

export const metadata: Metadata = {
  title: "HireSense AI",
  description: "Explainable AI-powered candidate screening and ranking decision support system.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-body text-ink-900 antialiased">{children}</body>
    </html>
  );
}

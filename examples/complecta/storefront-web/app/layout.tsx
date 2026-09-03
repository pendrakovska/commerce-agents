// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

import type { Metadata } from "next";
import { Playfair_Display } from "next/font/google";
import "./globals.css";

// Дизайн-система приложения Complecta: системный sans для текста (T.sans), Playfair Display — display/wordmark.
const playfair = Playfair_Display({ subsets: ["latin", "cyrillic"], variable: "--font-display", display: "swap", style: ["normal", "italic"] });

export const metadata: Metadata = {
  title: "Complecta AI",
  description: "Real furniture from Italian brands, chosen with ALXNDRA — the Complecta AI copilot.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={playfair.variable}>
      <body>{children}</body>
    </html>
  );
}

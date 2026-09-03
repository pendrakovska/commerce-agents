// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

import type { Metadata } from "next";
import { Inter, Playfair_Display } from "next/font/google";
import "./globals.css";

// Шрифты бренда Complecta AI: Playfair Display — заголовки и wordmark, Inter — текст и UI.
const inter = Inter({ subsets: ["latin", "cyrillic"], variable: "--font-body", display: "swap" });
const playfair = Playfair_Display({ subsets: ["latin", "cyrillic"], variable: "--font-display", display: "swap", style: ["normal", "italic"] });

export const metadata: Metadata = {
  title: "Complecta AI",
  description: "Real furniture from Italian brands, chosen with ALXNDRA — the Complecta AI copilot.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${playfair.variable}`}>
      <body>{children}</body>
    </html>
  );
}

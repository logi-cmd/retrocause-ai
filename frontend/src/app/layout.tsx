import type { Metadata } from "next";
import { Fraunces, IBM_Plex_Sans, JetBrains_Mono } from "next/font/google";
import { I18nProvider } from "@/lib/i18n";
import "./globals.css";

const fraunces = Fraunces({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
});

const ibmPlexSans = IBM_Plex_Sans({
  variable: "--font-sans",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "RetroCause — Evidence-Backed Causal Explorer",
  description: "Ask why something happened and inspect evidence-backed causal chains, graphs, and counterfactual reasoning.",
  icons: {
    icon: [
      {
        url: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect fill='%230066CC' width='32' height='32'/><path fill='white' d='M8 8h4v16H8zm6 4h4v12h-4zm6 4h4v8h-4z'/></svg>",
        type: "image/svg+xml",
      },
    ],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${fraunces.variable} ${ibmPlexSans.variable} ${jetbrainsMono.variable}`}>
      <body className="antialiased min-h-full flex flex-col bg-[var(--board-white)] text-[var(--ink-700)]">
        <I18nProvider>{children}</I18nProvider>
      </body>
    </html>
  );
}

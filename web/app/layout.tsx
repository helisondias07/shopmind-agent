import type { Metadata } from "next";
import type { ReactNode } from "react";
import { IBM_Plex_Mono, Space_Grotesk } from "next/font/google";
import { Header } from "@/components/header";
import { LocaleProvider } from "@/components/locale";
import "./globals.css";

const grotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const plex = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ShopMind",
  description:
    "Support console for the fictional Lume catalog. A LangGraph agent answers from stock, orders, and policies, and cites the source.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR" className={`${grotesk.variable} ${plex.variable}`}>
      <body className="min-h-screen font-sans text-snow antialiased">
        <LocaleProvider>
          <Header />
          <main>{children}</main>
        </LocaleProvider>
      </body>
    </html>
  );
}

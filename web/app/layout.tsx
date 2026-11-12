import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Fraunces, Outfit } from "next/font/google";
import { Header } from "@/components/header";
import { LocaleProvider } from "@/components/locale";
import "./globals.css";

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
  display: "swap",
});

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ShopMind — Lume & Co.",
  description:
    "Atendimento da loja fictícia Lume & Co. Um agente LangGraph cita o catálogo, o estoque e as políticas antes de responder.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR" className={`${fraunces.variable} ${outfit.variable}`}>
      <body className="min-h-screen font-sans text-ink antialiased">
        <LocaleProvider>
          <Header />
          <main>{children}</main>
        </LocaleProvider>
      </body>
    </html>
  );
}

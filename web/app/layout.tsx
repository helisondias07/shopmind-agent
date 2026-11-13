import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Atkinson_Hyperlegible, Syne } from "next/font/google";
import { Header } from "@/components/header";
import { LocaleProvider } from "@/components/locale";
import "./globals.css";

const syne = Syne({
  subsets: ["latin"],
  weight: ["500", "600", "700", "800"],
  variable: "--font-syne",
  display: "swap",
});

const atkinson = Atkinson_Hyperlegible({
  subsets: ["latin"],
  weight: ["400", "700"],
  style: ["normal", "italic"],
  variable: "--font-atkinson",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Lume",
  description:
    "Showroom da loja fictícia Lume. O atendimento responde com o preço, o estoque e a fonte do catálogo.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR" className={`${syne.variable} ${atkinson.variable}`}>
      <body>
        <LocaleProvider>
          <div className="page">
            <Header />
            {children}
          </div>
        </LocaleProvider>
      </body>
    </html>
  );
}

import type { Metadata } from "next";
import { Bricolage_Grotesque, Inter, JetBrains_Mono } from "next/font/google";
import "@/styles/globals.css";
import { Providers } from "./providers";

// Doop: k0kB5dc-Vo / tokens --font-display and --font-sans (frame Paleta e tipografia).
const bricolage = Bricolage_Grotesque({
  subsets: ["latin"],
  weight: ["700", "800"],
  display: "swap",
  variable: "--font-bricolage",
});
const inter = Inter({ subsets: ["latin"], display: "swap", variable: "--font-inter" });
// Doop: 11 · Convidar membro + M05 use JetBrains Mono for the invite link only; not preloaded elsewhere.
const mono = JetBrains_Mono({ subsets: ["latin"], weight: "700", display: "swap", preload: false, variable: "--font-jetbrains" });

export const metadata: Metadata = {
  title: "Varal",
  description: "Nenhuma conta vence sem que alguém saiba.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="pt-BR" className={`${bricolage.variable} ${inter.variable} ${mono.variable}`}>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}

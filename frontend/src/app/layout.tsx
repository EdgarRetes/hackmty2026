import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Factora | Financiamiento que impulsa",
  description: "Marketplace de financiamiento de facturas para empresas.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}

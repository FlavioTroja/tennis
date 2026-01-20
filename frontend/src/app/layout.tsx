import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "TennisML - Match Prediction",
  description: "AI-powered tennis match predictions and value bets",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="it">
      <body className={`${inter.variable} font-sans antialiased bg-gray-50`}>
        <Navbar />
        <main className="min-h-[calc(100vh-4rem)]">{children}</main>
        
        {/* Footer */}
        <footer className="bg-white border-t border-gray-200 py-6">
          <div className="max-w-6xl mx-auto px-4 text-center text-sm text-gray-500">
            <p>
              🎾 TennisML - Powered by Machine Learning
            </p>
            <p className="mt-1">
              Dati: <a href="https://github.com/JeffSackmann/tennis_atp" className="text-blue-600 hover:underline" target="_blank" rel="noopener">Jeff Sackmann / Tennis Abstract</a>
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}

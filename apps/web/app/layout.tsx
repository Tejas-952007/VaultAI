import type { Metadata } from "next";
// @ts-expect-error Next.js handles CSS imports at build time.
import "./globals.css";
import Navbar from "@/components/Navbar";
import AmbientRadarBg from "@/components/AmbientRadarBg";
import BootSplash from "@/components/BootSplash";
import AuthProvider from "@/components/AuthProvider";

export const metadata: Metadata = {
  title: "VaultAI | Sovereign Agentic Workbench",
  description: "Mangalore Refinery (MRPL) Local AI Environment",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased selection:bg-emerald-500/30 selection:text-emerald-200">
        <AuthProvider>
          <BootSplash />
          <AmbientRadarBg />

          <div className="relative flex min-h-screen flex-col">
            <Navbar />

            <main className="relative flex-1 overflow-y-auto">
              {children}
            </main>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
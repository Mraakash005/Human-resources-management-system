import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "HRMS — Every workday, perfectly aligned.",
  description: "AI-powered Human Resource Management System",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <html lang="en" className="dark">
        <body className={`${inter.variable} font-[family-name:var(--font-inter)] antialiased`}>
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}

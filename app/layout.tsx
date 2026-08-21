import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Dom 6012/26 · Digitálne dvojča",
  description:
    "Parametrické digitálne dvojča domu a parcely 6012/26 v Březí u Mikulova.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
  openGraph: {
    title: "Dom 6012/26 · Digitálne dvojča",
    description:
      "Parametrický 3D model parcely, domu, základov a inžinierskych sietí s jasnou provenienciou dát.",
    type: "website",
    locale: "sk_SK",
    images: [
      {
        url: "/og-digital-twin.png",
        width: 1200,
        height: 630,
        alt: "Abstraktný technický model domu nad vrstvami výkresu",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Dom 6012/26 · Digitálne dvojča",
    description: "Parametrický 3D model s transparentnou dôkazovou stopou.",
    images: ["/og-digital-twin.png"],
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: "#111713",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="sk">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}

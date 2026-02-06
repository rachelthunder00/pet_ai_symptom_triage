import type { Metadata } from "next";
import { Geist, Geist_Mono, Bubblegum_Sans, Poppins } from "next/font/google";
import "./globals.css";
import { PetProvider } from "../components/PetContext";
import { AuthProvider } from "../components/AuthContext";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const bubblegumSans = Bubblegum_Sans({
  variable: "--font-bubblegum-sans",
  weight: "400",
  subsets: ["latin"],
});

const poppins = Poppins({
  variable: "--font-poppins",
  weight: ["400", "500", "600", "700", "800"],
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Fuzzy Friend - Pet Health AI",
  description: "AI-powered pet symptom assessment and guidance",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} ${bubblegumSans.variable} ${poppins.variable} antialiased`}
      >
        <AuthProvider>
        <PetProvider>
          {children}
        </PetProvider>
        </AuthProvider>
      </body>
    </html>
  );
}

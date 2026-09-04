import type { Metadata } from "next";
import { Poppins, Noto_Nastaliq_Urdu } from "next/font/google";
import "./globals.css";

const poppins = Poppins({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800"],
  variable: "--font-poppins",
});

const nastaliq = Noto_Nastaliq_Urdu({
  subsets: ["arabic"],
  weight: ["400", "700"],
  variable: "--font-nastaliq",
});

export const metadata: Metadata = {
  title: "PakMind — Pakistan's AI-Powered Knowledge Platform",
  description:
    "Your AI companion for Pakistani government services, policy updates, and scholarship matching. Ask in English, Roman Urdu, or Urdu.",
  keywords: [
    "PakMind",
    "Pakistan AI",
    "government services",
    "scholarships Pakistan",
    "policy updates",
    "NADRA",
    "passport",
    "CNIC",
  ],
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${poppins.variable} ${nastaliq.variable} h-full antialiased`}
    >
      <body className="min-h-full font-sans">{children}</body>
    </html>
  );
}

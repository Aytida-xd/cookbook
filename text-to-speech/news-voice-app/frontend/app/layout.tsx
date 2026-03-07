import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "News Voice — Smallest AI",
  description: "AI-grouped news headlines with audio summaries powered by Smallest AI TTS",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

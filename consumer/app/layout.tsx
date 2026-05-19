import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Adopt a Kale — Singapore's AI-managed garden share",
  description:
    "80% of Singaporeans live in HDB flats. They want to grow their own food. They can't. We help them, with AI.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full">{children}</body>
    </html>
  );
}

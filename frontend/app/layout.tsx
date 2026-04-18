import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Zembil Vision",
  description: "Visual-first inventory for Telegram commerce",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

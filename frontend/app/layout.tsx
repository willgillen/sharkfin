import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Shark Fin - Financial Planning",
  description: "Open-source, self-hosted financial planning and budgeting application",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.Node;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

import type { Metadata } from "next";
import { AuthProvider } from "@/lib/hooks/useAuth";
import "./globals.css";

export const metadata: Metadata = {
  title: "Shark Fin - Financial Planning",
  description: "Open-source, self-hosted financial planning and budgeting application",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}

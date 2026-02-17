import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AaS | Argument as a Service",
  description: "Let your agents throw hands while you drink water.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

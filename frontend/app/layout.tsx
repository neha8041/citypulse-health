import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CityPulse Health",
  description:
    "AI-powered public health intelligence platform built on Google Cloud.",
  applicationName: "CityPulse Health",
  authors: [
    {
      name: "The B.A.N.K Labs"
    }
  ],
  keywords: [
    "CityPulse",
    "Healthcare",
    "Google Cloud",
    "Vertex AI",
    "BigQuery",
    "Public Health",
    "Hackathon"
  ],
  robots: {
    index: false,
    follow: false
  }
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <div id="root">
          {children}
        </div>
      </body>
    </html>
  );
}
import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import "./tailwind.css";
import "../../../frontend/src/styles.css";
import "../../../frontend/src/professional.css";
import "../../../frontend/src/cinematic.css";
import "./tradevelocity.css";

const siteOrigin = "https://gettradevelocity.onrender.com";
export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? siteOrigin),
  title: {default: "TradeVelocity | Intelligence Behind Every Trade", template: "%s · TradeVelocity"},
  description: "Explore stock data, practise trading, and track a virtual portfolio with TradeVelocity AI Analyst.",
  icons: {icon: "/tv-mark.svg", apple: "/icon-192.png"},
  openGraph: {title: "TradeVelocity", description: "Paper trading and market intelligence for your next decision.", type: "website", images: ["/icon-512.png"]},
  manifest: "/manifest.webmanifest",
};
export const viewport: Viewport = {themeColor: "#090c10"};

export default function Layout({children}: {children: ReactNode}) {
  return <html lang="en"><body>{children}</body></html>;
}

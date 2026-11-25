import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import "./tailwind.css";
import "../../../frontend/src/styles.css";
import "../../../frontend/src/professional.css";
import "../../../frontend/src/cinematic.css";

export const metadata: Metadata = {
  title: "TradeVelocity | Paper trading and market intelligence",
  description: "Explore stock data, practise trading, and track a virtual portfolio.",
  icons: "/favicon.svg",
  manifest: "/manifest.webmanifest",
};
export const viewport: Viewport = {themeColor: "#101d37"};

export default function Layout({children}: {children: ReactNode}) {
  return <html lang="en"><body>{children}</body></html>;
}

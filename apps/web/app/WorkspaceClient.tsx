"use client";

import { useEffect } from "react";
import AccessGate from "../../../frontend/src/AccessGate";
import Workspace from "../../../frontend/src/Workspace";
import { registerOfflineShell } from "../../../frontend/src/install";
import { desktopView } from "../../../frontend/src/desktopView";
import { AdminDesktop } from "../../../frontend/src/AdminActivity";
import { ThemeSelect, useAppearance } from "./Appearance";
import DesktopApproval from "./DesktopApproval";
import TradingWorkspace from "./TradingWorkspace";

export default function WorkspaceClient() {
  useEffect(registerOfflineShell, []);
  const appearance = useAppearance();
  const themeControl = <ThemeSelect {...appearance} />;
  const inDesktop = desktopView() !== null && navigator.userAgent.includes("Electron/")
    && new URLSearchParams(location.search).get("desktopBrowser") === "1";
  if (location.hostname === "127.0.0.1" && new URLSearchParams(location.search).get("offlineDemo") === "1") {
    return <TradingWorkspace trader={null} signOut={async () => {}} offline {...appearance} />;
  }
  return <AccessGate redesigned theme={appearance.theme} themeControl={themeControl} inDesktop={inDesktop}>{(trader, signOut) => {
    if (trader && location.pathname === "/desktop-sign-in") {
      return <DesktopApproval trader={trader} signOut={signOut} theme={appearance.theme} themeControl={themeControl} />;
    }
    if (desktopView() === "admin") return <div className="tv2" data-tv-theme={appearance.theme}>
      <AdminDesktop allowed={Boolean(trader?.admin)} themeControl={themeControl} />
    </div>;
    if (!trader) return <Workspace trader={null} />;
    return <TradingWorkspace key={trader.workspace_id} trader={trader} signOut={signOut} {...appearance} />;
  }}</AccessGate>;
}

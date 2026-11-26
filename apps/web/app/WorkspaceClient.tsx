"use client";

import { useEffect } from "react";
import AccessGate from "../../../frontend/src/AccessGate";
import Workspace from "../../../frontend/src/Workspace";
import { registerOfflineShell } from "../../../frontend/src/install";
import { desktopView } from "../../../frontend/src/desktopView";
import { AdminDesktop } from "../../../frontend/src/AdminActivity";
import { ThemeSelect, useAppearance } from "./Appearance";
import TradingWorkspace from "./TradingWorkspace";

export default function WorkspaceClient() {
  useEffect(registerOfflineShell, []);
  const appearance = useAppearance();
  const themeControl = <ThemeSelect {...appearance} />;
  return <AccessGate redesigned theme={appearance.theme} themeControl={themeControl}>{(trader, signOut) => {
    if (desktopView() === "admin") return <div className="tv2" data-tv-theme={appearance.theme}>
      <AdminDesktop allowed={Boolean(trader?.admin)} themeControl={themeControl} />
    </div>;
    if (!trader) return <Workspace trader={null} />;
    return <TradingWorkspace key={trader.workspace_id} trader={trader} signOut={signOut} {...appearance} />;
  }}</AccessGate>;
}

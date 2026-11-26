"use client";

import { useEffect } from "react";
import AccessGate from "../../../frontend/src/AccessGate";
import Workspace from "../../../frontend/src/Workspace";
import { registerOfflineShell } from "../../../frontend/src/install";
import { desktopView } from "../../../frontend/src/desktopView";
import { AdminDesktop } from "../../../frontend/src/AdminActivity";
import TradingWorkspace from "./TradingWorkspace";

export default function WorkspaceClient() {
  useEffect(registerOfflineShell, []);
  return <AccessGate redesigned>{(trader, signOut) => {
    if (desktopView() === "admin") return <AdminDesktop allowed={Boolean(trader?.admin)} />;
    if (!trader) return <Workspace trader={null} />;
    return <TradingWorkspace key={trader.workspace_id} trader={trader} signOut={signOut} />;
  }}</AccessGate>;
}

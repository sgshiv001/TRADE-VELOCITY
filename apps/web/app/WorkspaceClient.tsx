"use client";

import { useEffect } from "react";
import AccessGate from "../../../frontend/src/AccessGate";
import { registerOfflineShell } from "../../../frontend/src/install";
import { desktopView } from "../../../frontend/src/desktopView";
import { AdminDesktop } from "../../../frontend/src/AdminActivity";
import TradingWorkspace from "./TradingWorkspace";

export default function WorkspaceClient() {
  useEffect(registerOfflineShell, []);
  return <AccessGate redesigned>{(trader, signOut) => desktopView() === "admin"
    ? <AdminDesktop allowed={Boolean(trader?.admin)} />
    : <TradingWorkspace key={trader?.workspace_id ?? "local"} trader={trader} signOut={signOut} />}</AccessGate>;
}

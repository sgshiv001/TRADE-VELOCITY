"use client";

import { useEffect } from "react";
import AccessGate from "../../../frontend/src/AccessGate";
import Workspace from "../../../frontend/src/Workspace";
import { registerOfflineShell } from "../../../frontend/src/install";
import FundedChart from "./FundedChart";
import { desktopView } from "../../../frontend/src/desktopView";
import { AdminDesktop } from "../../../frontend/src/AdminActivity";

export default function WorkspaceClient() {
  useEffect(registerOfflineShell, []);
  return <AccessGate>{trader => desktopView() === "admin"
    ? <AdminDesktop allowed={Boolean(trader?.admin)} />
    : <Workspace key={trader?.workspace_id ?? "local"} trader={trader} Chart={FundedChart} />}</AccessGate>;
}

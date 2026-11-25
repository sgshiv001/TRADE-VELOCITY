"use client";

import { useEffect } from "react";
import AccessGate from "../../../frontend/src/AccessGate";
import Workspace from "../../../frontend/src/Workspace";
import { registerOfflineShell } from "../../../frontend/src/install";
import FundedChart from "./FundedChart";

export default function WorkspaceClient() {
  useEffect(registerOfflineShell, []);
  return <AccessGate>{trader => <Workspace key={trader?.workspace_id ?? "local"} trader={trader} Chart={FundedChart} />}</AccessGate>;
}

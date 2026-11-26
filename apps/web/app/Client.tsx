"use client";

import dynamic from "next/dynamic";

const WorkspaceClient = dynamic(() => import("./WorkspaceClient"), {
  ssr: false,
  loading: () => <main className="tv2 tv2-boot" role="status">Connecting to TradeVelocity…</main>,
});
export default WorkspaceClient;

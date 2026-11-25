"use client";

import dynamic from "next/dynamic";

const WorkspaceClient = dynamic(() => import("./WorkspaceClient"), {
  ssr: false,
  loading: () => <main className="tv:mx-auto tv:max-w-xl tv:p-8" role="status">Connecting to TradeVelocity…</main>,
});
export default WorkspaceClient;

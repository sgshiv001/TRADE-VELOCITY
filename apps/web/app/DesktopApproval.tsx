"use client";

import { useState, type ReactNode } from "react";
import { type Trader } from "../../../frontend/src/AccessGate";
import { api } from "../../../frontend/src/api";
import type { Theme } from "./Appearance";
import { Brand } from "./Brand";

export default function DesktopApproval({trader, signOut, theme, themeControl}: {
  trader: Trader;
  signOut(): Promise<void>;
  theme: Theme;
  themeControl: ReactNode;
}) {
  const requestId = new URLSearchParams(location.search).get("request") ?? "";
  const validRequest = /^[A-Za-z0-9_-]{32}$/.test(requestId);
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [approved, setApproved] = useState(false);
  const [error, setError] = useState("");

  async function approve() {
    setBusy(true);
    setError("");
    try {
      await api("/auth/desktop/approve", {method: "POST", body: JSON.stringify({request_id: requestId, code})});
      setApproved(true);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Desktop sign-in could not be approved.");
    } finally {
      setBusy(false);
    }
  }

  return <main className="tv2 tv2-desktop-approval" data-tv-theme={theme}>
    <section className="tv2-surface" aria-labelledby="desktop-approval-title">
      <div className="tv2-panel-head"><Brand />{themeControl}</div>
      <h1 id="desktop-approval-title">{approved ? "Desktop sign-in approved" : "Connect the desktop app"}</h1>
      {approved ? <p role="status">Return to TradeVelocity on your computer. You can close this tab.</p>
        : !validRequest ? <p role="alert">Open the TradeVelocity desktop app to start a new sign-in.</p>
        : <>
          <p>You’re signed in as <strong>{trader.username}</strong>. Enter the eight-digit code shown in the desktop app to approve access.</p>
          <form onSubmit={event => { event.preventDefault(); void approve(); }}>
            <label>Desktop code
              <input inputMode="numeric" autoComplete="off" spellCheck={false} pattern="[0-9]{8}" required
                value={code} onChange={event => setCode(event.target.value.replace(/\D/g, "").slice(0, 8))} />
            </label>
            <button className="tv2-button" disabled={busy || code.length !== 8}>{busy ? "Approving…" : "Approve desktop sign-in"}</button>
          </form>
          {error && <p className="notice error" role="alert">{error}</p>}
          <button className="tv2-button tv2-outline" onClick={() => void signOut()}>Use another account</button>
        </>}
    </section>
  </main>;
}

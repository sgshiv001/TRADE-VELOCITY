import { useEffect, useState, type ReactNode } from "react";

type Access = { required: boolean; authenticated: boolean };

export default function AccessGate({children}: {children: ReactNode}) {
  const [access, setAccess] = useState<Access | null>(null);
  const [key, setKey] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function status() {
    try {
      const response = await fetch("/api/auth/status");
      if (!response.ok) throw new Error("Cannot check workspace access.");
      setAccess(await response.json()); setError("");
    } catch { setError("Cannot reach the workspace. Check the app server and retry."); }
  }
  useEffect(() => {
    void status();
    const expired = () => { setAccess({required:true, authenticated:false}); setKey(""); };
    window.addEventListener("tradevelocity-access-expired",expired);
    return () => window.removeEventListener("tradevelocity-access-expired",expired);
  },[]);
  async function signIn() {
    setBusy(true); setError("");
    try {
      const response = await fetch("/api/auth/login", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({access_key:key})});
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail ?? "Sign-in failed.");
      setKey(""); await status();
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Sign-in failed."); }
    finally { setBusy(false); }
  }
  if (access?.authenticated) return <>
    {access.required && <div className="access-strip"><span>Private single-operator workspace</span><button className="secondary-button" onClick={async () => {
      try { const response = await fetch("/api/auth/logout",{method:"POST"}); if (!response.ok) throw new Error(); setAccess({required:true,authenticated:false}); }
      catch { setError("Sign-out failed. Retry or close the browser."); }
    }}>Sign out</button>{error && <span role="alert">{error}</span>}</div>}
    {children}
  </>;
  return <main className="access-page"><section className="panel access-panel">
    <div className="eyebrow">TRADEVELOCITY · PRIVATE ACCESS</div><h1>{access ? "Unlock your workspace" : "Connecting to workspace"}</h1>
    {error && <p className="notice error" role="alert">{error}</p>}
    {access ? <form onSubmit={event => {event.preventDefault(); void signIn();}}>
      <label>Workspace access key<input aria-label="Workspace access key" type="password" autoComplete="current-password" required maxLength={1024} value={key} onChange={event => setKey(event.target.value)} /></label>
      <button className="primary-button" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
      <p className="fine-print">The key is never saved in browser storage. Sign-in uses a secure, HTTP-only session cookie. This is a private workspace, not a public brokerage.</p>
    </form> : <button className="secondary-button" onClick={() => void status()}>Retry connection</button>}
  </section></main>;
}

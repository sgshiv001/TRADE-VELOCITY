import { useEffect, useState, type ReactNode } from "react";
import { setAccountWorkspace } from "./api";
import ProductPage from "./ProductPage";
import { desktopView, workspaceRoute } from "./desktopView";

export type Trader = { username: string; workspace_id: string; tutorial_seen: boolean; admin?: boolean };
type Access = { required: boolean; authenticated: boolean; mode?: "accounts"; trader?: Trader | null };

export default function AccessGate({children}: {children: (trader: Trader | null) => ReactNode}) {
  const [access, setAccess] = useState<Access | null>(null);
  const [key, setKey] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const desktopAdmin = desktopView() === "admin";
  const signup = !desktopAdmin && access?.mode === "accounts" && window.location.pathname === "/signup";

  async function status() {
    try {
      const response = await fetch("/api/auth/status");
      if (!response.ok) throw new Error("Cannot check workspace access.");
      const next: Access = await response.json();
      setAccountWorkspace(next.trader?.workspace_id ?? null);
      if (next.mode === "accounts" && next.authenticated && ["/login", "/signup"].includes(window.location.pathname)) {
        window.history.replaceState(null, "", workspaceRoute("/app"));
      } else if (next.mode === "accounts" && !next.authenticated && window.location.pathname === "/app") {
        window.history.replaceState(null, "", workspaceRoute("/login"));
      }
      setAccess(next);
      setError("");
    } catch { setError("Cannot reach the workspace. Check the app server and retry."); }
  }
  useEffect(() => {
    void status();
    const expired = () => {
      setAccountWorkspace(null);
      setAccess(previous => previous ? {...previous, authenticated: false, trader: null} : previous);
      setKey("");
      setPassword("");
    };
    window.addEventListener("tradevelocity-access-expired",expired);
    return () => window.removeEventListener("tradevelocity-access-expired",expired);
  },[]);
  async function signIn() {
    setBusy(true); setError("");
    try {
      const body = access?.mode === "accounts" ? {username, password} : {access_key:key};
      const response = await fetch(signup ? "/api/auth/register" : "/api/auth/login", {
        method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail ?? "Sign-in failed.");
      setKey("");
      setPassword("");
      await status();
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Sign-in failed."); }
    finally { setBusy(false); }
  }
  if (access?.mode === "accounts" && window.location.pathname === "/") {
    return <ProductPage signedIn={access.authenticated} />;
  }
  if (access?.authenticated) return <>
    {access.required && <div className="access-strip"><span>{access.trader ? `Signed in as ${access.trader.username}` : "Private single-operator workspace"}</span><button className="secondary-button" onClick={async () => {
      try {
        const response = await fetch("/api/auth/logout", {method: "POST"});
        if (!response.ok) throw new Error();
        setAccountWorkspace(null);
        if (access.mode === "accounts") window.history.replaceState(null, "", workspaceRoute("/login"));
        setAccess({...access, authenticated: false, trader: null});
        setError("");
      }
      catch { setError("Sign-out failed. Retry or close the browser."); }
    }}>Sign out</button>{error && <span role="alert">{error}</span>}</div>}
    {children(access.trader ?? null)}
  </>;
  if (access?.mode === "accounts") return <main className="access-page">
    <section className="panel access-panel trader-access" aria-labelledby="access-heading">
      <div className="trader-access-brand"><img src="/favicon.svg" alt="" /><span>TRADEVELOCITY</span></div>
      <h1 id="access-heading">{desktopAdmin ? "Admin sign in" : signup ? "Create your account" : "Sign in"}</h1>
      <p>{desktopAdmin ? "Sign in with the authorized TradeVelocity administrator account." : "Use your demo demat account to trade with virtual cash and shares."}</p>
      {error && <p className="notice error" role="alert">{error}</p>}
      <form onSubmit={event => { event.preventDefault(); void signIn(); }}>
        <label>Username<input autoComplete="username" autoCapitalize="none" spellCheck={false} required
          minLength={3} maxLength={32} pattern="[A-Za-z0-9_]+" value={username}
          onChange={event => setUsername(event.target.value)} /></label>
        {signup && <p className="fine-print">Use 3–32 letters, numbers, or underscores.</p>}
        <label>Password<input type="password" autoComplete={signup ? "new-password" : "current-password"}
          required minLength={signup ? 12 : 1} maxLength={128} value={password}
          onChange={event => setPassword(event.target.value)} /></label>
        {signup && <p className="fine-print">Use at least 12 characters.</p>}
        <button className="primary-button" disabled={busy}>{busy ? "Please wait…" : signup ? "Create account" : "Sign in"}</button>
      </form>
      {!desktopAdmin && <p>{signup ? "Already have an account? " : "New to TradeVelocity? "}
        <a href={workspaceRoute(signup ? "/login" : "/signup")}>{signup ? "Sign in" : "Create an account"}</a>
      </p>}
    </section>
  </main>;
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

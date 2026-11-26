import { useEffect, useState, type ReactNode } from "react";
import { setAccountWorkspace } from "./api";
import ProductPage from "./ProductPage";
import { desktopView, workspaceRoute } from "./desktopView";

export type Trader = { username: string; workspace_id: string; tutorial_seen: boolean; admin?: boolean };
type Access = { required: boolean; authenticated: boolean; mode?: "accounts"; trader?: Trader | null;
  signup_verification_required?: boolean };

export default function AccessGate({children, redesigned = false, theme, themeControl, inDesktop = false}: {
  children: (trader: Trader | null, signOut: () => Promise<void>) => ReactNode;
  redesigned?: boolean;
  theme?: "light" | "dark";
  themeControl?: ReactNode;
  inDesktop?: boolean;
}) {
  const [access, setAccess] = useState<Access | null>(null);
  const [key, setKey] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState("");
  const [verificationToken, setVerificationToken] = useState("");
  const [emailCode, setEmailCode] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const desktopAdmin = desktopView() === "admin";
  const desktopApproval = redesigned && window.location.pathname === "/desktop-sign-in";
  const signup = !desktopAdmin && access?.mode === "accounts" && window.location.pathname === "/signup";
  const verifySignup = signup && access?.signup_verification_required;
  const enteringCodes = verifySignup && Boolean(verificationToken);

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
  async function requestEmailCode() {
    setBusy(true); setError("");
    try {
      const response = await fetch("/api/auth/signup/start", {
        method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({username: username.trim(), email: email.trim()}),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail ?? "Could not send the email code.");
      setVerificationToken(result.verification_token);
      setEmailCode("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not send the email code."); }
    finally { setBusy(false); }
  }
  async function signIn() {
    if (verifySignup && !verificationToken) return requestEmailCode();
    setBusy(true); setError("");
    try {
      const body = access?.mode === "accounts" ? {username, password, ...(verifySignup ? {
        verification_token: verificationToken, email_code: emailCode,
      } : {})} : {access_key:key};
      const response = await fetch(signup ? "/api/auth/register" : "/api/auth/login", {
        method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail ?? "Sign-in failed.");
      setKey("");
      setPassword("");
      setEmail("");
      setVerificationToken("");
      setEmailCode("");
      await status();
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Sign-in failed."); }
    finally { setBusy(false); }
  }
  async function signOut() {
    try {
      const response = await fetch("/api/auth/logout", {method: "POST"});
      if (!response.ok) throw new Error();
      setAccountWorkspace(null);
      if (access?.mode === "accounts" && !desktopApproval) window.history.replaceState(null, "", workspaceRoute("/login"));
      setAccess(previous => previous ? {...previous, authenticated: false, trader: null} : previous);
      setError("");
    } catch { setError("Sign-out failed. Retry or close the browser."); }
  }
  if (access?.mode === "accounts" && window.location.pathname === "/") {
    return <ProductPage signedIn={access.authenticated} />;
  }
  if (access?.authenticated) return <>
    {access.required && (!redesigned || desktopAdmin) && <div className="access-strip" data-access-theme={theme}><span>{access.trader ? `Signed in as ${access.trader.username}` : "Private single-operator workspace"}</span><button className="secondary-button" onClick={() => void signOut()}>Sign out</button>{error && <span role="alert">{error}</span>}</div>}
    {redesigned && !desktopAdmin && error && <p className="notice error" role="alert">{error}</p>}
    {children(access.trader ?? null, signOut)}
  </>;
  if (access?.mode === "accounts") return <main className={redesigned ? "tv2 tv2-access" : "access-page"} data-tv-theme={theme}>
    {redesigned && <aside className="tv2-auth-intro"><a className="tv2-brand" href="/"><img src="/tv-mark.svg" alt="" width={36} height={36} /><span>TradeVelocity</span></a>
      <h2>{desktopAdmin ? "TradeVelocity administration" : "Intelligence behind every trade."}</h2>
      <p>{desktopAdmin ? "Monitor active accounts and service status." : "Research markets and practise trading with a virtual portfolio."}</p></aside>}
    <section className="panel access-panel trader-access" aria-labelledby="access-heading">
      {!redesigned && <div className="trader-access-brand"><img src="/favicon.svg" alt="" /><span>TRADEVELOCITY</span></div>}
      <h1 id="access-heading">{desktopAdmin ? "Admin sign in" : signup ? "Create your account" : "Sign in"}</h1>
      <p>{desktopApproval ? "Sign in to approve the request from your desktop app."
        : desktopAdmin ? "Sign in with the authorized TradeVelocity administrator account." : "Use your demo demat account to trade with virtual cash and shares."}</p>
      {themeControl}
      {error && <p className="notice error" role="alert">{error}</p>}
      {inDesktop ? <p><a className="tv2-button" href="tradevelocity-local:signin">Continue in browser</a></p>
        : <form onSubmit={event => { event.preventDefault(); void signIn(); }}>
        {enteringCodes ? <>
          <p role="status">Enter the code sent to your email. It expires after 10 minutes.</p>
          <label>Email code<input inputMode="numeric" autoComplete="one-time-code" required pattern="[0-9]{6}" maxLength={6}
            value={emailCode} onChange={event => setEmailCode(event.target.value)} /></label>
        </> : <>
          <label>Username<input autoComplete="username" autoCapitalize="none" spellCheck={false} required disabled={busy}
            minLength={3} maxLength={32} pattern="[A-Za-z0-9_]+" value={username}
            onChange={event => setUsername(event.target.value)} /></label>
          {signup && <p className="fine-print">Use 3–32 letters, numbers, or underscores.</p>}
          <label>Password<input type="password" autoComplete={signup ? "new-password" : "current-password"} disabled={busy}
            required minLength={signup ? 12 : 1} maxLength={128} value={password}
            onChange={event => setPassword(event.target.value)} /></label>
          {signup && <p className="fine-print">Use at least 12 characters.</p>}
          {verifySignup &&
            <label>Email<input type="email" autoComplete="email" required maxLength={254} disabled={busy}
              value={email} onChange={event => setEmail(event.target.value)} /></label>}
        </>}
        <button className="primary-button" disabled={busy}>{busy ? "Please wait…" : verifySignup && !enteringCodes
          ? "Send email code" : signup ? "Create account" : "Sign in"}</button>
        {enteringCodes && <>
          <button className="secondary-button" type="button" disabled={busy} onClick={() => void requestEmailCode()}>Send a new code</button>
          <button className="secondary-button" type="button" disabled={busy} onClick={() => {
            setVerificationToken(""); setEmailCode(""); setError("");
          }}>Edit email</button>
        </>}
      </form>}
      {!desktopAdmin && !desktopApproval && !inDesktop && <p>{signup ? "Already have an account? " : "New to TradeVelocity? "}
        <a href={workspaceRoute(signup ? "/login" : "/signup")}>{signup ? "Sign in" : "Create an account"}</a>
      </p>}
    </section>
  </main>;
  if (redesigned && !access) return <main className="tv2 tv2-boot" data-tv-theme={theme}>
    {error ? <><p role="alert">{error}</p><button className="tv2-button" onClick={() => void status()}>Retry connection</button></>
      : <p role="status">Connecting to TradeVelocity…</p>}
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

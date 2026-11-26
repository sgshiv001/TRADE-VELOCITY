import { useEffect, useState, type ReactNode } from "react";
import { api, number, tradeTime } from "./api";
import { ThemeToggle } from "./Trading";

type Activity = {
  registered: number;
  active: number;
  active_today: number;
  active_seconds: number;
  users: { username: string; active: boolean; last_active_at: string | null; orders: number; executions: number }[];
};
type ServiceStatus = {
  server: "Responding" | "Unavailable";
  database: "Ready" | "Unavailable";
  version: string | null;
  storage: string | null;
  checkedAt: string;
};

function ServiceHealth() {
  const [status, setStatus] = useState<ServiceStatus | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    let timer = 0;
    async function refresh() {
      const [health, ready] = await Promise.allSettled([
        api<{version: string; storage: string}>("/health", {signal: controller.signal, timeoutMs: 5000}),
        api<{status: string; storage: string}>("/ready", {signal: controller.signal, timeoutMs: 5000}),
      ]);
      if (controller.signal.aborted) return;
      const connected = health.status === "fulfilled";
      const databaseReady = ready.status === "fulfilled" && ready.value.status === "ready";
      setStatus({server: connected ? "Responding" : "Unavailable",
        database: databaseReady ? "Ready" : "Unavailable",
        version: connected ? health.value.version : null,
        storage: databaseReady ? ready.value.storage : null,
        checkedAt: new Date().toLocaleTimeString()});
      timer = window.setTimeout(refresh, 15_000);
    }
    void refresh();
    return () => { controller.abort(); window.clearTimeout(timer); };
  }, []);
  return <section className="panel" aria-label="Service health">
    <div className="panel-heading"><h2>Service status</h2><span className="fine-print">{status ? `Checked at ${status.checkedAt}` : "Checking…"}</span></div>
    <div className="metric-grid activity-metrics">
      <div className="metric-card"><span className="metric-head">Application</span><strong className="metric-value">{status?.server ?? "—"}</strong></div>
      <div className="metric-card"><span className="metric-head">Database</span><strong className="metric-value">{status?.database ?? "—"}</strong><span>{status?.storage ?? ""}</span></div>
      <div className="metric-card"><span className="metric-head">App version</span><strong className="metric-value">{status?.version ?? "—"}</strong></div>
    </div>
  </section>;
}

export function AdminDesktop({allowed, themeControl}: {allowed: boolean; themeControl?: ReactNode}) {
  useTraderActivity(allowed);
  return <main className="admin-desktop">
    <div className="admin-desktop-header">
      <div className="admin-desktop-brand"><img src="/favicon.svg" width={36} height={36} alt="" /><strong>TradeVelocity Admin</strong></div>
      {themeControl ?? <ThemeToggle />}
    </div>
    {allowed ? <AdminActivity /> : <section className="panel"><h1>Administrator access required</h1>
      <p>Your current login is a trader account. Use Sign out above, then sign in with the authorized administrator account.</p></section>}
  </main>;
}

export function useTraderActivity(enabled: boolean) {
  useEffect(() => {
    if (!enabled) return;
    let lastInteraction = Date.now();
    let lastSent = 0;
    function send() {
      const now = Date.now();
      if (document.hidden || now - lastInteraction > 60_000 || now - lastSent < 25_000) return;
      lastSent = now;
      void api("/auth/activity", {method: "POST"}).catch(() => {});
    }
    function interact() {
      lastInteraction = Date.now();
      send();
    }
    const events = ["pointerdown", "touchstart", "keydown", "wheel"] as const;
    for (const event of events) window.addEventListener(event, interact, {passive: true});
    document.addEventListener("visibilitychange", interact);
    const timer = window.setInterval(send, 30_000);
    send();
    return () => {
      for (const event of events) window.removeEventListener(event, interact);
      document.removeEventListener("visibilitychange", interact);
      window.clearInterval(timer);
    };
  }, [enabled]);
}

export default function AdminActivity() {
  const [activity, setActivity] = useState<Activity | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let stopped = false;
    let timer = 0;
    const controller = new AbortController();
    async function refresh() {
      try {
        const data = await api<Activity>("/admin/activity", {signal: controller.signal});
        if (!stopped) { setActivity(data); setError(""); }
      } catch (cause) {
        if (!stopped) setError(cause instanceof Error ? cause.message : "Could not load user activity.");
      } finally {
        if (!stopped) timer = window.setTimeout(refresh, 15_000);
      }
    }
    void refresh();
    return () => { stopped = true; controller.abort(); window.clearTimeout(timer); };
  }, []);
  return <>
    <div className="section-title"><div><h1>Admin activity</h1>
      <p>Activity refreshes every 15 seconds. Active users sent a signal from a visible workspace in the last {activity?.active_seconds ?? 90} seconds.</p></div></div>
    <ServiceHealth />
    {error && <p className="notice error" role="alert">{error}</p>}
    {activity ? <>
      <div className="metric-grid activity-metrics">
        <div className="metric-card"><span className="metric-head">Recently active</span><strong className="metric-value">{number(activity.active)}</strong></div>
        <div className="metric-card"><span className="metric-head">Active in 24 hours</span><strong className="metric-value">{number(activity.active_today)}</strong></div>
        <div className="metric-card"><span className="metric-head">Registered accounts</span><strong className="metric-value">{number(activity.registered)}</strong></div>
      </div>
      <section className="panel"><h2>Trader activity</h2>
        <div className="table-scroll"><table className="data-table"><thead><tr><th>ACCOUNT</th><th>STATUS</th><th>LAST ACTIVE</th><th>SHARED ORDERS</th><th>FILLS</th></tr></thead>
          <tbody>{activity.users.map(user => <tr key={user.username}><td>{user.username}</td><td className={user.active ? "success-text" : undefined}>{user.active ? "Active" : "Idle"}</td><td>{user.last_active_at ? tradeTime(user.last_active_at) : "No activity recorded"}</td><td>{number(user.orders)}</td><td>{number(user.executions)}</td></tr>)}</tbody>
        </table></div>
      </section>
    </> : !error && <p role="status">Loading activity…</p>}
  </>;
}

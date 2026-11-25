import { useEffect, useState } from "react";
import { api, number, tradeTime } from "./api";

type Activity = {
  registered: number;
  active: number;
  active_today: number;
  active_seconds: number;
  users: { username: string; active: boolean; last_active_at: string | null; orders: number; executions: number }[];
};

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

import { useEffect, useRef, useState, type FormEvent } from "react";
import { Moon, Sun, Play, RefreshCw, ShieldCheck, Download } from "lucide-react";
import { api, download, inr, number } from "./api";
import type { Measurement, Lab, Order } from "./types";

const message = (error: unknown) => error instanceof Error ? error.message : "Could not complete the request.";
type OrderResult = { order_id: string; filled: number; remaining: number; resting: boolean };
type AlertReview = { status: "open" | "reviewed" | "dismissed"; note: string };
type WatchdogReport = { status: string; observations: number; baseline_size: number; flagged: number; open_alerts: number; scored?: number; model_version: string; method: string; calibration: { fit_observations: number; cutoff_observations: number; forest_threshold?: number; robust_threshold?: number; baseline_warning?: string }; alerts: { event: number; order_id: string; price: number; quantity: number; score: number; reasons: string[]; detectors: string[]; review: AlertReview }[]; note: string };

export function ThemeToggle() {
  const [theme, setTheme] = useState(() => localStorage.getItem("tradevelocity-theme") === "dark" ? "dark" : "light");
  useEffect(() => { document.documentElement.dataset.theme = theme; localStorage.setItem("tradevelocity-theme", theme); }, [theme]);
  return <button className="theme-toggle" aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`} onClick={() => setTheme(theme === "light" ? "dark" : "light")}>{theme === "light" ? <Moon size={16} /> : <Sun size={16} />}<span>{theme === "light" ? "Dark" : "Light"} mode</span></button>;
}

export function OrderTicket({ symbol, lab, changed }: { symbol: string; lab: Lab; changed: () => Promise<void> }) {
  const [side, setSide] = useState("BUY"), [quantity, setQuantity] = useState(1), [price, setPrice] = useState("");
  const [kind, setKind] = useState("limit"), [busy, setBusy] = useState(false), [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [editing, setEditing] = useState<Order | null>(null);
  const [editQuantity, setEditQuantity] = useState(1), [editPrice, setEditPrice] = useState("");
  const pending = useRef<{intent: string; body: string; key: string} | null>(null);
  const describe = (result: OrderResult) => `${result.order_id}: ${result.filled} shares filled · ${result.remaining} unfilled · ${result.resting ? "resting on book" : "not resting"}`;
  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(""); setNotice("");
    try {
      const intent = JSON.stringify({symbol, side, quantity, price: kind === "market" ? null : price});
      if (pending.current && pending.current.intent !== intent) throw new Error("The previous order is not confirmed. Restore its inputs and retry it before submitting a different order.");
      pending.current ??= {intent, body: JSON.stringify({order_id: `TV-${crypto.randomUUID()}`, ...JSON.parse(intent)}), key: crypto.randomUUID()};
      const result = await api<OrderResult>("/lab/orders", { method: "POST", body: pending.current.body, requestKey: pending.current.key });
      pending.current = null; setNotice(describe(result)); await changed();
    }
    catch (cause) { setError(message(cause)); } finally { setBusy(false); }
  }
  async function cancel(id: string) {
    setBusy(true); setError("");
    try { await api(`/lab/orders/${encodeURIComponent(id)}`, { method: "DELETE" }); setNotice(`Cancelled ${id}`); if (editing?.order_id === id) setEditing(null); await changed(); }
    catch (cause) { setError(message(cause)); } finally { setBusy(false); }
  }
  async function amend(event: FormEvent) {
    event.preventDefault(); if (!editing) return; setBusy(true); setError("");
    try { const result = await api<OrderResult>(`/lab/orders/${encodeURIComponent(editing.order_id)}`, { method: "PATCH", body: JSON.stringify({ quantity: editQuantity, price: editPrice }) }); setNotice(`Amended ${describe(result)}`); setEditing(null); await changed(); }
    catch (cause) { setError(message(cause)); } finally { setBusy(false); }
  }
  const orders = lab.orders.filter(order => order.symbol === symbol);
  return <section className="panel"><div className="panel-heading"><div><div className="eyebrow">LOCAL ORDER ENTRY</div><h2>Place an order · {symbol}</h2></div><span className="venue-label">OWN MATCHING ENGINE</span></div>
    <form onSubmit={submit}><fieldset className="ticket-grid" disabled={busy}>
      <label>Side<select value={side} onChange={event => setSide(event.target.value)}><option>BUY</option><option>SELL</option></select></label>
      <label>Type<select value={kind} onChange={event => setKind(event.target.value)}><option value="limit">Limit</option><option value="market">Market</option></select></label>
      <label>Shares<input type="number" required min="1" max="1000000" step="1" value={quantity} onChange={event => setQuantity(Number(event.target.value))} /></label>
      <label>Limit price<input aria-label="Limit price" type="number" required={kind === "limit"} disabled={kind === "market"} min="0.01" step="0.01" placeholder="Enter a price" value={price} onChange={event => setPrice(event.target.value)} /></label>
      <button className="primary-button" type="submit">{busy ? "Processing…" : `Submit ${side.toLowerCase()}`}</button>
    </fieldset></form>
    {notice && <p className="notice" role="status">{notice}</p>}{error && <p className="notice error" role="alert">{error}</p>}
    {editing && <form onSubmit={amend} className="order-amend"><h3>Amend {editing.order_id}</h3><p className="fine-print">This sets the new remaining quantity and price, resets time priority, and may match immediately.</p><fieldset className="ticket-grid" disabled={busy}><label>New remaining shares<input aria-label="New remaining shares" type="number" required min="1" max="1000000" step="1" value={editQuantity} onChange={event => setEditQuantity(Number(event.target.value))} /></label><label>New limit price<input aria-label="New limit price" type="number" required min="0.01" step="0.01" value={editPrice} onChange={event => setEditPrice(event.target.value)} /></label><button className="primary-button" type="submit">Save amendment</button><button className="secondary-button" type="button" onClick={() => setEditing(null)}>Keep current order</button></fieldset></form>}
    <h3>Active orders · {orders.length}</h3>{orders.length ? <div className="table-scroll"><table className="data-table"><thead><tr><th>ORDER</th><th>SIDE</th><th>PRICE</th><th>REMAINING</th><th>ACTIONS</th></tr></thead><tbody>{orders.map(order => <tr key={order.order_id}><td>{order.order_id}</td><td>{order.side}</td><td>{inr(order.price)}</td><td>{number(order.remaining)}</td><td><div className="title-actions"><button className="secondary-button" disabled={busy} onClick={() => { setEditing(order); setEditQuantity(order.remaining); setEditPrice(order.price); }}>Amend</button><button className="secondary-button" disabled={busy} onClick={() => void cancel(order.order_id)}>Cancel order</button></div></td></tr>)}</tbody></table></div> : <p className="workspace-copy">No active orders for this symbol.</p>}
    <p className="fine-print">No automatic counterparties or broker execution. Market orders need opposite-side orders in this book; any unfilled quantity expires.</p>
  </section>;
}

export function SessionTools({ changed }: { changed: () => Promise<void> }) {
  const [confirm, setConfirm] = useState(false), [error, setError] = useState("");
  const [busy, setBusy] = useState(false), [notice, setNotice] = useState("");
  const [imported, setImported] = useState<{ version: number; events: unknown[] } | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  async function reset() { setBusy(true); setError(""); try { await api("/lab/reset", { method: "POST" }); await changed(); setConfirm(false); setNotice("Matching session cleared."); } catch (cause) { setError(message(cause)); } finally { setBusy(false); } }
  async function exportSession() { setBusy(true); try { download("tradevelocity-session.json", await api("/lab/export")); setError(""); } catch (cause) { setError(message(cause)); } finally { setBusy(false); } }
  async function readFile(file?: File) {
    setError(""); setImported(null); setConfirm(false);
    if (!file) return;
    try { if (file.size > 50_000_000) throw new Error("Session files must be smaller than 50 MB."); const payload = JSON.parse(await file.text()); if (![1,2].includes(payload.version) || !Array.isArray(payload.events)) throw new Error("Choose an exported TradeVelocity session JSON file."); setImported(payload); }
    catch (cause) { setError(message(cause)); }
    finally { if (fileInput.current) fileInput.current.value = ""; }
  }
  async function importSession() { setBusy(true); setError(""); try { await api("/lab/import", { method: "POST", body: JSON.stringify(imported) }); await changed(); setImported(null); setNotice("Session imported and replayed by the engine."); } catch (cause) { setError(message(cause)); } finally { setBusy(false); } }
  return <section className="panel"><div className="panel-heading"><div><div className="eyebrow">PERSISTENT WORKSPACE</div><h2>Your session, your records</h2><p className="fine-print">Orders are saved automatically. Export all commands or restore an exported session.</p></div><div className="title-actions"><button className="secondary-button" disabled={busy} onClick={() => void exportSession()}><Download size={15} /> Export session</button><button className="secondary-button" disabled={busy} onClick={() => fileInput.current?.click()}>Import session</button><button className="secondary-button" disabled={busy} onClick={() => { setConfirm(true); setImported(null); }}>Clear session</button><input ref={fileInput} type="file" accept=".json,application/json" hidden aria-label="Import session file" onChange={event => void readFile(event.target.files?.[0])} /></div></div>
    {confirm && <div className="confirmation"><p>Clear all orders and trade history in this session? Export first to keep your records.</p><button className="primary-button" disabled={busy} onClick={() => void reset()}>Confirm clear session</button><button className="secondary-button" disabled={busy} onClick={() => setConfirm(false)}>Keep session</button></div>}
    {imported && <div className="confirmation"><p>Replay {number(imported.events.length)} commands and replace the current orders and history? Export your current session first if needed.</p><button className="primary-button" disabled={busy} onClick={() => void importSession()}>Replace and import</button><button className="secondary-button" disabled={busy} onClick={() => setImported(null)}>Keep session</button></div>}
    {notice && <p className="notice" role="status">{notice}</p>}{error && <p className="notice error" role="alert">{error}</p>}
  </section>;
}

export function Watchdog({ symbol }: { symbol: string }) {
  const [report, setReport] = useState<WatchdogReport | null>(null), [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [reviewEvent, setReviewEvent] = useState<number | null>(null);
  const [review, setReview] = useState<AlertReview>({status: "reviewed", note: ""});
  const [saving, setSaving] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  const generation = useRef(0);
  async function refresh() {
    const current = ++generation.current; setBusy(true);
    try { const result = await api<WatchdogReport>(`/lab/watchdog?symbol=${encodeURIComponent(symbol)}`); if (current === generation.current) { setReport(result); setError(""); setLastUpdate(new Date().toLocaleTimeString()); } }
    catch (cause) { if (current === generation.current) setError(message(cause)); }
    finally { if (current === generation.current) setBusy(false); }
  }
  useEffect(() => { setReport(null); setReviewEvent(null); setLastUpdate(null); void refresh(); const timer = window.setInterval(refresh, 10000); return () => { window.clearInterval(timer); generation.current++; }; }, [symbol]);
  async function saveReview(event: FormEvent) {
    event.preventDefault(); setSaving(true); setError("");
    try { await api(`/lab/watchdog/reviews/${reviewEvent}?symbol=${encodeURIComponent(symbol)}`, {method: "PATCH", body: JSON.stringify(review)}); setReviewEvent(null); await refresh(); }
    catch (cause) { setError(message(cause)); } finally { setSaving(false); }
  }
  return <>
    <div className="section-title"><div><div className="eyebrow">AI EXECUTION MONITOR</div><h1>Market watchdog · {symbol}</h1><p>Review unusual activity from your submitted and matched orders.</p></div><div className="title-actions"><button className="secondary-button" disabled={busy} onClick={() => void refresh()}><RefreshCw size={15} className={busy ? "spin" : ""} /> Refresh</button><button className="secondary-button" disabled={!report} onClick={() => download("tradevelocity-watchdog.json", report)}><Download size={15} /> Export report</button></div></div>
    <div className="notice"><ShieldCheck size={18} /> AI monitors engine executions without changing matching decisions. Alerts suggest review, not proven fraud.</div>
    {report && <p className="fine-print">{report.method} · {report.model_version} · {report.calibration.fit_observations} fit observations + {report.calibration.cutoff_observations} cutoff observations. {report.calibration.baseline_warning} Scores are severity, not fraud probabilities.</p>}
    {error && <p className="notice error" role="alert">{error}</p>}
    <p className="fine-print">Last successful monitor refresh: {lastUpdate ?? "—"}{error && " · Report may be stale"}. {report ? `${report.flagged} total flagged; ${report.open_alerts} open in the latest 100-alert queue.` : "Waiting for a report."}</p>
    <div className="metric-grid four">{[["Executed-order observations", report?.observations ?? "—"], ["Baseline required", report?.baseline_size ?? 40], ["Later observations scored", report ? report.scored ?? 0 : "—"], ["Open review queue", report?.open_alerts ?? "—"]].map(([label, value]) => <div className="metric-card" key={label}><span className="metric-head">{label}</span><strong className="metric-value">{value}</strong></div>)}</div>
    <section className="panel"><div className="panel-heading"><div><div className="eyebrow">TRACEABLE ALERTS</div><h2>{report?.status === "warming_up" ? "Building the baseline" : "Execution review queue"}</h2></div><span className="venue-label">{report ? report.status === "monitoring" ? "MONITORING" : "WARMING UP" : "CONNECTING"}</span></div>
      {reviewEvent !== null && <form className="review-editor" onSubmit={saveReview}><h3>Review execution #{reviewEvent}</h3><label>Status<select aria-label="Review status" value={review.status} onChange={event => setReview({...review, status: event.target.value as AlertReview["status"]})}><option value="open">Open</option><option value="reviewed">Reviewed</option><option value="dismissed">Dismissed</option></select></label><label>Investigation notes<textarea aria-label="Investigation notes" maxLength={2000} value={review.note} onChange={event => setReview({...review, note: event.target.value})} /></label><div className="title-actions"><button className="primary-button" disabled={saving}>Save review</button><button className="secondary-button" type="button" disabled={saving} onClick={() => setReviewEvent(null)}>Keep current review</button></div></form>}
      {report?.alerts.length ? <div className="table-scroll"><table className="data-table"><thead><tr><th>EVENT / ORDER</th><th>PRICE</th><th>SHARES</th><th>SEVERITY</th><th>UNUSUAL MEASUREMENTS / DETECTORS</th><th>REVIEW</th></tr></thead><tbody>{report.alerts.slice().reverse().map(row => <tr key={row.event}><td>#{row.event} · {row.order_id}</td><td>{inr(row.price)}</td><td>{number(row.quantity)}</td><td>{row.score.toFixed(2)}</td><td>{row.reasons.join(", ").replaceAll("_", " ")}<p className="fine-print">{row.detectors.join(" + ").replaceAll("_", " ")}</p></td><td><span className="review-tag">{row.review.status}</span><p className="fine-print">{row.review.note}</p><button className="secondary-button" disabled={saving} onClick={() => { setReviewEvent(row.event); setReview(row.review.status === "open" ? {...row.review,status:"reviewed"} : row.review); }}>Review #{row.event}</button></td></tr>)}</tbody></table></div> : <div className="empty"><ShieldCheck size={30} /><strong>{report?.status === "monitoring" ? "No flagged executions" : "Waiting for executed orders"}</strong><p>{report?.observations ?? 0} observations collected. The first 40 establish a baseline; only later observations are scored.</p></div>}
      <p className="fine-print">{report?.note} The baseline's normality is an assumption. Listed measurements are deviations, not causal explanations, and scores are not probabilities.</p>
    </section>
  </>;
}

export function RealBenchmark() {
  const [rows, setRows] = useState<Measurement[]>([]), [busy, setBusy] = useState(false), [error, setError] = useState("");
  const [workload, setWorkload] = useState("mixed"), [count, setCount] = useState(1000);
  async function run() { setBusy(true); setError(""); try { setRows(await api<Measurement[]>("/experiments", { method: "POST", body: JSON.stringify({ workload, count }) })); } catch (cause) { setError(message(cause)); } finally { setBusy(false); } }
  return <><div className="section-title"><div><div className="eyebrow">ISOLATED ENGINE MEASUREMENTS</div><h1>Performance</h1><p>Compare indexed and linear books without changing your active session.</p></div><button className="secondary-button" disabled={!rows.length} onClick={() => download("tradevelocity-benchmark.json", rows)}><Download size={15} /> Export results</button></div><section className="panel"><div className="benchmark-controls"><label>Workload<select disabled={busy} value={workload} onChange={event => setWorkload(event.target.value)}><option value="mixed">Order submission & matching</option><option value="deep">Deep-book matching</option><option value="cancel">Cancellation</option></select></label><label>Commands<select disabled={busy} value={count} onChange={event => setCount(Number(event.target.value))}>{[100, 1000, 5000].map(value => <option key={value} value={value}>{number(value)}</option>)}</select></label><button className="primary-button" disabled={busy} onClick={() => void run()}>{busy ? <RefreshCw className="spin" size={16} /> : <Play size={16} />}{busy ? "Measuring…" : "Run benchmark"}</button></div><p className="fine-print">Generated measurement workloads run in isolated engines, never your orders. Three repetitions, checked for identical matching outcomes before timing. Throughput is machine-dependent.</p>{error && <p className="notice error" role="alert">{error}</p>}{rows.length ? <div className="table-scroll"><table className="data-table"><thead><tr><th>ENGINE</th><th>WORKLOAD</th><th>REPEAT</th><th>COMMANDS</th><th>SECONDS</th><th>COMMANDS / SEC</th><th>TRADES</th></tr></thead><tbody>{rows.map((row, index) => <tr key={index}><td>{row.engine}</td><td>{row.workload}</td><td>{row.repeat}</td><td>{number(row.commands)}</td><td>{row.seconds.toFixed(5)}</td><td>{number(Math.round(row.commands_per_second))}</td><td>{number(row.trades)}</td></tr>)}</tbody></table></div> : <p className="workspace-copy">Choose a workload to measure this machine. No fabricated results are displayed.</p>}</section></>;
}

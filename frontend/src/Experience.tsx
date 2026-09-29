import { useEffect, useState } from "react";
import { Moon, Sun, Play, RefreshCw, ShieldCheck, Download, AlertTriangle } from "lucide-react";
import { api, download, inr, number } from "./api";
import type { Measurement, Lab } from "./types";

type Observation = { event: number; order_id: string; timestamp: string; price: number; quantity: number; score: number; needs_review: boolean; reasons: string[]; trade_ids: number[] };
type WatchdogReport = { status: string; observations: number; baseline_size: number; flagged: number; scored?: number; alerts: Observation[]; timeline: Observation[]; note: string };
type Evaluation = { training: number; heldout: number; true_positives: number; false_positives: number; false_negatives: number; true_negatives: number; precision: number; recall: number; note: string };
type SimulationResult = { commands: number; filled_shares: number; trades: number; seconds: number; commands_per_second: number; note: string };
const message = (error: unknown) => error instanceof Error ? error.message : "Something went wrong. Please try again.";

export function ThemeToggle() {
  const [theme, setTheme] = useState(() => localStorage.getItem("tradevelocity-theme") === "dark" ? "dark" : "light");
  useEffect(() => { document.documentElement.dataset.theme = theme; localStorage.setItem("tradevelocity-theme", theme); }, [theme]);
  return <button className="theme-toggle" aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`} onClick={() => setTheme(theme === "light" ? "dark" : "light")}>{theme === "light" ? <Moon size={16} /> : <Sun size={16} />}<span>{theme === "light" ? "Dark" : "Light"} mode</span></button>;
}

export function OrderTicket({ symbol, lab, changed }: { symbol: string; lab: Lab | null; changed: () => void }) {
  const [side, setSide] = useState("BUY"), [quantity, setQuantity] = useState(25), [price, setPrice] = useState("100.00");
  const [kind, setKind] = useState("limit"), [busy, setBusy] = useState(false), [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  async function submit(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError(""); setNotice("");
    try { const result = await api<{ order_id: string; filled: number; remaining: number; resting: boolean }>("/lab/orders", { method: "POST", body: JSON.stringify({ order_id: `TV-${crypto.randomUUID()}`, symbol, side, quantity, price: kind === "market" ? null : price }) });
      setNotice(`${result.filled} shares filled · ${result.remaining} unfilled · ${result.resting ? "resting on book" : "not resting"}`); changed();
    } catch (cause) { setError(message(cause)); } finally { setBusy(false); }
  }
  async function cancel(id: string) {
    setBusy(true); setError("");
    try { await api(`/lab/orders/${encodeURIComponent(id)}`, { method: "DELETE" }); changed(); setNotice(`Cancelled ${id}`); }
    catch (cause) { setError(message(cause)); } finally { setBusy(false); }
  }
  const orders = (lab?.orders ?? []).filter(row => row.symbol === symbol);
  return <section className="panel"><div className="panel-heading"><div><div className="eyebrow">INTERACTIVE PAPER ORDER</div><h2>Place an order · {symbol}</h2></div><span className="lab-badge">NO REAL MONEY</span></div><form onSubmit={submit}><fieldset className="ticket-grid" disabled={busy}>
    <label>Side<select value={side} onChange={e => setSide(e.target.value)}><option>BUY</option><option>SELL</option></select></label>
    <label>Type<select value={kind} onChange={e => setKind(e.target.value)}><option value="limit">Limit</option><option value="market">Market</option></select></label>
    <label>Shares<input type="number" required min="1" max="1000000" step="1" value={quantity} onChange={e => setQuantity(Number(e.target.value))} /></label>
    <label>Limit price<input type="number" required={kind === "limit"} disabled={kind === "market"} min="0.01" step="0.01" value={price} onChange={e => setPrice(e.target.value)} /></label>
    <button className="primary-button" type="submit">{busy ? "Processing…" : `Submit ${side.toLowerCase()}`}</button>
  </fieldset></form>{notice && <p className="notice" role="status">{notice}</p>}{error && <p className="notice error" role="alert">{error}</p>}
    {orders.length > 0 && <details><summary>{orders.length} active orders · inspect or cancel</summary><div className="table-scroll"><table className="data-table"><thead><tr><th>ORDER</th><th>SIDE</th><th>PRICE</th><th>REMAINING</th><th>ACTION</th></tr></thead><tbody>{orders.slice(-30).map(row => <tr key={row.order_id}><td>{row.order_id}</td><td>{row.side}</td><td>{inr(row.price)}</td><td>{row.remaining}</td><td><button className="secondary-button" disabled={busy} onClick={() => cancel(row.order_id)}>Cancel order</button></td></tr>)}</tbody></table></div></details>}
    <p className="fine-print">Price–time priority is enforced by the engine. Market orders require existing opposite-side liquidity; unfilled market quantity expires.</p></section>;
}

export function LabSessionTools({ changed }: { changed: () => void }) {
  const [confirm, setConfirm] = useState(false), [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function reset() { setBusy(true); try { await api("/lab/reset", { method: "POST" }); changed(); setConfirm(false); setError(""); } catch (cause) { setError(message(cause)); } finally { setBusy(false); } }
  async function exportSession() { try { download("tradevelocity-session.json", await api("/lab/export")); setError(""); } catch (cause) { setError(message(cause)); } }
  return <section className="panel"><div className="panel-heading"><div><div className="eyebrow">LOCAL LAB SESSION</div><h2>Keep your experiment reproducible</h2><p className="fine-print">History shows the newest 100 trades. Session export includes all commands for replay.</p></div><div className="title-actions"><button className="secondary-button" onClick={exportSession}><Download size={15} /> Export session</button><button className="secondary-button" onClick={() => setConfirm(true)}>Reset lab</button></div></div>{confirm && <div className="confirmation"><p>Clear this lab’s orders and history? Your paper portfolio is unchanged. Export first if you want to keep the experiment.</p><button className="primary-button" disabled={busy} onClick={reset}>Clear lab</button><button className="secondary-button" onClick={() => setConfirm(false)}>Keep session</button></div>}{error && <p className="notice error" role="alert">{error}</p>}</section>;
}

export function RealSimulator({ changed }: { changed: () => void }) {
  const [scenario, setScenario] = useState("normal"), [count, setCount] = useState(500), [symbol, setSymbol] = useState("ACME");
  const [buy, setBuy] = useState(50), [market, setMarket] = useState(10), [seed, setSeed] = useState(42);
  const [busy, setBusy] = useState(false), [error, setError] = useState(""), [result, setResult] = useState<SimulationResult | null>(null);
  async function run() {
    setBusy(true); setError("");
    try { setResult(await api<SimulationResult>("/lab/simulate", { method: "POST", body: JSON.stringify({ count, scenario, symbol, seed, buy_probability: buy, market_percent: market }) })); changed(); }
    catch (cause) { setError(message(cause)); } finally { setBusy(false); }
  }
  return <><div className="section-title"><div><div className="eyebrow">CONTROLLED EXPERIMENTS</div><h1>Market simulator</h1><p>Real orders. Real matching. Reproducible scenarios.</p></div><span className="lab-badge">PAPER TRADING ONLY</span></div>
    <div className="sim-grid"><section className="panel"><h2>Build your workload</h2><p className="fine-print">Orders are added to your current lab book. Reset it from History for a fresh experiment.</p><fieldset disabled={busy} className="form-grid">
      <label>Symbol<select value={symbol} onChange={e => setSymbol(e.target.value)}><option>ACME</option><option>TECH</option></select></label>
      <label>Orders<select value={count} onChange={e => setCount(Number(e.target.value))}>{[100, 500, 1000, 2000].map(n => <option key={n} value={n}>{number(n)}</option>)}</select></label>
      <label>Scenario<select value={scenario} onChange={e => setScenario(e.target.value)}>{["normal", "bull", "bear", "volatile", "low_liquidity", "high_liquidity"].map(s => <option key={s} value={s}>{s.replaceAll("_", " ")}</option>)}</select></label>
      <label>Random seed<input type="number" min="0" max="1000000" value={seed} onChange={e => setSeed(Number(e.target.value))} /></label>
      <label>Buy probability · {buy}%<input type="range" value={buy} onChange={e => setBuy(Number(e.target.value))} /></label>
      <label>Market orders · {market}%<input type="range" value={market} onChange={e => setMarket(Number(e.target.value))} /></label>
    </fieldset><button className="primary-button" disabled={busy} onClick={run}>{busy ? <RefreshCw size={16} className="spin" /> : <Play size={16} />}{busy ? "Processing real orders…" : "Run simulation"}</button>{error && <p className="notice error" role="alert">{error}</p>}</section>
    <section className="panel"><div className="eyebrow">EXECUTION RECEIPT</div><h2>{result ? "Workload complete" : "Ready when you are"}</h2><p className="fine-print">No animated estimates: results appear after the engine processes every command.</p>{result ? <><div className="receipt-grid">{[["Orders processed", number(result.commands)], ["Trades executed", number(result.trades)], ["Shares matched", number(result.filled_shares)], ["Elapsed", `${result.seconds.toFixed(4)} s`], ["Commands / second", number(Math.round(result.commands_per_second))]].map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}</div><p className="fine-print">{result.note}</p></> : <div className="empty"><Play size={28} /><strong>Your next experiment starts here</strong><p>Choose a scenario and run it. Review trades in History and alerts in the Watchdog.</p></div>}</section></div></>;
}

export function Watchdog({ changed }: { changed: () => void }) {
  const [report, setReport] = useState<WatchdogReport | null>(null), [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [symbol, setSymbol] = useState("ACME"), [busy, setBusy] = useState(false), [error, setError] = useState("");
  const [confirm, setConfirm] = useState(false);
  async function refresh() { try { setReport(await api<WatchdogReport>(`/lab/watchdog?symbol=${symbol}`)); setError(""); } catch (cause) { setError(message(cause)); } }
  useEffect(() => { setEvaluation(null); void refresh(); const timer = window.setInterval(refresh, 10000); return () => window.clearInterval(timer); }, [symbol]);
  async function demo() { setBusy(true); setError(""); setConfirm(false); try { const data = await api<{ watchdog: WatchdogReport; evaluation: Evaluation }>("/lab/watchdog/demo", { method: "POST" }); setSymbol("ACME"); setReport(data.watchdog); setEvaluation(data.evaluation); changed(); } catch (cause) { setError(message(cause)); } finally { setBusy(false); } }
  return <><div className="section-title"><div><div className="eyebrow">TRADE-CONNECTED AI</div><h1>Market watchdog</h1><p>A second pair of eyes on your matching engine—not a trading decision-maker.</p></div><div className="title-actions"><select aria-label="Watchdog symbol" value={symbol} onChange={e => setSymbol(e.target.value)}><option>ACME</option><option>TECH</option></select><button className="secondary-button" onClick={refresh}><RefreshCw size={15} /> Refresh</button></div></div>
    <div className="notice"><ShieldCheck size={18} /> Isolation Forest observes actual simulated executions. Alerts mean “needs review”, never “fraud proven”.</div>
    {error && <div className="notice error" role="alert">{error}</div>}
    <div className="metric-grid four">{[["Engine observations", report?.observations ?? 0], ["Training baseline", report?.baseline_size ?? 40], ["Unseen observations scored", report?.scored ?? 0], ["Needs review", report?.flagged ?? 0]].map(([label, value]) => <div className="metric-card" key={label}><span className="metric-head">{label}</span><strong className="metric-value">{value}</strong></div>)}</div>
    <section className="panel demo-callout"><div><div className="eyebrow">CLASSROOM DEMONSTRATION</div><h2>Normal trading → unusual spikes → review</h2><p>40 baseline executions, 20 unseen normal executions, 10 injected spikes, then 20 normal executions.</p></div><button className="primary-button" disabled={busy} onClick={() => setConfirm(true)}>{busy ? <RefreshCw className="spin" size={16} /> : <Play size={16} />} Run classroom demo</button></section>
    {confirm && <section className="panel confirmation" role="alert"><AlertTriangle size={20} /><p>This replaces the current lab order book and trade history. Your paper portfolio is unchanged.</p><button className="primary-button" onClick={demo}>Replace lab and run</button><button className="secondary-button" onClick={() => setConfirm(false)}>Cancel</button></section>}
    {evaluation && <section className="panel"><div className="panel-heading"><div><div className="eyebrow">UNSEEN SYNTHETIC TEST SET · {evaluation.heldout} EXECUTIONS</div><h2>What the model caught—and missed</h2></div><button className="secondary-button" onClick={() => download("watchdog-evaluation.json", { evaluation, report })}><Download size={15} /> Export</button></div><div className="receipt-grid">{[["Detected spikes", evaluation.true_positives], ["Missed spikes", evaluation.false_negatives], ["False alarms", evaluation.false_positives], ["Correct normal", evaluation.true_negatives], ["Precision", `${(evaluation.precision * 100).toFixed(1)}%`], ["Recall", `${(evaluation.recall * 100).toFixed(1)}%`]].map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}</div><p className="fine-print">{evaluation.note} These results do not establish accuracy on real-market fraud.</p></section>}
    <section className="panel"><div className="panel-heading"><div><div className="eyebrow">TRACEABLE ALERTS</div><h2>{report?.status === "warming_up" ? "Building the baseline" : "Execution review queue"}</h2></div><span className="status"><i />{report?.status === "monitoring" ? "MONITORING" : "WARMING UP"}</span></div>
      {report?.alerts.length ? <div className="table-scroll"><table className="data-table"><thead><tr><th>EVENT / ORDER</th><th>PRICE</th><th>EXECUTED SHARES</th><th>SCORE</th><th>UNUSUAL MEASUREMENTS</th><th>STATUS</th></tr></thead><tbody>{report.alerts.slice().reverse().map(row => <tr key={row.event}><td>#{row.event} · {row.order_id}</td><td>{inr(row.price)}</td><td>{number(row.quantity)}</td><td>{row.score.toFixed(2)}</td><td>{row.reasons.join(", ").replaceAll("_", " ")}</td><td><span className="review-tag">Needs review</span></td></tr>)}</tbody></table></div> : <div className="empty"><ShieldCheck size={30} /><strong>{report?.status === "monitoring" ? "No flagged executions" : "Waiting for more executed orders"}</strong><p>The first 40 executed-order observations establish a baseline. Later executions are scored against it.</p></div>}
      <p className="fine-print">{report?.note} Listed measurements are deviations from baseline, not causal explanations. Scores are display indicators, not probabilities. Replay reconstructs features; replay timestamps reflect replay time.</p>
    </section></>;
}

export function RealBenchmark() {
  const [rows, setRows] = useState<Measurement[]>([]), [busy, setBusy] = useState(false), [error, setError] = useState("");
  const [workload, setWorkload] = useState("mixed"), [count, setCount] = useState(1000);
  async function run() { setBusy(true); setError(""); try { setRows(await api<Measurement[]>("/experiments", { method: "POST", body: JSON.stringify({ workload, count }) })); } catch (cause) { setError(message(cause)); } finally { setBusy(false); } }
  return <><div className="section-title"><div><div className="eyebrow">MEASURED, NOT ESTIMATED</div><h1>Performance lab</h1><p>Compare indexed and linear price-level books using identical commands.</p></div><button className="secondary-button" disabled={!rows.length} onClick={() => download("tradevelocity-benchmark.json", rows)}><Download size={15} /> Export results</button></div><section className="panel"><div className="benchmark-controls"><label>Workload<select disabled={busy} value={workload} onChange={e => setWorkload(e.target.value)}><option value="mixed">Order submission & matching</option><option value="deep">Deep-book matching</option><option value="cancel">Cancellation</option></select></label><label>Commands<select disabled={busy} value={count} onChange={e => setCount(Number(e.target.value))}>{[100, 1000, 5000].map(n => <option key={n} value={n}>{number(n)}</option>)}</select></label><button className="primary-button" disabled={busy} onClick={run}>{busy ? <RefreshCw className="spin" size={16} /> : <Play size={16} />}{busy ? "Measuring…" : "Run benchmark"}</button></div><p className="fine-print">Three repetitions. Full output equivalence is checked before timing. Wall-clock throughput is machine-dependent; no latency percentile or memory measurement is inferred.</p>{error && <p className="notice error" role="alert">{error}</p>}{rows.length ? <div className="table-scroll"><table className="data-table"><thead><tr><th>ENGINE</th><th>WORKLOAD</th><th>REPEAT</th><th>COMMANDS</th><th>SECONDS</th><th>COMMANDS / SEC</th><th>TRADES</th></tr></thead><tbody>{rows.map((row, i) => <tr key={i}><td>{row.engine}</td><td>{row.workload}</td><td>{row.repeat}</td><td>{number(row.commands)}</td><td>{row.seconds.toFixed(5)}</td><td>{number(Math.round(row.commands_per_second))}</td><td>{number(row.trades)}</td></tr>)}</tbody></table></div> : <div className="empty"><Play size={30} /><strong>Measure your machine</strong><p>Choose a workload and run the benchmark to see actual results.</p></div>}</section></>;
}

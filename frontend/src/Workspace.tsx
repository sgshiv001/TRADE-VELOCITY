import { useEffect, useRef, useState } from "react";
import { Activity, ArrowRight, BarChart3, BookOpen, BrainCircuit, Download, History as HistoryIcon, Layers3, Menu, RefreshCw, Search, Server, Star, Timer, X } from "lucide-react";
import { api, download, inr, number, percent, tradeTime } from "./api";
import PriceChart from "./PriceChart";
import { useLiveSession } from "./useLiveSession";
import { ThemeToggle, Watchdog, RealBenchmark, OrderTicket, SessionTools } from "./Trading";
import type { Analysis, AnomalyReport, History, Lab, Market, Trade } from "./types";

type Page = "dashboard" | "orders" | "markets" | "watchdog" | "history" | "performance";
const navigation = [
  { id: "dashboard", label: "Overview", icon: Activity },
  { id: "orders", label: "Orders & depth", icon: BookOpen },
  { id: "markets", label: "Market history", icon: BarChart3 },
  { id: "watchdog", label: "AI watchdog", icon: BrainCircuit },
  { id: "history", label: "Trade history", icon: HistoryIcon },
  { id: "performance", label: "Performance", icon: Timer },
] as const;
const errorMessage = (error: unknown) => error instanceof Error ? error.message : "Could not complete the request.";

function Metric({ label, value, note }: { label: string; value: string | number; note: string }) {
  return <div className="metric-card"><span className="metric-head">{label}</span><strong className="metric-value">{value}</strong><small>{note}</small></div>;
}

function Dashboard({ lab, symbol, openOrders }: { lab: Lab; symbol: string; openOrders: () => void }) {
  const latest = lab.trades.at(-1);
  return <>
    <div className="section-title"><div><div className="eyebrow">YOUR MATCHING ENGINE</div><h1>Workspace overview</h1><p>Submitted orders, executed trades, and saved session activity.</p></div><button className="primary-button" onClick={openOrders}>Place an order <ArrowRight size={16} /></button></div>
    <div className="metric-grid four">
      <Metric label="Active orders" value={number(lab.orders.length)} note="All symbols in this session" />
      <Metric label="Executed trades" value={number(lab.total_trades)} note="All symbols, all recorded trades" />
      <Metric label={`${symbol} matched shares`} value={number(lab.stats.volume)} note="From completed executions" />
      <Metric label={`${symbol} VWAP`} value={lab.stats.vwap ? inr(lab.stats.vwap) : "—"} note="Volume-weighted execution price" />
    </div>
    <div className="analytics-grid">
      <section className="panel"><div className="eyebrow">LATEST EXECUTION</div><h2>{latest ? `${latest.symbol} · ${number(latest.quantity)} shares` : "No trades yet"}</h2>
        {latest ? <><strong className="execution-price">{inr(latest.price)}</strong><div className="detail-list"><div><span>Buy order</span><strong>{latest.buy_order_id}</strong></div><div><span>Sell order</span><strong>{latest.sell_order_id}</strong></div><div><span>Time</span><strong>{tradeTime(latest.timestamp)}</strong></div></div></> : <p className="workspace-copy">The engine starts with an empty book. Submit a sell limit order and a compatible buy order in Orders & depth to execute a match. No liquidity is generated automatically.</p>}
      </section>
      <section className="panel"><div className="eyebrow">SESSION STATUS</div><h2>Built around your activity</h2><div className="detail-list"><div><span>Recorded commands</span><strong>{number(lab.events)}</strong></div><div><span>Traded / active symbols</span><strong>{lab.symbols.length}</strong></div><div><span>Matching priority</span><strong>Price → Arrival time</strong></div><div><span>Execution venue</span><strong>Local engine only</strong></div></div><p className="fine-print">Orders are matched inside TradeVelocity, not sent to NSE or a broker. No real money or securities are transferred.</p></section>
    </div>
  </>;
}

function Orders({ lab, symbol, changed, selectSymbol }: { lab: Lab; symbol: string; changed: () => Promise<void>; selectSymbol: (symbol: string) => void }) {
  const [customSymbol, setCustomSymbol] = useState("");
  const max = Math.max(1, ...[...lab.book.bids, ...lab.book.asks].map(level => level.quantity));
  const bid = lab.book.bids[0], ask = lab.book.asks[0];
  return <>
    <div className="section-title"><div><div className="eyebrow">PRICE–TIME MATCHING</div><h1>Orders & depth</h1><p>{symbol} · Submit, amend, and cancel orders against your own book.</p></div></div>
    <form className="custom-symbol-form" onSubmit={event => { event.preventDefault(); selectSymbol(customSymbol.toUpperCase()); setCustomSymbol(""); }}><label>Custom engine symbol<input aria-label="Custom engine symbol" required maxLength={16} pattern="[A-Za-z][A-Za-z0-9.]*" placeholder="For example, MYCOMPANY" value={customSymbol} onChange={event => setCustomSymbol(event.target.value)} /></label><button className="secondary-button" type="submit">Use symbol</button><span className="fine-print">Custom symbols do not have provider market history.</span></form>
    <OrderTicket key={symbol} symbol={symbol} lab={lab} changed={changed} />
    <div className="metric-grid four"><Metric label="Best bid" value={bid ? inr(bid.price) : "—"} note="Highest resting buy price" /><Metric label="Best ask" value={ask ? inr(ask.price) : "—"} note="Lowest resting sell price" /><Metric label="Spread" value={bid && ask ? inr(Number(ask.price) - Number(bid.price)) : "—"} note="Requires both sides of the book" /><Metric label="Resting shares" value={number([...lab.book.bids, ...lab.book.asks].reduce((sum, level) => sum + level.quantity, 0))} note="Top 30 levels on each side" /></div>
    <section className="panel"><div className="panel-heading"><div><div className="eyebrow">{symbol} / ORDER BOOK</div><h2>Market depth</h2></div><span className="status"><i /> LOCAL ENGINE</span></div>
      <div className="depth-sides">{(["bids", "asks"] as const).map(side => <div key={side}><h3 className={side === "bids" ? "success-text" : "danger-text"}>{side === "bids" ? "Buy orders" : "Sell orders"}</h3><div className="depth-header"><span>PRICE</span><span>SHARES</span><span>ORDERS</span></div>{lab.book[side].length ? lab.book[side].map(level => <div className={`depth-row ${side === "bids" ? "bid" : "ask"}`} key={level.price}><span className="depth-bar" style={{ width: `${level.quantity / max * 100}%` }} /><span>{inr(level.price)}</span><span>{number(level.quantity)}</span><span>{level.orders}</span></div>) : <p className="workspace-copy">No resting {side === "bids" ? "buy" : "sell"} orders.</p>}</div>)}</div>
      <p className="fine-print">Orders at the same price follow FIFO. Trades execute at the resting order's price. Unfilled limit quantities remain; unfilled market quantities expire.</p>
    </section>
  </>;
}

function Markets({ market, symbol, refresh, refreshing }: { market: Market | null; symbol: string; refresh: () => void; refreshing: boolean }) {
  const [period, setPeriod] = useState("1Y");
  const [history, setHistory] = useState<History | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [anomaly, setAnomaly] = useState<AnomalyReport | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const generation = useRef(0);
  useEffect(() => {
    const current = ++generation.current;
    setHistory(null); setAnalysis(null); setAnomaly(null); setError(""); setLoading(true); setAnalyzing(false);
    api<History>(`/companies/${encodeURIComponent(symbol)}?period=${period}`).then(data => { if (generation.current === current) setHistory(data); }).catch(cause => { if (generation.current === current) setError(errorMessage(cause)); }).finally(() => { if (generation.current === current) setLoading(false); });
    return () => { generation.current++; };
  }, [symbol, period, market]);
  async function analyze() {
    const current = generation.current;
    setAnalyzing(true); setError("");
    try {
      const [insight, report] = await Promise.all([api<Analysis>(`/analysis/${symbol}?period=${period}`), api<AnomalyReport>(`/ai/anomalies/${symbol}?period=${period}`)]);
      if (generation.current === current) { setAnalysis(insight); setAnomaly(report); }
    } catch (cause) { if (generation.current === current) setError(errorMessage(cause)); }
    finally { if (generation.current === current) setAnalyzing(false); }
  }
  const percentage = (value: number | null | undefined) => value == null ? "—" : `${value.toFixed(2)}%`;
  return <>
    <div className="section-title"><div><div className="eyebrow">PROVIDER-DOWNLOADED DAILY BARS</div><h1>Market history · {symbol}</h1><p>Historical prices with source and date shown. This is not a live exchange feed.</p></div><div className="title-actions"><select aria-label="History period" value={period} onChange={event => setPeriod(event.target.value)}>{["1M", "3M", "6M", "1Y", "5Y"].map(value => <option key={value}>{value}</option>)}</select><button className="secondary-button" disabled={refreshing} onClick={refresh}><RefreshCw size={15} className={refreshing ? "spin" : ""} />{refreshing ? "Downloading…" : "Refresh provider data"}</button></div></div>
    {error && <p className="notice error" role="alert">{error}</p>}{loading && <p className="notice" role="status">Loading history…</p>}
    {history && <>
      {history.history.length < 2 && <p className="notice amber" role="status">This period has fewer than two observations. Return and volatility are unavailable; choose a longer period.</p>}
      <div className="metric-grid four"><Metric label="Last daily close" value={history.metrics.last == null ? "—" : inr(history.metrics.last)} note={history.history.at(-1)?.date ?? ""} /><Metric label="Period return" value={history.metrics.growth_pct == null ? "—" : percent(history.metrics.growth_pct)} note="Adjusted-price change" /><Metric label="Annualized volatility" value={percentage(history.metrics.volatility_pct)} note="Daily returns × √252" /><Metric label="Maximum drawdown" value={percentage(history.metrics.drawdown_pct)} note="Selected historical window" /></div>
      <section className="panel"><div className="panel-heading"><div><div className="eyebrow">ADJUSTED DAILY OHLC</div><h2>{market?.companies.find(company => company.symbol === symbol)?.name ?? symbol}</h2></div></div><PriceChart bars={history.history} symbol={symbol} /><p className="fine-print">{history.source}. {history.basis}</p></section>
      <section className="panel"><div className="panel-heading"><div><div className="eyebrow">COMPUTED FROM THE SELECTED WINDOW</div><h2>Historical analysis</h2></div><button className="primary-button" disabled={analyzing} onClick={() => void analyze()}>{analyzing ? "Analyzing…" : "Analyze observations"}</button></div>{analysis ? <><h3>{analysis.headline}</h3><ul className="workspace-copy">{analysis.evidence.map(item => <li key={item}>{item}</li>)}</ul><p className="fine-print">{analysis.method}</p><p>{anomaly?.anomaly_count} of {anomaly?.observations} historical observations flagged as unusual.</p><p className="fine-print">{anomaly?.note} This model fits and scores the same historical window; this is not unseen-data accuracy.</p></> : <p className="workspace-copy">Calculate trend measurements and unusual historical observations. These are not trading instructions or future-price predictions.</p>}</section>
      <section className="panel"><h2>Recent daily bars</h2><div className="table-scroll"><table className="data-table"><thead><tr><th>DATE</th><th>ADJUSTED CLOSE</th><th>RAW CLOSE</th><th>VOLUME</th><th>RSI 14</th></tr></thead><tbody>{history.history.slice(-20).reverse().map(bar => <tr key={bar.date}><td>{bar.date}</td><td>{inr(bar.close)}</td><td>{inr(bar.raw_close)}</td><td>{number(bar.volume)}</td><td>{bar.rsi?.toFixed(2) ?? "—"}</td></tr>)}</tbody></table></div></section>
    </>}
  </>;
}

function TradeHistory({ revision, changed }: { revision: number; changed: () => Promise<void> }) {
  const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const [result, setResult] = useState<{ total: number; trades: Trade[] }>({ total: 0, trades: [] });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    let active = true; setLoading(true);
    const timer = window.setTimeout(() => {
      api<typeof result>(`/lab/trades?offset=${offset}&limit=50&query=${encodeURIComponent(query)}`).then(data => { if (active) { setResult(data); setError(""); if (offset > 0 && offset >= data.total) setOffset(Math.max(0, Math.floor((data.total - 1) / 50) * 50)); } }).catch(cause => { if (active) setError(errorMessage(cause)); }).finally(() => { if (active) setLoading(false); });
    }, 200);
    return () => { active = false; window.clearTimeout(timer); };
  }, [query, offset, revision]);
  async function exportCsv() {
    try {
      const trades = await api<Trade[]>("/lab/trades/export");
      const cell = (value: string | number) => `"${String(typeof value === "string" && /^[=+@-]/.test(value) ? `'${value}` : value).replaceAll('"', '""')}"`;
      const rows = trades.map(trade => [trade.trade_id, trade.symbol, Number(trade.price), trade.quantity, trade.buy_order_id, trade.sell_order_id, trade.timestamp ?? "Unknown (legacy record)"].map(cell).join(","));
      download("tradevelocity-all-trades.csv", "trade_id,symbol,price,quantity,buy_order_id,sell_order_id,timestamp\r\n" + rows.join("\r\n"), true); setError("");
    } catch (cause) { setError(errorMessage(cause)); }
  }
  return <>
    <div className="section-title"><div><div className="eyebrow">COMPLETE EXECUTION RECORD</div><h1>Trade history</h1><p>Search every recorded trade, not just the newest 100.</p></div><button className="secondary-button" onClick={() => void exportCsv()}><Download size={15} /> Export all trades</button></div>
    <SessionTools changed={changed} />
    <section className="panel"><label className="search-inline"><Search size={16} /><input aria-label="Search trades" value={query} placeholder="Symbol, order ID, or trade ID" onChange={event => { setQuery(event.target.value); setOffset(0); }} /></label>
      {error && <p className="notice error" role="alert">{error}</p>}
      <div className="table-scroll" aria-busy={loading}><table className="data-table"><thead><tr><th>TIME</th><th>SYMBOL</th><th>PRICE</th><th>SHARES</th><th>TRADE ID</th><th>BUY ORDER</th><th>SELL ORDER</th></tr></thead><tbody>{result.trades.map(trade => <tr key={trade.trade_id}><td>{tradeTime(trade.timestamp)}</td><td>{trade.symbol}</td><td>{inr(trade.price)}</td><td>{number(trade.quantity)}</td><td>{trade.trade_id}</td><td>{trade.buy_order_id}</td><td>{trade.sell_order_id}</td></tr>)}</tbody></table></div>
      {!loading && !result.trades.length && <p className="workspace-copy">No matching trades. Completed executions appear here automatically.</p>}
      <div className="history-pagination"><span className="fine-print">{loading ? "Loading…" : `${result.total ? offset + 1 : 0}–${Math.min(offset + 50, result.total)} of ${number(result.total)} trades`}</span><div className="title-actions"><button className="secondary-button" disabled={loading || offset === 0} onClick={() => setOffset(Math.max(0, offset - 50))}>Previous</button><button className="secondary-button" disabled={loading || offset + 50 >= result.total} onClick={() => setOffset(offset + 50)}>Next</button></div></div>
    </section>
  </>;
}

export default function Workspace() {
  const [page, setPage] = useState<Page>("dashboard");
  const [navOpen, setNavOpen] = useState(false);
  const [symbol, setSymbol] = useState("RELIANCE");
  const [lab, setLab] = useState<Lab | null>(null);
  const [market, setMarket] = useState<Market | null>(null);
  const [error, setError] = useState("");
  const [marketError, setMarketError] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const [revision, setRevision] = useState(0);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  const [version, setVersion] = useState("");
  const [watchlist, setWatchlist] = useState<string[]>(() => { try { const value = JSON.parse(localStorage.getItem("tradevelocity-watchlist") ?? "[]"); return Array.isArray(value) ? value.filter((item: unknown) => typeof item === "string" && /^[A-Z][A-Z0-9.]{0,15}$/.test(item)).slice(0,30) : []; } catch { return []; } });
  const seenRevision = useRef(-1);
  const requestVersion = useRef(0);
  async function loadLab() {
    const current = ++requestVersion.current;
    try { const data = await api<Lab>(`/lab?symbol=${encodeURIComponent(symbol)}`); if (current === requestVersion.current) { setLab(data); setError(""); setLastUpdate(new Date().toLocaleTimeString()); if (seenRevision.current !== data.revision) { seenRevision.current = data.revision; setRevision(value => value + 1); } } }
    catch (cause) { if (current === requestVersion.current) setError(errorMessage(cause)); }
  }
  const live = useLiveSession(loadLab);
  useEffect(() => { void loadLab(); return () => { requestVersion.current++; }; }, [symbol]);
  useEffect(() => { api<Market>("/market").then(setMarket).catch(cause => setMarketError(errorMessage(cause))); }, []);
  useEffect(() => { api<{version: string}>("/health").then(data => setVersion(data.version)).catch(() => {}); }, []);
  useEffect(() => { localStorage.setItem("tradevelocity-watchlist", JSON.stringify(watchlist)); }, [watchlist]);
  async function refreshMarket() {
    setRefreshing(true); setMarketError("");
    try { setMarket(await api<Market>("/market/refresh", { method: "POST" })); }
    catch (cause) { setMarketError(errorMessage(cause)); }
    finally { setRefreshing(false); }
  }
  const symbols = [...new Set(["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "BHARTIARTL", "LT", "ITC", symbol, ...watchlist, ...(lab?.symbols ?? [])])];
  const selectSymbol = (next: string) => { if (next !== symbol) { setLab(null); setSymbol(next); } };
  const navigate = (next: Page) => { setPage(next); setNavOpen(false); window.scrollTo({ top: 0 }); };
  return <div className="app-shell">
    {navOpen && <button className="nav-overlay" aria-label="Close navigation" onClick={() => setNavOpen(false)} />}
    <aside className={`sidebar ${navOpen ? "open" : ""}`}><div className="sidebar-brand"><div className="brand-box">TV</div><div><strong>TRADE<br />VELOCITY</strong><small>MATCHING WORKSPACE</small></div></div><div className="nav-label">WORKSPACE</div><nav aria-label="Main navigation">{navigation.map(({ id, label, icon: Icon }) => <button key={id} className={page === id ? "selected" : ""} aria-current={page === id ? "page" : undefined} onClick={() => navigate(id)}><Icon size={17} /><span>{label}</span></button>)}</nav><div className="sidebar-bottom"><div className="engine-status-label">EXECUTION VENUE</div><p className="fine-print">Your local matching engine.<br />No broker or real-money execution.</p><div className="engine-version"><Server size={13} /> Saved local session</div></div></aside>
    <div className="workspace"><header className="topbar"><button className="mobile-menu" aria-label="Open navigation" onClick={() => setNavOpen(true)}><Menu size={20} /></button><div className="crumb"><span>TRADEVELOCITY</span><ArrowRight size={13} /><strong>{navigation.find(item => item.id === page)?.label}</strong></div><label className="symbol-select"><Layers3 size={16} /><select aria-label="Select symbol" value={symbol} onChange={event => { setLab(null); setSymbol(event.target.value); }}>{symbols.map(value => <option key={value}>{value}</option>)}</select></label><div className="topbar-actions"><ThemeToggle /></div></header>
      <main className="content"><div className="data-strip"><span className={!live.online || error ? "danger-text" : "success-text"} role="status"><Activity size={12} />{!live.online ? "OFFLINE" : error ? "DATA UNAVAILABLE" : live.connected ? "LIVE WORKSPACE UPDATES" : "POLLING · RECONNECTING"}</span><span>LAST SYNC {lastUpdate ?? "—"} · MARKET HISTORY AS OF {market?.as_of ?? "—"}</span></div>
        <div className="watchlist-bar" aria-label="Watchlist"><button className="secondary-button" aria-label={`${watchlist.includes(symbol) ? "Remove" : "Add"} ${symbol} ${watchlist.includes(symbol) ? "from" : "to"} watchlist`} onClick={() => setWatchlist(list => list.includes(symbol) ? list.filter(item => item !== symbol) : [...list,symbol].slice(-30))}><Star size={14} fill={watchlist.includes(symbol) ? "currentColor" : "none"} />{watchlist.includes(symbol) ? "Watching" : "Watch"} {symbol}</button>{watchlist.map(item => <button key={item} className={`watchlist-chip ${item === symbol ? "selected" : ""}`} onClick={() => selectSymbol(item)}>{item}</button>)}</div>
        {error && <div className="notice error" role="alert"><X size={15} />{error}<button className="text-button" onClick={() => void loadLab()}>Retry connection</button></div>}
        {page === "markets" && marketError && <div className="notice error" role="alert">{marketError}</div>}
        {page === "markets" ? <Markets market={market} symbol={symbol} refresh={() => void refreshMarket()} refreshing={refreshing} /> : page === "performance" ? <RealBenchmark /> : page === "watchdog" ? <Watchdog symbol={symbol} /> : page === "history" ? <TradeHistory revision={revision} changed={loadLab} /> : lab ? page === "orders" ? <Orders lab={lab} symbol={symbol} changed={loadLab} selectSymbol={selectSymbol} /> : <Dashboard lab={lab} symbol={symbol} openOrders={() => navigate("orders")} /> : !error && <div className="loading-screen" role="status"><RefreshCw className="spin" size={22} /> Connecting to matching engine…</div>}
        <footer><span>TRADEVELOCITY {version && `v${version}`} · WINDOWS & WEB</span><span>Local orders only · Market history is not a live feed</span></footer>
      </main>
    </div>
  </div>;
}

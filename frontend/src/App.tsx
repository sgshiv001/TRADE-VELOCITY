import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  Activity,
  ArrowDown,
  ArrowRight,
  ArrowUp,
  BarChart3,
  BookOpen,
  BrainCircuit,
  Check,
  ChevronDown,
  CircleDot,
  Code2,
  Cpu,
  Database,
  Download,
  FlaskConical,
  GitBranch,
  Hash,
  History as HistoryIcon,
  Layers3,
  Menu,
  Network,
  Play,
  RefreshCw,
  Search,
  Server,
  Settings2,
  SlidersHorizontal,
  Sparkles,
  Table2,
  Timer,
  TrendingUp,
  X,
  Zap,
} from "lucide-react";
import { api, download, inr, number, percent, short } from "./api";
import { ThemeToggle, RealSimulator, Watchdog, RealBenchmark, OrderTicket, LabSessionTools } from "./Experience";
import type { Analysis, AnomalyReport, Depth, Lab, Market } from "./types";

type Page = "engine" | "orderbook" | "dsa" | "simulator" | "analytics" | "ai" | "watchdog" | "benchmark" | "history";
type DsaTab = "heap" | "avl" | "hash" | "queue" | "fenwick";

const navItems: { id: Page; label: string; icon: typeof Cpu }[] = [
  { id: "engine", label: "ENGINE", icon: Cpu },
  { id: "orderbook", label: "ORDER BOOK", icon: BookOpen },
  { id: "dsa", label: "DSA LAB", icon: Network },
  { id: "simulator", label: "SIMULATOR", icon: SlidersHorizontal },
  { id: "analytics", label: "ANALYTICS", icon: BarChart3 },
  { id: "watchdog", label: "WATCHDOG", icon: BrainCircuit },
  { id: "ai", label: "HISTORICAL AI", icon: BarChart3 },
  { id: "benchmark", label: "BENCHMARK", icon: Timer },
  { id: "history", label: "HISTORY", icon: HistoryIcon },
];

function Panel({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`panel ${className}`}>{children}</section>;
}

function SectionTitle({ eyebrow, title, subtitle, action }: { eyebrow?: string; title: string; subtitle?: string; action?: ReactNode }) {
  return <div className="section-title"><div>{eyebrow && <div className="eyebrow">{eyebrow}</div>}<h1>{title}</h1>{subtitle && <p>{subtitle}</p>}</div>{action}</div>;
}

function Status({ label = "ENGINE ONLINE" }: { label?: string }) {
  return <span className="status"><i />{label}</span>;
}

function Metric({ label, value, note, icon }: { label: string; value: ReactNode; note: string; icon: ReactNode }) {
  return <div className="metric-card"><div className="metric-head"><span>{label}</span><span className="metric-icon">{icon}</span></div><strong className="mono metric-value">{value}</strong><small>{note}</small></div>;
}

function Skeleton({ rows = 4 }: { rows?: number }) {
  return <div className="skeleton-list">{Array.from({ length: rows }).map((_, index) => <span key={index} />)}</div>;
}

function Empty({ title, body, action }: { title: string; body: string; action?: ReactNode }) {
  return <div className="empty"><Database size={24} /><strong>{title}</strong><p>{body}</p>{action}</div>;
}

function FlowNode({ label, icon, active = false }: { label: string; icon: ReactNode; active?: boolean }) {
  return <div className={`flow-node ${active ? "active" : ""}`}><span>{icon}</span><b>{label}</b></div>;
}

function Welcome({ enter }: { enter: () => void }) {
  return <main className="welcome-screen"><div className="welcome-grid" /><div className="welcome-theme"><ThemeToggle /></div><div className="welcome-copy"><div className="brand-mark"><span>TV</span><div><strong>TRADE<br />VELOCITY</strong><small>ALGORITHMIC MARKET LAB</small></div></div><div className="welcome-kicker"><CircleDot size={14} /> MCA SEMESTER PROJECT · DETERMINISTIC ENGINE</div><h1>HIGH-PERFORMANCE<br /><em>ORDER MATCHING</em><br />ENGINE</h1><p>Advanced data structures. Real-time simulation.<br />Interpretable market analytics.</p><button className="primary-button enter-button" onClick={enter}>ENTER ENGINE <ArrowRight size={17} /></button><div className="built-with">BUILT WITH <span>PYTHON</span><i>·</i><span>DSA</span><i>·</i><span>MACHINE LEARNING</span><i>·</i><span>REST API</span></div></div><div className="welcome-machine" aria-hidden="true"><div className="machine-caption mono">PROCESS GRAPH / 01</div><div className="machine-flow"><FlowNode label="ORDER" icon={<Layers3 size={20} />} active /><ArrowDown className="flow-arrow" /><FlowNode label="HASH TABLE" icon={<Hash size={20} />} /><ArrowDown className="flow-arrow" /><FlowNode label="AVL TREE" icon={<GitBranch size={20} />} /><ArrowDown className="flow-arrow" /><FlowNode label="FIFO QUEUE" icon={<Table2 size={20} />} /><ArrowDown className="flow-arrow" /><FlowNode label="MATCH" icon={<Zap size={20} />} active /><ArrowDown className="flow-arrow" /><FlowNode label="TRADE" icon={<TrendingUp size={20} />} /></div><div className="machine-scan" /></div></main>;
}

function Sidebar({ page, setPage, open, close }: { page: Page; setPage: (page: Page) => void; open: boolean; close: () => void }) {
  return <>{open && <button className="nav-overlay" aria-label="Close navigation" onClick={close} />}<aside className={`sidebar ${open ? "open" : ""}`}><div className="sidebar-brand"><div className="brand-box">TV</div><div><strong>TRADE<br />VELOCITY</strong><small>THE ENGINE LAB</small></div></div><div className="nav-label">WORKSPACE</div><nav aria-label="Main navigation">{navItems.map(({ id, label, icon: Icon }, index) => <button key={id} className={page === id ? "selected" : ""} onClick={() => { setPage(id); close(); }}><span className="nav-number">0{index + 1}</span><Icon size={16} /><span>{label}</span>{page === id && <i className="nav-active-dot" />}</button>)}</nav><div className="sidebar-bottom"><div className="engine-status-label">ENGINE STATUS</div><Status /><div className="engine-version"><Server size={13} /> Python Engine <span>v0.3.0</span></div></div></aside></>;
}

function Topbar({ page, market, selectedSymbol, setSelectedSymbol, refresh, toggleNav }: { page: Page; market: Market | null; selectedSymbol: string; setSelectedSymbol: (symbol: string) => void; refresh: () => void; toggleNav: () => void }) {
  const label = navItems.find((item) => item.id === page)?.label ?? "ENGINE";
  return <header className="topbar"><button className="mobile-menu" aria-label="Open navigation" onClick={toggleNav}><Menu size={20} /></button><div className="crumb"><span>TRADE VELOCITY</span><ArrowRight size={13} /><strong>{label}</strong></div>{market && <label className="symbol-select"><Search size={15} /><select aria-label="Select company" value={selectedSymbol} onChange={(event) => setSelectedSymbol(event.target.value)}>{market.companies.map((company) => <option key={company.symbol} value={company.symbol}>{company.symbol}</option>)}</select><ChevronDown size={13} /></label>}<div className="topbar-actions"><span className="demo-pill"><i /> DEMO MODE</span><button className="icon-button" aria-label="Refresh market data" onClick={refresh}><RefreshCw size={16} /></button><ThemeToggle /></div></header>;
}

function EnginePage({ lab, loadDemo, loading, market }: { lab: Lab | null; loadDemo: () => void; loading: boolean; market: Market | null }) {
  const [explain, setExplain] = useState(false);
  const latest = lab?.trades?.at(-1);
  const activeOrders = lab?.orders?.length ?? 0;
  const tradeCount = lab?.total_trades ?? 0;
  return <><SectionTitle eyebrow="01 / CORE SYSTEM" title="Matching Engine" subtitle="Real-time order processing and price-time matching" action={<div className="title-actions"><Status />{!tradeCount && <button className="secondary-button" onClick={loadDemo}>{loading ? <RefreshCw className="spin" size={15} /> : <Play size={15} />} Load demo flow</button>}</div>} />{market?.is_demo && <div className="notice"><CircleDot size={15} /> Market snapshot mode: historical data is shown for education. Orders below are simulated.</div>}<div className="metric-grid four"><Metric label="ORDERS / SEC" value="—" note="Run a benchmark to measure" icon={<Zap size={16} />} /><Metric label="TRADES / SEC" value="—" note="Measured, never fabricated" icon={<TrendingUp size={16} />} /><Metric label="ACTIVE ORDERS" value={number(activeOrders)} note="Across the local lab session" icon={<Layers3 size={16} />} /><Metric label="TRADES EXECUTED" value={number(tradeCount)} note="This local session" icon={<Activity size={16} />} /></div><div className="engine-grid"><Panel className="engine-visual-panel"><div className="panel-heading"><div><div className="eyebrow">LIVE MATCH VISUALIZATION</div><h2>Latest Match</h2></div><span className="mono muted">{latest?.symbol ?? "ACME"} / EXECUTION</span></div>{latest ? <div className="match-story"><div className="match-card"><span className="tag buy">BUY ORDER</span><strong className="mono">#{latest.buy_order_id}</strong><span>{latest.quantity} × {inr(latest.price)}</span></div><ArrowDown className="story-arrow" /><div className="match-step"><span className="tag">PRICE CHECK</span><strong className="mono">{inr(latest.price)} ≤ limit</strong><span className="success-text"><Check size={14} /> Compatible</span></div><ArrowDown className="story-arrow" /><div className="match-card"><span className="tag sell">BEST ASK</span><strong className="mono">#{latest.sell_order_id}</strong><span>{latest.quantity} × {inr(latest.price)}</span></div><ArrowDown className="story-arrow" /><div className="trade-result"><Sparkles size={18} /><span>TRADE EXECUTED</span><strong className="mono">{latest.quantity} × {inr(latest.price)}</strong></div><button className="text-button" onClick={() => setExplain(!explain)}>{explain ? "Hide explanation" : "Explain match"} <ArrowRight size={14} /></button>{explain && <div className="explanation"><strong>WHY DID THIS TRADE EXECUTE?</strong><ol><li>Best compatible sell order found.</li><li>Sell price was within the buyer's limit.</li><li>Price priority and time priority were satisfied.</li><li>Available quantity was matched and recorded.</li></ol><div className="structure-chips"><span>Hash Table → lookup</span><span>AVL Tree → price level</span><span>FIFO Queue → time priority</span></div></div>}</div> : <Empty title="NO MATCHES YET" body="Load the deterministic demo flow to see an order travel through the engine." action={<button className="primary-button" onClick={loadDemo}><Play size={15} /> START DEMO</button>} />}</Panel><Panel className="engine-pipeline"><div className="panel-heading"><div><div className="eyebrow">PROCESS GRAPH</div><h2>The Engine</h2></div><Code2 size={18} className="muted" /></div><div className="vertical-flow"><FlowNode label="INCOMING ORDER" icon={<Layers3 size={17} />} active /><ArrowDown /><FlowNode label="HASH TABLE LOOKUP" icon={<Hash size={17} />} /><ArrowDown /><FlowNode label="AVL PRICE LEVEL" icon={<GitBranch size={17} />} /><ArrowDown /><FlowNode label="FIFO PRIORITY" icon={<Table2 size={17} />} /><ArrowDown /><FlowNode label="DETERMINISTIC MATCH" icon={<Zap size={17} />} active /></div></Panel></div><Panel><div className="panel-heading"><div><div className="eyebrow">SYSTEM NOTES</div><h2>Precision over prediction</h2></div><Settings2 size={18} className="muted" /></div><div className="note-grid"><div><strong>01</strong><p>The matching engine is deterministic. AI never decides which orders trade.</p></div><div><strong>02</strong><p>Every simulated result can be traced back to a data structure and rule.</p></div><div><strong>03</strong><p>Performance values appear only after an actual benchmark is executed.</p></div></div></Panel></>;
}

function DepthRow({ level, max, side, onSelect }: { level: Depth; max: number; side: "bid" | "ask"; onSelect: () => void }) {
  return <button className={`depth-row ${side}`} onClick={onSelect}><span className="depth-bar" style={{ width: `${Math.max(8, (level.quantity / max) * 100)}%` }} /><span className="mono">{level.price}</span><span className="mono">{number(level.quantity)}</span><span className="muted">{level.orders}</span></button>;
}

function OrderBookPage({ lab, loadDemo, selectedSymbol, setSelectedSymbol, changed }: { lab: Lab | null; loadDemo: () => void; selectedSymbol: string; setSelectedSymbol: (symbol: string) => void; changed: () => void }) {
  const book = lab?.book;
  const bids = book?.bids ?? [];
  const asks = book?.asks ?? [];
  const max = Math.max(1, ...bids.map((row) => row.quantity), ...asks.map((row) => row.quantity));
  const [selected, setSelected] = useState<Depth | null>(null);
  const bidVolume = bids.reduce((sum, row) => sum + row.quantity, 0);
  const askVolume = asks.reduce((sum, row) => sum + row.quantity, 0);
  const spread = bids[0] && asks[0] ? Number(asks[0].price) - Number(bids[0].price) : null;
  return <><SectionTitle eyebrow="02 / PRICE-TIME PRIORITY" title="Live Order Book" subtitle="Price-time priority in action" action={<div className="control-row"><label className="compact-label">SYMBOL<select value={selectedSymbol} onChange={(event) => setSelectedSymbol(event.target.value)}><option value="ACME">ACME</option><option value="TECH">TECH</option></select></label><button className="secondary-button" onClick={loadDemo}><RefreshCw size={14} /> Reset demo</button></div>} /><OrderTicket symbol={selectedSymbol} lab={lab} changed={changed} /><div className="metric-grid five"><Metric label="BEST BID" value={bids[0]?.price ?? "—"} note="Highest buy price" icon={<ArrowUp size={16} />} /><Metric label="BEST ASK" value={asks[0]?.price ?? "—"} note="Lowest sell price" icon={<ArrowDown size={16} />} /><Metric label="SPREAD" value={spread == null ? "—" : inr(spread)} note="Ask minus bid" icon={<Activity size={16} />} /><Metric label="BUY VOLUME" value={number(bidVolume)} note={`${bids.length} price levels`} icon={<ArrowUp size={16} />} /><Metric label="SELL VOLUME" value={number(askVolume)} note={`${asks.length} price levels`} icon={<ArrowDown size={16} />} /></div><div className="book-grid"><Panel className="book-panel"><div className="book-toolbar"><div><div className="eyebrow">{selectedSymbol} / DEPTH</div><h2>Market depth</h2></div><span className="demo-pill"><i /> SIMULATED BOOK</span></div>{!bids.length && !asks.length ? <Empty title="ORDER BOOK EMPTY" body="Load the demo flow to populate price levels and FIFO queues." action={<button className="primary-button" onClick={loadDemo}><Play size={15} /> START SIMULATION</button>} /> : <div className="depth-table"><div className="depth-header"><span>PRICE</span><span>QUANTITY</span><span>ORDERS</span></div><div className="side-heading ask-heading"><span>SELL SIDE</span><small>Best ask at the top</small></div>{asks.map((row) => <DepthRow key={`ask-${row.price}`} level={row} max={max} side="ask" onSelect={() => setSelected(row)} />)}<div className="spread-line"><span>SPREAD</span><strong className="mono">{spread == null ? "—" : inr(spread)}</strong></div><div className="side-heading bid-heading"><span>BUY SIDE</span><small>Best bid at the top</small></div>{bids.map((row) => <DepthRow key={`bid-${row.price}`} level={row} max={max} side="bid" onSelect={() => setSelected(row)} />)}</div>}</Panel><Panel className="level-panel"><div className="eyebrow">SELECTED PRICE LEVEL</div>{selected ? <><div className="selected-price mono">{selected.price}</div><div className="detail-list"><div><span>Orders</span><strong>{selected.orders}</strong></div><div><span>Total quantity</span><strong>{number(selected.quantity)}</strong></div><div><span>Data structure</span><strong>FIFO Queue</strong></div><div><span>Priority</span><strong>Price → Time</strong></div></div><div className="mini-diagram"><span>PRICE LEVEL</span><ArrowDown size={15} /><span>FIFO QUEUE</span><ArrowDown size={15} /><span>EXECUTION</span></div></> : <Empty title="CLICK A PRICE" body="Select a level to inspect its queue and priority rules." />}</Panel></div></>;
}

function HeapVisual({ values }: { values: number[] }) {
  return <div className="heap-tree">{values.map((value, index) => <div key={`${value}-${index}`} className="heap-node" style={{ marginLeft: `${index === 0 ? 0 : index % 2 ? 32 : 12}px` }}><span className="mono">{value}</span></div>)}</div>;
}

function DsaLabPage() {
  const [tab, setTab] = useState<DsaTab>("heap");
  const [values, setValues] = useState([181, 179, 178, 175, 177, 176]);
  const [input, setInput] = useState("182");
  const addValue = () => { const value = Number(input); if (Number.isFinite(value)) setValues((current) => [...current, value].sort((a, b) => b - a).slice(0, 12)); };
  const reset = () => setValues([181, 179, 178, 175, 177, 176]);
  const operation = tab === "heap" ? "INSERT 182" : tab === "avl" ? "INSERT ₹182" : tab === "hash" ? "LOOKUP #TV-92831" : tab === "queue" ? "DEQUEUE ORDER A" : "RANGE QUERY 100–103";
  return <><SectionTitle eyebrow="03 / DATA STRUCTURES" title="Data Structure Laboratory" subtitle="See the algorithms behind the exchange" action={<span className="lab-badge"><FlaskConical size={15} /> EDUCATIONAL MODE</span>} /><div className="dsa-tabs">{(["heap", "avl", "hash", "queue", "fenwick"] as DsaTab[]).map((item) => <button key={item} className={tab === item ? "active" : ""} onClick={() => setTab(item)}>{item === "avl" ? "AVL TREE" : item === "hash" ? "HASH TABLE" : item === "fenwick" ? "FENWICK TREE" : item.toUpperCase()}</button>)}</div><div className="dsa-grid"><Panel className="visualizer"><div className="panel-heading"><div><div className="eyebrow">INTERACTIVE VISUALIZER</div><h2>{tab === "avl" ? "AVL Tree" : tab === "hash" ? "Separate-Chaining Hash Table" : tab === "queue" ? "FIFO Queue" : tab === "fenwick" ? "Fenwick Tree" : "Max Heap"}</h2></div><span className="mono operation-label">{operation}</span></div>{tab === "heap" && <><HeapVisual values={values} /><div className="visual-controls"><input aria-label="Structure value" value={input} onChange={(event) => setInput(event.target.value)} /><button className="primary-button" onClick={addValue}>Insert</button><button className="secondary-button" onClick={() => setValues((current) => current.slice(1))}>Extract</button><button className="icon-button" onClick={reset} aria-label="Reset heap"><RefreshCw size={15} /></button></div></>}{tab === "avl" && <TreeDiagram />}{tab === "hash" && <HashDiagram />}{tab === "queue" && <QueueDiagram />}{tab === "fenwick" && <FenwickDiagram />}</Panel><Panel className="concept-panel"><div className="eyebrow">CONCEPT</div><h2>{tab === "heap" ? "Price priority" : tab === "avl" ? "Balanced search" : tab === "hash" ? "Constant-time lookup" : tab === "queue" ? "Time priority" : "Prefix sums"}</h2><p>{tab === "heap" ? "A max heap keeps the highest buy price at the root. Insertion and extraction restore the heap property in logarithmic time." : tab === "avl" ? "An AVL tree is a binary search tree that rotates when its balance factor leaves the range −1 to +1." : tab === "hash" ? "Order IDs map to buckets. Separate chaining keeps colliding orders together without losing lookup correctness." : tab === "queue" ? "Orders at the same price level leave from the front in the same order they entered." : "Fenwick trees store partial sums so volume updates and range queries take O(log n)."}</p><div className="complexity-box"><span>COMPLEXITY</span><strong className="mono">{tab === "hash" ? "O(1) average" : "O(log n)"}</strong></div><div className="explain-list"><div><Check size={14} /> Deterministic operation</div><div><Check size={14} /> Observable state transition</div><div><Check size={14} /> Viva-ready explanation</div></div></Panel></div></>;
}

function TreeDiagram() { return <div className="tree-diagram"><div className="tree-level"><span>180</span></div><div className="tree-lines">╱　　　　　　　╲</div><div className="tree-level"><span>175</span><span>190</span></div><div className="tree-lines">╱　╲　　　　╱　╲</div><div className="tree-level small"><span>170</span><span>178</span><span>185</span><span>195</span></div><div className="rotation-callout"><GitBranch size={16} /> INSERT ₹182 → LEFT-RIGHT ROTATION → BALANCED</div></div>; }
function HashDiagram() { return <div className="hash-diagram"><div className="hash-flow"><span>ORDER ID</span><ArrowRight /><span>HASH FUNCTION</span><ArrowRight /><span>BUCKET</span><ArrowRight /><span>ORDER</span></div>{["0", "1  ·  #TV-182", "2", "3  ·  #TV-829 → #TV-921", "4"].map((value) => <div className="bucket" key={value}><span className="mono">Bucket {value.split("  ")[0]}</span><strong>{value.includes("·") ? value.split("  ").slice(1).join("  ") : "────────"}</strong></div>)}</div>; }
function QueueDiagram() { return <div className="queue-diagram"><div className="queue-labels"><span>FRONT / EARLIEST</span><span>REAR / LATEST</span></div><div className="queue-items"><span>Order A</span><b>→</b><span>Order B</span><b>→</b><span>Order C</span></div><div className="queue-note"><ArrowRight size={15} /> Dequeue always removes Order A first</div></div>; }
function FenwickDiagram() { return <div className="fenwick-diagram"><div className="fenwick-row"><span>100</span><b>+50</b></div><div className="fenwick-row"><span>101</span><b>+20</b></div><div className="fenwick-row"><span>102</span><b>+80</b></div><div className="fenwick-row"><span>103</span><b>+30</b></div><div className="fenwick-arrow"><ArrowDown size={16} /></div><div className="fenwick-result"><strong>Fenwick Tree</strong><span>UPDATE O(log n) · QUERY O(log n)</span><em>Prefix volume → 150</em></div></div>; }

function SimulatorPage({ changed }: { changed: () => void }) {
  return <RealSimulator changed={changed} />;
}

function Sparkline({ values }: { values: number[] }) { const min = Math.min(...values), range = Math.max(1, Math.max(...values) - min); const points = values.length ? values.map((value, index) => `${(index / Math.max(1, values.length - 1)) * 100},${100 - ((value - min) / range) * 82}`).join(" ") : "0,50 100,50"; return <svg className="sparkline" viewBox="0 0 100 100" preserveAspectRatio="none"><polyline points={points} fill="none" stroke="currentColor" strokeWidth="2.5" /></svg>; }

function AnalyticsPage({ market, selectedSymbol, setSelectedSymbol }: { market: Market; selectedSymbol: string; setSelectedSymbol: (symbol: string) => void }) {
  const company = market.companies.find((item) => item.symbol === selectedSymbol) ?? market.companies[0];
  const values = company?.sparkline ?? [];
  const min = Math.min(...values), max = Math.max(...values);
  return <><SectionTitle eyebrow="05 / OBSERVABILITY" title="Market Analytics" subtitle="A clean view of the data generated around the matching engine" action={<label className="compact-label">COMPANY<select value={selectedSymbol} onChange={(event) => setSelectedSymbol(event.target.value)}>{market.companies.map((item) => <option key={item.symbol}>{item.symbol}</option>)}</select></label>} /><div className="analytics-grid"><Panel className="chart-panel"><div className="panel-heading"><div><div className="eyebrow">ADJUSTED PRICE · 30 SESSIONS</div><h2>{company.name}</h2></div><strong className="mono chart-price">{inr(company.price)}</strong></div><div className="big-chart"><Sparkline values={values} /><div className="chart-axis"><span>{inr(min, 0)}</span><span>{inr((min + max) / 2, 0)}</span><span>{inr(max, 0)}</span></div></div><div className="chart-foot"><span>Latest daily bar: {company.as_of}</span><span className={company.day_change >= 0 ? "success-text" : "danger-text"}>{percent(company.day_change)}</span></div></Panel><Panel><div className="panel-heading"><div><div className="eyebrow">FEATURE SNAPSHOT</div><h2>Market signals</h2></div><Activity size={18} className="muted" /></div><div className="feature-bars"><FeatureBar label="VOLUME" value={Math.min(100, 35 + Math.abs(company.day_change) * 8)} note={short(company.volume)} /><FeatureBar label="VOLATILITY" value={Math.min(100, 25 + Math.abs(company.year_growth) / 2)} note="computed in analysis" /><FeatureBar label="SPREAD" value={18} note="order-book dependent" /><FeatureBar label="IMBALANCE" value={50} note="order-book dependent" /></div><p className="fine-print">Trade statistics are populated by the matching-lab session. Historical company data is kept separate from simulated liquidity.</p></Panel></div><div className="metric-grid four"><Metric label="VWAP" value="—" note="Awaiting executed trades" icon={<BarChart3 size={16} />} /><Metric label="VOLATILITY" value={`${Math.abs(company.year_growth).toFixed(1)}%`} note="Historical 1Y movement" icon={<Activity size={16} />} /><Metric label="TRADE FREQUENCY" value="—" note="Run a simulation first" icon={<Timer size={16} />} /><Metric label="DEPTH" value="—" note="Select Order Book" icon={<Layers3 size={16} />} /></div></>;
}
function FeatureBar({ label, value, note }: { label: string; value: number; note: string }) { return <div className="feature-bar"><div><span>{label}</span><small>{note}</small></div><div className="bar-track"><span style={{ width: `${value}%` }} /></div></div>; }

function AiMonitorPage({ market, selectedSymbol, setSelectedSymbol }: { market: Market; selectedSymbol: string; setSelectedSymbol: (symbol: string) => void }) {
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [anomaly, setAnomaly] = useState<AnomalyReport | null>(null);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    setLoading(true);
    Promise.all([
      api<Analysis>(`/analysis/${selectedSymbol}?period=1Y`),
      api<AnomalyReport>(`/ai/anomalies/${selectedSymbol}?period=1Y`),
    ]).then(([insight, report]) => {
      setAnalysis(insight);
      setAnomaly(report);
    }).catch(() => {
      setAnalysis(null);
      setAnomaly(null);
    }).finally(() => setLoading(false));
  }, [selectedSymbol]);
  const latest = anomaly?.latest;
  const anomalous = latest?.is_anomalous ?? false;
  const featureEntries = latest ? Object.entries(latest.features).slice(0, 6) : [];
  return <><SectionTitle eyebrow="06 / INTERPRETABLE AI" title="AI Market Monitor" subtitle="Detect potentially anomalous market activity without replacing deterministic matching" action={<label className="compact-label">SYMBOL<select value={selectedSymbol} onChange={(event) => setSelectedSymbol(event.target.value)}>{market.companies.map((item) => <option key={item.symbol}>{item.symbol}</option>)}</select></label>} /><div className={`notice ${anomalous ? "amber" : ""}`}><BrainCircuit size={15} /> Isolation Forest is trained on the selected historical feature window. Scores indicate unusualness, not fraud probability.</div><div className="ai-grid"><Panel className="ai-status"><div className="panel-heading"><div><div className="eyebrow">MODEL STATUS</div><h2>{anomalous ? "Potentially anomalous activity" : "Normal activity window"}</h2></div><span className={`status ${anomalous ? "amber-status" : ""}`}><i /> {anomalous ? "REVIEW" : "NORMAL"}</span></div><div className="ai-score"><span>ANOMALY SCORE</span><strong className="mono">{latest ? latest.anomaly_score.toFixed(2) : "—"}</strong><small>{latest ? `${anomaly?.anomaly_count} flagged observations across ${anomaly?.observations}` : "Loading feature window"}</small></div><div className="pipeline"><span className="done">MARKET DATA</span><ArrowRight /><span className="done">FEATURE ENGINEERING</span><ArrowRight /><span className="done">ISOLATION FOREST</span><ArrowRight /><span className="done">ANOMALY SCORE</span></div></Panel><Panel><div className="eyebrow">CURRENT INSIGHT</div>{loading ? <Skeleton rows={4} /> : analysis ? <><div className={`signal ${analysis.signal.toLowerCase()}`}>{analysis.signal.toUpperCase()}</div><h2>{analysis.headline}</h2><div className="insight-list">{analysis.evidence.map((item) => <div key={item}><Check size={14} />{item}</div>)}</div><div className="method-note">{analysis.method}</div></> : <Empty title="NO INSIGHT" body="Select a supported symbol to calculate an interpretable snapshot." />}</Panel></div><Panel><div className="panel-heading"><div><div className="eyebrow">LATEST FEATURE VECTOR</div><h2>{latest?.date ?? "—"}</h2></div><span className="mono muted">{anomaly?.method ?? "—"}</span></div>{featureEntries.length ? <div className="feature-grid">{featureEntries.map(([name, value]) => <span key={name}><b>{name.replaceAll("_", " ").toUpperCase()}</b><strong className="mono">{value.toLocaleString("en-IN", { maximumFractionDigits: 2 })}</strong></span>)}</div> : <Skeleton rows={3} />}<p className="fine-print">Top unusual features: {latest?.top_features.join(", ") || "calculating"}. {anomaly?.note}</p></Panel></>;
}

function BenchmarkPage() { return <RealBenchmark />; }

function HistoryPage({ lab }: { lab: Lab | null }) {
  const [query, setQuery] = useState("");
  const trades = (lab?.trades ?? []).filter((trade) => `${trade.trade_id} ${trade.symbol} ${trade.buy_order_id} ${trade.sell_order_id}`.toLowerCase().includes(query.toLowerCase()));
  const csv = trades.map((trade) => `${trade.trade_id},${trade.symbol},${trade.price},${trade.quantity},${trade.timestamp}`).join("\n");
  return <><SectionTitle eyebrow="08 / AUDIT TRAIL" title="Trade History" subtitle="Inspect the newest 100 executions; export the complete session for replay" action={<div className="control-row"><label className="search-inline"><Search size={14} /><input aria-label="Search trades" placeholder="Search trade ID or symbol" value={query} onChange={(event) => setQuery(event.target.value)} /></label><button className="secondary-button" onClick={() => download("trade-history.csv", `trade_id,symbol,price,quantity,timestamp\n${csv}`, true)}><Download size={14} /> Export CSV</button></div>} />{trades.length ? <Panel><div className="table-scroll"><table className="data-table"><thead><tr><th>TIME</th><th>SYMBOL</th><th>PRICE</th><th>QTY</th><th>TRADE ID</th><th>BUY ORDER</th><th>SELL ORDER</th></tr></thead><tbody>{trades.slice().reverse().map((trade) => <tr key={trade.trade_id}><td className="mono">{new Date(trade.timestamp).toLocaleTimeString()}</td><td>{trade.symbol}</td><td className="mono">{inr(trade.price)}</td><td className="mono">{number(trade.quantity)}</td><td className="mono">TV-{String(trade.trade_id).padStart(5, "0")}</td><td className="mono muted">{trade.buy_order_id}</td><td className="mono muted">{trade.sell_order_id}</td></tr>)}</tbody></table></div></Panel> : <Panel><Empty title="NO TRADE HISTORY" body="Load the engine demo to generate a searchable execution trail." /></Panel>}</>;
}

export default function App() {
  const [entered, setEntered] = useState(() => sessionStorage.getItem("trade-velocity-entered") === "1");
  const [page, setPage] = useState<Page>("engine");
  const [navOpen, setNavOpen] = useState(false);
  const [market, setMarket] = useState<Market | null>(null);
  const [lab, setLab] = useState<Lab | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState("RELIANCE");
  const [labSymbol, setLabSymbol] = useState("ACME");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const enter = () => { sessionStorage.setItem("trade-velocity-entered", "1"); setEntered(true); };
  const load = async () => { setLoading(true); setError(""); try { const [marketResult, labResult] = await Promise.all([api<Market>("/market"), api<Lab>(`/lab?symbol=${labSymbol}`)]); setMarket(marketResult); setLab(labResult); } catch (cause) { setError(cause instanceof Error ? cause.message : "Engine connection lost."); } finally { setLoading(false); } };
  const loadLab = async (symbol = labSymbol) => { try { setLab(await api<Lab>(`/lab?symbol=${symbol}`)); } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not read the order book."); } };
  const loadDemo = async () => { try { await api<{ events: number }>("/lab/demo", { method: "POST" }); await loadLab("ACME"); } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not load the demo flow."); } };
  useEffect(() => { if (entered) void load(); }, [entered]);
  useEffect(() => { if (entered) void loadLab(labSymbol); }, [labSymbol]);
  const content = useMemo(() => { if (loading && !market) return <div className="loading-screen"><RefreshCw className="spin" size={22} /> Connecting to Python engine…</div>; if (error && !market) return <div className="connection-error"><Server size={28} /><h2>ENGINE CONNECTION LOST</h2><p>{error}</p><button className="primary-button" onClick={load}><RefreshCw size={15} /> Retry connection</button></div>; if (!market) return null; switch (page) { case "engine": return <EnginePage lab={lab} loadDemo={loadDemo} loading={loading} market={market} />; case "orderbook": return <OrderBookPage lab={lab} loadDemo={loadDemo} selectedSymbol={labSymbol} setSelectedSymbol={setLabSymbol} changed={() => void loadLab()} />; case "dsa": return <DsaLabPage />; case "simulator": return <SimulatorPage changed={() => void loadLab()} />; case "watchdog": return <Watchdog changed={() => { setLabSymbol("ACME"); void loadLab("ACME"); }} />; case "analytics": return <AnalyticsPage market={market} selectedSymbol={selectedSymbol} setSelectedSymbol={setSelectedSymbol} />; case "ai": return <AiMonitorPage market={market} selectedSymbol={selectedSymbol} setSelectedSymbol={setSelectedSymbol} />; case "benchmark": return <BenchmarkPage />; case "history": return <><LabSessionTools changed={() => void loadLab()} /><HistoryPage lab={lab} /></>; } }, [page, market, lab, loading, error, selectedSymbol, labSymbol]);
  if (!entered) return <Welcome enter={enter} />;
  return <div className="app-shell"><Sidebar page={page} setPage={setPage} open={navOpen} close={() => setNavOpen(false)} /><div className="workspace"><Topbar page={page} market={market} selectedSymbol={selectedSymbol} setSelectedSymbol={setSelectedSymbol} refresh={load} toggleNav={() => setNavOpen(true)} /><main className="content"><div className="data-strip"><span><CircleDot size={11} /> LOCAL ENGINE / LOOPBACK</span><span>{market?.source ?? "PYTHON MATCHING ENGINE"}</span><span>DATA AS OF {market?.as_of ?? "—"}</span></div>{error && market && <div className="notice error"><X size={15} /> {error}</div>}{content}<footer><span>TRADE VELOCITY · ACADEMIC ALGORITHM LAB</span><span>All orders are simulated · No financial advice</span></footer></main></div></div>;
}

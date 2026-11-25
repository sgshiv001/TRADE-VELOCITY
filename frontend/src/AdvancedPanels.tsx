import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { api, ApiError, inr, number, tradeTime } from "./api";

type Wallet = {
  cash: string; available_cash: string; reserved: string; equity: string; invested: string;
  realized: string; unrealized: string; contributed: string; holdings_value: string; market_as_of: string; market_source: string;
  holdings: {symbol: string; quantity: number; average_cost: string; mark: string; mark_source: string; value: string; pnl: string}[];
  activity: {id: string; amount: string; timestamp: string | null; description: string; symbol?: string}[];
};

export type Profile = {revision: number; name: string; watchlists: {name: string; symbols: string[]}[]};
type Executions = {unread: number; items: {id: number; symbol: string; price: number; quantity: number; timestamp: string | null; read: boolean}[]};
type Journal = {total: number; orders: {
  order_id: string; symbol: string; side: string; order_type: string; requested_price: string | null;
  filled_quantity: number; remaining_quantity: number; average_fill_price: string | null; timestamp: string | null; status: string;
}[]};
type Analyst = {
  symbol: string; company: string; as_of: string; source: string; stale: boolean; signal: string;
  recommendation: string; recommendation_reason: string; evidence: string[]; risk_flags: string[]; macd_histogram: number;
  forecast: {horizon: string; method: string; reference_price: number; point: number; lower: number; upper: number;
    change_pct: number; interval_target: number; calibration_samples: number; ridge_mae_pct: number; baseline_mae_pct: number} | null;
};

const errorText = (error: unknown) => error instanceof Error ? error.message : "The request could not be completed.";
const statusLabels: Record<string, string> = {open: "Open", filled: "Filled", cancelled: "Cancelled", expired: "Expired", partially_filled: "Partially filled"};

function useResource<T>(path: string, revision = 0) {
  const [result, setResult] = useState<{path: string; data: T}>();
  const [error, setError] = useState("");
  const [refreshCount, retry] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    api<T>(path, {signal: controller.signal}).then(data => {
      if (!controller.signal.aborted) { setResult({path, data}); setError(""); }
    }).catch(cause => { if (!controller.signal.aborted) setError(errorText(cause)); });
    return () => controller.abort();
  }, [path, revision, refreshCount]);
  return {data: result?.path === path ? result.data : undefined, error, reload: () => retry(value => value + 1)};
}

function Header({title, children}: {title: string; children?: ReactNode}) {
  return <div className="section-title"><div><h1>{title}</h1>{children && <p>{children}</p>}</div></div>;
}

function Metrics({items}: {items: [string, string | number][]}) {
  return <div className="metric-grid four">{items.map(([label, value]) => <div className="metric-card" key={label}>
    <span className="metric-head">{label}</span><strong className="metric-value">{value}</strong>
  </div>)}</div>;
}

export function PaperPortfolio({funds, revision}: {funds: boolean; revision: number}) {
  const wallet = useResource<Wallet>("/account/portfolio", revision);
  const [input, setInput] = useState("");
  const [review, setReview] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [failure, setFailure] = useState("");
  const pending = useRef<{amount: number; key: string} | null>(null);
  async function add() {
    setBusy(true); setFailure("");
    const draft = pending.current ?? {amount: Number(input), key: crypto.randomUUID()};
    pending.current = draft;
    try {
      await api("/account/funds", {method: "POST", body: JSON.stringify({amount: draft.amount}), requestKey: draft.key});
      pending.current = null;
      setNotice(`Added ${inr(draft.amount)} in virtual funds.`);
      setInput(""); setReview(false); wallet.reload();
    } catch (error) {
      if (error instanceof ApiError && error.status < 500) pending.current = null;
      setFailure(errorText(error));
    } finally { setBusy(false); }
  }
  const data = wallet.data;
  return <><Header title={funds ? "Virtual funds" : "Portfolio"}>Funded paper trading account · INR</Header>
    {wallet.error && <p className="notice error" role="alert">{wallet.error}</p>}
    {!data && !wallet.error && <p role="status">Loading account…</p>}
    {data && <>
      <Metrics items={funds
        ? [["Available cash", inr(data.available_cash)], ["Reserved cash", inr(data.reserved)], ["Cash balance", inr(data.cash)], ["Virtual funds credited", inr(data.contributed)]]
        : [["Account value", inr(data.equity)], ["Holdings value", inr(data.holdings_value)], ["Realized P&L", inr(data.realized)], ["Unrealized P&L", inr(data.unrealized)]]} />
      {funds ? <>
        <section className="panel">
          <h2>Add virtual funds</h2>
          <form className="v1-inline" onSubmit={event => { event.preventDefault(); setReview(true); }}>
            <label>Amount in INR<input type="number" required min={1000} max={1000000} step={1}
              value={input} disabled={review || busy} onChange={event => setInput(event.target.value)} /></label>
            {!review && <button className="primary-button">Review top-up</button>}
          </form>
          {review && <div className="confirmation">
            <p>Credit {inr(input)} to your paper account?</p>
            <button className="primary-button" disabled={busy} onClick={() => void add()}>{pending.current ? "Retry top-up" : "Confirm top-up"}</button>
            <button className="secondary-button" disabled={busy || Boolean(pending.current)} onClick={() => setReview(false)}>Back</button>
          </div>}
          {notice && <p className="notice" role="status">{notice}</p>}
          {failure && <p className="notice error" role="alert">{failure}</p>}
        </section>
        <section className="panel"><h2>Wallet activity</h2>{data.activity.length ? <div className="table-scroll"><table className="data-table"><thead><tr><th>Date</th><th>Entry</th><th>Amount</th></tr></thead><tbody>
          {[...data.activity].sort((a, b) => (b.timestamp ?? "").localeCompare(a.timestamp ?? "")).map(row =>
            <tr key={row.id}><td>{tradeTime(row.timestamp)}</td><td>{row.description}{row.symbol && ` · ${row.symbol}`}</td><td>{inr(row.amount)}</td></tr>)}
        </tbody></table></div> : <p className="workspace-copy">You have no fills or top-ups yet.</p>}</section>
      </> : <section className="panel"><h2>Holdings</h2>
        <p className="fine-print">{data.market_source} · Daily prices through {data.market_as_of}. Practice symbols use the last simulated fill.</p>
        {data.holdings.length ? <div className="table-scroll"><table className="data-table"><thead><tr><th>Symbol</th><th>Shares</th><th>Average cost</th><th>Reference</th><th>Value</th><th>Open P&L</th></tr></thead><tbody>
          {data.holdings.map(row => <tr key={row.symbol}><td>{row.symbol}</td><td>{number(row.quantity)}</td><td>{inr(row.average_cost)}</td>
            <td>{inr(row.mark)} · {row.mark_source === "daily_close" ? "Daily close" : "Simulated fill"}</td><td>{inr(row.value)}</td><td>{inr(row.pnl)}</td></tr>)}
        </tbody></table></div> : <p className="workspace-copy">Holdings appear when a buy order fills in the funded book.</p>}
      </section>}
    </>}
  </>;
}

export function Ledger({hosted, revision}: {hosted: boolean; revision: number}) {
  const [venue, setVenue] = useState(hosted ? "/paper" : "/lab");
  const [offset, setOffset] = useState(0);
  const journal = useResource<Journal>(`${venue}/order-history?offset=${offset}`, revision);
  return <><Header title="Orders">Track how each order was handled by the matching engine.</Header>
    {hosted && <label className="v1-inline">Order book<select value={venue} onChange={event => { setVenue(event.target.value); setOffset(0); }}>
      <option value="/paper">Funded paper book</option><option value="/exchange">Shared practice book</option><option value="/lab">Private practice archive</option>
    </select></label>}
    <section className="panel">
      {journal.error && <p className="notice error" role="alert">{journal.error}</p>}
      {journal.data && <><div className="table-scroll"><table className="data-table"><thead><tr><th>Time</th><th>Symbol</th><th>Side</th><th>Type</th><th>Limit</th><th>Filled</th><th>Resting</th><th>Average fill</th><th>Status</th></tr></thead><tbody>
        {journal.data.orders.map(row => <tr key={row.order_id}><td>{tradeTime(row.timestamp)}</td><td>{row.symbol}</td><td>{row.side}</td>
          <td>{row.order_type}</td><td>{row.requested_price ? inr(row.requested_price) : "—"}</td><td>{row.filled_quantity}</td>
          <td>{row.remaining_quantity}</td><td>{row.average_fill_price ? inr(row.average_fill_price) : "—"}</td><td>{statusLabels[row.status]}</td></tr>)}
      </tbody></table></div>
      {!journal.data.total && <p className="workspace-copy">No orders in this book yet.</p>}
      {journal.data.total > 50 && <div className="title-actions">
        <button className="secondary-button" disabled={!offset} onClick={() => setOffset(value => Math.max(0, value - 50))}>Previous orders</button>
        <button className="secondary-button" disabled={offset + 50 >= journal.data.total} onClick={() => setOffset(value => value + 50)}>Next orders</button>
      </div>}</>}
    </section>
  </>;
}

export function Inbox({revision}: {revision: number}) {
  const inbox = useResource<Executions>("/account/notifications", revision);
  const [error, setError] = useState("");
  async function mark() {
    try { await api("/account/notifications/read", {method: "POST"}); inbox.reload(); setError(""); }
    catch (cause) { setError(errorText(cause)); }
  }
  return <><Header title="Notifications">Recent fills and read status across your signed-in devices.</Header>
    <section className="panel">
      <div className="panel-heading"><h2>Executions {inbox.data && `· ${inbox.data.unread} unread`}</h2>
        <button className="secondary-button" disabled={!inbox.data?.unread} onClick={() => void mark()}>Mark all read</button></div>
      {(error || inbox.error) && <p className="notice error" role="alert">{error || inbox.error}</p>}
      {inbox.data?.items.map(row => <div className="v1-notification" key={row.id}><strong>{row.symbol} · {row.quantity} shares at {inr(row.price)}</strong><span>{row.read ? "Read" : "Unread"} · {tradeTime(row.timestamp)}</span></div>)}
      {inbox.data && !inbox.data.items.length && <p className="workspace-copy">There are no funded paper fills yet.</p>}
    </section></>;
}

export function EditLists({profile, save, select}: {profile: Profile; save(draft: Profile): Promise<Profile>; select(symbol: string): void}) {
  const [draft, setDraft] = useState(profile);
  const [selected, setSelected] = useState(0);
  const [stock, setStock] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const list = draft.watchlists[selected] ?? draft.watchlists[0];
  function update(patch: Partial<typeof list>) {
    setDraft(value => ({...value, watchlists: value.watchlists.map((row, index) => index === selected ? {...row, ...patch} : row)}));
  }
  function addStock(event: FormEvent) {
    event.preventDefault();
    const symbol = stock.trim().toUpperCase();
    if (!list.symbols.includes(symbol) && list.symbols.length < 50) update({symbols: [...list.symbols, symbol]});
    setStock("");
  }
  async function commit() {
    setBusy(true);
    try { setDraft(await save(draft)); setNotice("Saved to your account."); }
    catch (cause) { setNotice(errorText(cause)); }
    finally { setBusy(false); }
  }
  return <><Header title="Watchlists">Saved lists follow your account across devices.</Header><section className="panel">
    <div className="v1-inline"><label>List<select value={selected} onChange={event => setSelected(Number(event.target.value))}>{draft.watchlists.map((row, index) => <option key={index} value={index}>{row.name}</option>)}</select></label>
      <button className="secondary-button" disabled={draft.watchlists.length >= 12} onClick={() => {
        setSelected(draft.watchlists.length);
        setDraft({...draft, watchlists: [...draft.watchlists, {name: `New list ${draft.watchlists.length + 1}`, symbols: []}]});
      }}>New list</button>
      <button className="secondary-button" disabled={draft.watchlists.length === 1} onClick={() => {
        setDraft({...draft, watchlists: draft.watchlists.filter((_, index) => index !== selected)}); setSelected(0);
      }}>Remove list</button></div>
    <label className="v1-inline">List name<input value={list.name} maxLength={50} onChange={event => update({name: event.target.value})} /></label>
    <form className="v1-inline" onSubmit={addStock}><label>Stock symbol<input required maxLength={16} pattern={String.raw`[A-Za-z][A-Za-z0-9.&\-]*`} value={stock} onChange={event => setStock(event.target.value)} /></label><button className="secondary-button">Add symbol</button></form>
    {list.symbols.map((symbol, index) => <div key={symbol} className="v1-symbol">
      <button className="text-button" onClick={() => select(symbol)}>{symbol}</button>
      <button className="secondary-button" disabled={!index} aria-label={`Move ${symbol} up`} onClick={() => {
        const symbols = [...list.symbols]; [symbols[index - 1], symbols[index]] = [symbols[index], symbols[index - 1]]; update({symbols});
      }}>Move up</button>
      <button className="secondary-button" aria-label={`Remove ${symbol}`} onClick={() => update({symbols: list.symbols.filter(item => item !== symbol)})}>Remove</button>
    </div>)}
    <div className="title-actions"><button className="primary-button" disabled={busy} onClick={() => void commit()}>Save watchlists</button>
      {profile.revision !== draft.revision && <button className="secondary-button" onClick={() => { setDraft(profile); setSelected(0); setNotice(""); }}>Load saved lists</button>}</div>
    {notice && <p role="status" className="notice">{notice}</p>}
  </section></>;
}

export function AnalystPage({symbol}: {symbol: string}) {
  const {data, error} = useResource<Analyst>(`/analyst/${encodeURIComponent(symbol)}`);
  return <><Header title="AI Analyst">{symbol} · Data, signals and a one-session forecast.</Header>
    {error && <p className="notice error" role="alert">{error}</p>}
    {!data && !error && <p role="status">Analysing daily data…</p>}
    {data && <>
      <Metrics items={[["Paper signal", data.recommendation], ["Historical trend", data.signal], ["MACD histogram", data.macd_histogram], ["Data through", data.as_of]]} />
      <section className="panel"><h2>{data.company}</h2><p>{data.recommendation_reason}</p>
        {data.evidence.map(item => <p key={item} className="workspace-copy">{item}</p>)}
        {data.risk_flags.map(item => <p key={item} className="fine-print">{item}</p>)}
        <p className="fine-print">{data.source} · {data.as_of}</p>
      </section>
      {data.forecast && <section className="panel"><h2>{data.stale ? "Historical forecast" : data.forecast.horizon}</h2>
        <p>{data.forecast.method} · Reference {inr(data.forecast.reference_price)}</p>
        <Metrics items={[["Lower estimate", inr(data.forecast.lower)], ["Point estimate", inr(data.forecast.point)], ["Upper estimate", inr(data.forecast.upper)], ["Estimated change", `${data.forecast.change_pct}%`]]} />
        <p className="fine-print">The range targets {data.forecast.interval_target}% coverage using {data.forecast.calibration_samples} separate historical errors. Market changes can move results outside the range.</p>
        <p className="fine-print">Model selection mean absolute log-return error: ridge {data.forecast.ridge_mae_pct}% · baseline {data.forecast.baseline_mae_pct}%.</p>
      </section>}
    </>}
  </>;
}

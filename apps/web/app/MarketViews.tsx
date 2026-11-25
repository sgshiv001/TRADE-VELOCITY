"use client";

import { useMemo, useState } from "react";
import { ArrowUpRight, Star } from "lucide-react";
import { useResource, type Wallet } from "../../../frontend/src/AdvancedPanels";
import { download, inr, number, tradeTime } from "../../../frontend/src/api";
import type { Company, Market, Trade } from "../../../frontend/src/types";
import { DataState } from "./Terminal";

export function PriceChange({value}: {value: number | null}) {
  return <span className={value == null ? "" : value >= 0 ? "tv2-up" : "tv2-down"}>
    {value == null ? "—" : `${value > 0 ? "+" : ""}${value.toFixed(2)}%`}
  </span>;
}

function Instruments({companies, trade, watched, toggle}: {
  companies: Company[]; trade(symbol: string): void; watched?: string[]; toggle?(symbol: string): void;
}) {
  return <div className="tv2-table-scroll"><table className="tv2-table">
    <thead><tr><th>Instrument</th><th>Sector</th><th>Daily close</th><th>Day change</th><th>Volume</th>{toggle && <th>Watchlist</th>}</tr></thead>
    <tbody>{companies.map(company => <tr key={company.symbol}>
      <td><button className="tv2-symbol-link" onClick={() => trade(company.symbol)}>
        <span className="tv2-symbol-glyph">{company.symbol.slice(0, 2)}</span><span><strong>{company.symbol}</strong><small>{company.name}</small></span>
      </button></td>
      <td>{company.sector}</td><td>{inr(company.price)}</td><td><PriceChange value={company.day_change} /></td>
      <td>{number(company.volume)}</td>
      {toggle && <td><button className="tv2-icon" aria-label={`${watched?.includes(company.symbol) ? "Remove" : "Watch"} ${company.symbol}`}
        aria-pressed={!!watched?.includes(company.symbol)} onClick={() => toggle(company.symbol)}><Star size={16} /></button></td>}
    </tr>)}</tbody>
  </table>{!companies.length && <p className="tv2-data-state">No instruments match these filters.</p>}</div>;
}

export function Overview({wallet, market, watched, trade, onMarkets}: {
  wallet?: Wallet; market?: Market; watched: string[]; trade(symbol: string): void; onMarkets(): void;
}) {
  const positions = wallet?.holdings ?? [];
  const names = market?.companies ?? [];
  const watchlist = names.filter(company => watched.includes(company.symbol));
  const up = names.filter(company => (company.day_change ?? 0) > 0).sort((a, b) => (b.day_change ?? 0) - (a.day_change ?? 0));
  const down = names.filter(company => (company.day_change ?? 0) < 0).sort((a, b) => (a.day_change ?? 0) - (b.day_change ?? 0));
  return <>
    <div className="tv2-heading"><div><span className="tv2-kicker">PAPER TRADING WORKSPACE</span><h1>Overview</h1>
      <p>Your account, watchlist, and the latest available closing data.</p></div>
      <button className="tv2-button" onClick={() => trade("RELIANCE")}>Open terminal <ArrowUpRight size={17} /></button>
    </div>
    <div className="tv2-overview-layout">
      <section className="tv2-surface tv2-equity">
        <span className="tv2-kicker">Account equity</span><strong className="tv2-equity-value">{wallet ? inr(wallet.equity) : "—"}</strong>
        <p>Virtual cash and marked holdings</p>
        <div className="tv2-overview-stats">
          {[["Available cash", wallet?.available_cash], ["Holdings", wallet?.holdings_value],
            ["Realized P&L", wallet?.realized], ["Unrealized P&L", wallet?.unrealized]].map(([label, value]) =>
            <span key={label}><small>{label}</small><strong>{value == null ? "—" : inr(value)}</strong></span>)}
        </div>
      </section>
      <section className="tv2-surface tv2-allocation">
        <div className="tv2-panel-head"><h2>Holdings allocation</h2></div>
        {positions.length ? positions.slice(0, 5).map(row => {
          const weight = Number(row.value) / Number(wallet?.holdings_value) * 100;
          return <div className="tv2-allocation-line" key={row.symbol}><span>{row.symbol}</span>
            <progress max={100} value={Number.isFinite(weight) ? weight : 0} aria-label={`${row.symbol} allocation`} />
            <strong>{inr(row.value)}</strong></div>;
        }) : <p>Positions appear here once a demo order fills.</p>}
      </section>
    </div>
    <div className="tv2-movers">
      {([["Top gainers", up], ["Top losers", down]] as const).map(([label, companies]) =>
        <section className="tv2-surface" key={label}>
          <div className="tv2-panel-head"><h2>{label}</h2><span className="tv2-badge">NSE snapshot</span></div>
          {companies.slice(0, 4).map(company => <button className="tv2-mover" key={company.symbol} onClick={() => trade(company.symbol)}>
            <strong>{company.symbol}</strong><span>{inr(company.price)}</span><PriceChange value={company.day_change} />
          </button>)}
          {!companies.length && <p>No movers for the latest available snapshot.</p>}
        </section>)}
    </div>
    <section className="tv2-surface"><div className="tv2-panel-head"><h2>Your watchlist</h2><button className="tv2-button tv2-outline" onClick={onMarkets}>Browse markets</button></div>
      {watchlist.length ? <Instruments companies={watchlist} trade={trade} /> : <p>Star an instrument in Markets to add it to your watchlist.</p>}
      {market && <p className="tv2-source">{market.source} · {market.as_of}</p>}
    </section>
  </>;
}

export function Explore({market, error, retry, trade, watched, toggle}: {
  market?: Market; error: string; retry(): void; trade(symbol: string): void; watched: string[]; toggle?(symbol: string): void;
}) {
  const [query, setQuery] = useState("");
  const [sector, setSector] = useState("");
  const [sort, setSort] = useState("symbol");
  const sectors = [...new Set(market?.companies.map(row => row.sector))].sort();
  const companies = useMemo(() => {
    const term = query.trim().toLowerCase();
    return market?.companies.filter(company => (!sector || company.sector === sector) &&
      `${company.symbol} ${company.name}`.toLowerCase().includes(term)).sort((a, b) =>
      sort === "volume" ? b.volume - a.volume : sort === "change" ? (b.day_change ?? -Infinity) - (a.day_change ?? -Infinity) : a.symbol.localeCompare(b.symbol)) ?? [];
  }, [market, query, sector, sort]);
  return <>
    <div className="tv2-heading"><div><h1>Explore markets</h1><p>Screen supported NSE instruments using the latest available daily data.</p></div></div>
    <section className="tv2-surface">
      <div className="tv2-filters">
        <label>Filter stocks<input placeholder="Symbol or company" value={query} onChange={event => setQuery(event.target.value)} /></label>
        <label>Sector<select value={sector} onChange={event => setSector(event.target.value)}><option value="">All sectors</option>
          {sectors.map(value => <option key={value}>{value}</option>)}</select></label>
        <label>Sort by<select value={sort} onChange={event => setSort(event.target.value)}><option value="symbol">Symbol</option><option value="change">Day change</option><option value="volume">Volume</option></select></label>
      </div>
      {market ? <Instruments companies={companies} trade={trade} watched={watched} toggle={toggle} />
        : <DataState error={error} retry={retry} loading="Loading market coverage…" />}
      {market && <p className="tv2-source">{market.source} · {market.as_of}</p>}
    </section>
  </>;
}

export function ExecutedTrades({funded, revision}: {funded: boolean; revision: number}) {
  const [search, setSearch] = useState("");
  const [current, setCurrent] = useState("");
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState("");
  const path = `/${funded ? "paper" : "lab"}/trades`;
  const query = new URLSearchParams({offset: String(offset), limit: "50", query: current});
  const response = useResource<{total: number; trades: Trade[]}>(`${path}?${query}`, revision);
  async function exportCsv() {
    setError("");
    try { await download(`${path}/export`, "tradevelocity-executions.csv"); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "The export is unavailable."); }
  }
  return <>
    <div className="tv2-heading"><div><h1>Trade history</h1><p>Review completed executions and export their details.</p></div><button className="tv2-button tv2-outline" onClick={() => void exportCsv()}>Export CSV</button></div>
    <section className="tv2-surface">
      <form className="tv2-filters" onSubmit={event => { event.preventDefault(); setCurrent(search); setOffset(0); }}>
        <label>Search executions<input placeholder="Symbol or order ID" maxLength={100} value={search} onChange={event => setSearch(event.target.value)} /></label>
        <button className="tv2-button">Search</button>
      </form>
      {error && <p role="alert">{error}</p>}
      {!response.data ? <DataState error={response.error} retry={response.reload} loading="Loading executions…" /> :
        <><div className="tv2-table-scroll"><table className="tv2-table"><thead><tr><th>Time</th><th>Symbol</th><th>Price</th><th>Shares</th><th>Trade ID</th></tr></thead>
          <tbody>{response.data.trades.map(row => <tr key={row.trade_id}><td>{tradeTime(row.timestamp)}</td><td>{row.symbol}</td>
            <td>{inr(row.price)}</td><td>{number(row.quantity)}</td><td>{row.trade_id}</td></tr>)}</tbody></table></div>
          <div className="tv2-pagination"><span>{response.data.total ? `${offset + 1}–${Math.min(offset + 50, response.data.total)} of ${response.data.total}` : "No matching executions"}</span>
            <button className="tv2-button tv2-outline" disabled={!offset} onClick={() => setOffset(value => Math.max(0, value - 50))}>Previous</button>
            <button className="tv2-button tv2-outline" disabled={offset + 50 >= response.data.total} onClick={() => setOffset(value => value + 50)}>Next</button></div></>}
    </section>
  </>;
}

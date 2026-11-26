"use client";

import { useEffect, useState } from "react";
import { useResource } from "../../../frontend/src/AdvancedPanels";
import { api, inr, number, tradeTime } from "../../../frontend/src/api";
import { MarketPrice, OrderTicket } from "../../../frontend/src/Trading";
import type { Company, Depth, History, Lab, Quote } from "../../../frontend/src/types";
import type { Theme } from "./Appearance";
import { ChartStyle, ExchangeChartLink, MarketChart, type ChartMode } from "./MarketChart";
import { QuoteChart, useQuoteSession, type QuoteChartMode } from "./QuoteChart";

const quoteStyles = {baseline: "Baseline", line: "Line", area: "Area"};

export function DataState({error, retry, loading}: {error: string; retry: () => void; loading: string}) {
  return <div className="tv2-data-state" role={error ? "alert" : "status"}>
    <span>{error || loading}</span>{error && <button className="tv2-button tv2-outline" onClick={retry}>Retry</button>}
  </div>;
}

function Levels({side, levels}: {side: "Bid" | "Ask"; levels: Depth[]}) {
  const max = Math.max(1, ...levels.map(level => level.quantity));
  return <div className={side === "Bid" ? "tv2-bids" : "tv2-asks"}>
    <div className="tv2-level"><span>{side} price</span><span>Shares</span></div>
    {levels.slice(0, 7).map(level => <div className="tv2-level" key={level.price}>
      <i style={{width: `${level.quantity / max * 100}%`}} /><strong>{inr(level.price)}</strong><span>{number(level.quantity)}</span>
    </div>)}
    {!levels.length && <p>No resting {side === "Bid" ? "bids" : "asks"}</p>}
  </div>;
}

export default function Terminal({symbol, company, funded, theme, revision, online, refresh, holdings, cash}: {
  symbol: string; company?: Company; funded: boolean; theme: Theme; revision: number; online: boolean;
  refresh(): Promise<void>; holdings?: number; cash?: string;
}) {
  const [period, setPeriod] = useState("3M");
  const [view, setView] = useState<"history" | "intraday">("history");
  const [mode, setMode] = useState<ChartMode>("candles");
  const [quoteMode, setQuoteMode] = useState<QuoteChartMode>("baseline");
  const [average, setAverage] = useState(false);
  const [showVolume, setShowVolume] = useState(true);
  const [follow, setFollow] = useState(funded);
  const [refreshingDepth, setRefreshingDepth] = useState(false);
  const [quoteCycle, setQuoteCycle] = useState(0);
  const [sidePanel, setSidePanel] = useState<"order" | "depth">("order");
  const [depthError, setDepthError] = useState("");
  const current = encodeURIComponent(symbol);
  const book = useResource<Lab>(`/${funded ? "paper" : "lab"}?symbol=${current}`, revision);
  const reference = useResource<Quote>(`/quote/${current}`, quoteCycle);
  const chart = useResource<History>(view === "history" ? `/companies/${current}?period=${period}` : null);
  const receivedQuote = reference.data ?? null;
  const quoteSession = useQuoteSession(symbol, receivedQuote);
  const quote = receivedQuote?.kind === "intraday" && quoteSession &&
    Date.parse(receivedQuote.as_of ?? "") < quoteSession.points.at(-1)!.time * 1000 ? quoteSession.latest : receivedQuote;

  useEffect(() => {
    if (!online) return;
    const timer = window.setInterval(() => { if (!document.hidden) setQuoteCycle(count => count + 1); }, 60_000);
    return () => window.clearInterval(timer);
  }, [online]);

  useEffect(() => {
    if (!funded || !follow || !online || !quote?.simulation_supported || quote.price == null) return;
    const controller = new AbortController();
    api<{updated: boolean}>(`/paper/liquidity/${current}?follow=true`, {method: "POST", signal: controller.signal, timeoutMs: 20_000})
      .then(result => {
        if (controller.signal.aborted) return;
        setDepthError("");
        if (result.updated) void refresh();
      })
      .catch(error => { if (!controller.signal.aborted) setDepthError(error.message); });
    return () => controller.abort();
  }, [funded, follow, online, quote, current, refresh]);

  async function reloadDepth() {
    setRefreshingDepth(true);
    setDepthError("");
    try {
      await api(`/paper/liquidity/${current}`, {method: "POST", timeoutMs: 20_000});
      await refresh();
    } catch (error) {
      setDepthError(error instanceof Error ? error.message : "Simulated depth could not refresh.");
    } finally {
      setRefreshingDepth(false);
    }
  }

  return <>
    <div className="tv2-heading"><div><span className="tv2-kicker">NSE · {company?.sector ?? "Paper trading"}</span>
      <h1>{company?.name ?? symbol}</h1><p>{symbol} · {funded ? "Funded paper trading" : "Local practice session"}</p></div>
      <MarketPrice quote={quote ?? (reference.error ? {symbol, price: null, kind: "unavailable", source: null, as_of: null} : null)} />
    </div>
    {!online && <p className="tv2-info" role="status">You’re offline. Reconnect to submit an order.</p>}
    <div className="tv2-terminal">
      <section className="tv2-surface tv2-terminal-chart">
        <div className="tv2-panel-head"><h2>Price chart</h2><span className="tv2-badge">NSE · {symbol}</span></div>
        <div className="tv2-tabs" role="group" aria-label="Market chart view">
          <button aria-pressed={view === "history"} onClick={() => setView("history")}>Daily history</button>
          <button aria-pressed={view === "intraday"} onClick={() => setView("intraday")}>Intraday quotes</button>
        </div>
        {view === "history" ? <>
          <div className="tv2-chart-controls" role="group" aria-label="Daily chart options">
            {["1M", "3M", "6M", "1Y", "5Y"].map(value => <button key={value} aria-pressed={period === value} onClick={() => setPeriod(value)}>{value}</button>)}
            <ChartStyle mode={mode} setMode={setMode} />
            <label><input type="checkbox" checked={showVolume} onChange={event => setShowVolume(event.target.checked)} /> Volume</label>
            <label><input type="checkbox" checked={average} onChange={event => setAverage(event.target.checked)} /> SMA 20</label>
          </div>
          {chart.data?.history.length ? <>
            <MarketChart key={symbol + period} bars={chart.data.history} symbol={symbol} mode={mode} average={average} showVolume={showVolume} theme={theme} />
            <p className="tv2-source">{chart.data.source} · Adjusted daily prices through {chart.data.history.at(-1)?.date}.</p>
          </> : <DataState error={chart.error} retry={chart.reload} loading={chart.data ? "No bars for this period." : "Loading historical prices…"} />}
        </> : <>
          <div className="tv2-chart-controls" role="group" aria-label="Intraday chart options">
            <ChartStyle mode={quoteMode} setMode={value => setQuoteMode(value as QuoteChartMode)} styles={quoteStyles} />
            <button disabled={!online} onClick={reference.reload}>Refresh quote</button>
          </div>
          {quoteSession
            ? <QuoteChart key={`${symbol}-${quoteSession.date}-${quoteSession.source}`} session={quoteSession} symbol={symbol} mode={quoteMode} theme={theme} />
            : <DataState error={reference.error} retry={reference.reload} loading={quote ? "No intraday quote is available. View daily history or open the exchange chart below." : "Checking for an intraday quote…"} />}
          <p className="tv2-source">{!online ? "Quote checks paused while offline." : reference.error && quoteSession ? "Latest quote check failed. Showing the last observations." : "Checks every minute while this tab is visible. New timestamps appear as the provider updates."}</p>
        </>}
        {(company || quote?.simulation_supported) && <ExchangeChartLink symbol={symbol} copyOnly={navigator.userAgent.includes("Electron/")} />}
      </section>
      <div className="tv2-terminal-ticket">
        <div className="tv2-tabs" aria-label="Terminal side panel">
          <button aria-pressed={sidePanel === "order"} onClick={() => setSidePanel("order")}>Place order</button>
          <button aria-pressed={sidePanel === "depth"} onClick={() => setSidePanel("depth")}>Market depth</button>
        </div>
        {funded && <div className="tv2-ticket-balance"><span>Available <strong>{cash == null ? "—" : inr(cash)}</strong></span><span>Shares held <strong>{holdings == null ? "—" : number(holdings)}</strong></span></div>}
        {!book.data ? <DataState error={book.error} retry={book.reload} loading="Loading simulated order book…" />
          : sidePanel === "order" ? <OrderTicket key={symbol} symbol={symbol} lab={book.data} changed={refresh} quote={quote} shared={funded} funded={funded} />
          : <section className="tv2-surface tv2-depth"><div className="tv2-panel-head"><h2>Order book</h2><span className="tv2-badge">Simulated</span></div>
            <Levels side="Ask" levels={book.data.book.asks} /><Levels side="Bid" levels={book.data.book.bids} />
          </section>}
      </div>
    </div>
    {funded && <div className="tv2-liquidity">
      <label><input type="checkbox" checked={follow} onChange={event => setFollow(event.target.checked)} /> Follow provider quotes</label>
      <button className="tv2-button tv2-outline" disabled={!online || !quote?.simulation_supported || quote.price == null || refreshingDepth}
        onClick={() => void reloadDepth()}>{refreshingDepth ? "Refreshing…" : "Refresh simulated depth"}</button>
      <span>Virtual bids and offers follow supported quotes. Your confirmed limits keep their prices.</span>
      {depthError && <span role="alert">{depthError}</span>}
    </div>}
    {book.data && <section className="tv2-surface">
      <div className="tv2-panel-head"><h2>Recent executions</h2><span className="tv2-badge">Simulated fills</span></div>
      {book.data.trades.length ? <div className="tv2-table-scroll"><table className="tv2-table">
        <thead><tr><th>Time</th><th>Price</th><th>Shares</th></tr></thead>
        <tbody>{book.data.trades.slice(0, 8).map(trade => <tr key={trade.trade_id}>
          <td>{tradeTime(trade.timestamp)}</td><td>{inr(trade.price)}</td><td>{number(trade.quantity)}</td>
        </tr>)}</tbody></table></div> : <p>No executions for {symbol} yet.</p>}
    </section>}
  </>;
}

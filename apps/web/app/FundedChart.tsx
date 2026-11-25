"use client";

import { useEffect, useRef, useState } from "react";
import { CandlestickSeries, ColorType, createChart, type CandlestickData, type Time } from "lightweight-charts";
import { api, inr } from "../../../frontend/src/api";
import type { History } from "../../../frontend/src/types";

export default function FundedChart({symbol}: {symbol: string}) {
  const root = useRef<HTMLDivElement>(null);
  const [history, setHistory] = useState<History | null>(null);
  const [detail, setDetail] = useState<CandlestickData<Time>>();
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    setHistory(null); setDetail(undefined); setError("");
    api<History>(`/companies/${encodeURIComponent(symbol)}?period=6M`, {signal: controller.signal})
      .then(value => { if (!controller.signal.aborted) setHistory(value); })
      .catch(() => { if (!controller.signal.aborted) setError("Daily chart data is unavailable for this symbol."); });
    return () => controller.abort();
  }, [symbol]);
  useEffect(() => {
    if (!root.current || !history?.history.length) return;
    const chart = createChart(root.current, {autoSize: true, height: 280, layout: {
      background: {type: ColorType.Solid, color: "#111827"}, textColor: "#cbd5e1",
      attributionLogo: true,
    }, grid: {vertLines: {color: "#28354b"}, horzLines: {color: "#28354b"}},
    localization: {priceFormatter: (value: number) => inr(value)}});
    const bars = chart.addSeries(CandlestickSeries, {upColor: "#22c55e", downColor: "#ef4444",
      wickUpColor: "#22c55e", wickDownColor: "#ef4444", borderVisible: false});
    const data = history.history.map(row => ({time: row.date as Time, open: row.open, high: row.high, low: row.low, close: row.close}));
    bars.setData(data);
    const last = data.at(-1);
    setDetail(last);
    chart.subscribeCrosshairMove(event => {
      const selected = event.seriesData.get(bars);
      setDetail(selected && "open" in selected ? selected as CandlestickData<Time> : last);
    });
    chart.timeScale().fitContent();
    return () => chart.remove();
  }, [history]);
  return <section className="panel">
    <h2>{symbol} daily chart</h2>
    {error && <p className="fine-print">{error}</p>}
    {!history && !error && <p role="status">Loading historical prices…</p>}
    {history && <div ref={root} style={{height: 280}} aria-label={`${symbol} historical candlestick chart`} role="img" />}
    {detail && <p className="fine-print">{String(detail.time)} · Open {inr(detail.open)} · High {inr(detail.high)} · Low {inr(detail.low)} · Close {inr(detail.close)}</p>}
    {history && <p className="fine-print">{history.source} · {history.basis}. Scroll to zoom or drag to move through dates.</p>}
  </section>;
}

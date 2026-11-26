"use client";

import { useEffect, useRef, useState } from "react";
import { AreaSeries, BaselineSeries, LineSeries, type ISeriesApi, type Time, type UTCTimestamp } from "lightweight-charts";
import { inr } from "../../../frontend/src/api";
import type { Quote } from "../../../frontend/src/types";
import type { Theme } from "./Appearance";
import { baselineOptions, priceChart, PriceMove } from "./MarketChart";

type Observation = {time: UTCTimestamp; value: number};
type QuoteSession = {date: string; source: string; points: Observation[]; latest: Quote};
export type QuoteChartMode = "line" | "area" | "baseline";
const marketDate = new Intl.DateTimeFormat("en-IN", {timeZone: "Asia/Kolkata", dateStyle: "medium"});
const marketTime = new Intl.DateTimeFormat("en-IN", {timeZone: "Asia/Kolkata", hour: "2-digit", minute: "2-digit", hourCycle: "h23"});

export function useQuoteSession(symbol: string, quote: Quote | null) {
  const [session, setSession] = useState<QuoteSession>();
  useEffect(() => {
    if (quote?.symbol !== symbol || quote.kind !== "intraday" || !quote.as_of || !quote.source ||
        quote.price == null || !Number.isFinite(quote.price) || quote.price <= 0) return;
    const stamp = Date.parse(quote.as_of);
    if (!Number.isFinite(stamp)) return;
    const point = {time: Math.floor(stamp / 1000) as UTCTimestamp, value: quote.price};
    const date = marketDate.format(stamp);
    const source = quote.source;
    setSession(previous => {
      const last = previous?.points.at(-1);
      if (last && (point.time < last.time || (point.time === last.time && point.value === last.value && source === previous?.source))) return previous;
      const points = previous?.date === date && previous.source === source ? previous.points : [];
      const recent = (point.time === points.at(-1)?.time ? points.slice(0, -1) : points).slice(-399);
      return {date, source, points: [...recent, point], latest: quote};
    });
  }, [quote, symbol]);
  return session;
}

export function QuoteChart({session, symbol, mode, theme}: {
  session: QuoteSession; symbol: string; mode: QuoteChartMode; theme: Theme;
}) {
  const root = useRef<HTMLDivElement>(null);
  const plot = useRef<{series: ISeriesApi<"Line" | "Area" | "Baseline">; fit(): void; up: string; down: string; count: number}>(null);
  const {points, source, date} = session;
  const base = points[0].value;
  const last = points.at(-1)!;

  useEffect(() => {
    if (!root.current) return;
    const {chart, up, down} = priceChart(root.current, theme);
    const format = (time: number) => marketTime.format(time * 1000);
    chart.applyOptions({localization: {timeFormatter: format}, timeScale: {timeVisible: true,
      tickMarkFormatter: (time: Time) => typeof time === "number" ? format(time) : null}});
    const markers = {pointMarkersVisible: true, pointMarkersRadius: 3, lineWidth: 2 as const};
    const series = mode === "baseline" ? chart.addSeries(BaselineSeries, {...markers, ...baselineOptions(base, up, down)})
      : mode === "area" ? chart.addSeries(AreaSeries, markers) : chart.addSeries(LineSeries, markers);
    plot.current = {series, fit: () => chart.timeScale().fitContent(), up, down, count: 0};
    return () => { plot.current = null; chart.remove(); };
  }, [base, mode, theme]);

  useEffect(() => {
    const active = plot.current;
    if (!active) return;
    const color = last.value >= base ? active.up : active.down;
    if (mode === "line") active.series.applyOptions({color});
    if (mode === "area") active.series.applyOptions({lineColor: color, topColor: color + "55", bottomColor: color + "08"});
    active.series.setData(points);
    if (active.count < 2) active.fit();
    active.count = points.length;
  }, [base, last, mode, points, theme]);

  return <>
    <div className="tv2-ohlc" aria-label={`${symbol} latest chart observation`}>
      <span>{date} · {marketTime.format(last.time * 1000)} IST</span><strong>{inr(last.value)}</strong>
      {points.length > 1 && <PriceMove value={last.value} base={base} label="since first observation" />}
    </div>
    <div className="tv2-chart" ref={root} role="img" aria-label={`${symbol} intraday quote chart`} />
    <p className="tv2-source">{source} · {points.length} {points.length === 1 ? "observation" : "observations"} this session · Quotes may be delayed.</p>
  </>;
}

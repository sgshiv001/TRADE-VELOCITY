"use client";

import { useEffect, useRef, useState } from "react";
import {
  AreaSeries, BarSeries, BaselineSeries, CandlestickSeries, ColorType, HistogramSeries, LineSeries,
  createChart, type Time, type CandlestickData,
} from "lightweight-charts";
import { inr, number } from "../../../frontend/src/api";
import type { Theme } from "./Appearance";

export type ChartBar = {date: string; open: number; high: number; low: number; close: number; volume: number; ma20?: number | null};
export const chartStyles = {candles: "Candlesticks", bars: "OHLC bars", line: "Line", area: "Area", baseline: "Baseline"} as const;
export type ChartMode = keyof typeof chartStyles;

export function ChartStyle({mode, setMode, styles = chartStyles}: {
  mode: ChartMode; setMode(mode: ChartMode): void; styles?: Partial<Record<ChartMode, string>>;
}) {
  return <select aria-label="Chart style" value={mode} onChange={event => setMode(event.target.value as ChartMode)}>
    {Object.entries(styles).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
  </select>;
}

export function priceChart(container: HTMLElement, theme: Theme) {
  const light = theme === "light";
  const grid = light ? "#e5ebec" : "#202b31";
  const up = light ? "#087856" : "#10b981";
  const down = light ? "#b63543" : "#f37179";
  const chart = createChart(container, {
    autoSize: true,
    layout: {
      background: {type: ColorType.Solid, color: light ? "#ffffff" : "#11171d"},
      textColor: light ? "#516169" : "#9aafb7", attributionLogo: true,
    },
    grid: {horzLines: {color: grid}, vertLines: {color: grid}},
    rightPriceScale: {borderColor: grid},
    timeScale: {borderColor: grid},
    localization: {priceFormatter: inr},
  });
  return {chart, up, down};
}

export function baselineOptions(base: number, up: string, down: string) {
  return {
    baseValue: {type: "price" as const, price: base},
    topLineColor: up, topFillColor1: up + "55", topFillColor2: up + "08",
    bottomLineColor: down, bottomFillColor1: down + "08", bottomFillColor2: down + "55",
  };
}

export function MarketChart({bars, symbol, mode = "candles", average = false, showVolume = true, theme = "dark"}: {
  bars: ChartBar[]; symbol: string; mode?: ChartMode;
  average?: boolean; showVolume?: boolean; theme?: Theme;
}) {
  const root = useRef<HTMLDivElement>(null);
  const [cursor, setCursor] = useState<ChartBar>();
  useEffect(() => {
    if (!root.current || !bars.length) return;
    const {chart, up, down} = priceChart(root.current, theme);
    chart.priceScale("right").applyOptions({scaleMargins: {top: .12, bottom: showVolume ? .26 : .12}});
    const data: CandlestickData<Time>[] = bars.map(({date, open, high, low, close}) => ({
      time: date, open, high, low, close,
    }));
    const closes = data.map(({time, close}) => ({time, value: close}));
    if (mode === "candles") {
      chart.addSeries(CandlestickSeries, {
        upColor: up, downColor: down, wickUpColor: up, wickDownColor: down, borderVisible: false,
      }).setData(data);
    } else if (mode === "bars") {
      chart.addSeries(BarSeries, {upColor: up, downColor: down}).setData(data);
    } else if (mode === "baseline") {
      chart.addSeries(BaselineSeries, baselineOptions(closes[0].value, up, down)).setData(closes);
    } else {
      const trend = closes.at(-1)!.value >= closes[0].value ? up : down;
      if (mode === "line") chart.addSeries(LineSeries, {color: trend, lineWidth: 2}).setData(closes);
      else chart.addSeries(AreaSeries, {lineColor: trend, topColor: trend + "45", bottomColor: trend + "04"}).setData(closes);
    }
    if (showVolume) {
      const volume = chart.addSeries(HistogramSeries, {priceScaleId: "", priceFormat: {type: "volume"}, priceLineVisible: false, lastValueVisible: false});
      volume.priceScale().applyOptions({scaleMargins: {top: .81, bottom: 0}});
      volume.setData(bars.map(row => ({
        time: row.date, value: row.volume, color: (row.close >= row.open ? up : down) + "55",
      })));
    }
    if (average) chart.addSeries(LineSeries, {color: theme === "light" ? "#175f84" : "#65bfe6", lineWidth: 1, priceLineVisible: false})
      .setData(bars.flatMap(row => row.ma20 == null ? [] : [{time: row.date, value: row.ma20}]));
    const byDate = new Map(bars.map(row => [row.date, row]));
    setCursor(undefined);
    chart.subscribeCrosshairMove(({time}) => setCursor(typeof time === "string" ? byDate.get(time) : undefined));
    chart.timeScale().fitContent();
    return () => chart.remove();
  }, [bars, mode, average, showVolume, theme]);

  const displayed = cursor ?? bars.at(-1);
  const previous = displayed && bars[bars.indexOf(displayed) - 1];
  return <>
    {displayed && <div className="tv2-ohlc" aria-label={`${symbol} daily prices`}>
      <span>{displayed.date}</span><span>O <strong>{inr(displayed.open)}</strong></span>
      <span>H <strong>{inr(displayed.high)}</strong></span><span>L <strong>{inr(displayed.low)}</strong></span>
      <span>C <strong>{inr(displayed.close)}</strong></span><span>Vol <strong>{number(displayed.volume)}</strong></span>
      {previous && <PriceMove value={displayed.close} base={previous.close} label="vs. prior close" />}
    </div>}
    <div className="tv2-chart" ref={root} role="img" aria-label={`${symbol} historical price and volume chart`} />
  </>;
}

export function PriceMove({value, base, label}: {value: number; base: number; label: string}) {
  const change = (value - base) / base;
  const tone = change > 0 ? "tv2-up" : change < 0 ? "tv2-down" : "";
  const percent = change.toLocaleString("en-IN", {style: "percent", maximumFractionDigits: 2, signDisplay: "exceptZero"});
  return <span><b className={tone}>{percent}</b> {label}</span>;
}

export function ExchangeChartLink({symbol, copyOnly = false}: {symbol: string; copyOnly?: boolean}) {
  const url = `https://www.tradingview.com/chart/?symbol=${encodeURIComponent(`NSE:${symbol}`)}`;
  const [notice, setNotice] = useState("");
  if (copyOnly) return <div className="tv2-chart-controls">
    <button onClick={() => void navigator.clipboard.writeText(url).then(
      () => setNotice("Chart link copied"), () => setNotice(url),
    )}>Copy {symbol} TradingView link</button>
    <span className="tv2-source" role="status">{notice}</span>
  </div>;
  return <a className="tv2-exchange-chart" href={url} target="_blank" rel="noopener noreferrer">Open {symbol} on TradingView ↗</a>;
}

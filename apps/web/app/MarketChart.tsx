"use client";

import { useEffect, useRef, useState } from "react";
import {
  AreaSeries, CandlestickSeries, ColorType, HistogramSeries, LineSeries,
  createChart, type Time, type CandlestickData,
} from "lightweight-charts";
import { inr, number } from "../../../frontend/src/api";
import type { Theme } from "./Appearance";

export type ChartBar = {date: string; open: number; high: number; low: number; close: number; volume: number; ma20?: number | null};

export function MarketChart({bars, symbol, mode = "candles", average = false, theme = "dark"}: {
  bars: ChartBar[]; symbol: string; mode?: "candles" | "line" | "area";
  average?: boolean; theme?: Theme;
}) {
  const root = useRef<HTMLDivElement>(null);
  const [cursor, setCursor] = useState<ChartBar>();
  useEffect(() => {
    if (!root.current || !bars.length) return;
    const onLight = theme === "light";
    const grid = onLight ? "#e5ebec" : "#202b31";
    const up = onLight ? "#087856" : "#10b981";
    const down = onLight ? "#b63543" : "#f37179";
    const chart = createChart(root.current, {
      autoSize: true,
      layout: {
        background: {type: ColorType.Solid, color: onLight ? "#ffffff" : "#11171d"},
        textColor: onLight ? "#516169" : "#9aafb7", attributionLogo: true,
      },
      grid: {horzLines: {color: grid}, vertLines: {color: grid}},
      rightPriceScale: {borderColor: grid, scaleMargins: {top: .12, bottom: .26}},
      timeScale: {borderColor: grid},
      localization: {priceFormatter: (value: number) => inr(value)},
    });
    const data: CandlestickData<Time>[] = bars.map(({date, open, high, low, close}) => ({
      time: date, open, high, low, close,
    }));
    const closes = data.map(({time, close}) => ({time, value: close}));
    if (mode === "candles") {
      chart.addSeries(CandlestickSeries, {
        upColor: up, downColor: down, wickUpColor: up, wickDownColor: down, borderVisible: false,
      }).setData(data);
    } else if (mode === "line") {
      chart.addSeries(LineSeries, {color: up, lineWidth: 2}).setData(closes);
    } else {
      chart.addSeries(AreaSeries, {lineColor: up, topColor: up + "45", bottomColor: up + "04"}).setData(closes);
    }
    const volume = chart.addSeries(HistogramSeries, {priceScaleId: "", priceFormat: {type: "volume"}, priceLineVisible: false, lastValueVisible: false});
    volume.priceScale().applyOptions({scaleMargins: {top: .81, bottom: 0}});
    volume.setData(bars.map(row => ({
      time: row.date, value: row.volume, color: (row.close >= row.open ? up : down) + "55",
    })));
    if (average) chart.addSeries(LineSeries, {color: onLight ? "#175f84" : "#65bfe6", lineWidth: 1, priceLineVisible: false})
      .setData(bars.flatMap(row => row.ma20 == null ? [] : [{time: row.date, value: row.ma20}]));
    const byDate = new Map(bars.map(row => [row.date, row]));
    setCursor(undefined);
    chart.subscribeCrosshairMove(({time}) => setCursor(typeof time === "string" ? byDate.get(time) : undefined));
    chart.timeScale().fitContent();
    return () => chart.remove();
  }, [bars, mode, average, theme]);

  const displayed = cursor ?? bars.at(-1);
  return <>
    {displayed && <div className="tv2-ohlc" aria-label={`${symbol} daily prices`}>
      <span>{displayed.date}</span><span>O <strong>{inr(displayed.open)}</strong></span>
      <span>H <strong>{inr(displayed.high)}</strong></span><span>L <strong>{inr(displayed.low)}</strong></span>
      <span>C <strong>{inr(displayed.close)}</strong></span><span>Vol <strong>{number(displayed.volume)}</strong></span>
    </div>}
    <div className="tv2-chart" ref={root} role="img" aria-label={`${symbol} historical price and volume chart`} />
  </>;
}

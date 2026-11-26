"use client";

import { useState } from "react";
import { ChartStyle, ExchangeChartLink, MarketChart, type ChartBar, type ChartMode } from "./MarketChart";
import { inr } from "../../../frontend/src/api";

export function PublicPreview({instruments, source}: {
  instruments: {symbol: string; name: string; bars: ChartBar[]}[]; source: string;
}) {
  const [index, setIndex] = useState(0);
  const [mode, setMode] = useState<ChartMode>("candles");
  const selected = instruments[index];
  if (!selected) return null;
  const close = selected.bars.at(-1);
  return <section className="tv2-preview" aria-label="Interactive TradeVelocity preview">
    <div className="tv2-preview-top"><span>Trading terminal</span><span>Historical preview</span></div>
    <div className="tv2-preview-quote">
      <div><label htmlFor="preview-symbol">NSE instrument</label>
        <select id="preview-symbol" value={index} onChange={event => setIndex(Number(event.target.value))}>
          {instruments.map((instrument, i) => <option key={instrument.symbol} value={i}>{instrument.symbol} · {instrument.name}</option>)}
        </select></div>
      <strong>{close ? inr(close.close) : "—"}</strong>
    </div>
    <div className="tv2-chart-controls">
      <ChartStyle mode={mode} setMode={setMode} />
    </div>
    <MarketChart key={selected.symbol} bars={selected.bars} symbol={selected.symbol} mode={mode} />
    <div className="tv2-preview-source"><span>{source} · Adjusted daily bars</span><ExchangeChartLink symbol={selected.symbol} /></div>
  </section>;
}

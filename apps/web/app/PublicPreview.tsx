"use client";

import { useState } from "react";
import { MarketChart, type ChartBar } from "./MarketChart";
import { inr } from "../../../frontend/src/api";

export function PublicPreview({instruments, source}: {
  instruments: {symbol: string; name: string; bars: ChartBar[]}[]; source: string;
}) {
  const [index, setIndex] = useState(0);
  const [mode, setMode] = useState<"candles" | "area">("candles");
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
    <div className="tv2-chart-controls" aria-label="Chart style">
      <button aria-pressed={mode === "candles"} onClick={() => setMode("candles")}>Candles</button>
      <button aria-pressed={mode === "area"} onClick={() => setMode("area")}>Area</button>
    </div>
    <MarketChart key={selected.symbol} bars={selected.bars} symbol={selected.symbol} mode={mode} />
    <div className="tv2-preview-source">{source} · Adjusted daily bars</div>
  </section>;
}

import { useEffect, useState } from "react";
import type { Bar } from "./types";
import { inr } from "./api";

export default function PriceChart({ bars, symbol }: { bars: Bar[]; symbol: string }) {
  const [mode, setMode] = useState("candles"), [size, setSize] = useState(60), [end, setEnd] = useState(bars.length);
  const [hovered, setHovered] = useState<Bar | null>(null);
  useEffect(() => { setEnd(bars.length); setHovered(null); }, [bars]);
  const start = Math.max(0, end - size), visible = bars.slice(start, end);
  const low = Math.min(...visible.map(bar => bar.low)), high = Math.max(...visible.map(bar => bar.high));
  const span = Math.max(1, high - low), y = (price: number) => 180 - (price - low) / span * 160;
  const step = 920 / Math.max(1, visible.length), x = (index: number) => 20 + step * (index + .5);
  const points = visible.map((bar, index) => `${x(index)},${y(bar.close)}`).join(" ");
  const selected = hovered ?? visible.at(-1);
  return <div>
    <div className="chart-controls"><label>Chart style<select aria-label="Chart style" value={mode} onChange={event => setMode(event.target.value)}><option value="candles">Candlesticks</option><option value="line">Closing line</option></select></label><label>Visible trading days<select aria-label="Chart zoom" value={size} onChange={event => setSize(Number(event.target.value))}>{[30,60,120,250].map(value => <option key={value} value={value}>{value} days</option>)}</select></label><button className="secondary-button" disabled={start === 0} onClick={() => setEnd(Math.max(Math.min(size, bars.length), end - Math.ceil(size / 2)))}>Earlier</button><button className="secondary-button" disabled={end >= bars.length} onClick={() => setEnd(Math.min(bars.length, end + Math.ceil(size / 2)))}>Later</button></div>
    <div className="chart-readout" aria-live="polite">{selected ? <>{selected.date} · O {inr(selected.open)} · H {inr(selected.high)} · L {inr(selected.low)} · C {inr(selected.close)}</> : "No bars available"}</div>
    {visible.length > 0 && <svg className="candle-chart" viewBox="0 0 1040 210" role="img" aria-label={`${symbol} adjusted ${mode === "candles" ? "candlestick" : "closing line"} chart, ${visible.length} trading days`}>
      {[low, low + span / 2, low + span].map(value => <g key={value}><line x1="20" x2="950" y1={y(value)} y2={y(value)} className="chart-gridline" /><text x="960" y={y(value) + 4} className="chart-axis">{value.toFixed(2)}</text></g>)}
      {mode === "line" && <polyline points={points} fill="none" stroke="var(--accent)" strokeWidth="2" />}
      {visible.map((bar, index) => <g key={bar.date} onMouseEnter={() => setHovered(bar)} onFocus={() => setHovered(bar)} tabIndex={0} aria-label={`${bar.date}: open ${bar.open}, high ${bar.high}, low ${bar.low}, close ${bar.close}`}>
        <title>{bar.date}: O {inr(bar.open)} H {inr(bar.high)} L {inr(bar.low)} C {inr(bar.close)}</title>
        <rect x={x(index) - step / 2} y="15" width={step} height="180" fill="transparent" />
        {mode === "candles" ? <g fill={bar.close >= bar.open ? "var(--success)" : "var(--danger)"} stroke={bar.close >= bar.open ? "var(--success)" : "var(--danger)"}><line x1={x(index)} x2={x(index)} y1={y(bar.high)} y2={y(bar.low)} /><rect x={x(index) - Math.max(1,step * .3)} y={Math.min(y(bar.open),y(bar.close))} width={Math.max(2,step * .6)} height={Math.max(1,Math.abs(y(bar.open)-y(bar.close)))} /></g> : <circle cx={x(index)} cy={y(bar.close)} r="2" fill="var(--accent)" />}
      </g>)}
    </svg>}<div className="chart-foot"><span>{visible[0]?.date ?? "—"}</span><span>{visible.at(-1)?.date ?? "—"}</span></div><p className="fine-print">Zoom changes visible bars, not the selected period's metrics. Hover or focus a bar for adjusted OHLC values.</p>
  </div>;
}

"use client";

import { useState, type FormEvent } from "react";
import { ArrowUpRight, BrainCircuit, CircleHelp } from "lucide-react";
import { useResource, type Analyst, type Wallet } from "../../../frontend/src/AdvancedPanels";
import { inr, number } from "../../../frontend/src/api";
import { DataState } from "./Terminal";

type Topic = "signal" | "forecast" | "risk" | "portfolio";
const prompts: Record<Topic, string> = {
  signal: "Explain this signal", forecast: "Show the forecast range",
  risk: "What risks did the analysis find?", portfolio: "Review my portfolio exposure",
};

export default function Intelligence({symbol, mode, wallet, trade}: {
  symbol: string; mode: "analyst" | "predictions" | "recommendations" | "assistant"; wallet?: Wallet; trade(): void;
}) {
  const analysis = useResource<Analyst>(`/analyst/${encodeURIComponent(symbol)}`);
  const data = analysis.data;
  const [topic, setTopic] = useState<Topic>("signal");
  const [conversation, setConversation] = useState<{question: string; answer: string; source: string}[]>([]);
  const title = {analyst: "AI Analyst", predictions: "Predictions", recommendations: "Recommendations", assistant: "AI Assistant"}[mode];
  const forecast = data?.forecast;

  function explain(event: FormEvent) {
    event.preventDefault();
    if (!data && topic !== "portfolio") return;
    const answer = topic === "portfolio"
      ? wallet ? `Your paper account holds ${wallet.holdings.length} positions worth ${inr(wallet.holdings_value)}. Available virtual cash is ${inr(wallet.available_cash)}. ${wallet.holdings.length === 1 ? "All invested value is in one symbol." : "See Portfolio for the value of each position."}`
        : "Portfolio details become available after you sign in to a funded paper account."
      : topic === "forecast"
        ? forecast ? `The ${forecast.horizon.toLowerCase()} estimate is ${inr(forecast.point)}, with a range of ${inr(forecast.lower)} to ${inr(forecast.upper)}. ${data?.stale ? "The underlying observations are historical." : "The range is estimated from historical errors."}`
          : "The model has insufficient validated observations for a forecast."
        : topic === "risk" ? data?.risk_flags.join(" ") || "The analysis returned no specific risk flags. Market prices can still move unexpectedly."
        : `${symbol}: ${data?.recommendation}. ${data?.recommendation_reason} ${data?.evidence[0] ?? ""}`;
    const source = topic === "portfolio" ? "TradeVelocity paper account" : `${data?.source} · ${data?.as_of}`;
    setConversation(previous => [...previous, {question: prompts[topic], answer, source}]);
  }

  return <>
    <div className="tv2-heading"><div><span className="tv2-kicker">{symbol} · Market intelligence</span><h1>{title}</h1>
      <p>{mode === "assistant" ? "Ask a supported question about the selected stock or your paper account." : "Review the market evidence and its date before making a paper trading decision."}</p></div>
      <button className="tv2-button tv2-outline" onClick={trade}>Open terminal <ArrowUpRight size={16} /></button>
    </div>
    {mode === "assistant" ? <section className="tv2-surface tv2-assistant">
      <div className="tv2-panel-head"><h2><BrainCircuit size={20} /> Research assistant</h2><span className="tv2-badge">Read-only</span></div>
      <p>Answers are generated from the available TradeVelocity market analysis and account totals.</p>
      {analysis.error && <DataState error={analysis.error} retry={analysis.reload} loading="" />}
      <div className="tv2-conversation" aria-live="polite">
        {conversation.map((message, index) => <article key={index}><h3>{message.question}</h3><p>{message.answer}</p><small>{message.source}</small></article>)}
      </div>
      <form onSubmit={explain}>
        <label>Ask about<select value={topic} onChange={event => setTopic(event.target.value as Topic)}>
          {Object.entries(prompts).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select></label>
        <button className="tv2-button" disabled={topic !== "portfolio" && !data}>Ask assistant</button>
        {conversation.length > 0 && <button type="button" className="tv2-button tv2-outline" onClick={() => setConversation([])}>Clear conversation</button>}
      </form>
    </section> : !data ? <DataState error={analysis.error} retry={analysis.reload} loading="Analysing daily market data…" />
      : <>
        {data.stale && <p className="tv2-info" role="status">Historical analysis. The most recent observation used was {data.as_of}.</p>}
        {mode !== "predictions" && <section className="tv2-surface tv2-signal">
          <div className="tv2-panel-head"><div><span className="tv2-kicker">Paper signal</span><h2>{data.company}</h2></div>
            <strong className="tv2-signal-value">{data.recommendation}</strong></div>
          <p>{data.recommendation_reason}</p>
          <p>Observed trend: <strong>{data.signal}</strong></p>
          <details open={mode === "analyst"}><summary>Supporting evidence and risks</summary>
            <ul>{[...data.evidence, ...data.risk_flags].map(item => <li key={item}>{item}</li>)}</ul>
          </details>
          <p className="tv2-source">{data.source} · {data.as_of}</p>
        </section>}
        {mode !== "recommendations" && <section className="tv2-surface">
          <div className="tv2-panel-head"><h2>Forecast range</h2><span className="tv2-badge">{forecast?.horizon ?? "Unavailable"}</span></div>
          {forecast ? <>
            <p>Reference close {inr(forecast.reference_price)} · Estimated move {forecast.change_pct}%</p>
            <div className="tv2-forecast">
              <span><small>Lower estimate</small><strong>{inr(forecast.lower)}</strong></span>
              <span><small>Point estimate</small><strong>{inr(forecast.point)}</strong></span>
              <span><small>Upper estimate</small><strong>{inr(forecast.upper)}</strong></span>
            </div>
            <p className="tv2-source"><CircleHelp size={14} /> Calibrated to target {forecast.interval_target}% coverage using {number(forecast.calibration_samples)} historical errors. Future prices can fall outside this range.</p>
          </> : <p>The amount or quality of market history is insufficient for a validated forecast.</p>}
        </section>}
      </>}
  </>;
}

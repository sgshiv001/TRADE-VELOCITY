"use client";

import { useState } from "react";
import { ArrowRight, RotateCcw } from "lucide-react";
import { api, inr } from "../../../frontend/src/api";
import type { Depth } from "../../../frontend/src/types";

type Demo = {
  orders: {id: string; side: string; quantity: number; filled: number; remaining: number}[];
  book: {bids: Depth[]; asks: Depth[]};
  executions: {buyer: string; seller: string; quantity: number; price: string}[];
};
const actions = ["Place Buy 1 · 10 @ ₹100", "Place Buy 2 · 10 @ ₹100", "Place Sell · 15 @ ₹100"];
const outcomes = ["Both sides are empty.", "Buy 1 is resting for 10 shares.", "20 shares are resting at ₹100. Buy 1 has priority.",
  "Buy 1 filled 10 shares. Buy 2 filled 5 shares and has 5 resting."];
const freshSymbol = () => `DEMO${crypto.randomUUID().slice(0, 8).toUpperCase()}`;

export default function PresentationDemo() {
  const [symbol, setSymbol] = useState(freshSymbol);
  const [step, setStep] = useState(0);
  const [data, setData] = useState<Demo>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function advance() {
    setBusy(true);
    setError("");
    try {
      const next = step + 1;
      setData(await api<Demo>(`/demo/fifo/${symbol}?step=${next}`));
      setStep(next);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The demo could not reach its engine. Try again.");
    } finally { setBusy(false); }
  }

  return <>
    <div className="tv2-heading"><div><span className="tv2-kicker">MATCHING ENGINE DEMONSTRATION</span>
      <h1>Price–time priority</h1><p>{symbol} · Synthetic instrument</p></div>
      <button className="tv2-button tv2-outline" disabled={busy} onClick={() => {
        setSymbol(freshSymbol()); setStep(0); setData(undefined); setError("");
      }}><RotateCcw size={16} /> Reset demo</button>
    </div>
    <p className="tv2-info" role="status">{outcomes[step]} This exercise uses an isolated order book.</p>
    {error && <p className="tv2-info" role="alert">{error}</p>}
    <div className="tv2-demo-grid">
      <section className="tv2-surface"><div className="tv2-panel-head"><h2>Order ticket</h2><span className="tv2-badge">Simulated</span></div>
        <ol className="tv2-demo-steps">{actions.map((label, index) => <li key={label} data-completed={index < step}>{label.replace("Place ", "")}</li>)}</ol>
        {step < actions.length && <button className="tv2-button" disabled={busy} onClick={() => void advance()}>
          {busy ? "Matching…" : actions[step]} <ArrowRight size={16} /></button>}
      </section>
      <section className="tv2-surface"><div className="tv2-panel-head"><h2>Order book</h2></div>
        {data?.book.bids.length ? <div className="tv2-table-scroll"><table className="tv2-table" aria-label="Demo bids">
          <thead><tr><th>Bid</th><th>Shares</th><th>Orders</th></tr></thead>
          <tbody>{data.book.bids.map(row => <tr key={row.price}><td>{inr(row.price)}</td><td>{row.quantity}</td><td>{row.orders}</td></tr>)}</tbody>
        </table></div> : <p>No resting bids.</p>}
        <p>No resting asks.</p>
      </section>
      <section className="tv2-surface"><div className="tv2-panel-head"><h2>Recent executions</h2></div>
        {data?.executions.length ? <div className="tv2-table-scroll"><table className="tv2-table" aria-label="Demo executions">
          <thead><tr><th>Buyer</th><th>Shares</th><th>Price</th></tr></thead>
          <tbody>{data.executions.map(row => <tr key={row.buyer}><td>{row.buyer}</td><td>{row.quantity}</td><td>{inr(row.price)}</td></tr>)}</tbody>
        </table></div> : <p>No executions yet.</p>}
      </section>
    </div>
    <section className="tv2-surface"><div className="tv2-panel-head"><h2>Order results</h2></div>
      {data?.orders.length ? <div className="tv2-table-scroll"><table className="tv2-table" aria-label="Demo order results">
        <thead><tr><th>Order</th><th>Submitted</th><th>Filled</th><th>Resting</th></tr></thead>
        <tbody>{data.orders.map(row => <tr key={row.id}><td>{row.id}</td><td>{row.quantity}</td><td>{row.filled}</td><td>{row.remaining}</td></tr>)}</tbody>
      </table></div> : <p>Place the first buy to start the demonstration.</p>}
    </section>
  </>;
}

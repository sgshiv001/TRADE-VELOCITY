export interface Company {
  symbol: string;
  name: string;
  sector: string;
  description: string;
  website: string;
  color: string;
  ticker: string;
  quote_url: string;
  price: number;
  day_change: number;
  year_growth: number;
  volume: number;
  as_of: string;
  sparkline: number[];
}
export interface Market {
  companies: Company[];
  as_of: string;
  source: string;
  fetched_at: string;
  is_demo: boolean;
  message: string;
  gainers: number;
  losers: number;
  basket_change: number;
}
export interface Bar {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  raw_close: number;
  volume: number;
  ma20: number | null;
  ma50: number | null;
  rsi: number | null;
  drawdown: number;
}
export interface History {
  history: Bar[];
  period: string;
  source: string;
  basis: string;
  is_demo: boolean;
  performance: { period: string; return_pct: number }[];
  metrics: {
    last: number;
    change_pct: number;
    growth_pct: number;
    cagr_pct: number | null;
    volatility_pct: number;
    drawdown_pct: number;
    volume: number;
  };
}
export interface Analysis {
  symbol: string;
  company: string;
  sector: string;
  period: string;
  as_of: string;
  signal: "Bullish" | "Bearish" | "Mixed";
  headline: string;
  snapshot: {
    price: number;
    return_pct: number;
    rsi: number;
    volatility_pct: number;
    drawdown_pct: number;
    volume_ratio: number;
    moving_average: "above" | "below";
  };
  evidence: string[];
  risk_flags: string[];
  method: string;
  generated_at: string;
}
export interface AnomalyReport {
  symbol: string;
  company: string;
  period: string;
  method: string;
  model: string;
  contamination: number;
  observations: number;
  anomaly_count: number;
  latest: {
    date: string;
    anomaly_score: number;
    is_anomalous: boolean;
    features: Record<string, number>;
    top_features: string[];
  };
  timeline: { date: string; anomaly_score: number; is_anomalous: boolean }[];
  feature_explanations: Record<string, string>;
  note: string;
  trees: number;
}
export interface Holding {
  Symbol: string;
  Shares: number;
  "Average cost (₹)": number;
  "Mark price (₹)": number;
  "Cost basis (₹)": number;
  "Market value (₹)": number;
  "Unrealized P/L (₹)": number;
  "Return %": number;
}
export interface Fill {
  "Time (UTC)": string;
  Order: string;
  Symbol: string;
  Side: string;
  Shares: number;
  "Price (₹)": string;
  "Realized P/L (₹)": string;
  Note: string;
}
export interface Portfolio {
  initial_cash: number | string;
  cash: number | string;
  equity: number | string;
  market_value: number | string;
  total_pnl: number | string;
  realized_pnl: number | string;
  unrealized_pnl: number | string;
  holdings: Holding[];
  fills: Fill[];
  history: { Time: string; "Equity (₹)": number; "P/L (₹)": number }[];
}
export interface Order {
  order_id: string;
  symbol: string;
  side: string;
  price: string;
  quantity: number;
  remaining: number;
}
export interface Depth {
  price: string;
  quantity: number;
  orders: number;
}
export interface Trade {
  trade_id: number;
  symbol: string;
  price: number | string;
  quantity: number;
  buy_order_id: string;
  sell_order_id: string;
  timestamp: string;
}
export interface Lab {
  symbols: string[];
  orders: Order[];
  book: { symbol: string; bids: Depth[]; asks: Depth[] };
  trades: Trade[];
  events: number;
  stats: {
    volume: number;
    trades: number;
    last: string | null;
    vwap: string | null;
  };
}
export interface Measurement {
  workload: string;
  engine: string;
  commands: number;
  seconds: number;
  commands_per_second: number;
  trades: number;
  repeat: number;
  peak_traced_mb: number | null;
}

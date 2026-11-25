import { z } from "zod";

export const symbolSchema = z.string().trim().toUpperCase().regex(/^[A-Z][A-Z0-9.&-]{0,15}$/);
export const limitOrderSchema = z.object({
  order_id: z.string().min(1).max(100),
  symbol: symbolSchema,
  side: z.enum(["BUY", "SELL"]),
  quantity: z.number().int().min(1).max(1_000_000),
  price: z.string().regex(/^\d{1,10}(\.\d{1,2})?$/).refine(value => Number(value) > 0),
  confirmed: z.literal(true),
});
export type LimitOrder = z.infer<typeof limitOrderSchema>;

export type Trader = {username: string; workspace_id: string; tutorial_seen: boolean; admin: boolean};
export type Profile = {revision: number; name: string; watchlists: {name: string; symbols: string[]}[]};
export type Quote = {symbol: string; price: number | null; kind: "intraday" | "close" | "unavailable"; source: string | null; as_of: string | null};
export type DepthLevel = {price: string; quantity: number; orders: number};
export type Depth = {book: {symbol: string; bids: DepthLevel[]; asks: DepthLevel[]}; revision: number};
export type Portfolio = {
  cash: string; available_cash: string; reserved: string; contributed: string; invested: string;
  holdings_value: string; equity: string; realized: string; unrealized: string; market_as_of: string;
  holdings: {symbol: string; quantity: number; average_cost: string; mark: string; mark_source: string; value: string; pnl: string}[];
  activity: {id: string; amount: string; timestamp: string | null; description: string; symbol?: string}[];
};
export type ExecutionInbox = {unread: number; items: {id: number; symbol: string; quantity: number; price: number; timestamp: string | null; read: boolean}[]};

export function formatINR(value: number | string) {
  return new Intl.NumberFormat("en-IN", {style: "currency", currency: "INR"}).format(Number(value));
}

export class TradeVelocityApiError extends Error {
  constructor(message: string, readonly status: number) { super(message); }
}

export function createClient(base: string, session?: {token?: string; workspace?: string}) {
  const origin = base.replace(/\/$/, "");
  return async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
    if (!path.startsWith("/") || path.startsWith("//")) throw new Error("Invalid API path");
    const headers = new Headers(init.headers);
    if (init.body) headers.set("Content-Type", "application/json");
    if (session?.token) headers.set("Authorization", `Bearer ${session.token}`);
    if (session?.workspace) headers.set("X-Session-ID", session.workspace);
    const response = await fetch(`${origin}/api${path}`, {...init, headers, credentials: "same-origin"});
    const body = await response.json().catch(() => null);
    if (!response.ok) {
      throw new TradeVelocityApiError(typeof body?.detail === "string" ? body.detail : "The workspace could not complete that request.", response.status);
    }
    return body as T;
  };
}

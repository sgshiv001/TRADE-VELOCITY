import { useCallback, useEffect, useState } from "react";
import { useWorkspace } from "./workspace";

export type MarketCompany = {symbol: string; name: string; price: number; day_change: number | null; as_of: string};
export type MarketOverview = {companies: MarketCompany[]; source: string; as_of: string};
export type MarketBar = {date: string; open: number; high: number; low: number; close: number};
export type MarketHistory = {history: MarketBar[]; source: string};

export function useData<T>(path: string | null) {
  const {request, revision} = useWorkspace();
  const [result, setResult] = useState<{path: string; data?: T; error?: string; loading: boolean}>();
  const [refreshNumber, setRefreshNumber] = useState(0);
  const refresh = useCallback(() => setRefreshNumber(value => value + 1), []);
  useEffect(() => {
    if (!path) return;
    const controller = new AbortController();
    const update = (loading: boolean, error?: string) => setResult(previous => ({
      path, data: previous?.path === path ? previous.data : undefined, loading, error,
    }));
    update(true);
    const timeout = setTimeout(() => {
      controller.abort();
      update(false, "The server took too long to respond. Try again.");
    }, 18_000);
    request<T>(path, {signal: controller.signal}).then(data => {
      if (!controller.signal.aborted) setResult({path, data, loading: false});
    }).catch((cause: unknown) => {
      if (!controller.signal.aborted) update(false, cause instanceof Error ? cause.message : "Unable to load data.");
    }).finally(() => clearTimeout(timeout));
    return () => { clearTimeout(timeout); controller.abort(); };
  }, [path, request, revision, refreshNumber]);
  const current = result?.path === path ? result : undefined;
  return {data: current?.data, error: current?.error, loading: current?.loading ?? Boolean(path), refresh};
}

export function quoteTime(value: string) {
  if (!value.includes("T")) return value;
  const date = new Date(value);
  if (!Number.isFinite(date.valueOf())) return value;
  return `${date.toLocaleString("en-IN", {timeZone: "Asia/Kolkata", day: "numeric", month: "short", hour: "numeric", minute: "2-digit"})} IST`;
}

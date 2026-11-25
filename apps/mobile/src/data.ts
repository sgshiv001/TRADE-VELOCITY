import { useEffect, useState } from "react";
import { useWorkspace } from "./workspace";

export type MarketOverview = {companies: {symbol: string; name: string; price: number; day_change: number | null; as_of: string}[]; source: string};

export function useData<T>(path: string) {
  const {request, revision} = useWorkspace();
  const [result, setResult] = useState<{path: string; data: T}>();
  const [error, setError] = useState("");
  const [refreshNumber, refresh] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    request<T>(path, {signal: controller.signal}).then(data => {
      if (!controller.signal.aborted) { setResult({path, data}); setError(""); }
    }).catch((cause: unknown) => {
      if (!controller.signal.aborted) setError(cause instanceof Error ? cause.message : "Unable to load data");
    });
    return () => controller.abort();
  }, [path, revision, refreshNumber]);
  return {data: result?.path === path ? result.data : undefined, error, refresh: () => refresh(value => value + 1)};
}

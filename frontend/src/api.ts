let sessionPromise: Promise<string> | null = null;
type ApiOptions = RequestInit & { timeoutMs?: number; requestKey?: string };

async function fetchTimed(path: string, options: RequestInit, timeoutMs: number) {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  const abort = () => controller.abort();
  options.signal?.addEventListener("abort", abort, { once: true });
  if (options.signal?.aborted) controller.abort();
  try {
    const response = await fetch(path, { ...options, signal: controller.signal });
    const body = await response.json();
    return { response, body };
  } finally {
    window.clearTimeout(timer);
    options.signal?.removeEventListener("abort", abort);
  }
}

export async function sessionId(): Promise<string> {
  const existing = localStorage.getItem("marketlab-session");
  if (existing) return existing;
  if (!sessionPromise)
    sessionPromise = fetchTimed("/api/session", { method: "POST" }, 15000)
      .then(({response, body}) => {
        if (!response.ok)
          throw new Error("Could not start a matching-engine session.");
        localStorage.setItem("marketlab-session", body.session_id);
        return body.session_id as string;
      })
      .finally(() => {
        sessionPromise = null;
      });
  return sessionPromise;
}

export async function api<T>(
  path: string,
  options: ApiOptions = {},
  recover = true,
): Promise<T> {
  const id = await sessionId();
  const { timeoutMs = path === "/market/refresh" ? 120000 : path === "/experiments" ? 60000 : 15000, requestKey, ...request } = options;
  const mutation = request.method && request.method !== "GET" && path.startsWith("/lab/");
  const key = mutation ? requestKey ?? crypto.randomUUID() : undefined;
  const headers = new Headers(request.headers);
  headers.set("Content-Type", "application/json"); headers.set("X-Session-ID", id);
  if (key) headers.set("Idempotency-Key", key);
  for (let attempt = 0; attempt < 2; attempt++) {
    let result;
    try { result = await fetchTimed(`/api${path}`, { ...request, headers }, timeoutMs); }
    catch {
      if (request.signal?.aborted) throw new Error("Request cancelled.");
      if (attempt === 0 && (key || !request.method || request.method === "GET")) continue;
      throw new Error(key ? "Connection lost or request timed out. Retry the same action; its request key prevents duplicate execution." : "Connection lost or request timed out. Check the app server and try again.");
    }
    const {response, body} = result;
    if (!response.ok) {
      if (response.status === 401 && body.detail === "Sign in to access this workspace") {
        window.dispatchEvent(new Event("tradevelocity-access-expired"));
        throw new Error("Your access has expired. Sign in again.");
      }
      if (recover && [401,404].includes(response.status) && ["local session was not found", "invalid local session"].includes(body.detail)) {
        localStorage.removeItem("marketlab-session");
        return api<T>(path, { ...options, requestKey: key }, false);
      }
      if (attempt === 0 && key && response.status === 503) continue;
      throw new Error(typeof body.detail === "string" ? body.detail : "Could not complete the request. Check your inputs and try again.");
    }
    return body as T;
  }
  throw new Error("Could not complete the request.");
}

export function download(name: string, data: unknown, csv = false) {
  const body = csv ? String(data) : JSON.stringify(data, null, 2);
  const url = URL.createObjectURL(
    new Blob([body], { type: csv ? "text/csv" : "application/json" }),
  );
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export const inr = (value: number | string, digits = 2) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(Number(value));
export const number = (value: number) =>
  new Intl.NumberFormat("en-IN").format(value);
export const percent = (value: number) =>
  `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
export const short = (value: number) =>
  new Intl.NumberFormat("en-IN", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
export const tradeTime = (value: string | null) => value ? new Date(value).toLocaleString() : "Unknown (legacy record)";

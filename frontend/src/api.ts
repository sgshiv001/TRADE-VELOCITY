let sessionPromise: Promise<string> | null = null;

export async function sessionId(): Promise<string> {
  const existing = localStorage.getItem("marketlab-session");
  if (existing) return existing;
  if (!sessionPromise)
    sessionPromise = fetch("/api/session", { method: "POST" })
      .then(async (response) => {
        if (!response.ok)
          throw new Error("Could not start a local paper account.");
        const data = await response.json();
        localStorage.setItem("marketlab-session", data.session_id);
        return data.session_id;
      })
      .finally(() => {
        sessionPromise = null;
      });
  return sessionPromise;
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
  retry = true,
): Promise<T> {
  const id = await sessionId();
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Session-ID": id,
      ...options.headers,
    },
  });
  if (response.status === 404 && retry && path.startsWith("/portfolio")) {
    localStorage.removeItem("marketlab-session");
    return api<T>(path, options, false);
  }
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      typeof error.detail === "string"
        ? error.detail
        : "Please check your inputs and try again.",
    );
  }
  return response.json();
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

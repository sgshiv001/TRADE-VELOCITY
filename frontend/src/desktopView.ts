export type DesktopView = "admin" | "trader";

export function desktopView(): DesktopView | null {
  const value = new URLSearchParams(window.location.search).get("desktopView");
  return value === "admin" || value === "trader" ? value : null;
}

export function workspaceRoute(path: "/app" | "/login" | "/signup") {
  const current = new URLSearchParams(window.location.search);
  const query = new URLSearchParams();
  for (const name of ["desktopView", "desktopBrowser", "presentation", "view", "symbol"]) {
    const value = current.get(name);
    if (value) query.set(name, value);
  }
  return query.size ? `${path}?${query}` : path;
}

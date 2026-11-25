export type DesktopView = "admin" | "trader";

export function desktopView(): DesktopView | null {
  const value = new URLSearchParams(window.location.search).get("desktopView");
  return value === "admin" || value === "trader" ? value : null;
}

export function workspaceRoute(path: "/app" | "/login" | "/signup") {
  const view = desktopView();
  return view ? `${path}?desktopView=${view}` : path;
}

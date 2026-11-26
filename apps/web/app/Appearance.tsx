"use client";

import { useEffect, useState } from "react";

export type Theme = "dark" | "light";
export type Appearance = Theme | "system";
const storageKey = "tradevelocity-appearance";
const systemLight = "(prefers-color-scheme: light)";

function readAppearance(): Appearance {
  try {
    const value = localStorage.getItem(storageKey);
    if (value === "dark" || value === "light" || value === "system") return value;
  } catch { /* The device preference still works without storage. */ }
  return "system";
}

export function useAppearance() {
  const [appearance, setAppearance] = useState(readAppearance);
  const [prefersLight, setPrefersLight] = useState(() => matchMedia(systemLight).matches);

  useEffect(() => {
    const media = matchMedia(systemLight);
    const update = () => setPrefersLight(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    try { localStorage.setItem(storageKey, appearance); }
    catch { /* The theme stays usable in this tab. */ }
  }, [appearance]);

  const theme: Theme = appearance === "system" ? (prefersLight ? "light" : "dark") : appearance;
  return {appearance, setAppearance, theme};
}

export function ThemeSelect({appearance, setAppearance}: {
  appearance: Appearance;
  setAppearance(value: Appearance): void;
}) {
  return <label className="tv2-theme-select">Theme
    <select value={appearance} onChange={event => setAppearance(event.target.value as Appearance)}>
      <option value="system">System</option>
      <option value="light">Light</option>
      <option value="dark">Dark</option>
    </select>
  </label>;
}

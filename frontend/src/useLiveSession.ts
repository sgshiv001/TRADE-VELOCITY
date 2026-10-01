import { useEffect, useRef, useState } from "react";
import { sessionId } from "./api";

export function useLiveSession(changed: () => Promise<void>) {
  const callback = useRef(changed);
  callback.current = changed;
  const [connected, setConnected] = useState(false);
  const [online, setOnline] = useState(navigator.onLine);
  useEffect(() => {
    let stopped = false, socket: WebSocket | null = null, timer = 0, delay = 1000;
    const network = () => setOnline(navigator.onLine);
    window.addEventListener("online", network); window.addEventListener("offline", network);
    async function connect() {
      try {
        const id = await sessionId();
        if (stopped) return;
        socket = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/api/live?session_id=${encodeURIComponent(id)}`);
        socket.onopen = () => { setConnected(true); delay = 1000; };
        socket.onmessage = event => {
          try { const update = JSON.parse(event.data); if (["connected", "changed"].includes(update.type)) void callback.current(); }
          catch { /* Ignore malformed transport messages; API reads remain authoritative. */ }
        };
        socket.onclose = () => { if (!stopped) { setConnected(false); timer = window.setTimeout(connect, delay); delay = Math.min(15000, delay * 2); } };
        socket.onerror = () => socket?.close();
      } catch { if (!stopped) { setConnected(false); timer = window.setTimeout(connect, delay); delay = Math.min(15000, delay * 2); } }
    }
    void connect();
    return () => { stopped = true; window.clearTimeout(timer); socket?.close(); window.removeEventListener("online", network); window.removeEventListener("offline", network); };
  }, []);
  useEffect(() => { const timer = window.setInterval(() => void callback.current(), connected ? 30000 : 15000); return () => window.clearInterval(timer); }, [connected]);
  return { connected, online };
}

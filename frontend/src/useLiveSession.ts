import { useEffect, useRef, useState } from "react";
import { sessionId } from "./api";

export function useLiveSession(changed: () => Promise<void>) {
  const callback = useRef(changed);
  callback.current = changed;
  const [connected, setConnected] = useState(false);
  const [online, setOnline] = useState(navigator.onLine);
  useEffect(() => {
    let stopped = false, connecting = false, socket: WebSocket | null = null, timer = 0, delay = 1000;
    function reconnect() {
      if (stopped || !navigator.onLine) return;
      timer = window.setTimeout(() => void connect(), delay);
      delay = Math.min(15000, delay * 2);
    }
    const network = () => {
      const available = navigator.onLine;
      setOnline(available);
      if (!available) {
        window.clearTimeout(timer);
        setConnected(false);
        const current = socket;
        socket = null;
        current?.close();
      } else if (!socket || socket.readyState === WebSocket.CLOSED) {
        window.clearTimeout(timer);
        delay = 1000;
        void connect();
      }
    };
    window.addEventListener("online", network); window.addEventListener("offline", network);
    async function connect() {
      if (stopped || !navigator.onLine || connecting || (socket && socket.readyState !== WebSocket.CLOSED)) return;
      connecting = true;
      try {
        const id = await sessionId();
        if (stopped || !navigator.onLine) return;
        const connection = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/api/live?session_id=${encodeURIComponent(id)}`);
        socket = connection;
        connection.onopen = () => {
          if (stopped || socket !== connection) { connection.close(); return; }
          setConnected(true); delay = 1000;
        };
        connection.onmessage = event => {
          try { const update = JSON.parse(event.data); if (["connected", "changed"].includes(update.type)) void callback.current(); }
          catch { /* Ignore malformed transport messages; API reads remain authoritative. */ }
        };
        connection.onclose = () => {
          if (socket === connection) socket = null;
          if (!stopped) { setConnected(false); reconnect(); }
        };
        connection.onerror = () => connection.close();
      } catch { if (!stopped) { setConnected(false); reconnect(); } }
      finally { connecting = false; }
    }
    void connect();
    return () => { stopped = true; window.clearTimeout(timer); socket?.close(); window.removeEventListener("online", network); window.removeEventListener("offline", network); };
  }, []);
  useEffect(() => { if (!online) return; const timer = window.setInterval(() => void callback.current(), connected ? 30000 : 15000); return () => window.clearInterval(timer); }, [connected, online]);
  return { connected, online };
}

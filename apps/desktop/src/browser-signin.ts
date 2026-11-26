import { shell, type BrowserWindow } from "electron";
import { createHash, randomBytes } from "node:crypto";
import { setTimeout as pause } from "node:timers/promises";

const cookieName = "__Host-tradevelocity-access";
const startCommand = "tradevelocity-local:signin";
const reopenCommand = "tradevelocity-local:reopen";

export function browserSignIn(window: BrowserWindow, origin: string, workspace: string, view: "trader" | "admin") {
  let active: AbortController | undefined;
  let verificationUrl: string | undefined;
  let localPage: string | undefined;

  function cancel() {
    active?.abort();
    active = undefined;
    verificationUrl = undefined;
    localPage = undefined;
  }

  async function display(code?: string, message?: string) {
    const instructions = code
      ? "Enter this code in your browser, then return here. The workspace opens after you approve."
      : message ?? "Check your internet connection, then start a new browser sign-in.";
    const formattedCode = code ? code.slice(0, 4) + " " + code.slice(4) : "";
    const markup = `<!doctype html><html lang="en"><head><meta charset="utf-8">
      <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'">
      <meta name="viewport" content="width=device-width, initial-scale=1"><title>TradeVelocity browser sign-in</title>
      <style>
        :root{color-scheme:dark;background:#090c10;color:#eff5f4;font:16px/1.55 system-ui}
        body{margin:0;min-height:100vh;display:grid;place-items:center;padding:24px;box-sizing:border-box}
        main{max-width:440px;padding:28px;border:1px solid #7a9e9380;border-radius:16px;animation:enter .22s ease-out}
        h1{margin:0;font-size:clamp(25px,4.7vw,36px);line-height:1.15}
        p{margin:14px 0} code{display:block;font-size:clamp(21px,6vw,40px);letter-spacing:.12em;padding-block:7px}
        a{display:inline-block;margin:7px 16px 0 0;color:#53e3ae;text-underline-offset:4px}
        a:focus-visible{outline:2px solid currentColor;outline-offset:4px}
        @keyframes enter{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
        @media(prefers-color-scheme:light){:root{color-scheme:light;background:#f3f6f5;color:#15211f}a{color:#08664d}}
        @media(prefers-reduced-motion:reduce){main{animation:none}}
      </style></head><body><main>
      <h1>${code ? "Continue in your browser" : "Browser sign-in ended"}</h1>
      <p>${instructions}</p>${code ? `<code aria-label="Desktop code">${formattedCode}</code><a href="${reopenCommand}">Open browser again</a>` : ""}
      <a href="${startCommand}">Start a new sign-in</a>
      </main></body></html>`;
    localPage = "data:text/html;charset=utf-8," + encodeURIComponent(markup);
    await window.loadURL(localPage);
  }

  async function start() {
    cancel();
    const attempt = new AbortController();
    active = attempt;
    const verifier = randomBytes(32).toString("base64url");
    async function post(path: string, body: Record<string, string>) {
      return fetch(origin + "/api/auth/desktop/" + path, {
        method: "POST", redirect: "error", headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body), signal: AbortSignal.any([attempt.signal, AbortSignal.timeout(25_000)]),
      });
    }
    try {
      const response = await post("start", {view, challenge: createHash("sha256").update(verifier).digest("hex")});
      if (!response.ok) throw new Error("Desktop sign-in could not be started");
      const {request_id, code, interval, expires_in} = await response.json();
      if (typeof request_id !== "string" || !/^[A-Za-z0-9_-]{32}$/.test(request_id)
        || typeof code !== "string" || !/^[0-9]{8}$/.test(code)
        || interval !== 3 || expires_in !== 300) throw new Error("Invalid sign-in request");
      attempt.signal.throwIfAborted();
      const deadline = Date.now() + expires_in * 1000;
      verificationUrl = origin + "/desktop-sign-in?request=" + request_id;
      await display(code);
      attempt.signal.throwIfAborted();
      await shell.openExternal(verificationUrl);
      while (Date.now() < deadline) {
        await pause(interval * 1000, undefined, {signal: attempt.signal});
        const result = await post("exchange", {request_id, verifier});
        if (result.status === 202) continue;
        if (!result.ok) throw new Error("Desktop sign-in ended");
        const {token, expires_in: lifetime} = await result.json();
        if (typeof token !== "string" || !/^[A-Za-z0-9_-]{43}$/.test(token)
          || !Number.isSafeInteger(lifetime) || lifetime <= 0 || lifetime > 7 * 86400) {
          throw new Error("Invalid desktop session");
        }
        attempt.signal.throwIfAborted();
        await window.webContents.session.cookies.set({
          url: origin, name: cookieName, value: token, path: "/", secure: true,
          httpOnly: true, sameSite: "strict", expirationDate: Date.now() / 1000 + lifetime,
        });
        attempt.signal.throwIfAborted();
        cancel();
        try {
          await window.loadURL(workspace);
        } catch {
          if (window.isDestroyed()) return;
          void display(undefined, "You’re signed in. Reconnect, then choose Workspace from the View menu.").catch(() => {});
        }
        if (!window.isDestroyed()) {
          if (window.isMinimized()) window.restore();
          window.show();
          if (process.platform === "win32") window.moveTop();
          window.focus();
          if (process.platform === "win32" && !window.isFocused()) {
            window.flashFrame(true);
            window.once("focus", () => window.flashFrame(false));
          }
        }
        return;
      }
      throw new Error("Desktop sign-in expired");
    } catch {
      if (attempt.signal.aborted || window.isDestroyed()) return;
      verificationUrl = undefined;
      await display().catch(() => {});
    }
  }

  window.once("closed", cancel);
  return {
    cancel,
    handle(address: string, from: string) {
      const fromLocal = localPage !== undefined && from === localPage;
      if (address === startCommand && (fromLocal || from.startsWith(origin + "/"))) {
        if (!active || fromLocal) void start();
        return true;
      }
      if (address === reopenCommand && fromLocal) {
        if (verificationUrl) void shell.openExternal(verificationUrl).catch(() => {});
        return true;
      }
      return false;
    },
  };
}

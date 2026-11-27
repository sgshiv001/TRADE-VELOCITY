import { app, type Session } from "electron";
import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import { randomBytes } from "node:crypto";
import { mkdirSync } from "node:fs";
import { join } from "node:path";
import { createInterface } from "node:readline";
import { setTimeout as pause } from "node:timers/promises";

export function createOfflineEngine() {
  let child: ChildProcessWithoutNullStreams | undefined;
  let pending: Promise<string> | undefined;
  let listening = "";
  let key = "";

  function prepareSession(session: Session) {
    session.webRequest.onBeforeSendHeaders((details, reply) => {
      const url = new URL(details.url);
      const loopback = url.origin.replace(/^ws:/, "http:");
      const headers = details.requestHeaders;
      if (listening && loopback === listening) headers["X-TradeVelocity-Offline-Key"] = key;
      reply({requestHeaders: headers});
    });
  }

  async function start() {
    const data = join(app.getPath("userData"), "offline-demo", "sessions");
    mkdirSync(data, {recursive: true});
    key = randomBytes(32).toString("hex");
    const processHandle = spawn(join(process.resourcesPath, "engine", "TradeVelocityEngine.exe"),
      ["--data-dir", data, "--frontend", join(process.resourcesPath, "web")],
      {windowsHide: true, env: {...process.env, TRADEVELOCITY_OFFLINE_KEY: key}});
    child = processHandle;
    processHandle.stderr.resume();
    const lines = createInterface({input: processHandle.stdout});
    child.once("exit", () => {
      if (child === processHandle) { child = undefined; pending = undefined; listening = ""; key = ""; }
    });
    const port = await new Promise<number>((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error("The local engine took too long to start.")), 45_000);
      const fail = () => { clearTimeout(timer); reject(new Error("The local engine exited before starting.")); };
      processHandle.once("error", fail);
      processHandle.once("exit", fail);
      lines.once("line", line => {
        clearTimeout(timer);
        try {
          const {port} = JSON.parse(line);
          if (!Number.isInteger(port) || port < 1024 || port > 65535) throw new Error("Invalid loopback port");
          resolve(port);
        } catch (cause) { reject(cause); }
      });
    });
    const origin = `http://127.0.0.1:${port}`;
    for (let attempt = 0; attempt < 40; attempt++) {
      const ready = await fetch(`${origin}/api/ready`, {headers: {"X-TradeVelocity-Offline-Key": key}, signal: AbortSignal.timeout(1000)})
        .then(response => response.ok, () => false);
      if (ready) { listening = origin; return `${origin}/app?offlineDemo=1&view=demo`; }
      if (processHandle.exitCode !== null) break;
      await pause(200);
    }
    throw new Error("The local demo did not pass its readiness check.");
  }

  function stop() {
    child?.stdin.end();
    child = undefined;
    pending = undefined;
    listening = "";
    key = "";
  }

  return {
    prepareSession,
    matches(address: string) {
      try { return Boolean(listening) && new URL(address).origin === listening; }
      catch { return false; }
    },
    open() {
      pending ??= start().catch(error => { child?.kill(); stop(); throw error; });
      return pending;
    },
    stop,
  };
}

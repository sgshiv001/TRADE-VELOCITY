import { Brand } from "./Brand";
import { releases } from "./releases";

export default function DownloadPage() {
  return <div className="tv2 tv2-site">
    <header className="tv2-site-header"><div className="tv2-site-width tv2-site-nav"><Brand /><a href="/app">Open workspace</a></div></header>
    <main className="tv2-site-width tv2-download">
      <h1>Download TradeVelocity</h1>
      <p>Use the web workspace for the current build. The files below are prior published releases.</p>
      <div className="tv2-release-grid">
        {releases.map(release => <article className="tv2-surface" key={release.platform}>
          <span className="tv2-kicker">{release.kind}</span><h2>{release.platform}</h2>
          <p>Version {release.version} · {release.date}</p><p>{release.requirements} · {(release.bytes / 1e6).toFixed(1)} MB</p>
          <a className="tv2-button" href={release.href}>Download {release.format}</a>
          <a className="tv2-release-notes" href={release.notes}>Release notes</a>
          <details><summary>SHA-256 checksum</summary><code>{release.checksum}</code></details>
        </article>)}
        <article className="tv2-surface"><h2>Web and PWA</h2><p>Open the trading workspace in a supported browser. Use the browser’s install option to add it to your device.</p><a className="tv2-button" href="/app">Open app</a></article>
        {["iOS", "macOS", "Linux"].map(platform => <article className="tv2-surface" key={platform}><h2>{platform}</h2><p>A published installer is unavailable. Open TradeVelocity in your browser.</p></article>)}
      </div>
    </main>
  </div>;
}

import { Brand } from "./Brand";
import { releases } from "./releases";

export default function DownloadPage() {
  return <div className="tv2 tv2-site">
    <header className="tv2-site-header"><div className="tv2-site-width tv2-site-nav"><Brand /><a href="/app">Open workspace</a></div></header>
    <main className="tv2-site-width tv2-download">
      <h1>Download TradeVelocity</h1>
      <p>TradeVelocity 2.0 beta downloads connect to the live paper-trading workspace.</p>
      <div className="tv2-release-grid">
        {releases.map(release => <article className="tv2-surface" key={release.platform}>
          <h2>{release.platform}</h2>
          <p>{release.description}</p>
          {release.files.map(file => <div className="tv2-download-file" key={file.href}>
            <a className="tv2-button" href={file.href}>{file.label}</a>
            <p>{file.requirements} · {(file.bytes / 1e6).toFixed(1)} MB</p>
            <details><summary>SHA-256 checksum</summary><code>{file.checksum}</code></details>
          </div>)}
          <a className="tv2-release-notes" href={release.notes}>Release notes</a>
        </article>)}
        <article className="tv2-surface">
          <h2>iOS and iPadOS</h2>
          <p>Open TradeVelocity in Safari. Tap Share, choose Add to Home Screen, then turn on Open as Web App.</p>
          <a className="tv2-button" href="/app">Open iPhone and iPad web app</a>
          <p>Native iOS distribution is pending.</p>
        </article>
        <article className="tv2-surface">
          <h2>Web app</h2>
          <p>Use the live trading workspace from a desktop or mobile browser.</p>
          <a className="tv2-button" href="/app">Open workspace</a>
        </article>
      </div>
    </main>
  </div>;
}

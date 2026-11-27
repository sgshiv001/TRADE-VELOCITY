import { Brand } from "./Brand";
import { releaseChecksums, releaseNotes, releaseVersion, windowsDownload } from "./releases";

export default function DownloadPage() {
  return <div className="tv2 tv2-site">
    <header className="tv2-site-header"><div className="tv2-site-width tv2-site-nav"><Brand /><a href="/app">Open workspace</a></div></header>
    <main className="tv2-site-width tv2-download">
      <h1>TradeVelocity {releaseVersion}</h1>
      <p>Use the same paper-trading workspace on Windows and in your browser.</p>
      <div className="tv2-release-grid">
        <article className="tv2-surface"><h2>Windows x64</h2>
          <p>Double-click the standalone EXE. Approve sign-in in your browser to open your live account, or choose <strong>View → Offline demo</strong> for the bundled local workspace.</p>
          <a className="tv2-button" href={windowsDownload}>Download Windows EXE</a>
          <p>Windows x64 · Unsigned</p>
          <a href={releaseChecksums}>SHA-256 checksum</a> · <a href={releaseNotes}>Release notes</a>
        </article>
        <article className="tv2-surface"><h2>Web app</h2>
          <p>Sign in to trade with virtual funds, or open the presentation demo and walk through a partial fill.</p>
          <a className="tv2-button" href="/app?view=demo">Open presentation demo</a>
        </article>
      </div>
    </main>
  </div>;
}

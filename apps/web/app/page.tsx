import { ArrowRight, ChartNoAxesCombined, Focus, Layers3, Wallet } from "lucide-react";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { Brand } from "./Brand";
import { PublicPreview } from "./PublicPreview";

const previewSymbols = [["RELIANCE", "Reliance Industries"], ["TCS", "Tata Consultancy Services"], ["INFY", "Infosys"]];

async function historicalPreview() {
  const path = resolve(process.cwd(), "../../src/stock_engine/data/market-history.json");
  const snapshot: {source: string; histories: Record<string, Record<string, number | string>[]>} =
    JSON.parse(await readFile(path, "utf8"));
  return {
    source: snapshot.source,
    instruments: previewSymbols.flatMap(([symbol, name]) => {
      const history = snapshot.histories[symbol];
      if (!history?.length) return [];
      const bars = history.slice(-60).map(row => {
        const ratio = Number(row["Adj Close"]) / Number(row.Close);
        return {date: String(row.Date).slice(0, 10), close: Number(row["Adj Close"]),
          open: Number(row.Open) * ratio, high: Number(row.High) * ratio,
          low: Number(row.Low) * ratio, volume: Number(row.Volume)};
      });
      return [{symbol, name, bars}];
    }),
  };
}

export default async function Page() {
  const preview = await historicalPreview();
  return <div className="tv2 tv2-site">
    <header className="tv2-site-header">
      <div className="tv2-site-width tv2-site-nav">
        <Brand />
        <nav aria-label="Product navigation">
          <a href="#trading">Trading</a><a href="#analyst">AI Analyst</a><a href="#markets">Markets</a>
          <a href="/download">Download</a><a href="#help">Help</a>
        </nav>
        <div className="tv2-site-account"><a href="/login">Sign in</a><a className="tv2-button" href="/signup">Create account</a></div>
        <details className="tv2-site-mobile"><summary>Menu</summary>
          <a href="#trading">Trading</a><a href="#analyst">AI Analyst</a><a href="#markets">Markets</a>
          <a href="/download">Download</a><a href="#help">Help</a><a href="/login">Sign in</a><a href="/signup">Create account</a>
        </details>
      </div>
    </header>

    <main id="main">
      <section className="tv2-site-width tv2-hero">
        <div className="tv2-hero-copy">
          <span className="tv2-kicker"><i /> PAPER TRADING & MARKET INTELLIGENCE</span>
          <h1>Intelligence behind <em>every trade.</em></h1>
          <p>Explore real market history, understand price movements, and practise your next trade with a virtual portfolio.</p>
          <div className="tv2-hero-actions">
            <a className="tv2-button" href="/signup">Start paper trading <ArrowRight size={17} /></a>
            <a className="tv2-button tv2-outline" href="#trading">Explore TradeVelocity</a>
          </div>
          <p className="tv2-hero-note">₹10 lakh in virtual funds to start · One account across supported devices</p>
        </div>
        <PublicPreview {...preview} />
      </section>

      <section className="tv2-site-band" id="trading">
        <div className="tv2-site-width">
          <div className="tv2-section-intro"><h2>A workspace for your trading decisions</h2><p>Go from researching a company to reviewing a practice order in one place.</p></div>
          <div className="tv2-feature-grid">
            <article><Layers3 /><h3>Trading terminal</h3><p>Open a chart, check the order book, and review a limit order before submitting it to the simulated exchange.</p><a href="/app?view=trade">Open terminal <ArrowRight size={15} /></a></article>
            <article id="analyst"><Focus /><h3>AI Analyst</h3><p>Explore technical signals, supporting evidence, and next-session estimates where the data supports a forecast.</p><a href="/app?view=analyst">Explore analysis <ArrowRight size={15} /></a></article>
            <article id="markets"><ChartNoAxesCombined /><h3>Market discovery</h3><p>Find companies in the supported NSE universe, compare daily moves, and build a watchlist.</p><a href="/app?view=markets">Browse markets <ArrowRight size={15} /></a></article>
            <article><Wallet /><h3>Portfolio and funds</h3><p>Track holdings, virtual cash, reservations, and your simulated trade history in the same account.</p><a href="/app?view=portfolio">View portfolio <ArrowRight size={15} /></a></article>
          </div>
        </div>
      </section>
      <section className="tv2-site-width tv2-site-faq" id="help">
        <div><h2>Before you start</h2><p>TradeVelocity is an educational paper trading platform.</p><a href="/download">See supported downloads <ArrowRight size={15} /></a></div>
        <div>
          <details><summary>How do practice orders work?</summary><p>The matching engine executes orders against simulated bids and offers. A limit can fill in part or remain open.</p></details>
          <details><summary>Where do prices come from?</summary><p>Charts use sourced historical bars. Quotes show the provider and observation time and may be delayed.</p></details>
          <details><summary>Can I trade with real money?</summary><p>All balances and orders are virtual. TradeVelocity does not connect to a brokerage.</p></details>
          <details><summary>How should I read an AI forecast?</summary><p>Use the estimate and its uncertainty range as research inputs. Real prices can move outside the range.</p></details>
        </div>
      </section>
    </main>
    <footer className="tv2-site-width tv2-site-footer"><Brand /><a href="/download">Downloads</a><span>Simulated trading · Educational use</span></footer>
  </div>;
}

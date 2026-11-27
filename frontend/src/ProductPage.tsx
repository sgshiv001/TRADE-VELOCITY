import { useState } from "react";
import {
  ArrowRight, ArrowUpRight, BarChart3, BookOpen, Check, ChevronRight,
  Download, Github, Layers3, Menu, Monitor, ShieldCheck,
  Sparkles, X,
} from "lucide-react";
import "./product-page.css";

const features = [
  {icon: Layers3, title: "A shared practice order book", text: "Place limit or market orders with other traders. Check the reference market price, best bid, best ask, and resting quantities."},
  {icon: ArrowRight, title: "Every fill has a reason", text: "Watch price priority and arrival order determine each match. Partial fills leave the correct quantity open."},
  {icon: BarChart3, title: "Historical market context", text: "Explore dated daily bars, adjusted charts, volatility, drawdown, and RSI for eight supported companies."},
  {icon: Sparkles, title: "Advisory AI review", text: "Review unusual patterns in your simulated executions. Signals explain what was flagged and never block an order."},
  {icon: BookOpen, title: "A complete activity trail", text: "Search trades, inspect executions, amend or cancel orders, and export the record of your practice session."},
  {icon: ShieldCheck, title: "A workspace of your own", text: "Create a trader account for a separate saved workspace. The guided tour can be skipped and reopened later."},
];

const faq = [
  {question: "Does TradeVelocity place real trades?", answer: "No. Every order stays inside TradeVelocity’s matching engine. The app is a practice and learning tool, with no broker connection or transfer of money or securities."},
  {question: "Are the market prices live?", answer: "No. Market history uses dated daily data and shows its source and as-of date. Your simulated order book is separate from that historical data."},
  {question: "Do I need an account?", answer: "A free trader account is needed for the hosted workspace so your simulated orders and tutorial preference can be saved between visits."},
];

export default function ProductPage({signedIn}: {signedIn: boolean}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const workspaceHref = signedIn ? "/app" : "/signup";
  const workspaceLabel = signedIn ? "Open workspace" : "Start practicing";

  return <div className="product-site">
    <header className="product-header">
      <a className="product-brand" href="/" aria-label="TradeVelocity home">
        <span className="product-brand-mark">TV</span>
        <span>TRADE<span>VELOCITY</span><small>THE MATCHING WORKSPACE</small></span>
      </a>
      <button className="product-menu" type="button" aria-label={menuOpen ? "Close menu" : "Open menu"}
        aria-expanded={menuOpen} onClick={() => setMenuOpen(value => !value)}>{menuOpen ? <X size={22} /> : <Menu size={22} />}</button>
      <nav className={menuOpen ? "product-nav open" : "product-nav"} aria-label="Product navigation">
        <a href="#features" onClick={() => setMenuOpen(false)}>Features</a>
        <a href="#how-it-works" onClick={() => setMenuOpen(false)}>How it works</a>
        <a href="#platforms" onClick={() => setMenuOpen(false)}>Platforms</a>
        <a href="#questions" onClick={() => setMenuOpen(false)}>FAQ</a>
      </nav>
      <div className="product-header-actions">
        {!signedIn && <a className="product-signin" href="/login">Sign in</a>}
        <a className="product-header-cta" href={workspaceHref}>{workspaceLabel}<ArrowUpRight size={16} /></a>
      </div>
    </header>

    <main>
      <section className="product-hero" aria-labelledby="product-heading">
        <div className="product-hero-glow" aria-hidden="true" />
        <div className="product-hero-inner">
          <div className="product-hero-copy">
            <span className="product-status"><span /> WEB WORKSPACE IS LIVE</span>
            <p className="product-kicker">A CLEARER WAY TO LEARN MARKET MATCHING</p>
            <h1 id="product-heading">Every order has a place.<br /><em>Every match has a story.</em></h1>
            <p className="product-hero-description">Place practice orders, see how the price–time book responds, and follow each fill from entry to execution. TradeVelocity makes the mechanics visible.</p>
            <div className="product-hero-actions">
              <a className="product-button product-button-primary" href={workspaceHref}>{workspaceLabel}<ArrowRight size={18} /></a>
              <a className="product-button product-button-ghost" href="#how-it-works">See how it works<ChevronRight size={18} /></a>
            </div>
            <p className="product-hero-note"><ShieldCheck size={16} /> Simulation only. No broker connection or real-money trades.</p>
          </div>
          <div className="product-hero-visual">
            <div className="product-preview-frame">
              <div className="product-preview-top"><span className="product-preview-dots"><i /><i /><i /></span><span>TradeVelocity / Market history</span><span>LIVE WORKSPACE</span></div>
              <img src="/product/market-light.png" alt="Actual TradeVelocity market history workspace showing a dated price chart and analysis panels" />
            </div>
            <div className="product-preview-caption"><span className="product-preview-caption-icon"><BarChart3 size={20} /></span><span><strong>Built to be explored</strong><small>Actual app interface, not a concept image</small></span><Check size={18} /></div>
          </div>
        </div>
      </section>

      <div className="product-proof" aria-label="Product highlights"><span><Layers3 size={18} /> Price → time priority</span><span><ShieldCheck size={18} /> Separate trader workspaces</span><span><BookOpen size={18} /> Recorded executions</span><span><Monitor size={18} /> Web and Windows</span></div>

      <section id="features" className="product-section product-features" aria-labelledby="features-heading">
        <div className="product-section-head"><div><p className="product-kicker">THE WORKSPACE</p><h2 id="features-heading">The whole matching process,<br />in one place.</h2></div><p>From a new order to the resting book, a partial fill, and the final record—see what happened and why.</p></div>
        <div className="product-feature-grid">{features.map(({icon: Icon, title, text}) => <article className="product-feature" key={title}><span className="product-feature-icon"><Icon size={23} strokeWidth={1.8} /></span><h3>{title}</h3><p>{text}</p></article>)}</div>
      </section>

      <section id="how-it-works" className="product-section product-process" aria-labelledby="process-heading">
        <div className="product-process-copy"><p className="product-kicker">MATCHING, MADE VISIBLE</p><h2 id="process-heading">See a partial fill<br />from both sides.</h2><p>The order book chooses the best compatible price. At a price level, earlier orders go first. The trade uses the resting order’s price.</p><a href={workspaceHref} className="product-inline-link">Try it in your workspace <ArrowRight size={18} /></a><small>Illustrative example. The live workspace starts with an empty book.</small></div>
        <div className="product-example" aria-label="Example of a partial fill">
          <div className="product-example-heading"><span>PRICE–TIME MATCHING</span><span>01 / 03</span></div>
          <div className="product-order-card"><span className="product-order-side sell">SELL LIMIT</span><strong>5 shares <small>@ ₹100</small></strong><span className="product-order-meta">Rests in the order book first</span></div>
          <div className="product-example-join"><span /><ArrowRight size={18} /><span /></div>
          <div className="product-order-card"><span className="product-order-side buy">BUY LIMIT</span><strong>3 shares <small>@ ₹101</small></strong><span className="product-order-meta">Compatible with the resting sell</span></div>
          <div className="product-match-result"><span><Check size={18} /> EXECUTED</span><strong>3 shares match at ₹100</strong><small>2 sell shares remain open on the book</small></div>
        </div>
      </section>

      <section className="product-section product-showcase" aria-labelledby="showcase-heading"><div className="product-showcase-copy"><p className="product-kicker">DESIGNED FOR CLARITY</p><h2 id="showcase-heading">A workspace that shows its work.</h2><p>View market history beside your own simulated activity. Each screen makes its data source and role clear, so historical prices are never confused with live orders.</p><a href={workspaceHref} className="product-inline-link">Explore the app <ArrowRight size={18} /></a></div><div className="product-showcase-image"><img src="/product/market-light.png" alt="TradeVelocity market history screen with dated chart and recent daily bars" loading="lazy" /></div></section>

      <section id="platforms" className="product-section product-platforms" aria-labelledby="platforms-heading"><div className="product-section-head"><div><p className="product-kicker">YOUR WAY IN</p><h2 id="platforms-heading">Learn from the browser.<br />Keep going on desktop.</h2></div><p>Use the same saved workspace in the browser and the Windows app. The Windows executable also includes an offline demo.</p></div><div className="product-platform-grid">
        <article className="product-platform-card featured"><span className="product-platform-icon"><Monitor size={25} /></span><div><h3>Web workspace</h3><p>Open the live app, create an account, and follow the skippable guided tour.</p></div><a href={workspaceHref}>Open web app <ArrowUpRight size={17} /></a></article>
        <article className="product-platform-card"><span className="product-platform-icon"><Download size={25} /></span><div><h3>Windows desktop</h3><p>Double-click the standalone Windows x64 executable.</p></div><a href="/download">Windows download <ArrowUpRight size={17} /></a></article>
      </div></section>

      <section id="questions" className="product-section product-faq" aria-labelledby="faq-heading"><div><p className="product-kicker">GOOD TO KNOW</p><h2 id="faq-heading">A few clear answers.</h2><p>TradeVelocity is a matching-engine learning tool with carefully separated simulated orders and historical data.</p></div><div className="product-faq-list">{faq.map(item => <details key={item.question}><summary>{item.question}<span>+</span></summary><p>{item.answer}</p></details>)}</div></section>

      <section className="product-final-cta"><div><p className="product-kicker">READY TO SEE THE BOOK MOVE?</p><h2>Make your first match.</h2><p>Create a workspace, follow the tutorial, and see what happens when two orders meet.</p></div><a className="product-button product-button-light" href={workspaceHref}>{workspaceLabel}<ArrowRight size={18} /></a></section>
    </main>
    <footer className="product-footer"><a className="product-brand" href="/"><span className="product-brand-mark">TV</span><span>TRADE<span>VELOCITY</span><small>THE MATCHING WORKSPACE</small></span></a><p>Simulation only · No broker connection · Historical market data is not a live feed.</p><a href="https://github.com/sgshiv001/TRADE-VELOCITY" rel="noopener noreferrer"><Github size={18} /> GitHub <ArrowUpRight size={15} /></a></footer>
  </div>;
}

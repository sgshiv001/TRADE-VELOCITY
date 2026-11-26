"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  Bell, BookOpen, BrainCircuit, ChartCandlestick, CircleHelp, Compass, History,
  LayoutDashboard, LogOut, Menu, MessageCircle, PanelLeftClose, Search, Settings,
  Sparkles, Star, TrendingUp, Wallet, X,
} from "lucide-react";
import type { Trader } from "../../../frontend/src/AccessGate";
import { useTraderActivity } from "../../../frontend/src/AdminActivity";
import { EditLists, Inbox, Ledger, PaperPortfolio, useResource, type Executions, type Profile, type Wallet as WalletData } from "../../../frontend/src/AdvancedPanels";
import { api } from "../../../frontend/src/api";
import { desktopView } from "../../../frontend/src/desktopView";
import Tutorial, { fundedTutorialSteps } from "../../../frontend/src/Tutorial";
import type { Market } from "../../../frontend/src/types";
import { useLiveSession } from "../../../frontend/src/useLiveSession";
import { ThemeSelect, type Appearance, type Theme } from "./Appearance";
import { Brand } from "./Brand";
import Intelligence from "./Intelligence";
import { ExecutedTrades, Explore, Overview } from "./MarketViews";
import Terminal, { DataState } from "./Terminal";

const groups = [
  {title: "Trading", pages: [
    {id: "overview", label: "Overview", icon: LayoutDashboard}, {id: "trade", label: "Trading terminal", icon: ChartCandlestick},
    {id: "markets", label: "Explore markets", icon: Compass}, {id: "watchlist", label: "Watchlists", icon: Star, account: true},
    {id: "portfolio", label: "Portfolio", icon: Wallet, account: true}, {id: "orders", label: "Orders", icon: BookOpen},
    {id: "trades", label: "Trade history", icon: History}, {id: "funds", label: "Funds", icon: Wallet, account: true},
  ]},
  {title: "Intelligence", pages: [
    {id: "analyst", label: "AI Analyst", icon: BrainCircuit}, {id: "predictions", label: "Predictions", icon: TrendingUp},
    {id: "recommendations", label: "Recommendations", icon: Sparkles}, {id: "assistant", label: "AI Assistant", icon: MessageCircle},
  ]},
  {title: "Account", pages: [
    {id: "notifications", label: "Notifications", icon: Bell, account: true}, {id: "settings", label: "Settings", icon: Settings},
    {id: "help", label: "Help", icon: CircleHelp},
  ]},
] as const;

type Page = typeof groups[number]["pages"][number]["id"];

const menuPages = groups.flatMap(group => [...group.pages] as {id: Page; label: string; icon: typeof Wallet; account?: boolean}[]);
const symbolPattern = /^[A-Z][A-Z0-9.&-]{0,15}$/;
const sectionLoading = "Loading account information…";

function route(account: boolean) {
  const parameters = new URLSearchParams(location.search);
  const page = menuPages.find(entry => entry.id === parameters.get("view") && (!entry.account || account))?.id;
  const symbol = parameters.get("symbol");
  return {page: page ?? (desktopView() === "trader" ? "trade" : "overview"), symbol: symbol && symbolPattern.test(symbol) ? symbol : "RELIANCE"} as const;
}

export default function TradingWorkspace({trader, signOut, appearance, setAppearance, theme}: {
  trader: Trader | null;
  signOut(): Promise<void>;
  appearance: Appearance;
  setAppearance(value: Appearance): void;
  theme: Theme;
}) {
  const account = Boolean(trader);
  const [selection, setSelection] = useState(() => route(account));
  const {page, symbol} = selection;
  const [compact, setCompact] = useState(false);
  const [menu, setMenu] = useState(false);
  const [revision, setRevision] = useState(0);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [tutorialStep, setTutorialStep] = useState<number | null>(trader && !trader.tutorial_seen ? 0 : null);
  const searchDialog = useRef<HTMLDialogElement>(null);
  const market = useResource<Market>("/market");
  const wallet = useResource<WalletData>(account ? "/account/portfolio" : null, revision);
  const profile = useResource<Profile>(account ? "/account/profile" : null, revision);
  const inbox = useResource<Executions>(account ? "/account/notifications" : null, revision);
  const options = market.data?.companies ?? [];
  const selected = options.find(company => company.symbol === symbol);
  const watched = profile.data?.watchlists[0]?.symbols ?? [];
  const refresh = useCallback(async () => { setRevision(value => value + 1); }, []);
  const live = useLiveSession(refresh);
  useTraderActivity(account);

  useEffect(() => {
    function handleHistory() { setSelection(route(account)); }
    window.addEventListener("popstate", handleHistory);
    return () => window.removeEventListener("popstate", handleHistory);
  }, [account]);

  useEffect(() => {
    const keyboard = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        if (!searchDialog.current?.open) searchDialog.current?.showModal();
      }
    };
    window.addEventListener("keydown", keyboard);
    return () => window.removeEventListener("keydown", keyboard);
  }, []);

  function navigate(next: Page, nextSymbol = symbol) {
    const url = new URL(location.href);
    url.pathname = "/app";
    url.searchParams.set("view", next);
    url.searchParams.set("symbol", nextSymbol);
    if (url.href !== location.href) history.pushState(null, "", url);
    setSelection({page: next, symbol: nextSymbol});
    searchDialog.current?.close();
    setSearch("");
    setMenu(false);
    window.scrollTo({top: 0});
  }

  async function saveProfile(draft: Profile) {
    const saved = await api<Profile>("/account/profile", {method: "PUT", body: JSON.stringify(draft)});
    await refresh();
    return saved;
  }

  async function toggle(symbol: string) {
    if (!profile.data) return;
    const [first, ...rest] = profile.data.watchlists;
    const symbols = watched.includes(symbol) ? watched.filter(value => value !== symbol) : [...watched, symbol];
    if (symbols.length > 50) { setError("This watchlist already contains 50 instruments."); return; }
    try { await saveProfile({...profile.data, watchlists: [{...first, symbols}, ...rest]}); setError(""); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to update your watchlist."); await refresh(); }
  }

  const filtered = options.filter(company =>
    `${company.symbol} ${company.name}`.toLowerCase().includes(search.trim().toLowerCase())).slice(0, 10);

  return <div className="tv2 tv2-app" data-tv-theme={theme} data-compact={compact}>
    <a className="tv2-skip" href="#workspace-main">Skip to workspace</a>
    {menu && <button className="tv2-scrim" aria-label="Close navigation" onClick={() => setMenu(false)} />}
    <aside className={`tv2-sidebar${menu ? " tv2-sidebar-open" : ""}`}>
      <div className="tv2-sidebar-brand"><Brand /><button className="tv2-icon tv2-collapse" aria-label={compact ? "Expand sidebar" : "Collapse sidebar"}
        onClick={() => setCompact(value => !value)}><PanelLeftClose size={17} /></button></div>
      <nav aria-label="Main navigation">
        {groups.map(group => {
          const pages = menuPages.filter(entry => group.pages.some(item => item.id === entry.id) && (!entry.account || account));
          return <div className="tv2-nav-group" key={group.title}><span>{group.title}</span>
            {pages.map(({id, label, icon: Icon}) => <button key={id} title={label} aria-label={label} aria-current={page === id ? "page" : undefined}
              onClick={() => navigate(id)}><Icon size={17} /><span>{label}</span></button>)}
          </div>;
        })}
      </nav>
      <div className="tv2-nav-foot"><i /> <span>{account ? "Paper trading" : "Local practice"}</span></div>
    </aside>
    <div className="tv2-main">
      <header className="tv2-topbar">
        <button className="tv2-icon tv2-open-menu" aria-label="Open navigation" onClick={() => setMenu(true)}><Menu size={22} /></button>
        <button className="tv2-top-search" aria-label="Search stocks and pages" onClick={() => searchDialog.current?.showModal()}>
          <Search size={18} /><span>Search stocks and pages</span><kbd>Ctrl K</kbd>
        </button>
        <div className="tv2-top-right">
          <span className="tv2-connection" role="status"><i data-online={live.online} />{!live.online ? "Offline" : live.connected ? "Connected" : "Syncing"}</span>
          <label className="tv2-symbol-select"><span className="tv2-visually-hidden">Select symbol</span>
            <select value={symbol} onChange={event => navigate(page, event.target.value)}>
              {[symbol, ...options.map(company => company.symbol).filter(value => value !== symbol)].map(value => <option key={value}>{value}</option>)}
            </select></label>
          {account && <button className="tv2-icon" onClick={() => navigate("notifications")}
            aria-label={`Notifications, ${inbox.data?.unread ?? 0} unread`}><Bell size={20} />{!!inbox.data?.unread && <i />}</button>}
          <button className="tv2-icon tv2-avatar" aria-label="Account settings" onClick={() => navigate("settings")}>
            {trader ? trader.username.slice(0, 2).toUpperCase() : <Settings size={19} />}
          </button>
        </div>
      </header>

      <main className="tv2-work" id="workspace-main" tabIndex={-1}>
        {!live.online && page !== "trade" && <p className="tv2-info" role="status">Offline. Displayed data may be out of date.</p>}
        {error && <p className="tv2-info" role="alert">{error}</p>}
        <div className="tv2-page" key={page}>
          {page === "overview" && <>
            {wallet.error && <DataState error={wallet.error} retry={wallet.reload} loading="" />}
            <Overview wallet={wallet.data} market={market.data} watched={watched} trade={value => navigate("trade", value)} onMarkets={() => navigate("markets")} />
          </>}
          {page === "trade" && <Terminal key={symbol} symbol={symbol} company={selected} funded={account} revision={revision} theme={theme}
            online={live.online} refresh={refresh} cash={wallet.data?.available_cash}
            holdings={wallet.data ? wallet.data.holdings.find(row => row.symbol === symbol)?.quantity ?? 0 : undefined} />}
          {page === "markets" && <Explore market={market.data} error={market.error} retry={market.reload} trade={value => navigate("trade", value)}
            watched={watched} toggle={profile.data ? value => void toggle(value) : undefined} />}
          {page === "watchlist" && (profile.data ? <EditLists profile={profile.data} save={saveProfile} select={value => navigate("trade", value)} />
            : <DataState error={profile.error} retry={profile.reload} loading={sectionLoading} />)}
          {(page === "portfolio" || page === "funds") && <PaperPortfolio funds={page === "funds"} revision={revision} />}
          {page === "orders" && <Ledger revision={revision} hosted={account} />}
          {page === "trades" && <ExecutedTrades revision={revision} funded={account} />}
          {(page === "analyst" || page === "predictions" || page === "recommendations" || page === "assistant") &&
            <Intelligence key={symbol + page} symbol={symbol} mode={page} wallet={wallet.data} trade={() => navigate("trade")} />}
          {page === "notifications" && <Inbox revision={revision} />}
          {page === "settings" && <>
            <div className="tv2-heading"><div><h1>Settings</h1><p>{trader?.username ?? "Local workspace"}</p></div></div>
            <section className="tv2-surface tv2-settings"><h2>Appearance</h2>
              <ThemeSelect appearance={appearance} setAppearance={setAppearance} />
              <label><input type="checkbox" checked={compact} onChange={event => setCompact(event.target.checked)} /> Compact sidebar</label>
            </section>
            <section className="tv2-surface tv2-settings"><h2>Account</h2>
              <button className="tv2-button tv2-outline" onClick={() => void signOut()}><LogOut size={16} /> Sign out</button>
              <a href="/download">Downloads and release notes</a>
            </section>
          </>}
          {page === "help" && <>
            <div className="tv2-heading"><div><h1>Help</h1><p>Get started with the paper trading workspace.</p></div></div>
            <section className="tv2-surface tv2-settings"><h2>Paper trading guide</h2>
              <p>Choose a stock, review its timestamped quote, and open the trading terminal. A confirmed limit order can fill, partially fill, or rest in the simulated book. Check Orders and Trade History for the result.</p>
              {account && <button className="tv2-button tv2-outline" onClick={() => setTutorialStep(0)}>Open guided tutorial</button>}
              <a href="/#help">Frequently asked questions</a>
            </section>
          </>}
        </div>
        <footer className="tv2-work-footer"><span>TradeVelocity · Paper trading</span><span>{market.data?.as_of ? `Market history through ${market.data.as_of}` : "Market history unavailable"}</span></footer>
      </main>
    </div>
    <dialog className="tv2-search-dialog" ref={searchDialog} aria-labelledby="tv2-search-title">
      <div className="tv2-panel-head"><h2 id="tv2-search-title">Find a stock or page</h2><button className="tv2-icon" onClick={() => searchDialog.current?.close()} aria-label="Close search"><X size={20} /></button></div>
      <input aria-label="Search query" placeholder="Search by symbol, company, or page" value={search} onChange={event => setSearch(event.target.value)} />
      <div className="tv2-search-results">
        {filtered.map(company => <button key={company.symbol} onClick={() => navigate(page === "overview" || page === "markets" ? "trade" : page, company.symbol)}>
          <strong>{company.symbol}</strong><span>{company.name}</span></button>)}
        {menuPages.filter(item => (!item.account || account) && item.label.toLowerCase().includes(search.trim().toLowerCase())).slice(0, 6)
          .map(item => <button key={item.id} onClick={() => navigate(item.id)}><item.icon size={14} /><span>{item.label}</span></button>)}
      </div>
    </dialog>
    {tutorialStep != null && <Tutorial step={tutorialStep} steps={fundedTutorialSteps}
      onStep={step => { setTutorialStep(step); navigate(step === 2 ? "portfolio" : "trade"); }}
      onDismiss={() => { setTutorialStep(null); void api("/auth/tutorial", {method: "POST"}).catch(() => setError("Tutorial preference could not be saved.")); }} />}
  </div>;
}

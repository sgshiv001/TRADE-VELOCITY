import { useCallback, useEffect, useState } from "react";
import { Alert, AppState, Pressable, Text, TextInput, View } from "react-native";
import { useFocusEffect, useLocalSearchParams } from "expo-router";
import { ArrowDownRight, ArrowUpRight, Search } from "lucide-react-native";
import { formatINR, limitOrderSchema, symbolSchema, TradeVelocityApiError, type Depth, type LimitOrder, type Quote } from "@tradevelocity/client";
import { Action, DataState, Screen, useMobileTheme, useWorkspace } from "../src/workspace";
import { quoteTime, useData, type MarketHistory } from "../src/data";
import { Choices, PricePlot } from "../src/market-chart";

const ranges = [{key: "1D", label: "Intraday"}, {key: "1M", label: "1M"}, {key: "3M", label: "3M"}, {key: "1Y", label: "1Y"}] as const;
const styles = [{key: "line", label: "Line"}, {key: "candles", label: "Candles"}] as const;
const sides = [{key: "BUY", label: "Buy"}, {key: "SELL", label: "Sell"}] as const;

export default function Trade() {
  const {theme, colors} = useMobileTheme();
  const link = useLocalSearchParams<{symbol?: string}>();
  const [symbol, setSymbol] = useState("RELIANCE"), [input, setInput] = useState("RELIANCE");
  const [shares, setShares] = useState(""), [price, setPrice] = useState("");
  const [notice, setNotice] = useState(""), [busy, setBusy] = useState(false);
  const [noticeError, setNoticeError] = useState(false);
  const [symbolError, setSymbolError] = useState("");
  const [depthError, setDepthError] = useState("");
  const [depthBusy, setDepthBusy] = useState(false);
  const [pending, setPending] = useState<LimitOrder | null>(null);
  const [side, setSide] = useState<LimitOrder["side"]>("BUY");
  const [range, setRange] = useState<(typeof ranges)[number]["key"]>("1M");
  const [chartStyle, setChartStyle] = useState<(typeof styles)[number]["key"]>("line");
  const [recorded, setRecorded] = useState<{symbol: string; date: string; points: {time: number; value: number}[]}>();
  const {request} = useWorkspace();
  const depth = useData<Depth>(`/paper?symbol=${encodeURIComponent(symbol)}`);
  const quote = useData<Quote>(`/quote/${encodeURIComponent(symbol)}`);
  const history = useData<MarketHistory>(range === "1D" ? null : `/companies/${encodeURIComponent(symbol)}?period=${range}`);
  const intraday = recorded?.symbol === symbol ? recorded.points : [];
  const refreshQuote = quote.refresh;

  useFocusEffect(useCallback(() => {
    const timer = setInterval(() => { if (AppState.currentState === "active") refreshQuote(); }, 60_000);
    return () => clearInterval(timer);
  }, [refreshQuote]));

  useEffect(() => {
    const latest = quote.data;
    if (!latest?.as_of || latest.kind !== "intraday" || latest.price == null || !Number.isFinite(latest.price)) return;
    const point = {time: Date.parse(latest.as_of), value: latest.price};
    if (!Number.isFinite(point.time)) return;
    const date = new Date(point.time).toLocaleDateString("en-IN", {timeZone: "Asia/Kolkata"});
    setRecorded(previous => {
      const points = previous?.symbol === symbol && previous.date === date ? previous.points : [];
      const last = points.at(-1);
      if (last && (last.time > point.time || (last.time === point.time && last.value === point.value))) return previous;
      return {symbol, date, points: [...(last?.time === point.time ? points.slice(0, -1) : points).slice(-399), point]};
    });
  }, [quote.data, symbol]);

  useEffect(() => {
    const result = symbolSchema.safeParse(link.symbol);
    if (result.success && result.data !== symbol && !pending) {
      setSymbol(result.data); setInput(result.data); setPrice(""); setShares(""); setNotice(""); setSymbolError(""); setDepthError("");
    }
  }, [link.symbol]);

  function choose() {
    const result = symbolSchema.safeParse(input);
    if (result.success) {
      if (result.data !== symbol) { setPrice(""); setShares(""); }
      setSymbol(result.data); setInput(result.data); setNotice(""); setSymbolError(""); setDepthError("");
    } else setSymbolError("Enter a valid NSE or practice symbol.");
  }

  async function submit(order: LimitOrder) {
    setBusy(true); setPending(order); setNotice("");
    try {
      const result = await request<{filled: number; remaining: number}>("/paper/orders", {
        method: "POST", headers: {"Idempotency-Key": order.order_id}, body: JSON.stringify(order),
      });
      setNoticeError(false);
      setNotice(`Filled ${result.filled} · Resting ${result.remaining}`);
      setPending(null); setShares(""); depth.refresh();
    } catch (cause) {
      if (cause instanceof TradeVelocityApiError && [400, 409, 422].includes(cause.status)) setPending(null);
      setNoticeError(true);
      setNotice(cause instanceof Error ? cause.message : "The order could not be confirmed.");
    } finally { setBusy(false); }
  }

  function review(side: "BUY" | "SELL") {
    const result = limitOrderSchema.safeParse({order_id: `mobile-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`,
      symbol, side, quantity: Number(shares), price, confirmed: true});
    if (!result.success) { setNoticeError(true); setNotice("Enter whole shares and a positive limit price with up to two decimal places."); return; }
    const order = result.data;
    Alert.alert("Confirm paper order", `${side} ${order.quantity} ${symbol} at a limit of ${formatINR(order.price)}`, [
      {text: "Back", style: "cancel"}, {text: "Confirm", onPress: () => void submit(order)},
    ]);
  }

  const previousClose = history.data?.history.at(-2)?.close;
  const lastClose = history.data?.history.at(-1)?.close;
  const base = range === "1D" ? intraday[0]?.value : previousClose;
  const latest = range === "1D" ? intraday.at(-1)?.value : lastClose;
  const percent = base && latest != null ? (latest - base) / base * 100 : null;
  const changeColor = percent != null && percent < 0 ? colors.error : colors.action;
  const quotePrice = quote.data?.price;
  const quantity = Number(shares);
  const limit = Number(price);
  const canPrice = Number.isFinite(limit) && limit > 0 && Number.isInteger(quantity) && quantity > 0;
  const ticketDisabled = busy || Boolean(pending);

  return <Screen title="Trade" subtitle="Paper trading · Limit orders"
    refresh={() => { depth.refresh(); quote.refresh(); history.refresh(); }} refreshing={depth.loading || quote.loading || history.loading}>
    <View style={theme.row}>
      <View style={[theme.row, {flex: 1, backgroundColor: colors.raised, borderRadius: 12, borderWidth: 1, borderColor: colors.line, paddingLeft: 12}]}>
        <Search size={17} color={colors.muted} />
        <TextInput accessibilityLabel="Stock symbol" autoCapitalize="characters" autoCorrect={false} returnKeyType="search"
          style={[theme.field, {flex: 1, borderWidth: 0, paddingLeft: 0}]} value={input} onChangeText={setInput}
          editable={!ticketDisabled} onSubmitEditing={choose} />
      </View>
      <Action title="Load stock" kind="secondary" disabled={ticketDisabled} onPress={choose} />
    </View>
    {Boolean(symbolError) && <Text accessibilityLiveRegion="polite" style={theme.error}>{symbolError}</Text>}
    <View style={theme.panel}>
      <View style={theme.between}>
        <Text style={theme.sectionTitle}>{symbol}</Text>
        <Text style={theme.eyebrow}>{quote.data?.kind === "close" ? "DAILY CLOSE" : "NSE REFERENCE"}</Text>
      </View>
      <Text style={theme.value}>{quotePrice == null ? quote.loading ? "Loading…" : "—" : formatINR(quotePrice)}</Text>
      <Text style={theme.subtle}>{quote.data?.as_of ? `${quote.data.source} · ${quoteTime(quote.data.as_of)}${quote.data.kind === "intraday" ? " · May be delayed" : ""}`
        : quote.error || (quote.loading ? "Checking for a market quote…" : "A market reference price is unavailable.")}</Text>
      <Choices options={ranges} value={range} onChange={setRange} />
      {range === "1D" ? <>
        {intraday.length ? <PricePlot symbol={symbol} quotes={intraday} /> : <Text style={theme.subtle}>Waiting for an intraday quote.</Text>}
        <Text style={theme.subtle}>{intraday.length} {intraday.length === 1 ? "observation" : "observations"} · Checks every minute while Trade is open.</Text>
      </> : <>
        {history.data?.history.length ? <PricePlot symbol={symbol} daily={history.data.history} candles={chartStyle === "candles"} />
          : history.error ? <Text style={theme.error}>{history.error}</Text>
          : <Text style={theme.subtle}>{history.loading ? "Loading daily prices…" : "No daily prices for this stock."}</Text>}
        {Boolean(history.data?.history.length) && <View style={theme.between}>
          <Choices options={styles} value={chartStyle} onChange={setChartStyle} />
          <Text style={[theme.subtle, {textAlign: "right", flexShrink: 1}]}>Adjusted daily prices</Text>
        </View>}
      </>}
      {percent !== null && (range !== "1D" || intraday.length > 1) && <View style={theme.row}>
        {percent < 0 ? <ArrowDownRight size={16} color={changeColor} /> : <ArrowUpRight size={16} color={changeColor} />}
        <Text style={[theme.subtle, {color: changeColor}]}>{percent > 0 ? "+" : ""}{percent.toFixed(2)}% {range === "1D" ? "since first observation" : "vs. prior daily close"}</Text>
      </View>}
    </View>
    <View style={theme.panel}>
      <View style={theme.between}><Text style={theme.sectionTitle}>Order ticket</Text><Choices options={sides} value={side} onChange={setSide} disabled={ticketDisabled} /></View>
      <View style={{flexDirection: "row", flexWrap: "wrap", gap: 10}}>
        <View style={{flex: 1, minWidth: 108, gap: 4}}><Text style={theme.subtle}>Shares</Text>
          <TextInput style={theme.field} accessibilityLabel="Shares" placeholder="Quantity" placeholderTextColor={colors.muted}
            keyboardType="number-pad" editable={!ticketDisabled} value={shares} onChangeText={setShares} /></View>
        <View style={{flex: 1, minWidth: 108, gap: 4}}><Text style={theme.subtle}>Limit price (₹)</Text>
          <TextInput style={theme.field} accessibilityLabel="Limit price" placeholder="Price per share" placeholderTextColor={colors.muted}
            keyboardType="decimal-pad" editable={!ticketDisabled} value={price} onChangeText={setPrice} /></View>
      </View>
      {quotePrice != null && !ticketDisabled && <Pressable accessibilityRole="button" onPress={() => setPrice(quotePrice.toFixed(2))}
        style={{minHeight: 44, justifyContent: "center", alignSelf: "flex-start"}}><Text style={theme.link}>Use reference price</Text></Pressable>}
      {canPrice && <View style={theme.between}><Text style={theme.subtle}>Order value at limit</Text><Text style={theme.number}>{formatINR(limit * quantity)}</Text></View>}
      {pending ? <Action title={busy ? "Submitting…" : "Retry confirmed order"} disabled={busy} onPress={() => void submit(pending)} />
        : <Action title={side === "BUY" ? "Review buy" : "Review sell"} disabled={busy} onPress={() => review(side)} />}
      {Boolean(notice) && <Text accessibilityLiveRegion="polite" style={noticeError ? theme.error : theme.subtle}>{notice}</Text>}
    </View>
    <View style={theme.panel}>
      <Text style={theme.sectionTitle}>Simulated market depth</Text>
      {depth.data ? <>
        <View style={theme.row}>
          <View style={{flex: 1}}><Text style={theme.subtle}>Best bid</Text><Text style={[theme.number, {color: colors.action}]}>{depth.data.book.bids[0] ? formatINR(depth.data.book.bids[0].price) : "—"}</Text></View>
          <View style={{flex: 1}}><Text style={theme.subtle}>Best ask</Text><Text style={[theme.number, {color: colors.error}]}>{depth.data.book.asks[0] ? formatINR(depth.data.book.asks[0].price) : "—"}</Text></View>
        </View>
        {(depth.data.book.bids.length > 0 || depth.data.book.asks.length > 0) && <View style={{flexDirection: "row", gap: 10}}>
          {[depth.data.book.bids, depth.data.book.asks].map((levels, index) => <View style={{flex: 1, gap: 4}} key={index}>
            {levels.slice(0, 4).map(level => <View key={level.price} style={theme.between}>
              <Text style={theme.subtle}>{formatINR(level.price)}</Text><Text style={theme.subtle}>{level.quantity}</Text>
            </View>)}
          </View>)}
        </View>}
      </> : <DataState message="Loading bids and asks…" error={depth.error} retry={depth.refresh} />}
      <Action title={depthBusy ? "Refreshing…" : "Refresh simulated depth"} kind="secondary" disabled={depthBusy || quotePrice == null} onPress={() => {
        setDepthBusy(true); setDepthError("");
        void request(`/paper/liquidity/${encodeURIComponent(symbol)}`, {method: "POST"})
          .then(() => depth.refresh())
          .catch(error => setDepthError(error instanceof Error ? error.message : "Depth could not refresh."))
          .finally(() => setDepthBusy(false));
      }} />
      {Boolean(depthError) && <Text accessibilityLiveRegion="polite" style={theme.error}>{depthError}</Text>}
    </View>
  </Screen>;
}

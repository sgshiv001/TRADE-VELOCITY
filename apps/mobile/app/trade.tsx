import { useEffect, useState } from "react";
import { Alert, Text, TextInput, View } from "react-native";
import { useLocalSearchParams } from "expo-router";
import { formatINR, limitOrderSchema, symbolSchema, TradeVelocityApiError, type Depth, type LimitOrder, type Quote } from "@tradevelocity/client";
import { Action, Screen, theme, useWorkspace } from "../src/workspace";
import { useData } from "../src/data";

export default function Trade() {
  const link = useLocalSearchParams<{symbol?: string}>();
  const [symbol, setSymbol] = useState("RELIANCE"), [input, setInput] = useState("RELIANCE");
  const [shares, setShares] = useState(""), [price, setPrice] = useState("");
  const [notice, setNotice] = useState(""), [busy, setBusy] = useState(false);
  const [pending, setPending] = useState<LimitOrder | null>(null);
  const {request} = useWorkspace();
  const depth = useData<Depth>(`/paper?symbol=${encodeURIComponent(symbol)}`);
  const quote = useData<Quote>(`/quote/${encodeURIComponent(symbol)}`);
  useEffect(() => {
    const result = symbolSchema.safeParse(link.symbol);
    if (result.success) { setSymbol(result.data); setInput(result.data); }
  }, [link.symbol]);

  function choose() {
    const result = symbolSchema.safeParse(input);
    if (result.success) { setSymbol(result.data); setInput(result.data); setNotice(""); }
    else setNotice("Enter a valid NSE or practice symbol.");
  }

  async function submit(order: LimitOrder) {
    setBusy(true); setPending(order);
    try {
      const result = await request<{filled: number; remaining: number}>("/paper/orders", {
        method: "POST", headers: {"Idempotency-Key": order.order_id}, body: JSON.stringify(order),
      });
      setNotice(`Filled ${result.filled} · Resting ${result.remaining}`);
      setPending(null); setShares(""); depth.refresh();
    } catch (cause) {
      if (cause instanceof TradeVelocityApiError && [400, 409, 422].includes(cause.status)) setPending(null);
      setNotice(cause instanceof Error ? cause.message : "The order could not be confirmed.");
    } finally { setBusy(false); }
  }

  function review(side: "BUY" | "SELL") {
    const result = limitOrderSchema.safeParse({order_id: `mobile-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`,
      symbol, side, quantity: Number(shares), price, confirmed: true});
    if (!result.success) { setNotice("Enter whole shares and a positive limit price with up to two decimal places."); return; }
    const order = result.data;
    Alert.alert("Confirm paper order", `${side} ${order.quantity} ${symbol} at a limit of ${formatINR(order.price)}`, [
      {text: "Back", style: "cancel"}, {text: "Confirm", onPress: () => void submit(order)},
    ]);
  }

  return <Screen title="Paper trading">
    <Text style={theme.subtle}>Funded simulation · Limit orders</Text>
    <TextInput accessibilityLabel="Symbol" autoCapitalize="characters" style={theme.field} value={input} onChangeText={setInput} />
    <Action title="Show symbol" onPress={choose} />
    <View style={theme.panel}>
      <Text style={theme.text}>{symbol} reference price {quote.data?.price ? formatINR(quote.data.price) : "—"}</Text>
      {quote.data?.as_of && <Text style={theme.subtle}>{quote.data.source} · {quote.data.as_of}</Text>}
      {depth.data && <Text style={theme.subtle}>Best bid {depth.data.book.bids[0] ? formatINR(depth.data.book.bids[0].price) : "—"} · Best ask {depth.data.book.asks[0] ? formatINR(depth.data.book.asks[0].price) : "—"}</Text>}
      <Action title="Load simulated depth" disabled={busy} onPress={() => {
        void request(`/paper/liquidity/${encodeURIComponent(symbol)}`, {method: "POST"})
          .then(() => { depth.refresh(); setNotice("Simulated bid and ask updated."); })
          .catch(error => setNotice(String(error)));
      }} />
    </View>
    {depth.error && <Text style={theme.error}>{depth.error}</Text>}
    <TextInput style={theme.field} accessibilityLabel="Shares" placeholder="Shares" placeholderTextColor="#94a3b8" keyboardType="number-pad" value={shares} onChangeText={setShares} />
    <TextInput style={theme.field} accessibilityLabel="Limit price" placeholder="Limit price" placeholderTextColor="#94a3b8" keyboardType="decimal-pad" value={price} onChangeText={setPrice} />
    <Action title="Review buy" disabled={busy || Boolean(pending)} onPress={() => review("BUY")} />
    <Action title="Review sell" disabled={busy || Boolean(pending)} onPress={() => review("SELL")} />
    {pending && <Action title="Retry confirmed order" disabled={busy} onPress={() => void submit(pending)} />}
    {notice && <Text accessibilityLiveRegion="polite" style={theme.subtle}>{notice}</Text>}
  </Screen>;
}

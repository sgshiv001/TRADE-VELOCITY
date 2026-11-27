import { useState } from "react";
import { Text, View } from "react-native";
import { Action, MobileThemePicker, Screen, useMobileTheme, useWorkspace } from "../src/workspace";
import { formatINR, type ExecutionInbox, type Portfolio } from "@tradevelocity/client";
import { useData } from "../src/data";

export default function Home() {
  const {theme} = useMobileTheme();
  const {trader, signOut, enableLock, request} = useWorkspace();
  const portfolio = useData<Portfolio>("/account/portfolio");
  const inbox = useData<ExecutionInbox>("/account/notifications");
  const [notice, setNotice] = useState("");
  function action(operation: () => Promise<unknown>, success: string) {
    void operation().then(() => setNotice(success)).catch(error => setNotice(String(error)));
  }
  return <Screen title="Overview" refresh={() => { portfolio.refresh(); inbox.refresh(); }}>
    <Text style={theme.subtle}>Signed in as {trader.username} · INR paper trading</Text>
    {portfolio.error && <Text style={theme.error}>{portfolio.error}</Text>}
    {portfolio.data && <View style={theme.panel}>
      <Text style={theme.subtle}>Virtual account value</Text><Text style={theme.title}>{formatINR(portfolio.data.equity)}</Text>
      <Text style={theme.text}>{formatINR(portfolio.data.available_cash)} available</Text>
    </View>}
    <View style={theme.panel}>
      <Text style={theme.text}>Execution inbox · {inbox.data?.unread ?? "—"} unread</Text>
      {inbox.error && <Text style={theme.error}>{inbox.error}</Text>}
      {inbox.data?.items.slice(0, 5).map(item => <Text key={item.id} style={theme.subtle}>{item.symbol} · {item.quantity} shares · {formatINR(item.price)}</Text>)}
      {Boolean(inbox.data?.unread) && <Action title="Mark all as read" onPress={() => action(async () => {
        await request("/account/notifications/read", {method: "POST"});
        inbox.refresh();
      }, "Inbox updated")} />}
    </View>
    <MobileThemePicker />
    <Action title="Enable biometric unlock" onPress={() => action(enableLock, "Device lock preference saved")} />
    <Action title="Sign out" onPress={() => action(signOut, "")} />
    {notice && <Text accessibilityLiveRegion="polite" style={theme.subtle}>{notice}</Text>}
  </Screen>;
}

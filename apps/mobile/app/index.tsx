import { useState } from "react";
import { Modal, Pressable, Text, View } from "react-native";
import { router } from "expo-router";
import { ArrowUpRight, Bell, ChartNoAxesCombined, Settings2 } from "lucide-react-native";
import { Action, DataState, MobileThemePicker, Screen, useMobileTheme, useWorkspace } from "../src/workspace";
import { formatINR, type ExecutionInbox } from "@tradevelocity/client";
import { useData } from "../src/data";
import { PortfolioBalance, usePortfolio } from "../src/portfolio";

export default function Home() {
  const {theme, colors} = useMobileTheme();
  const {trader, signOut, enableLock, request} = useWorkspace();
  const portfolio = usePortfolio();
  const inbox = useData<ExecutionInbox>("/account/notifications");
  const [notice, setNotice] = useState("");
  const [settings, setSettings] = useState(false);
  function action(operation: () => Promise<unknown>, success: string) {
    setNotice("");
    void operation().then(() => setNotice(success)).catch(error => setNotice(error instanceof Error ? error.message : "Could not update your account."));
  }
  return <Screen title="TradeVelocity" subtitle="Your paper trading workspace"
    refresh={() => { portfolio.refresh(); inbox.refresh(); }} refreshing={portfolio.loading || inbox.loading}
    accessory={<Pressable accessibilityRole="button" accessibilityLabel="Account settings" onPress={() => { setNotice(""); setSettings(true); }}
      style={[theme.action, {minWidth: 46, backgroundColor: colors.panel, borderWidth: 1, borderColor: colors.line}]}>
      <Settings2 size={21} color={colors.text} />
    </Pressable>}>
    {(!portfolio.data || portfolio.error) && <DataState message="Loading your paper account…" error={portfolio.error} retry={portfolio.refresh} />}
    {portfolio.data && <PortfolioBalance data={portfolio.data} />}
    <Pressable accessibilityRole="button" accessibilityLabel="Explore markets" onPress={() => router.navigate("/markets")}
      style={({pressed}) => [theme.panel, theme.between, pressed && {opacity: .8}]}>
      <ChartNoAxesCombined color={colors.action} size={22} />
      <View style={{flex: 1}}><Text style={theme.sectionTitle}>Explore markets</Text><Text style={theme.subtle}>Check NSE prices and open a paper trade.</Text></View>
      <ArrowUpRight color={colors.muted} size={18} />
    </Pressable>
    <View style={theme.panel}>
      <View style={theme.row}><Bell size={18} color={colors.action} /><Text style={theme.sectionTitle}>Trade notifications</Text></View>
      {inbox.error ? <Text style={theme.error}>{inbox.error}</Text> : <Text style={theme.subtle}>
        {inbox.data ? inbox.data.items.length ? `${inbox.data.unread} unread` : "Fills appear here when your orders match." : "Loading notifications…"}
      </Text>}
      {inbox.data?.items.slice(0, 3).map(item => <Text key={item.id} style={theme.text}>{item.symbol} · {item.quantity} shares · {formatINR(item.price)}</Text>)}
      {Boolean(inbox.data?.unread) && <Action title="Mark all as read" kind="secondary" onPress={() => action(async () => {
        await request("/account/notifications/read", {method: "POST"});
        inbox.refresh();
      }, "Inbox updated")} />}
    </View>
    {!settings && Boolean(notice) && <Text accessibilityLiveRegion="polite" style={theme.subtle}>{notice}</Text>}
    <Modal visible={settings} animationType="slide" onRequestClose={() => setSettings(false)}>
      <Screen title="Settings" subtitle={trader.username} accessory={<Action title="Done" kind="secondary" onPress={() => setSettings(false)} />}>
        <MobileThemePicker />
        <Action title="Enable biometric unlock" kind="secondary" onPress={() => action(enableLock, "Device lock preference saved")} />
        <Action title="Sign out" kind="danger" onPress={() => action(signOut, "")} />
        {Boolean(notice) && <Text accessibilityLiveRegion="polite" style={theme.subtle}>{notice}</Text>}
      </Screen>
    </Modal>
  </Screen>;
}

import { Tabs } from "expo-router";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";
import { MobileSession, useMobileTheme } from "../src/workspace";

export default function Layout() {
  const {colors, mode} = useMobileTheme();
  return <SafeAreaProvider><StatusBar style={mode === "dark" ? "light" : "dark"} />
    <MobileSession>
      <Tabs screenOptions={{headerStyle: {backgroundColor: colors.background}, headerTintColor: colors.text,
        tabBarStyle: {backgroundColor: colors.panel, borderTopColor: colors.line}, tabBarActiveTintColor: colors.action, tabBarInactiveTintColor: colors.muted}}>
        <Tabs.Screen name="index" options={{title: "Home"}} />
        <Tabs.Screen name="markets" options={{title: "Markets"}} />
        <Tabs.Screen name="trade" options={{title: "Trade"}} />
        <Tabs.Screen name="analyst" options={{title: "AI Analyst"}} />
        <Tabs.Screen name="portfolio" options={{title: "Portfolio"}} />
      </Tabs>
    </MobileSession>
  </SafeAreaProvider>;
}

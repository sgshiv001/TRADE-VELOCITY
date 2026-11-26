import { Tabs } from "expo-router";
import { ArrowLeftRight, ChartNoAxesCombined, LayoutDashboard, Sparkles, Wallet } from "lucide-react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";
import { PortfolioProvider } from "../src/portfolio";
import { MobileAppearance, MobileSession, useMobileTheme } from "../src/workspace";

export default function Layout() {
  return <MobileAppearance><AppLayout /></MobileAppearance>;
}

function AppLayout() {
  const {colors, mode} = useMobileTheme();
  return <SafeAreaProvider style={{backgroundColor: colors.background}}><StatusBar style={mode === "dark" ? "light" : "dark"} />
    <MobileSession><PortfolioProvider>
      <Tabs screenOptions={{sceneStyle: {backgroundColor: colors.background}, headerShown: false, tabBarHideOnKeyboard: true,
        tabBarStyle: {backgroundColor: colors.panel, borderTopColor: colors.line, paddingTop: 5},
        tabBarLabelStyle: {fontWeight: "600", fontSize: 11}, tabBarActiveTintColor: colors.action, tabBarInactiveTintColor: colors.muted}}>
        <Tabs.Screen name="index" options={{title: "Home", tabBarIcon: ({color, size}) => <LayoutDashboard color={color} size={size} />}} />
        <Tabs.Screen name="markets" options={{title: "Markets", tabBarIcon: ({color, size}) => <ChartNoAxesCombined color={color} size={size} />}} />
        <Tabs.Screen name="trade" options={{title: "Trade", tabBarIcon: ({color, size}) => <ArrowLeftRight color={color} size={size} />}} />
        <Tabs.Screen name="analyst" options={{title: "Analyst", tabBarIcon: ({color, size}) => <Sparkles color={color} size={size} />}} />
        <Tabs.Screen name="portfolio" options={{title: "Portfolio", tabBarIcon: ({color, size}) => <Wallet color={color} size={size} />}} />
      </Tabs>
    </PortfolioProvider></MobileSession>
  </SafeAreaProvider>;
}

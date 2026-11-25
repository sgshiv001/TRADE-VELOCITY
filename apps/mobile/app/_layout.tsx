import { Tabs } from "expo-router";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";
import { MobileSession } from "../src/workspace";

export default function Layout() {
  return <SafeAreaProvider><StatusBar style="light" />
    <MobileSession>
      <Tabs screenOptions={{headerStyle: {backgroundColor: "#111827"}, headerTintColor: "#fff",
        tabBarStyle: {backgroundColor: "#111827"}, tabBarActiveTintColor: "#c7d2fe", tabBarInactiveTintColor: "#aab7ca"}}>
        <Tabs.Screen name="index" options={{title: "Home"}} />
        <Tabs.Screen name="markets" options={{title: "Markets"}} />
        <Tabs.Screen name="trade" options={{title: "Trade"}} />
        <Tabs.Screen name="portfolio" options={{title: "Portfolio"}} />
      </Tabs>
    </MobileSession>
  </SafeAreaProvider>;
}

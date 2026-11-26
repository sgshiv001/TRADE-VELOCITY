import { Text, View } from "react-native";
import { router } from "expo-router";
import { Layers3 } from "lucide-react-native";
import { formatINR } from "@tradevelocity/client";
import { Action, DataState, Screen, useMobileTheme } from "../src/workspace";
import { PortfolioBalance, usePortfolio } from "../src/portfolio";
import { quoteTime } from "../src/data";

export default function Portfolio() {
  const {theme, colors} = useMobileTheme();
  const {data, error, loading, refresh} = usePortfolio();
  return <Screen title="Portfolio" subtitle="Virtual balance and positions" refresh={refresh} refreshing={loading}>
    {(!data || error) && <DataState message="Loading portfolio…" error={error} retry={refresh} />}
    {data && <>
      <PortfolioBalance data={data} detail />
      <View style={theme.between}><Text style={theme.sectionTitle} accessibilityRole="header">Holdings</Text>
        <Text style={theme.subtle}>{data.holdings.length} {data.holdings.length === 1 ? "position" : "positions"}</Text></View>
      {data.holdings.length === 0 ? <View style={theme.panel}>
        <View style={theme.row}><Layers3 size={17} color={colors.action} /><Text style={theme.sectionTitle}>No holdings yet</Text></View>
        <Text style={theme.subtle}>Positions appear here after a paper buy fills.</Text>
        <Action title="Explore stocks" kind="secondary" onPress={() => router.navigate("/markets")} />
      </View> : <View style={{gap: 8}}>
        {data.holdings.map(row => <View key={row.symbol} style={theme.panel}>
          <View style={theme.between}><Text style={theme.sectionTitle}>{row.symbol}</Text><Text style={theme.number}>{formatINR(row.value)}</Text></View>
          <Text style={theme.subtle}>{row.quantity} shares · Average cost {formatINR(row.average_cost)}</Text>
          <Text style={theme.subtle}>{row.mark_source === "provider_quote" ? "Provider quote" : row.mark_source === "last_simulated_fill" ? "Last simulated fill" : "Daily close"} {formatINR(row.mark)}</Text>
          <Text style={[theme.number, {color: Number(row.pnl) < 0 ? colors.error : colors.action}]}>{formatINR(row.pnl)} P&L</Text>
        </View>)}
        <Text style={theme.subtle}>Daily marks through {data.market_as_of} where available.</Text>
      </View>}
      {Boolean(data.activity.length) && <View style={theme.panel}>
        <Text style={theme.sectionTitle} accessibilityRole="header">Recent activity</Text>
        {data.activity.slice(0, 6).map(row => <View style={theme.between} key={row.id}>
          <View style={{flex: 1}}><Text style={theme.text}>{row.description}</Text>{row.timestamp && <Text style={theme.subtle}>{quoteTime(row.timestamp)}</Text>}</View>
          <Text style={theme.number}>{formatINR(row.amount)}</Text>
        </View>)}
      </View>}
    </>}
  </Screen>;
}

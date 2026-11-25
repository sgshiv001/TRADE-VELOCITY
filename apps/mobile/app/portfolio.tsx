import { Text, View } from "react-native";
import { formatINR, type Portfolio as Values } from "@tradevelocity/client";
import { Action, Screen, theme } from "../src/workspace";
import { useData } from "../src/data";

export default function Portfolio() {
  const {data, error, refresh} = useData<Values>("/account/portfolio");
  return <Screen title="Portfolio">
    {error && <Text style={theme.error}>{error}</Text>}
    <Action title="Refresh portfolio" onPress={refresh} />
    {data && <>
      <View style={theme.panel}>
        <Text style={theme.text}>Account value {formatINR(data.equity)}</Text>
        <Text style={theme.text}>Available cash {formatINR(data.available_cash)}</Text>
        <Text style={theme.subtle}>Reserved cash {formatINR(data.reserved)}</Text>
        <Text style={theme.subtle}>Realized P&L {formatINR(data.realized)} · Open P&L {formatINR(data.unrealized)}</Text>
        <Text style={theme.subtle}>Provider close data through {data.market_as_of}</Text>
      </View>
      {!data.holdings.length && <Text style={theme.subtle}>Your holdings appear after a funded paper buy fills.</Text>}
      {data.holdings.map(row => <View key={row.symbol} style={theme.panel}>
        <Text style={theme.text}>{row.symbol} · {row.quantity} shares</Text>
        <Text style={theme.subtle}>Average cost {formatINR(row.average_cost)} · Value {formatINR(row.value)}</Text>
        <Text style={theme.subtle}>{row.mark_source === "last_simulated_fill" ? "Last simulated fill" : "Daily close"} {formatINR(row.mark)}</Text>
      </View>)}
    </>}
  </Screen>;
}

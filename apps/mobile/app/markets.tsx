import { useState } from "react";
import { Text, TextInput, View } from "react-native";
import { router } from "expo-router";
import { formatINR } from "@tradevelocity/client";
import { Action, Screen, theme } from "../src/workspace";
import { useData, type MarketOverview } from "../src/data";

export default function Markets() {
  const [search, setSearch] = useState("");
  const market = useData<MarketOverview>("/market");
  const query = search.trim().toLowerCase();
  const rows = market.data?.companies.filter(row => `${row.name} ${row.symbol}`.toLowerCase().includes(query)) ?? [];
  return <Screen title="Explore markets">
    <TextInput style={theme.field} accessibilityLabel="Search stocks" placeholder="Search stocks"
      placeholderTextColor="#94a3b8" value={search} onChangeText={setSearch} />
    {market.error && <Text style={theme.error}>{market.error}</Text>}
    {market.data && <Text style={theme.subtle}>{market.data.source}</Text>}
    {market.data && !rows.length && <Text style={theme.subtle}>No symbols match your search.</Text>}
    {rows.map(row => <View style={theme.panel} key={row.symbol}>
      <Text style={theme.text}>{row.symbol} · {row.name}</Text>
      <Text style={theme.text}>{formatINR(row.price)} {row.day_change !== null && `· ${row.day_change.toFixed(2)}%`}</Text>
      <Text style={theme.subtle}>Daily close · {row.as_of}</Text>
      <Action title={`Trade ${row.symbol}`} onPress={() => router.navigate({pathname: "/trade", params: {symbol: row.symbol}})} />
    </View>)}
  </Screen>;
}

import { useState } from "react";
import { Pressable, Text, TextInput, View } from "react-native";
import { router } from "expo-router";
import { formatINR } from "@tradevelocity/client";
import { ChevronRight, Search } from "lucide-react-native";
import { DataState, Screen, useMobileTheme } from "../src/workspace";
import { useData, type MarketOverview } from "../src/data";

export default function Markets() {
  const {theme, colors} = useMobileTheme();
  const [search, setSearch] = useState("");
  const market = useData<MarketOverview>("/market");
  const query = search.trim().toLowerCase();
  const rows = market.data?.companies.filter(row => `${row.name} ${row.symbol}`.toLowerCase().includes(query)) ?? [];
  return <Screen title="Markets" subtitle="Explore NSE stocks" refresh={market.refresh} refreshing={market.loading}>
    <View style={[theme.row, {backgroundColor: colors.raised, borderRadius: 12, borderWidth: 1, borderColor: colors.line, paddingLeft: 12}]}>
      <Search size={19} color={colors.muted} />
      <TextInput style={[theme.field, {flex: 1, borderWidth: 0, paddingLeft: 0}]} accessibilityLabel="Search stocks" placeholder="Search by name or symbol"
        placeholderTextColor={colors.muted} value={search} onChangeText={setSearch} />
    </View>
    {(!market.data || market.error) && <DataState message="Loading stocks…" error={market.error} retry={market.refresh} />}
    {market.data && !rows.length && <Text style={theme.subtle}>No stocks match your search.</Text>}
    {Boolean(rows.length) && <View style={[theme.panel, {gap: 0, paddingVertical: 0}]}>
      {rows.map((row, index) => <Pressable key={row.symbol} accessibilityRole="button" accessibilityLabel={`Trade ${row.symbol}`}
        onPress={() => router.navigate({pathname: "/trade", params: {symbol: row.symbol}})}
        style={({pressed}) => [theme.between, {minHeight: 67, paddingVertical: 10, borderBottomWidth: index === rows.length - 1 ? 0 : 1, borderColor: colors.line}, pressed && {opacity: .75}]}>
        <View style={{flex: 1, gap: 2}}><Text style={theme.number}>{row.symbol}</Text><Text style={theme.subtle} numberOfLines={1}>{row.name}</Text></View>
        <View style={{alignItems: "flex-end"}}><Text style={theme.number}>{formatINR(row.price)}</Text>
          {row.day_change !== null && <Text style={[theme.subtle, {color: row.day_change < 0 ? colors.error : colors.action}]}>
            {row.day_change > 0 ? "+" : ""}{row.day_change.toFixed(2)}%
          </Text>}
        </View><ChevronRight size={16} color={colors.muted} />
      </Pressable>)}
    </View>}
    {market.data && <Text style={theme.subtle}>{market.data.source} · Through {market.data.as_of}</Text>}
  </Screen>;
}

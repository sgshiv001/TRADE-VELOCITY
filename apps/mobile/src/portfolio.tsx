import { createContext, useContext, type ReactNode } from "react";
import { Text, View } from "react-native";
import { Wallet } from "lucide-react-native";
import { formatINR, type Portfolio } from "@tradevelocity/client";
import { useData } from "./data";
import { useMobileTheme } from "./workspace";

const PortfolioContext = createContext<ReturnType<typeof useData<Portfolio>> | null>(null);

export function PortfolioProvider({children}: {children: ReactNode}) {
  const portfolio = useData<Portfolio>("/account/portfolio");
  return <PortfolioContext.Provider value={portfolio}>{children}</PortfolioContext.Provider>;
}

export function usePortfolio() {
  const portfolio = useContext(PortfolioContext);
  if (!portfolio) throw new Error("The portfolio needs a signed-in workspace");
  return portfolio;
}

export function PortfolioBalance({data, detail = false}: {data: Portfolio; detail?: boolean}) {
  const {theme, colors} = useMobileTheme();
  const metrics = detail ? [["Available cash", data.available_cash], ["Holdings value", data.holdings_value],
    ["Reserved cash", data.reserved], ["Realized P&L", data.realized], ["Open P&L", data.unrealized]]
    : [["Available cash", data.available_cash], ["Holdings value", data.holdings_value]];
  return <View style={theme.hero}>
    <View style={theme.between}><Text style={theme.eyebrow}>PAPER ACCOUNT</Text><Wallet color={colors.action} size={20} /></View>
    <View><Text style={theme.subtle}>Account value</Text><Text style={theme.value}>{formatINR(data.equity)}</Text></View>
    <View style={{flexDirection: "row", flexWrap: "wrap", gap: 10, borderTopWidth: 1, borderColor: colors.heroLine, paddingTop: 10}}>
      {metrics.map(([label, value]) => <View key={label} style={{flexGrow: 1, flexBasis: "44%", gap: 2}}>
        <Text style={theme.subtle}>{label}</Text>
        <Text style={[theme.number, label.endsWith("P&L") && {color: Number(value) < 0 ? colors.error : colors.action}]}>{formatINR(value)}</Text>
      </View>)}
    </View>
  </View>;
}

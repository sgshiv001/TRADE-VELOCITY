import { useState } from "react";
import { Text, TextInput, View } from "react-native";
import { router } from "expo-router";
import { formatINR, symbolSchema } from "@tradevelocity/client";
import { Action, Screen, useMobileTheme } from "../src/workspace";
import { useData } from "../src/data";

type Report = {
  company: string; recommendation: string; recommendation_reason: string;
  as_of: string; source: string; stale: boolean; evidence: string[]; risk_flags: string[];
  forecast: {horizon: string; point: number; lower: number; upper: number; interval_target: number} | null;
};

export default function Analyst() {
  const {theme, colors} = useMobileTheme();
  const [symbol, setSymbol] = useState("RELIANCE");
  const [input, setInput] = useState(symbol);
  const [inputError, setInputError] = useState("");
  const report = useData<Report>(`/analyst/${encodeURIComponent(symbol)}`);
  const data = report.data;
  return <Screen title="AI Analyst" refresh={report.refresh}>
    <Text style={theme.subtle}>Historical evidence and supported forecasts for paper trading.</Text>
    <TextInput style={theme.field} accessibilityLabel="Stock symbol" placeholder="NSE symbol"
      placeholderTextColor={colors.muted} value={input} onChangeText={setInput} autoCapitalize="characters" />
    <Action title="Analyse stock" onPress={() => {
      const result = symbolSchema.safeParse(input);
      if (result.success) { setSymbol(result.data); setInputError(""); }
      else setInputError("Enter a supported NSE symbol.");
    }} />
    {(inputError || report.error) && <Text accessibilityRole="alert" style={theme.error}>{inputError || report.error}</Text>}
    {!data && !report.error && <Text style={theme.subtle}>Loading the available analysis…</Text>}
    {data && <>
      <View style={theme.panel}>
        <Text style={theme.title}>{data.company}</Text>
        <Text style={theme.link}>{data.recommendation} · Paper signal</Text>
        <Text style={theme.text}>{data.recommendation_reason}</Text>
        <Text style={theme.subtle}>{data.stale ? "Historical analysis" : data.source} · {data.as_of}</Text>
      </View>
      <View style={theme.panel}>
        <Text style={theme.text}>{data.forecast?.horizon ?? "Forecast unavailable"}</Text>
        {data.forecast && <>
          <Text style={theme.title}>{formatINR(data.forecast.point)}</Text>
          <Text style={theme.subtle}>Range {formatINR(data.forecast.lower)} to {formatINR(data.forecast.upper)}</Text>
          <Text style={theme.subtle}>The range targets {data.forecast.interval_target}% historical coverage.</Text>
        </>}
      </View>
      <View style={theme.panel}>
        <Text style={theme.text}>Evidence and risks</Text>
        {[...data.evidence, ...data.risk_flags].map(reason => <Text key={reason} style={theme.subtle}>{reason}</Text>)}
      </View>
      <Action title="Open trading ticket" onPress={() => router.navigate({pathname: "/trade", params: {symbol}})} />
    </>}
  </Screen>;
}

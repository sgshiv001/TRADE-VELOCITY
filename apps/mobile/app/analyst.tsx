import { useState } from "react";
import { Text, TextInput, View } from "react-native";
import { router } from "expo-router";
import { Sparkles } from "lucide-react-native";
import { formatINR, symbolSchema } from "@tradevelocity/client";
import { Action, DataState, Screen, useMobileTheme } from "../src/workspace";
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
  function analyse() {
    const result = symbolSchema.safeParse(input);
    if (result.success) { setSymbol(result.data); setInputError(""); }
    else setInputError("Enter a supported NSE symbol.");
  }
  return <Screen title="AI Analyst" subtitle="Historical evidence and forecasts" refresh={report.refresh} refreshing={report.loading}>
    <View style={theme.row}>
      <TextInput style={[theme.field, {flex: 1}]} accessibilityLabel="Stock symbol" placeholder="NSE symbol" onSubmitEditing={analyse}
        placeholderTextColor={colors.muted} value={input} onChangeText={setInput} autoCapitalize="characters" autoCorrect={false} />
      <Action title="Analyse stock" kind="secondary" onPress={analyse} />
    </View>
    {Boolean(inputError) && <Text accessibilityRole="alert" style={theme.error}>{inputError}</Text>}
    {(!data || report.error) && <DataState message="Loading analysis…" error={report.error} retry={report.refresh} />}
    {data && <>
      <View style={theme.hero}>
        <View style={theme.row}><Sparkles size={17} color={colors.action} /><Text style={theme.eyebrow}>PAPER SIGNAL</Text></View>
        <Text style={theme.sectionTitle}>{data.company}</Text>
        <Text style={theme.number}>{data.recommendation}</Text>
        <Text style={theme.text}>{data.recommendation_reason}</Text>
        <Text style={theme.subtle}>{data.stale ? "Historical analysis" : data.source} · {data.as_of}</Text>
      </View>
      <View style={theme.panel}>
        <Text style={theme.sectionTitle}>{data.forecast?.horizon ?? "Forecast unavailable"}</Text>
        {data.forecast && <>
          <Text style={theme.value}>{formatINR(data.forecast.point)}</Text>
          <Text style={theme.subtle}>Range {formatINR(data.forecast.lower)} to {formatINR(data.forecast.upper)}</Text>
          <Text style={theme.subtle}>The range targets {data.forecast.interval_target}% historical coverage.</Text>
        </>}
      </View>
      <View style={theme.panel}>
        <Text style={theme.sectionTitle}>Evidence and risks</Text>
        {[...data.evidence, ...data.risk_flags].map(reason => <Text key={reason} style={theme.subtle}>{reason}</Text>)}
      </View>
      <Action title="Open trading ticket" onPress={() => router.navigate({pathname: "/trade", params: {symbol}})} />
    </>}
  </Screen>;
}

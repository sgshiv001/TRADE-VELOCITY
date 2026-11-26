import { Pressable, Text, View } from "react-native";
import Svg, { Circle, Defs, Line, LinearGradient, Path, Rect, Stop } from "react-native-svg";
import { formatINR } from "@tradevelocity/client";
import type { MarketBar } from "./data";
import { useMobileTheme } from "./workspace";

export function Choices<T extends string>({options, value, onChange, disabled = false}: {
  options: readonly {key: T; label: string}[]; value: T; onChange(key: NoInfer<T>): void; disabled?: boolean;
}) {
  const {theme, colors} = useMobileTheme();
  return <View style={{flexDirection: "row", flexWrap: "wrap", gap: 4}}>
    {options.map(({key, label}) => <Pressable key={key} accessibilityRole="button" accessibilityState={{selected: key === value, disabled}}
      disabled={disabled} onPress={() => onChange(key)} style={{minHeight: 44, minWidth: 44, justifyContent: "center", alignItems: "center", paddingHorizontal: 10,
        borderRadius: 9, backgroundColor: key === value ? colors.raised : "transparent"}}>
      <Text style={key === value ? theme.link : theme.subtle}>{label}</Text>
    </Pressable>)}
  </View>;
}

type Prices = {time: number; value: number}[];

export function PricePlot({symbol, daily, quotes, candles = false}: {
  symbol: string; daily?: MarketBar[]; quotes?: Prices; candles?: boolean;
}) {
  const {theme, colors} = useMobileTheme();
  const bars = daily?.slice(-260).filter(bar => [bar.open, bar.high, bar.low, bar.close].every(Number.isFinite)) ?? [];
  const observations = quotes ?? [];
  const values = daily ? bars.map(bar => bar.close) : observations.map(point => point.value);
  if (!values.length) return null;
  const high = Math.max(...(candles ? bars.map(bar => bar.high) : values));
  const low = Math.min(...(candles ? bars.map(bar => bar.low) : values));
  const width = 290, height = 112, pad = 5;
  const minuteSpan = observations.length > 1 ? observations.at(-1)!.time - observations[0].time : 0;
  const x = (index: number) => values.length === 1 ? width / 2 : daily
    ? pad + index * (width - 2 * pad) / (values.length - 1)
    : pad + (observations[index].time - observations[0].time) * (width - 2 * pad) / minuteSpan;
  const y = (value: number) => high === low ? height / 2 : pad + (high - value) * (height - 2 * pad) / (high - low);
  const last = values.at(-1)!;
  const tone = last < values[0] ? colors.error : colors.action;
  const line = values.map((value, index) => `${index === 0 ? "M" : "L"}${x(index)} ${y(value)}`).join(" ");
  const candleWidth = Math.max(1, Math.min(7, width / values.length * .64));
  const dateLabel = (index: number) => daily ? bars[index].date.slice(5).replace("-", "/")
    : new Date(observations[index].time).toLocaleTimeString("en-IN", {timeZone: "Asia/Kolkata", hour: "2-digit", minute: "2-digit", hourCycle: "h23"});

  return <View accessible accessibilityRole="image" accessibilityLabel={`${symbol} ${daily ? "daily" : "intraday"} chart, last ${formatINR(last)}, low ${formatINR(low)}, high ${formatINR(high)}`}>
    <View style={theme.row}>
      <View style={{flex: 1}}><Svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
        <Defs><LinearGradient id="chartFill" x1="0" x2="0" y1="0" y2="100%">
          <Stop offset="0%" stopColor={tone} stopOpacity={.23} /><Stop offset="100%" stopColor={tone} stopOpacity={.02} />
        </LinearGradient></Defs>
        {[pad, height / 2, height - pad].map(level => <Line key={level} x1={0} x2={width} y1={level} y2={level} stroke={colors.line} strokeWidth={1} />)}
        {candles ? bars.map((bar, i) => {
          const color = bar.close < bar.open ? colors.error : colors.action;
          return <SvgCandle key={bar.date} x={x(i)} width={candleWidth} high={y(bar.high)} low={y(bar.low)} open={y(bar.open)} close={y(bar.close)} color={color} />;
        }) : <>
          {values.length > 1 && <Path d={`${line} L${x(values.length - 1)} ${height} L${x(0)} ${height} Z`} fill="url(#chartFill)" />}
          {values.length > 1 && <Path d={line} stroke={tone} strokeWidth={2.2} fill="none" />}
          <Circle cx={x(values.length - 1)} cy={y(last)} r={3} fill={tone} />
        </>}
      </Svg>
        <View style={theme.between}><Text style={theme.subtle}>{dateLabel(0)}</Text>
          {values.length > 1 && <Text style={theme.subtle}>{dateLabel(values.length - 1)}</Text>}</View>
      </View>
      <View style={{alignSelf: "stretch", justifyContent: "space-between", alignItems: "flex-end", paddingBottom: 18}}>
        <Text style={theme.subtle}>{formatINR(high)}</Text><Text style={theme.subtle}>{formatINR(low)}</Text>
      </View>
    </View>
  </View>;
}

function SvgCandle({x, width, high, low, open, close, color}: {
  x: number; width: number; high: number; low: number; open: number; close: number; color: string;
}) {
  return <>
    <Line x1={x} x2={x} y1={high} y2={low} stroke={color} strokeWidth={1} />
    <Rect x={x - width / 2} y={Math.min(open, close)} width={width} height={Math.max(1.2, Math.abs(open - close))} fill={color} />
  </>;
}

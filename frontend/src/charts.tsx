import { useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Bar as PriceBar } from "./types";
import { inr, short } from "./api";

const green = "#138464";
const red = "#da5262";
const grid = "#e9eeec";
const tick = { fill: "#8b9892", fontSize: 11 };
const tooltip = {
  background: "#fff",
  border: "1px solid #e5ebe7",
  borderRadius: 12,
  boxShadow: "0 5px 20px #152b2012",
  fontSize: 12,
};
export const dateLabel = (date: string) =>
  new Date(`${date}T12:00:00`).toLocaleDateString("en-IN", {
    month: "short",
    day: "numeric",
  });

export function Sparkline({
  values,
  positive = true,
}: {
  values: number[];
  positive?: boolean;
}) {
  if (!values.length) return null;
  const min = Math.min(...values),
    max = Math.max(...values),
    range = max - min || 1;
  const points = values
    .map(
      (v, i) =>
        `${(i / Math.max(1, values.length - 1)) * 100},${27 - ((v - min) / range) * 24}`,
    )
    .join(" ");
  return (
    <svg
      width="100"
      height="30"
      viewBox="0 0 100 30"
      aria-label="30-session price trend"
    >
      <polyline
        points={points}
        fill="none"
        stroke={positive ? green : red}
        strokeWidth="1.7"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function PriceChart({
  rows,
  moving = false,
  height = 280,
}: {
  rows: PriceBar[];
  moving?: boolean;
  height?: number;
}) {
  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={rows}
          margin={{ top: 10, right: 8, left: -12, bottom: 0 }}
        >
          <defs>
            <linearGradient id="price-fill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={green} stopOpacity={0.18} />
              <stop offset="100%" stopColor={green} stopOpacity={0.005} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke={grid} vertical={false} strokeDasharray="3 3" />
          <XAxis
            dataKey="date"
            tickFormatter={dateLabel}
            minTickGap={50}
            axisLine={false}
            tickLine={false}
            tick={tick}
          />
          <YAxis
            domain={["auto", "auto"]}
            tickFormatter={(v) => short(Number(v))}
            tick={tick}
            axisLine={false}
            tickLine={false}
            width={60}
          />
          <Tooltip
            contentStyle={tooltip}
            labelFormatter={(v) => String(v)}
            formatter={(v, name) => [
              inr(Number(v)),
              name === "close" ? "Adjusted price" : String(name),
            ]}
          />
          <Area
            type="monotone"
            dataKey="close"
            stroke={green}
            strokeWidth={2.2}
            fill="url(#price-fill)"
            animationDuration={450}
          />
          {moving && (
            <>
              <Area
                type="monotone"
                dataKey="ma20"
                name="20-day MA"
                stroke="#dfa855"
                fill="transparent"
                strokeWidth={1.4}
                connectNulls
              />
              <Area
                type="monotone"
                dataKey="ma50"
                name="50-day MA"
                stroke="#8a83ce"
                fill="transparent"
                strokeWidth={1.4}
                connectNulls
              />
            </>
          )}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function Candles({ rows }: { rows: PriceBar[] }) {
  const [hover, setHover] = useState<number | null>(null);
  if (!rows.length) return null;
  const left = 14,
    right = 64,
    top = 24,
    bottom = 35,
    width = 900,
    height = 300;
  const min = Math.min(...rows.map((r) => r.low)) * 0.995,
    max = Math.max(...rows.map((r) => r.high)) * 1.005;
  const scale = (v: number) =>
    top + ((max - v) / (max - min || 1)) * (height - top - bottom);
  const step = (width - left - right) / rows.length;
  const active = rows[Math.min(rows.length - 1, hover ?? rows.length - 1)];
  return (
    <div className="candles">
      <div className="candle-legend">
        <span>{active.date}</span>
        <span>O {inr(active.open)}</span>
        <span>H {inr(active.high)}</span>
        <span>L {inr(active.low)}</span>
        <strong
          className={active.close >= active.open ? "positive" : "negative"}
        >
          C {inr(active.close)}
        </strong>
      </div>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label="Interactive adjusted candlestick history"
        onMouseLeave={() => setHover(null)}
        onMouseMove={(e) => {
          const box = e.currentTarget.getBoundingClientRect();
          setHover(
            Math.max(
              0,
              Math.min(
                rows.length - 1,
                Math.floor(
                  (((e.clientX - box.left) / box.width) * width - left) / step,
                ),
              ),
            ),
          );
        }}
      >
        {Array.from({ length: 5 }, (_, i) => {
          const value = min + ((max - min) * i) / 4;
          return (
            <g key={i}>
              <line
                x1={left}
                x2={width - right}
                y1={scale(value)}
                y2={scale(value)}
                stroke={grid}
                strokeDasharray="3 3"
              />
              <text
                x={width - right + 10}
                y={scale(value) + 4}
                fill="#8b9892"
                fontSize="11"
              >
                {short(value)}
              </text>
            </g>
          );
        })}
        {rows.map((row, i) => {
          const x = left + (i + 0.5) * step,
            color = row.close >= row.open ? green : red;
          return (
            <g key={row.date}>
              <line
                x1={x}
                x2={x}
                y1={scale(row.high)}
                y2={scale(row.low)}
                stroke={color}
              />
              <rect
                x={x - Math.max(0.6, step * 0.33)}
                width={Math.max(1.2, step * 0.66)}
                y={scale(Math.max(row.open, row.close))}
                height={Math.max(
                  1,
                  Math.abs(scale(row.open) - scale(row.close)),
                )}
                fill={color}
                rx="0.4"
              />
            </g>
          );
        })}
        {hover !== null && (
          <line
            x1={left + (hover + 0.5) * step}
            x2={left + (hover + 0.5) * step}
            y1={top}
            y2={height - bottom}
            stroke="#677e72"
            strokeDasharray="4 4"
          />
        )}
        {[0, 0.25, 0.5, 0.75, 1].map((f, i) => (
          <text
            key={i}
            x={left + f * (width - left - right)}
            y={height - 10}
            textAnchor={i === 0 ? "start" : i === 4 ? "end" : "middle"}
            fill="#8b9892"
            fontSize="11"
          >
            {dateLabel(rows[Math.round(f * (rows.length - 1))].date)}
          </text>
        ))}
      </svg>
    </div>
  );
}

export function VolumeChart({ rows }: { rows: PriceBar[] }) {
  return (
    <div style={{ height: 140 }}>
      <ResponsiveContainer>
        <BarChart data={rows} margin={{ left: -15, right: 8 }}>
          <XAxis dataKey="date" hide />
          <YAxis
            tickFormatter={(v) => short(Number(v))}
            tick={tick}
            axisLine={false}
            tickLine={false}
            width={60}
          />
          <Tooltip
            contentStyle={tooltip}
            formatter={(v) => [short(Number(v)), "Shares"]}
          />
          <Bar dataKey="volume" radius={[2, 2, 0, 0]}>
            {rows.map((row) => (
              <Cell
                key={row.date}
                fill={row.close >= row.open ? "#82c3ab" : "#e3a9b1"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function SimpleBars({
  rows,
  valueKey,
  color = green,
  height = 210,
}: {
  rows: Record<string, unknown>[];
  valueKey: string;
  color?: string;
  height?: number;
}) {
  return (
    <div style={{ height }}>
      <ResponsiveContainer>
        <BarChart data={rows} margin={{ left: -12, right: 10, top: 10 }}>
          <CartesianGrid stroke={grid} vertical={false} />
          <XAxis dataKey="name" tick={tick} axisLine={false} tickLine={false} />
          <YAxis
            tick={tick}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => short(Number(v))}
          />
          <Tooltip contentStyle={tooltip} />
          <Bar dataKey={valueKey} radius={[5, 5, 0, 0]} maxBarSize={42}>
            {rows.map((row, i) => (
              <Cell key={i} fill={Number(row[valueKey]) < 0 ? red : color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function Allocation({
  rows,
}: {
  rows: { name: string; value: number; color: string }[];
}) {
  return (
    <div style={{ height: 240 }}>
      <ResponsiveContainer>
        <PieChart>
          <Pie
            data={rows}
            dataKey="value"
            nameKey="name"
            innerRadius={65}
            outerRadius={87}
            paddingAngle={3}
            stroke="none"
          >
            {rows.map((row) => (
              <Cell key={row.name} fill={row.color} />
            ))}
          </Pie>
          <Tooltip contentStyle={tooltip} formatter={(v) => inr(Number(v))} />
          <Legend
            verticalAlign="bottom"
            iconType="circle"
            iconSize={8}
            wrapperStyle={{ fontSize: 11 }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ComparisonChart({
  rows,
}: {
  rows: Record<string, number | string>[];
}) {
  return (
    <div style={{ height: 270 }}>
      <ResponsiveContainer>
        <LineChart data={rows} margin={{ left: 0, right: 20, top: 20 }}>
          <CartesianGrid stroke={grid} vertical={false} />
          <XAxis
            dataKey="commands"
            tick={tick}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tickFormatter={(v) => short(Number(v))}
            tick={tick}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={tooltip}
            formatter={(v) => `${Math.round(Number(v)).toLocaleString()}/s`}
          />
          <Legend
            iconType="circle"
            iconSize={8}
            wrapperStyle={{ fontSize: 12 }}
          />
          <Line
            type="monotone"
            dataKey="indexed"
            name="Heap + AVL + hash"
            stroke={green}
            strokeWidth={2.5}
          />
          <Line
            type="monotone"
            dataKey="linear"
            name="Unsorted list"
            stroke="#e8ab63"
            strokeWidth={2.5}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

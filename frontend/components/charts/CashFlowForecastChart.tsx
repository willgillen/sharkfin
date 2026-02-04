"use client";

import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { CashFlowProjection } from "@/types";
import { formatCurrency, formatMonthYear } from "@/lib/utils/format";

interface CashFlowForecastChartProps {
  projections: CashFlowProjection[];
  currentBalance: string;
}

export default function CashFlowForecastChart({
  projections,
  currentBalance,
}: CashFlowForecastChartProps) {
  const chartData = projections.map((item) => ({
    month: formatMonthYear(item.month),
    income: parseFloat(item.projected_income),
    expenses: parseFloat(item.projected_expenses),
    net: parseFloat(item.projected_net),
    balance: parseFloat(item.projected_balance),
    confidence: item.confidence,
  }));

  const confidenceColors: Record<string, string> = {
    high: "#10b981",
    medium: "#f59e0b",
    low: "#ef4444",
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const confidence = payload[0]?.payload?.confidence;
      return (
        <div className="bg-surface p-3 border border-border-light rounded shadow-lg">
          <p className="font-medium text-text-primary mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {formatCurrency(entry.value)}
            </p>
          ))}
          {confidence && (
            <p
              className="text-sm mt-2 font-medium"
              style={{ color: confidenceColors[confidence] }}
            >
              Confidence: {confidence.charAt(0).toUpperCase() + confidence.slice(1)}
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-text-tertiary">
        No forecast data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={400}>
      <ComposedChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="month" />
        <YAxis
          yAxisId="left"
          tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
        />
        <YAxis
          yAxisId="right"
          orientation="right"
          tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        <ReferenceLine
          y={parseFloat(currentBalance)}
          yAxisId="right"
          stroke="#6b7280"
          strokeDasharray="5 5"
          label={{ value: "Current", position: "insideTopRight", fill: "#6b7280" }}
        />
        <Bar
          yAxisId="left"
          dataKey="income"
          fill="#10b981"
          name="Projected Income"
          radius={[4, 4, 0, 0]}
        />
        <Bar
          yAxisId="left"
          dataKey="expenses"
          fill="#ef4444"
          name="Projected Expenses"
          radius={[4, 4, 0, 0]}
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="balance"
          stroke="#3b82f6"
          strokeWidth={3}
          dot={{ fill: "#3b82f6", strokeWidth: 2 }}
          name="Projected Balance"
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

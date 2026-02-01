"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { NetWorthDataPoint } from "@/types";
import { formatCurrency } from "@/lib/utils/format";

interface NetWorthChartProps {
  data: NetWorthDataPoint[];
}

export default function NetWorthChart({ data }: NetWorthChartProps) {
  const chartData = data.map((item) => ({
    date: new Date(item.date).toLocaleDateString("en-US", {
      month: "short",
      year: "2-digit",
    }),
    assets: parseFloat(item.total_assets),
    liabilities: parseFloat(item.total_liabilities),
    netWorth: parseFloat(item.net_worth),
  }));

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-surface p-3 border border-border-light rounded shadow-lg">
          <p className="font-medium text-text-primary mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {formatCurrency(entry.value)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-text-tertiary">
        No net worth data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={400}>
      <AreaChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        <Area
          type="monotone"
          dataKey="assets"
          stackId="1"
          stroke="#10b981"
          fill="#10b981"
          fillOpacity={0.3}
          name="Assets"
        />
        <Area
          type="monotone"
          dataKey="liabilities"
          stackId="2"
          stroke="#ef4444"
          fill="#ef4444"
          fillOpacity={0.3}
          name="Liabilities"
        />
        <Area
          type="monotone"
          dataKey="netWorth"
          stroke="#3b82f6"
          fill="#3b82f6"
          fillOpacity={0.5}
          name="Net Worth"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

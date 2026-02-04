"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { CategoryTrend } from "@/types";
import { formatCurrency, formatMonthYear } from "@/lib/utils/format";

// Color palette for categories
const CATEGORY_COLORS = [
  "#3b82f6", // blue
  "#10b981", // green
  "#f59e0b", // amber
  "#ef4444", // red
  "#8b5cf6", // purple
  "#ec4899", // pink
  "#06b6d4", // cyan
  "#84cc16", // lime
  "#f97316", // orange
  "#6366f1", // indigo
];

interface SpendingTrendsChartProps {
  data: CategoryTrend[];
  months: string[];
  selectedCategories?: number[];
}

export default function SpendingTrendsChart({
  data,
  months,
  selectedCategories,
}: SpendingTrendsChartProps) {
  // Filter categories if selection provided
  const filteredData = selectedCategories?.length
    ? data.filter((c) => selectedCategories.includes(c.category_id))
    : data.slice(0, 8); // Limit to top 8 categories for readability

  // Transform data for stacked bar chart
  const chartData = months.map((month) => {
    const monthData: Record<string, any> = {
      month: formatMonthYear(month),
    };

    filteredData.forEach((category) => {
      const monthEntry = category.monthly_data.find((m) => m.month === month);
      monthData[category.category_name] = monthEntry
        ? parseFloat(monthEntry.amount)
        : 0;
    });

    return monthData;
  });

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const total = payload.reduce(
        (sum: number, entry: any) => sum + (entry.value || 0),
        0
      );
      return (
        <div className="bg-surface p-3 border border-border-light rounded shadow-lg max-w-xs">
          <p className="font-medium text-text-primary mb-2">{label}</p>
          {payload
            .filter((entry: any) => entry.value > 0)
            .sort((a: any, b: any) => b.value - a.value)
            .map((entry: any, index: number) => (
              <p key={index} className="text-sm" style={{ color: entry.color }}>
                {entry.name}: {formatCurrency(entry.value)}
              </p>
            ))}
          <p className="text-sm font-medium text-text-primary mt-2 pt-2 border-t border-border">
            Total: {formatCurrency(total)}
          </p>
        </div>
      );
    }
    return null;
  };

  if (chartData.length === 0 || filteredData.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-text-tertiary">
        No spending trend data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="month" />
        <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        {filteredData.map((category, index) => (
          <Bar
            key={category.category_id}
            dataKey={category.category_name}
            stackId="spending"
            fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip, Sector } from "recharts";
import { CategorySpending } from "@/types";
import { formatCurrency } from "@/lib/utils/format";
import { useState } from "react";

interface CategorySpendingChartProps {
  data: CategorySpending[];
  onCategoryClick?: (categoryId: number, categoryName: string) => void;
}

const COLORS = [
  "#3b82f6", // blue-500
  "#10b981", // green-500
  "#f59e0b", // amber-500
  "#ef4444", // red-500
  "#8b5cf6", // violet-500
  "#ec4899", // pink-500
  "#06b6d4", // cyan-500
  "#f97316", // orange-500
];

export default function CategorySpendingChart({ data, onCategoryClick }: CategorySpendingChartProps) {
  const [activeIndex, setActiveIndex] = useState<number | undefined>(undefined);

  const chartData = data.map((item) => ({
    name: item.category_name,
    value: parseFloat(item.amount),
    percentage: parseFloat(item.percentage),
    category_id: item.category_id,
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-surface p-3 border border-border-light rounded shadow-lg">
          <p className="font-medium text-text-primary">{payload[0].name}</p>
          <p className="text-sm text-text-secondary">
            {formatCurrency(payload[0].value)}
          </p>
          <p className="text-xs text-text-tertiary">
            {payload[0].payload.percentage.toFixed(1)}% of total
          </p>
          {onCategoryClick && (
            <p className="text-xs text-primary-500 mt-1">
              Click to view transactions
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  // Active shape for hover effect
  const renderActiveShape = (props: any) => {
    const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill, payload, percent } = props;

    return (
      <g>
        <Sector
          cx={cx}
          cy={cy}
          innerRadius={innerRadius}
          outerRadius={outerRadius + 10}
          startAngle={startAngle}
          endAngle={endAngle}
          fill={fill}
          style={{ cursor: onCategoryClick ? "pointer" : "default" }}
        />
        <text x={cx} y={cy - 10} textAnchor="middle" fill="#333" className="text-sm font-medium">
          {payload.name}
        </text>
        <text x={cx} y={cy + 10} textAnchor="middle" fill="#666" className="text-xs">
          {(percent * 100).toFixed(1)}%
        </text>
      </g>
    );
  };

  const handleClick = (data: any, index: number) => {
    if (onCategoryClick && chartData[index]) {
      onCategoryClick(chartData[index].category_id, chartData[index].name);
    }
  };

  const handleMouseEnter = (_: any, index: number) => {
    setActiveIndex(index);
  };

  const handleMouseLeave = () => {
    setActiveIndex(undefined);
  };

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-text-tertiary">
        No spending data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          labelLine={false}
          outerRadius={100}
          fill="#8884d8"
          dataKey="value"
          label={activeIndex === undefined ? ({ name, percentage }) => `${name} (${percentage.toFixed(0)}%)` : false}
          activeIndex={activeIndex}
          activeShape={renderActiveShape}
          onClick={handleClick}
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
          style={{ cursor: onCategoryClick ? "pointer" : "default" }}
        >
          {chartData.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={COLORS[index % COLORS.length]}
              style={{ cursor: onCategoryClick ? "pointer" : "default" }}
            />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
      </PieChart>
    </ResponsiveContainer>
  );
}

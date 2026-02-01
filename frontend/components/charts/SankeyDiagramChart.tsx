"use client";

import { Sankey, Tooltip, Layer, Rectangle } from "recharts";
import { SankeyNode, SankeyLink } from "@/types";
import { formatCurrency } from "@/lib/utils/format";

interface SankeyDiagramChartProps {
  nodes: SankeyNode[];
  links: SankeyLink[];
}

// Color palette for nodes
const NODE_COLORS: Record<string, string> = {
  income: "#10b981", // Green for income sources
  total_income: "#059669", // Darker green for total income hub
  savings: "#3b82f6", // Blue for savings
  expense: "#ef4444", // Red for expenses
};

// Generate colors for nodes based on their type
function getNodeColor(nodeId: string): string {
  if (nodeId === "total_income") return NODE_COLORS.total_income;
  if (nodeId === "savings") return NODE_COLORS.savings;
  if (nodeId.startsWith("income_")) return NODE_COLORS.income;
  return NODE_COLORS.expense;
}

// Custom node component
function CustomNode({ x, y, width, height, payload }: any) {
  const color = getNodeColor(payload.id);
  return (
    <Layer>
      <Rectangle
        x={x}
        y={y}
        width={width}
        height={height}
        fill={color}
        fillOpacity={0.9}
        rx={4}
        ry={4}
      />
      {/* Node label */}
      <text
        x={x + width / 2}
        y={y + height / 2}
        textAnchor="middle"
        dominantBaseline="middle"
        fontSize={12}
        fill="#fff"
        fontWeight={500}
      >
        {payload.name.length > 12 ? payload.name.slice(0, 10) + "..." : payload.name}
      </text>
    </Layer>
  );
}

// Custom link component
function CustomLink({
  sourceX,
  targetX,
  sourceY,
  targetY,
  sourceControlX,
  targetControlX,
  linkWidth,
  payload,
}: any) {
  const sourceColor = getNodeColor(payload.source);
  const targetColor = getNodeColor(payload.target);

  // Create gradient path from source to target
  const gradientId = `gradient-${payload.source}-${payload.target}`;

  return (
    <Layer>
      <defs>
        <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor={sourceColor} stopOpacity={0.4} />
          <stop offset="100%" stopColor={targetColor} stopOpacity={0.4} />
        </linearGradient>
      </defs>
      <path
        d={`
          M${sourceX},${sourceY}
          C${sourceControlX},${sourceY} ${targetControlX},${targetY} ${targetX},${targetY}
          L${targetX},${targetY + linkWidth}
          C${targetControlX},${targetY + linkWidth} ${sourceControlX},${sourceY + linkWidth} ${sourceX},${sourceY + linkWidth}
          Z
        `}
        fill={`url(#${gradientId})`}
        stroke="none"
      />
    </Layer>
  );
}

export default function SankeyDiagramChart({
  nodes,
  links,
}: SankeyDiagramChartProps) {
  // Transform data for recharts Sankey
  // Recharts expects nodes as array and links with source/target as indices
  const nodeMap = new Map<string, number>();
  const chartNodes = nodes.map((node, index) => {
    nodeMap.set(node.id, index);
    return {
      name: node.name,
      id: node.id,
      value: parseFloat(node.value),
    };
  });

  const chartLinks = links
    .map((link) => {
      const sourceIndex = nodeMap.get(link.source);
      const targetIndex = nodeMap.get(link.target);
      if (sourceIndex === undefined || targetIndex === undefined) {
        return null;
      }
      return {
        source: sourceIndex,
        target: targetIndex,
        value: parseFloat(link.value),
        sourceName: link.source,
        targetName: link.target,
      };
    })
    .filter((link): link is NonNullable<typeof link> => link !== null);

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      // Check if it's a node or a link
      if (data.name && !data.sourceName) {
        // Node tooltip
        return (
          <div className="bg-surface p-3 border border-border-light rounded shadow-lg">
            <p className="font-medium text-text-primary">{data.name}</p>
            <p className="text-sm text-text-secondary">
              {formatCurrency(data.value.toString())}
            </p>
          </div>
        );
      } else if (data.sourceName) {
        // Link tooltip
        const sourceNode = chartNodes.find((n) => n.id === data.sourceName);
        const targetNode = chartNodes.find((n) => n.id === data.targetName);
        return (
          <div className="bg-surface p-3 border border-border-light rounded shadow-lg">
            <p className="font-medium text-text-primary">
              {sourceNode?.name || data.sourceName} → {targetNode?.name || data.targetName}
            </p>
            <p className="text-sm text-text-secondary">
              {formatCurrency(data.value.toString())}
            </p>
          </div>
        );
      }
    }
    return null;
  };

  if (chartNodes.length === 0 || chartLinks.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-text-tertiary">
        No money flow data available
      </div>
    );
  }

  // Calculate appropriate height based on number of nodes
  const height = Math.max(400, Math.min(chartNodes.length * 50, 600));

  return (
    <div style={{ width: "100%", height }}>
      <Sankey
        width={800}
        height={height}
        data={{ nodes: chartNodes, links: chartLinks }}
        node={<CustomNode />}
        link={<CustomLink />}
        nodePadding={30}
        nodeWidth={20}
        margin={{ top: 20, right: 200, bottom: 20, left: 200 }}
      >
        <Tooltip content={<CustomTooltip />} />
      </Sankey>
    </div>
  );
}

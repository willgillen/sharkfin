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
function getNodeColor(nodeId: string | undefined): string {
  if (!nodeId || typeof nodeId !== "string") return NODE_COLORS.expense;
  if (nodeId === "total_income") return NODE_COLORS.total_income;
  if (nodeId === "savings") return NODE_COLORS.savings;
  if (nodeId.startsWith("income_")) return NODE_COLORS.income;
  return NODE_COLORS.expense;
}

// Custom node component - receives payload with our node data
function CustomNode({ x, y, width, height, payload }: any) {
  // payload contains our node data including the 'id' field we set
  const nodeId = payload?.id;
  const color = getNodeColor(nodeId);
  const name = payload?.name || "";

  // Determine label position based on node type
  // Income nodes (left side) get label on left, expense nodes (right side) get label on right
  const isLeftSide = nodeId?.startsWith("income_") || nodeId === "total_income";
  const labelX = isLeftSide ? x - 8 : x + width + 8;
  const textAnchor = isLeftSide ? "end" : "start";

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
      {/* Node label - positioned outside the node */}
      <text
        x={labelX}
        y={y + height / 2}
        textAnchor={textAnchor}
        dominantBaseline="middle"
        fontSize={12}
        fill="#374151"
        fontWeight={500}
      >
        {name.length > 15 ? name.slice(0, 13) + "..." : name}
      </text>
    </Layer>
  );
}

// Custom link component with gradient coloring
// The recharts Sankey provides sourceY/targetY as the TOP of the link area
function CustomLink(props: any) {
  const {
    sourceX,
    targetX,
    sourceY,
    targetY,
    sourceControlX,
    targetControlX,
    linkWidth,
    payload,
    index,
  } = props;

  // payload.source and payload.target are indices, not string IDs
  // We store the original IDs as sourceName and targetName
  const sourceId = payload?.sourceName;
  const targetId = payload?.targetName;
  const sourceColor = getNodeColor(sourceId);
  const targetColor = getNodeColor(targetId);

  // Create gradient for the link
  const gradientId = `sankey-link-gradient-${index}`;

  // Calculate the half-width offset to center the link
  const halfWidth = linkWidth / 2;

  // Top edge of the curved band
  const sy0 = sourceY - halfWidth;
  const ty0 = targetY - halfWidth;
  // Bottom edge of the curved band
  const sy1 = sourceY + halfWidth;
  const ty1 = targetY + halfWidth;

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
          M${sourceX},${sy0}
          C${sourceControlX},${sy0} ${targetControlX},${ty0} ${targetX},${ty0}
          L${targetX},${ty1}
          C${targetControlX},${ty1} ${sourceControlX},${sy1} ${sourceX},${sy1}
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
        // Store original string IDs for color lookups
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
  const numExpenseNodes = nodes.filter(n => n.id.startsWith("expense_")).length;
  const numIncomeNodes = nodes.filter(n => n.id.startsWith("income_")).length;
  const maxNodes = Math.max(numExpenseNodes, numIncomeNodes, 3);
  const height = Math.max(350, Math.min(maxNodes * 60, 550));

  return (
    <div style={{ width: "100%", height, minWidth: "600px" }}>
      <Sankey
        width={700}
        height={height}
        data={{ nodes: chartNodes, links: chartLinks }}
        node={<CustomNode />}
        link={<CustomLink />}
        nodePadding={24}
        nodeWidth={16}
        margin={{ top: 20, right: 120, bottom: 20, left: 120 }}
      >
        <Tooltip content={<CustomTooltip />} />
      </Sankey>
    </div>
  );
}

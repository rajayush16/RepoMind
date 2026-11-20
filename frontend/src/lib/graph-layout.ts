import type { Edge, Node } from "@xyflow/react";
import type { GraphEdge, GraphNode } from "@/lib/queries/code";

const COLUMN_X: Record<string, number> = { file: 0, symbol: 360, module: 720 };
const ROW_HEIGHT = 56;

const NODE_COLORS: Record<string, string> = {
  file: "#6d6cf7",
  symbol: "#4dd7e8",
  module: "#d9a441",
};

export function toReactFlow(nodes: GraphNode[], edges: GraphEdge[]): { nodes: Node[]; edges: Edge[] } {
  const countByType: Record<string, number> = {};
  const nodeIds = new Set(nodes.map((n) => n.id));

  const flowNodes: Node[] = nodes.map((node) => {
    const row = countByType[node.type] ?? 0;
    countByType[node.type] = row + 1;

    return {
      id: node.id,
      position: { x: COLUMN_X[node.type] ?? 0, y: row * ROW_HEIGHT },
      data: { label: node.label, type: node.type, meta: node },
      style: {
        borderColor: NODE_COLORS[node.type] ?? "#6d6cf7",
        borderWidth: 1.5,
        fontSize: 12,
        padding: 6,
      },
    };
  });

  const flowEdges: Edge[] = edges
    .filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target))
    .map((edge, index) => ({
      id: `${edge.source}->${edge.target}-${index}`,
      source: edge.source,
      target: edge.target,
      label: edge.type,
      animated: edge.type === "CALLS",
      style: { stroke: edge.type === "IMPORTS" ? "#d9a441" : edge.type === "CALLS" ? "#4dd7e8" : "#6d6cf7" },
    }));

  return { nodes: flowNodes, edges: flowEdges };
}

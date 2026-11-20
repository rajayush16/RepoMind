"use client";

import { useMemo } from "react";
import { ReactFlow, Background, Controls, MiniMap } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Loader2, Workflow } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";
import { RepositorySelector } from "@/components/repositories/repository-selector";
import { useRepositories } from "@/lib/queries/repositories";
import { useArchitectureGraph } from "@/lib/queries/code";
import { useRepositoryStore } from "@/stores/repository-store";
import { toReactFlow } from "@/lib/graph-layout";

const LEGEND = [
  { label: "File", color: "#6d6cf7" },
  { label: "Symbol", color: "#4dd7e8" },
  { label: "Module", color: "#d9a441" },
];

export default function ArchitecturePage() {
  const { data: repositories } = useRepositories();
  const selectedRepositoryId = useRepositoryStore((state) => state.selectedRepositoryId);
  const repository = repositories?.find((r) => r.id === selectedRepositoryId);
  const hasIndexedRepo = Boolean(repository && repository.indexing_status === "indexed");

  const graphQuery = useArchitectureGraph(selectedRepositoryId ?? "", hasIndexedRepo);
  const { nodes, edges } = useMemo(
    () => toReactFlow(graphQuery.data?.nodes ?? [], graphQuery.data?.edges ?? []),
    [graphQuery.data],
  );

  return (
    <div className="flex flex-1 flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Architecture Graph</h1>
          <p className="text-sm text-muted-foreground">
            Files, symbols, imports and calls, sourced directly from the Neo4j code graph.
          </p>
        </div>
        <RepositorySelector />
      </div>

      {!repositories || repositories.length === 0 ? (
        <EmptyState
          icon={Workflow}
          title="No repository connected yet"
          description="Connect and index a repository first, from the Repositories page."
        />
      ) : !hasIndexedRepo ? (
        <EmptyState
          icon={Workflow}
          title="This repository hasn't been indexed yet"
          description="Index it from the Repositories page, then come back here."
        />
      ) : graphQuery.isLoading ? (
        <div className="flex flex-1 items-center justify-center">
          <Loader2 className="size-5 animate-spin text-muted-foreground" />
        </div>
      ) : graphQuery.data && !graphQuery.data.available ? (
        <EmptyState
          icon={Workflow}
          title="Code graph unavailable"
          description={`Neo4j is unreachable: ${graphQuery.data.reason}. Start Neo4j and re-index this repository to populate the graph.`}
        />
      ) : nodes.length === 0 ? (
        <EmptyState
          icon={Workflow}
          title="No graph data yet"
          description="The repository index didn't produce any graph nodes. Re-index it once Neo4j is reachable."
        />
      ) : (
        <div className="flex flex-1 flex-col gap-2">
          <div className="flex gap-4 text-xs text-muted-foreground">
            {LEGEND.map((item) => (
              <span key={item.label} className="flex items-center gap-1.5">
                <span className="size-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                {item.label}
              </span>
            ))}
            <span className="ml-auto">
              {nodes.length} nodes · {edges.length} edges
            </span>
          </div>
          <div className="min-h-0 flex-1 overflow-hidden rounded-lg border border-border bg-card">
            <ReactFlow nodes={nodes} edges={edges} fitView>
              <Background />
              <Controls />
              <MiniMap pannable zoomable />
            </ReactFlow>
          </div>
        </div>
      )}
    </div>
  );
}

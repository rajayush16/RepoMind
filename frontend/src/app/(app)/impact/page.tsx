import { Waypoints } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";

export default function ImpactPage() {
  return (
    <div className="flex flex-1 flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Change Impact Analysis</h1>
        <p className="text-sm text-muted-foreground">
          Select a function, class, or file and see what could break if you change it.
        </p>
      </div>

      <EmptyState
        icon={Waypoints}
        title="No dependency graph to analyse yet"
        description="Impact analysis is built directly from the Neo4j code graph (callers, imports, inheritance, API consumers, related tests). It lands in Phase 7, after indexing and graph construction (Phases 4-5) exist to query against."
      />
    </div>
  );
}

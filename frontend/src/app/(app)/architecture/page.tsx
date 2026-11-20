import { Workflow } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";

export default function ArchitecturePage() {
  return (
    <div className="flex flex-1 flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Architecture Graph</h1>
        <p className="text-sm text-muted-foreground">
          Zoomable, interactive visualization of files, modules, classes, and their
          dependencies, sourced from the Neo4j code graph.
        </p>
      </div>

      <EmptyState
        icon={Workflow}
        title="No code graph built yet"
        description="This graph is populated from Neo4j once a repository has been indexed (Phases 4-5). It will never be a hardcoded diagram — every node and edge here will reflect real, extracted code relationships."
      />
    </div>
  );
}

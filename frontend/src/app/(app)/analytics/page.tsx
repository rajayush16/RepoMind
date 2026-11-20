import { BarChart3 } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";

export default function AnalyticsPage() {
  return (
    <div className="flex flex-1 flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Analytics</h1>
        <p className="text-sm text-muted-foreground">
          Indexing throughput, query volume, LLM token usage and cost, latency, and agent
          success rates — all computed from stored records.
        </p>
      </div>

      <EmptyState
        icon={BarChart3}
        title="No usage data recorded yet"
        description="Analytics will be calculated from real llm_usage, indexing_jobs, and investigation records once those systems exist (Phases 4, 6-9). Nothing here is ever an invented number."
      />
    </div>
  );
}

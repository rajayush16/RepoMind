import { Bug } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";

export default function InvestigationsPage() {
  return (
    <div className="flex flex-1 flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Bug Investigation</h1>
        <p className="text-sm text-muted-foreground">
          Describe a bug, error message, or stack trace and get an evidence-backed root
          cause investigation with a visible timeline.
        </p>
      </div>

      <EmptyState
        icon={Bug}
        title="Investigation agent not implemented yet"
        description="This multi-step debugging workflow (parse error -> trace execution -> evaluate root causes -> report) is planned for Phase 7 and requires an indexed repository and the multi-agent system. No investigation form is shown until it can produce real, verifiable findings."
      />
    </div>
  );
}

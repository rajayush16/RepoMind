import { FlaskConical } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";

export default function TestsPage() {
  return (
    <div className="flex flex-1 flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Test Generation</h1>
        <p className="text-sm text-muted-foreground">
          Generate tests for a selected function or module, then run them in an isolated
          sandbox and see real results.
        </p>
      </div>

      <EmptyState
        icon={FlaskConical}
        title="Test generation agent not implemented yet"
        description="Planned for Phase 7, backed by the sandboxed Docker execution service. Generated tests will never be reported as passing unless they were actually executed in that sandbox."
      />
    </div>
  );
}

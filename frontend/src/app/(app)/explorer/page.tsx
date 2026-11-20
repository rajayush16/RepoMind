import { Code2 } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";

export default function ExplorerPage() {
  return (
    <div className="flex flex-1 flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Code Explorer</h1>
        <p className="text-sm text-muted-foreground">
          Browse the file tree, read source with Monaco, and navigate symbol references.
        </p>
      </div>

      <EmptyState
        icon={Code2}
        title="No indexed repository to explore"
        description="The code explorer reads from a repository's parsed file tree and extracted symbols. Connect and index a repository first (Phases 3-4) — this view will then render real files, not sample content."
      />
    </div>
  );
}

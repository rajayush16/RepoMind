import { FolderGit2 } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";

export default function RepositoriesPage() {
  return (
    <div className="flex flex-1 flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Repositories</h1>
        <p className="text-sm text-muted-foreground">
          Connect, index, and manage the GitHub repositories RepoMind understands.
        </p>
      </div>

      <EmptyState
        icon={FolderGit2}
        title="GitHub connection not yet available"
        description="Repository discovery and indexing require GitHub OAuth and the indexing pipeline, which are not implemented yet (see IMPLEMENTATION_PLAN.md, Phases 3-4). This page will let you browse authorized repositories, trigger indexing, and track progress once that work lands."
      />
    </div>
  );
}

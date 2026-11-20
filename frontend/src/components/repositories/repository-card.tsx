import { Lock, Loader2, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Repository } from "@/lib/types";

const STATUS_LABEL: Record<string, string> = {
  not_indexed: "Not indexed",
  queued: "Queued",
  indexing: "Indexing",
  indexed: "Indexed",
  failed: "Indexing failed",
};

export function RepositoryCard({
  repository,
  onDelete,
  isDeleting,
}: {
  repository: Repository;
  onDelete: () => void;
  isDeleting: boolean;
}) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border bg-card p-4">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <span className="truncate text-sm font-medium">{repository.full_name}</span>
          {repository.is_private && <Lock className="size-3.5 text-muted-foreground" />}
        </div>
        <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          {repository.primary_language && <span>{repository.primary_language}</span>}
          <span>Branch: {repository.selected_branch}</span>
          <Badge variant="secondary" className="text-[11px]">
            {STATUS_LABEL[repository.indexing_status] ?? repository.indexing_status}
          </Badge>
          <span>{repository.file_count} files</span>
          <span>{repository.symbol_count} symbols</span>
        </div>
      </div>

      <Button
        variant="ghost"
        size="icon"
        className="size-8 shrink-0 text-muted-foreground hover:text-destructive"
        aria-label={`Disconnect ${repository.full_name}`}
        onClick={onDelete}
        disabled={isDeleting}
      >
        {isDeleting ? <Loader2 className="size-4 animate-spin" /> : <Trash2 className="size-4" />}
      </Button>
    </div>
  );
}

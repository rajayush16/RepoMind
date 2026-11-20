import { Lock, Loader2, PlayCircle, RefreshCw, Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Repository } from "@/lib/types";
import { useLatestIndexingJob, useTriggerIndexing } from "@/lib/queries/indexing";

const STATUS_LABEL: Record<string, string> = {
  not_indexed: "Not indexed",
  queued: "Queued",
  indexing: "Indexing",
  indexed: "Indexed",
  failed: "Indexing failed",
};

const IN_PROGRESS = new Set(["not_indexed", "queued", "indexing"]);

export function RepositoryCard({
  repository,
  onDelete,
  isDeleting,
}: {
  repository: Repository;
  onDelete: () => void;
  isDeleting: boolean;
}) {
  const { data: job } = useLatestIndexingJob(repository.id, true);
  const triggerIndexing = useTriggerIndexing();

  const isRunning = repository.indexing_status === "queued" || repository.indexing_status === "indexing";
  const canStart = !isRunning && !triggerIndexing.isPending;

  return (
    <div className="flex flex-col gap-2 rounded-lg border border-border bg-card p-4">
      <div className="flex items-center justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="truncate text-sm font-medium">{repository.full_name}</span>
            {repository.is_private && <Lock className="size-3.5 text-muted-foreground" />}
          </div>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            {repository.primary_language && <span>{repository.primary_language}</span>}
            <span>Branch: {repository.selected_branch}</span>
            <Badge variant={repository.indexing_status === "failed" ? "destructive" : "secondary"} className="text-[11px]">
              {STATUS_LABEL[repository.indexing_status] ?? repository.indexing_status}
            </Badge>
            <span>{repository.file_count} files</span>
            <span>{repository.symbol_count} symbols</span>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-1">
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5"
            disabled={!canStart}
            onClick={() => triggerIndexing.mutate(repository.id)}
          >
            {isRunning || triggerIndexing.isPending ? (
              <Loader2 className="size-3.5 animate-spin" />
            ) : repository.indexing_status === "not_indexed" ? (
              <PlayCircle className="size-3.5" />
            ) : (
              <RefreshCw className="size-3.5" />
            )}
            {repository.indexing_status === "not_indexed" ? "Index" : "Re-index"}
          </Button>

          <Button
            variant="ghost"
            size="icon"
            className="size-8 text-muted-foreground hover:text-destructive"
            aria-label={`Disconnect ${repository.full_name}`}
            onClick={onDelete}
            disabled={isDeleting}
          >
            {isDeleting ? <Loader2 className="size-4 animate-spin" /> : <Trash2 className="size-4" />}
          </Button>
        </div>
      </div>

      {IN_PROGRESS.has(repository.indexing_status) && job && job.files_discovered > 0 && (
        <p className="text-xs text-muted-foreground">
          {job.files_processed}/{job.files_discovered} files parsed, {job.symbols_extracted} symbols
          found so far.
        </p>
      )}

      {repository.indexing_status === "failed" && job?.error_message && (
        <p className="text-xs text-destructive">{job.error_message}</p>
      )}
    </div>
  );
}

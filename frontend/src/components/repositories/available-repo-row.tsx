import { Loader2, Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { AvailableGithubRepo } from "@/lib/types";

export function AvailableRepoRow({
  repo,
  onConnect,
  isConnecting,
}: {
  repo: AvailableGithubRepo;
  onConnect: () => void;
  isConnecting: boolean;
}) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border/60 px-4 py-3">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <span className="truncate text-sm font-medium">{repo.full_name}</span>
          {repo.is_private && <Lock className="size-3.5 text-muted-foreground" />}
        </div>
        {repo.description && (
          <p className="mt-0.5 truncate text-xs text-muted-foreground">{repo.description}</p>
        )}
      </div>

      <Button
        size="sm"
        variant={repo.already_connected ? "secondary" : "outline"}
        disabled={repo.already_connected || isConnecting}
        onClick={onConnect}
        className="shrink-0"
      >
        {isConnecting ? (
          <Loader2 className="size-3.5 animate-spin" />
        ) : repo.already_connected ? (
          "Connected"
        ) : (
          "Connect"
        )}
      </Button>
    </div>
  );
}

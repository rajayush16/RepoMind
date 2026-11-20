import Link from "next/link";
import { FolderGit2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/shared/empty-state";

export default function OverviewPage() {
  return (
    <div className="flex flex-1 flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Overview</h1>
        <p className="text-sm text-muted-foreground">
          Your workspace at a glance — connected repositories, indexing status, and recent
          activity.
        </p>
      </div>

      <EmptyState
        icon={FolderGit2}
        title="No repositories connected yet"
        description="Connect a GitHub repository to start indexing its code, exploring its architecture, and asking questions about it. Dashboard metrics will populate here once real indexing activity exists — nothing shown here is placeholder data."
      >
        <Button asChild className="mt-2">
          <Link href="/repositories">Go to Repositories</Link>
        </Button>
      </EmptyState>
    </div>
  );
}

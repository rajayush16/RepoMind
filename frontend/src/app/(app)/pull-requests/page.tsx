import { GitPullRequest } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";

export default function PullRequestsPage() {
  return (
    <div className="flex flex-1 flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Pull Request Review</h1>
        <p className="text-sm text-muted-foreground">
          Automated, structured review of GitHub pull requests with evidence-backed
          findings you approve before anything is posted.
        </p>
      </div>

      <EmptyState
        icon={GitPullRequest}
        title="GitHub PR integration not implemented yet"
        description="This requires GitHub OAuth/API access (Phase 3) and the review agent (Phase 7). RepoMind will never auto-post review comments — every finding will be previewed here first and require your explicit confirmation to publish."
      />
    </div>
  );
}

"use client";

import { useState } from "react";
import { AlertTriangle, CheckCircle2, GitPullRequest, Loader2 } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";
import { RepositorySelector } from "@/components/repositories/repository-selector";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { FindingCard } from "@/components/pull-requests/finding-card";
import { useRepositories } from "@/lib/queries/repositories";
import { useReview, useReviews, useStartReview, usePublishReview } from "@/lib/queries/pull-requests";
import { useRepositoryStore } from "@/stores/repository-store";

export default function PullRequestsPage() {
  const { data: repositories } = useRepositories();
  const selectedRepositoryId = useRepositoryStore((state) => state.selectedRepositoryId);
  const repository = repositories?.find((r) => r.id === selectedRepositoryId);
  const hasIndexedRepo = Boolean(repository && repository.indexing_status === "indexed");

  const reviewsQuery = useReviews(selectedRepositoryId ?? "", hasIndexedRepo);
  const startReview = useStartReview(selectedRepositoryId ?? "");
  const publishReview = usePublishReview();
  const [prNumberInput, setPrNumberInput] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const reviewQuery = useReview(selectedId);
  const [confirmingPublish, setConfirmingPublish] = useState(false);

  if (!repositories || repositories.length === 0 || !hasIndexedRepo) {
    return (
      <div className="flex flex-1 flex-col gap-6">
        <PageHeader />
        <EmptyState
          icon={GitPullRequest}
          title={!repositories || repositories.length === 0 ? "No repository connected yet" : "This repository hasn't been indexed yet"}
          description="Connect and index a repository first, from the Repositories page."
        />
      </div>
    );
  }

  const review = reviewQuery.data;

  return (
    <div className="flex flex-1 flex-col gap-4">
      <PageHeader />

      <div className="flex min-h-0 flex-1 gap-4 overflow-hidden">
        <div className="flex w-64 shrink-0 flex-col gap-3 overflow-y-auto rounded-lg border border-border bg-surface p-3">
          <h2 className="text-xs font-medium text-muted-foreground">Review a pull request</h2>
          <Input
            placeholder="PR number, e.g. 42"
            value={prNumberInput}
            onChange={(e) => setPrNumberInput(e.target.value)}
            type="number"
            className="h-8 text-xs"
          />
          <Button
            size="sm"
            disabled={!prNumberInput || startReview.isPending}
            onClick={() =>
              startReview.mutate(Number(prNumberInput), {
                onSuccess: (r) => {
                  setSelectedId(r.id);
                  setPrNumberInput("");
                },
              })
            }
          >
            {startReview.isPending ? <Loader2 className="size-3.5 animate-spin" /> : "Start review"}
          </Button>

          <div className="mt-2 border-t border-border pt-2">
            <h2 className="mb-1 text-xs font-medium text-muted-foreground">Past reviews</h2>
            <div className="flex flex-col gap-0.5">
              {reviewsQuery.data?.map((r) => (
                <button
                  key={r.id}
                  onClick={() => setSelectedId(r.id)}
                  className="truncate rounded-md px-2 py-1.5 text-left text-xs hover:bg-secondary"
                >
                  PR #{r.pr_number} -- {r.pr_title}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto rounded-lg border border-border bg-card p-4">
          {!review ? (
            <EmptyState
              icon={GitPullRequest}
              title="No review selected"
              description="Start a review or select one from the list."
            />
          ) : (
            <div className="flex flex-col gap-4">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-semibold">
                  PR #{review.pr_number} -- {review.pr_title}
                </h3>
                <Badge variant={review.status === "failed" ? "destructive" : "secondary"}>
                  {review.status === "pending" ? (
                    <span className="flex items-center gap-1"><Loader2 className="size-3 animate-spin" /> reviewing</span>
                  ) : (
                    review.status
                  )}
                </Badge>
                {review.published && (
                  <Badge variant="secondary" className="gap-1">
                    <CheckCircle2 className="size-3" /> published
                  </Badge>
                )}
              </div>

              {review.status === "failed" && (
                <div className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                  <AlertTriangle className="mt-0.5 size-4 shrink-0" />
                  {review.error_detail}
                </div>
              )}

              {review.status === "complete" && (
                <>
                  <p className="text-sm text-muted-foreground">{review.summary}</p>

                  <div className="flex flex-col gap-2">
                    {review.findings.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No findings -- looks clean.</p>
                    ) : (
                      review.findings.map((f) => <FindingCard key={f.id} finding={f} />)
                    )}
                  </div>

                  {!review.published && (
                    <div className="flex flex-col items-start gap-2">
                      {!confirmingPublish ? (
                        <Button size="sm" variant="outline" onClick={() => setConfirmingPublish(true)}>
                          Publish to GitHub
                        </Button>
                      ) : (
                        <div className="flex items-center gap-2 rounded-md border border-warning/30 bg-warning/10 p-2">
                          <span className="text-xs">
                            This posts the summary and findings as a real comment on the PR. Continue?
                          </span>
                          <Button
                            size="sm"
                            disabled={publishReview.isPending}
                            onClick={() => publishReview.mutate(review.id, { onSettled: () => setConfirmingPublish(false) })}
                          >
                            {publishReview.isPending ? <Loader2 className="size-3.5 animate-spin" /> : "Confirm"}
                          </Button>
                          <Button size="sm" variant="ghost" onClick={() => setConfirmingPublish(false)}>
                            Cancel
                          </Button>
                        </div>
                      )}
                    </div>
                  )}

                  {review.published_comment_url && (
                    <a
                      href={review.published_comment_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs text-primary hover:underline"
                    >
                      View published comment on GitHub
                    </a>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function PageHeader() {
  return (
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Pull Request Review</h1>
        <p className="text-sm text-muted-foreground">
          Automated, evidence-backed review you approve before anything is posted to GitHub.
        </p>
      </div>
      <RepositorySelector />
    </div>
  );
}

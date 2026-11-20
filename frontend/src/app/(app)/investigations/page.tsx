"use client";

import { useState } from "react";
import { AlertTriangle, Bug, Loader2 } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";
import { RepositorySelector } from "@/components/repositories/repository-selector";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { InvestigationTimeline } from "@/components/investigations/investigation-timeline";
import { useRepositories } from "@/lib/queries/repositories";
import { useInvestigation, useInvestigations, useStartInvestigation } from "@/lib/queries/investigations";
import { useRepositoryStore } from "@/stores/repository-store";

export default function InvestigationsPage() {
  const { data: repositories } = useRepositories();
  const selectedRepositoryId = useRepositoryStore((state) => state.selectedRepositoryId);
  const repository = repositories?.find((r) => r.id === selectedRepositoryId);
  const hasIndexedRepo = Boolean(repository && repository.indexing_status === "indexed");

  const investigationsQuery = useInvestigations(selectedRepositoryId ?? "", hasIndexedRepo);
  const startInvestigation = useStartInvestigation(selectedRepositoryId ?? "");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const investigationQuery = useInvestigation(selectedId);

  const [bugDescription, setBugDescription] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [stackTrace, setStackTrace] = useState("");

  function handleSubmit() {
    if (!bugDescription.trim()) return;
    startInvestigation.mutate(
      {
        bug_description: bugDescription,
        error_message: errorMessage || undefined,
        stack_trace: stackTrace || undefined,
      },
      {
        onSuccess: (investigation) => {
          setSelectedId(investigation.id);
          setBugDescription("");
          setErrorMessage("");
          setStackTrace("");
        },
      },
    );
  }

  if (!repositories || repositories.length === 0 || !hasIndexedRepo) {
    return (
      <div className="flex flex-1 flex-col gap-6">
        <PageHeader />
        <EmptyState
          icon={Bug}
          title={!repositories || repositories.length === 0 ? "No repository connected yet" : "This repository hasn't been indexed yet"}
          description="Connect and index a repository first, from the Repositories page."
        />
      </div>
    );
  }

  const investigation = investigationQuery.data;

  return (
    <div className="flex flex-1 flex-col gap-4">
      <PageHeader />

      <div className="flex min-h-0 flex-1 gap-4 overflow-hidden">
        <div className="flex w-72 shrink-0 flex-col gap-3 overflow-y-auto rounded-lg border border-border bg-surface p-3">
          <h2 className="text-xs font-medium text-muted-foreground">New investigation</h2>
          <Textarea
            placeholder="Describe the bug..."
            value={bugDescription}
            onChange={(e) => setBugDescription(e.target.value)}
            rows={3}
            className="text-xs"
          />
          <Input
            placeholder="Error message (optional)"
            value={errorMessage}
            onChange={(e) => setErrorMessage(e.target.value)}
            className="h-8 text-xs"
          />
          <Textarea
            placeholder="Stack trace (optional)"
            value={stackTrace}
            onChange={(e) => setStackTrace(e.target.value)}
            rows={3}
            className="font-mono text-xs"
          />
          <Button
            size="sm"
            onClick={handleSubmit}
            disabled={!bugDescription.trim() || startInvestigation.isPending}
          >
            {startInvestigation.isPending ? <Loader2 className="size-3.5 animate-spin" /> : "Start investigation"}
          </Button>

          <div className="mt-2 border-t border-border pt-2">
            <h2 className="mb-1 text-xs font-medium text-muted-foreground">Past investigations</h2>
            <div className="flex flex-col gap-0.5">
              {investigationsQuery.data?.map((inv) => (
                <button
                  key={inv.id}
                  onClick={() => setSelectedId(inv.id)}
                  className="truncate rounded-md px-2 py-1.5 text-left text-xs hover:bg-secondary"
                >
                  {inv.bug_description}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto rounded-lg border border-border bg-card p-4">
          {!investigation ? (
            <EmptyState
              icon={Bug}
              title="No investigation selected"
              description="Start a new investigation or select one from the list."
            />
          ) : (
            <div className="flex flex-col gap-5">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold">{investigation.bug_description}</h3>
                  <Badge variant={investigation.status === "failed" ? "destructive" : "secondary"}>
                    {investigation.status}
                  </Badge>
                </div>
                {investigation.error_message && (
                  <p className="mt-1 font-mono text-xs text-muted-foreground">{investigation.error_message}</p>
                )}
              </div>

              <InvestigationTimeline steps={investigation.steps} isRunning={investigation.status === "running"} />

              {investigation.status === "failed" && (
                <div className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                  <AlertTriangle className="mt-0.5 size-4 shrink-0" />
                  {investigation.error_detail}
                </div>
              )}

              {investigation.status === "complete" && investigation.root_cause && (
                <div className="flex flex-col gap-3 rounded-lg border border-border bg-surface p-4">
                  <div>
                    <h4 className="text-xs font-medium text-muted-foreground">Probable root cause</h4>
                    <p className="text-sm">{investigation.root_cause}</p>
                  </div>
                  {investigation.confidence_explanation && (
                    <div>
                      <h4 className="text-xs font-medium text-muted-foreground">Confidence</h4>
                      <p className="text-sm text-muted-foreground">{investigation.confidence_explanation}</p>
                    </div>
                  )}
                  {investigation.suggested_fix && (
                    <div>
                      <h4 className="text-xs font-medium text-muted-foreground">Suggested fix</h4>
                      <p className="text-sm">{investigation.suggested_fix}</p>
                    </div>
                  )}
                  {investigation.potential_side_effects && (
                    <div>
                      <h4 className="text-xs font-medium text-muted-foreground">Potential side effects</h4>
                      <p className="text-sm text-muted-foreground">{investigation.potential_side_effects}</p>
                    </div>
                  )}
                </div>
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
        <h1 className="text-xl font-semibold tracking-tight">Bug Investigation</h1>
        <p className="text-sm text-muted-foreground">
          Describe a bug and get an evidence-backed root cause investigation with a visible timeline.
        </p>
      </div>
      <RepositorySelector />
    </div>
  );
}

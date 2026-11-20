"use client";

import { useState } from "react";
import Link from "next/link";
import { Loader2, Waypoints } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";
import { RepositorySelector } from "@/components/repositories/repository-selector";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useRepositories } from "@/lib/queries/repositories";
import { useImpactAnalysis } from "@/lib/queries/impact";
import { useRepositoryStore } from "@/stores/repository-store";

const RISK_VARIANT: Record<string, "secondary" | "destructive"> = {
  low: "secondary",
  medium: "secondary",
  high: "destructive",
  unknown: "secondary",
};

export default function ImpactPage() {
  const { data: repositories } = useRepositories();
  const selectedRepositoryId = useRepositoryStore((state) => state.selectedRepositoryId);
  const repository = repositories?.find((r) => r.id === selectedRepositoryId);
  const hasIndexedRepo = Boolean(repository && repository.indexing_status === "indexed");

  const [input, setInput] = useState("");
  const [symbol, setSymbol] = useState("");
  const impactQuery = useImpactAnalysis(selectedRepositoryId ?? "", symbol);

  if (!repositories || repositories.length === 0 || !hasIndexedRepo) {
    return (
      <div className="flex flex-1 flex-col gap-6">
        <PageHeader />
        <EmptyState
          icon={Waypoints}
          title={!repositories || repositories.length === 0 ? "No repository connected yet" : "This repository hasn't been indexed yet"}
          description="Connect and index a repository first, from the Repositories page."
        />
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col gap-6">
      <PageHeader />

      <div className="flex gap-2">
        <Input
          placeholder="Symbol name, e.g. authenticate"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && setSymbol(input)}
          className="max-w-sm"
        />
        <Button onClick={() => setSymbol(input)} disabled={!input.trim()}>
          Analyse
        </Button>
      </div>

      {!symbol ? (
        <EmptyState
          icon={Waypoints}
          title="What could break if I change this?"
          description="Enter a function or method name to see its real callers and dependent files, from the Neo4j code graph."
        />
      ) : impactQuery.isLoading ? (
        <Loader2 className="size-5 animate-spin text-muted-foreground" />
      ) : impactQuery.data && !impactQuery.data.available ? (
        <EmptyState
          icon={Waypoints}
          title="Impact analysis unavailable"
          description={`Neo4j is unreachable: ${impactQuery.data.reason}. Start Neo4j and re-index this repository.`}
        />
      ) : impactQuery.data ? (
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold">{impactQuery.data.symbol_name}</h2>
            <Badge variant={RISK_VARIANT[impactQuery.data.risk]}>{impactQuery.data.risk} risk</Badge>
            <span className="text-xs text-muted-foreground">
              — statically discovered from the code graph, not a speculative AI guess
            </span>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-lg border border-border bg-card p-4">
              <h3 className="mb-2 text-xs font-medium text-muted-foreground">
                Direct callers ({impactQuery.data.direct_callers.length})
              </h3>
              {impactQuery.data.direct_callers.length === 0 ? (
                <p className="text-sm text-muted-foreground">No callers found in the code graph.</p>
              ) : (
                <ul className="flex flex-col gap-1.5">
                  {impactQuery.data.direct_callers.map((caller, i) => (
                    <li key={i} className="text-sm">
                      <span className="font-medium">{caller.name}</span>
                      {caller.file_path && (
                        <Link
                          href={`/explorer?repo=${selectedRepositoryId}&file=${encodeURIComponent(caller.file_path)}`}
                          className="ml-1.5 text-xs text-muted-foreground hover:underline"
                        >
                          {caller.file_path}
                        </Link>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="rounded-lg border border-border bg-card p-4">
              <h3 className="mb-2 text-xs font-medium text-muted-foreground">
                Affected files ({impactQuery.data.dependent_files.length})
              </h3>
              {impactQuery.data.dependent_files.length === 0 ? (
                <p className="text-sm text-muted-foreground">No affected files found.</p>
              ) : (
                <ul className="flex flex-col gap-1.5">
                  {impactQuery.data.dependent_files.map((f, i) => (
                    <li key={i}>
                      <Link
                        href={`/explorer?repo=${selectedRepositoryId}&file=${encodeURIComponent(f.file_path)}`}
                        className="text-sm hover:underline"
                      >
                        {f.file_path}
                      </Link>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function PageHeader() {
  return (
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Change Impact Analysis</h1>
        <p className="text-sm text-muted-foreground">
          Select a function and see what could break if you modify it.
        </p>
      </div>
      <RepositorySelector />
    </div>
  );
}

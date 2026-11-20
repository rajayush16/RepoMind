"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { FlaskConical, Loader2, PlayCircle } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";
import { RepositorySelector } from "@/components/repositories/repository-selector";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useRepositories } from "@/lib/queries/repositories";
import {
  useExecuteTest,
  useGenerateTest,
  useGeneratedTests,
  useLatestExecution,
} from "@/lib/queries/test-generation";
import { useRepositoryStore } from "@/stores/repository-store";
import { monacoLanguageFor } from "@/lib/monaco-language";

const MonacoEditor = dynamic(() => import("@monaco-editor/react"), { ssr: false });

const STATUS_LABEL: Record<string, string> = {
  pending: "Queued",
  running: "Running in sandbox",
  passed: "Passed",
  failed: "Failed",
  sandbox_unavailable: "Sandbox unavailable",
  unsupported_framework: "Framework not supported",
};

export default function TestsPage() {
  const { data: repositories } = useRepositories();
  const selectedRepositoryId = useRepositoryStore((state) => state.selectedRepositoryId);
  const repository = repositories?.find((r) => r.id === selectedRepositoryId);
  const hasIndexedRepo = Boolean(repository && repository.indexing_status === "indexed");

  const testsQuery = useGeneratedTests(selectedRepositoryId ?? "", hasIndexedRepo);
  const generateTest = useGenerateTest(selectedRepositoryId ?? "");
  const executeTest = useExecuteTest();

  const [symbolName, setSymbolName] = useState("");
  const [filePath, setFilePath] = useState("");
  const [framework, setFramework] = useState("pytest");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const selectedTest = testsQuery.data?.find((t) => t.id === selectedId);
  const executionQuery = useLatestExecution(selectedId);

  if (!repositories || repositories.length === 0 || !hasIndexedRepo) {
    return (
      <div className="flex flex-1 flex-col gap-6">
        <PageHeader />
        <EmptyState
          icon={FlaskConical}
          title={!repositories || repositories.length === 0 ? "No repository connected yet" : "This repository hasn't been indexed yet"}
          description="Connect and index a repository first, from the Repositories page."
        />
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col gap-4">
      <PageHeader />

      <div className="flex min-h-0 flex-1 gap-4 overflow-hidden">
        <div className="flex w-72 shrink-0 flex-col gap-3 overflow-y-auto rounded-lg border border-border bg-surface p-3">
          <h2 className="text-xs font-medium text-muted-foreground">Generate a test</h2>
          <Input
            placeholder="Symbol name, e.g. authenticate"
            value={symbolName}
            onChange={(e) => setSymbolName(e.target.value)}
            className="h-8 text-xs"
          />
          <Input
            placeholder="File path, e.g. app/auth.py"
            value={filePath}
            onChange={(e) => setFilePath(e.target.value)}
            className="h-8 text-xs"
          />
          <Select value={framework} onValueChange={setFramework}>
            <SelectTrigger className="h-8 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="pytest">pytest</SelectItem>
              <SelectItem value="jest">Jest</SelectItem>
            </SelectContent>
          </Select>
          <Button
            size="sm"
            disabled={!symbolName || !filePath || generateTest.isPending}
            onClick={() =>
              generateTest.mutate(
                { symbol_name: symbolName, file_path: filePath, framework },
                { onSuccess: (t) => setSelectedId(t.id) },
              )
            }
          >
            {generateTest.isPending ? <Loader2 className="size-3.5 animate-spin" /> : "Generate"}
          </Button>
          {generateTest.isError && (
            <p className="text-xs text-destructive">Could not generate a test -- check the symbol/file path.</p>
          )}

          <div className="mt-2 border-t border-border pt-2">
            <h2 className="mb-1 text-xs font-medium text-muted-foreground">Generated tests</h2>
            <div className="flex flex-col gap-0.5">
              {testsQuery.data?.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setSelectedId(t.id)}
                  className="truncate rounded-md px-2 py-1.5 text-left text-xs hover:bg-secondary"
                >
                  {t.symbol_name} ({t.framework})
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="flex min-w-0 flex-1 flex-col gap-3">
          {!selectedTest ? (
            <EmptyState
              icon={FlaskConical}
              title="No test selected"
              description="Generate a test or select one from the list."
            />
          ) : (
            <>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold">
                    {selectedTest.symbol_name} -- {selectedTest.file_path}
                  </h3>
                  {executionQuery.data && (
                    <Badge
                      variant={
                        executionQuery.data.status === "passed"
                          ? "secondary"
                          : executionQuery.data.status === "failed"
                            ? "destructive"
                            : "secondary"
                      }
                    >
                      {STATUS_LABEL[executionQuery.data.status] ?? executionQuery.data.status}
                    </Badge>
                  )}
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  className="gap-1.5"
                  disabled={executeTest.isPending}
                  onClick={() => executeTest.mutate(selectedTest.id)}
                >
                  {executeTest.isPending ? (
                    <Loader2 className="size-3.5 animate-spin" />
                  ) : (
                    <PlayCircle className="size-3.5" />
                  )}
                  Run in sandbox
                </Button>
              </div>

              <div className="h-64 overflow-hidden rounded-lg border border-border">
                <MonacoEditor
                  height="100%"
                  theme="vs-dark"
                  language={monacoLanguageFor(selectedTest.framework === "jest" ? "javascript" : "python")}
                  value={selectedTest.code}
                  options={{ readOnly: true, minimap: { enabled: false }, fontSize: 13 }}
                />
              </div>

              {executionQuery.data?.output && (
                <div className="flex-1 overflow-y-auto rounded-lg border border-border bg-card p-3">
                  <h4 className="mb-1 text-xs font-medium text-muted-foreground">Sandbox output</h4>
                  <pre className="whitespace-pre-wrap font-mono text-xs">{executionQuery.data.output}</pre>
                </div>
              )}
            </>
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
        <h1 className="text-xl font-semibold tracking-tight">Test Generation</h1>
        <p className="text-sm text-muted-foreground">
          Generate tests for a real symbol, then run them in an isolated sandbox.
        </p>
      </div>
      <RepositorySelector />
    </div>
  );
}

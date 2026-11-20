"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import { Code2, Loader2, Search } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";
import { Input } from "@/components/ui/input";
import { RepositorySelector } from "@/components/repositories/repository-selector";
import { FileTreeView } from "@/components/explorer/file-tree-view";
import { SymbolOutline } from "@/components/explorer/symbol-outline";
import { useRepositories } from "@/lib/queries/repositories";
import { useFileContent, useRepositoryFiles, useRepositorySearch, useSymbols } from "@/lib/queries/code";
import { useRepositoryStore } from "@/stores/repository-store";
import { buildFileTree } from "@/lib/file-tree";
import { monacoLanguageFor } from "@/lib/monaco-language";

const MonacoEditor = dynamic(() => import("@monaco-editor/react"), { ssr: false });

export function ExplorerView() {
  const searchParams = useSearchParams();
  const { data: repositories } = useRepositories();
  const selectedRepositoryId = useRepositoryStore((state) => state.selectedRepositoryId);
  const setSelectedRepositoryId = useRepositoryStore((state) => state.setSelectedRepositoryId);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const editorRef = useRef<{ revealLineInCenter: (line: number) => void } | null>(null);

  // Deep-link support: /explorer?repo=<id>&file=<path>&line=<n>, used by the AI
  // Assistant's citation chips to jump straight to the cited source.
  useEffect(() => {
    const repo = searchParams.get("repo");
    const file = searchParams.get("file");
    if (repo) setSelectedRepositoryId(repo);
    if (file) setSelectedPath(file);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const searchQuery = useRepositorySearch(selectedRepositoryId ?? "", searchTerm);

  const repository = repositories?.find((r) => r.id === selectedRepositoryId);
  const hasIndexedRepo = Boolean(repository && repository.indexing_status === "indexed");

  const filesQuery = useRepositoryFiles(selectedRepositoryId ?? "", hasIndexedRepo);
  const tree = useMemo(() => buildFileTree(filesQuery.data ?? []), [filesQuery.data]);

  const contentQuery = useFileContent(selectedRepositoryId ?? "", selectedPath);
  const symbolsQuery = useSymbols(selectedRepositoryId ?? "", selectedPath, Boolean(selectedPath) && hasIndexedRepo);

  useEffect(() => {
    const line = searchParams.get("line");
    if (line && contentQuery.data && editorRef.current) {
      editorRef.current.revealLineInCenter(Number(line));
    }
  }, [contentQuery.data, searchParams]);

  function jumpToLine(line: number) {
    editorRef.current?.revealLineInCenter(line);
  }

  if (!repositories || repositories.length === 0) {
    return (
      <div className="flex flex-1 flex-col gap-6">
        <PageHeader />
        <EmptyState
          icon={Code2}
          title="No repository connected yet"
          description="Connect and index a repository first, from the Repositories page."
        />
      </div>
    );
  }

  if (!hasIndexedRepo) {
    return (
      <div className="flex flex-1 flex-col gap-6">
        <PageHeader />
        <EmptyState
          icon={Code2}
          title="This repository hasn't been indexed yet"
          description="Go to Repositories and click Index on the selected repository, then come back here."
        />
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col gap-4">
      <PageHeader />

      <div className="flex min-h-0 flex-1 overflow-hidden rounded-lg border border-border">
        <div className="flex w-60 shrink-0 flex-col border-r border-border bg-surface">
          <div className="border-b border-border p-2">
            <div className="relative">
              <Search className="absolute left-2 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search symbols..."
                className="h-7 pl-7 text-xs"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-2">
            {searchTerm.trim() ? (
              <div className="flex flex-col gap-0.5">
                {searchQuery.data?.length ? (
                  searchQuery.data.map((result, index) => (
                    <button
                      key={`${result.file_path}-${result.symbol_name}-${index}`}
                      onClick={() => setSelectedPath(result.file_path)}
                      className="flex flex-col items-start rounded-md px-2 py-1.5 text-left text-xs hover:bg-secondary"
                    >
                      <span className="font-medium">{result.symbol_name ?? result.file_path}</span>
                      <span className="truncate text-muted-foreground">{result.file_path}</span>
                    </button>
                  ))
                ) : searchQuery.isLoading ? (
                  <Loader2 className="m-2 size-4 animate-spin text-muted-foreground" />
                ) : (
                  <p className="px-2 py-1.5 text-xs text-muted-foreground">No matches.</p>
                )}
              </div>
            ) : filesQuery.isLoading ? (
              <Loader2 className="m-1 size-4 animate-spin text-muted-foreground" />
            ) : (
              <FileTreeView tree={tree} selectedPath={selectedPath} onSelect={setSelectedPath} />
            )}
          </div>
        </div>

        <div className="flex min-w-0 flex-1 flex-col">
          {selectedPath && contentQuery.data ? (
            <MonacoEditor
              key={selectedPath}
              height="100%"
              theme="vs-dark"
              language={monacoLanguageFor(contentQuery.data.language)}
              value={contentQuery.data.content}
              options={{ readOnly: true, minimap: { enabled: false }, fontSize: 13 }}
              onMount={(editor) => {
                editorRef.current = editor;
              }}
            />
          ) : (
            <div className="flex flex-1 items-center justify-center text-sm text-muted-foreground">
              {contentQuery.isLoading ? <Loader2 className="size-4 animate-spin" /> : "Select a file to view its source."}
            </div>
          )}
        </div>

        <div className="w-64 shrink-0 overflow-y-auto border-l border-border bg-surface">
          <div className="border-b border-border px-3 py-2 text-xs font-medium text-muted-foreground">
            Outline
          </div>
          {selectedPath ? (
            <SymbolOutline symbols={symbolsQuery.data ?? []} onJump={jumpToLine} />
          ) : (
            <p className="px-3 py-4 text-xs text-muted-foreground">Select a file to see its symbols.</p>
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
        <h1 className="text-xl font-semibold tracking-tight">Code Explorer</h1>
        <p className="text-sm text-muted-foreground">
          Browse the file tree, read real indexed source, and navigate extracted symbols.
        </p>
      </div>
      <RepositorySelector />
    </div>
  );
}

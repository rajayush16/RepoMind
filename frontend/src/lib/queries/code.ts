import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export interface FileEntry {
  relative_path: string;
  language: string;
  symbol_count: number;
  size_bytes: number;
}

export interface FileContent {
  relative_path: string;
  language: string;
  content: string;
}

export interface SymbolEntry {
  id: string;
  name: string;
  symbol_type: string;
  parent_name: string | null;
  start_line: number;
  end_line: number;
  signature: string;
  file_path: string;
}

export interface SearchResult {
  file_path: string;
  symbol_name: string | null;
  symbol_type: string | null;
  start_line: number | null;
  end_line: number | null;
  snippet: string;
  sources: string[];
  score: number;
}

export interface GraphNode {
  id: string;
  type: "file" | "symbol" | "module";
  label: string;
  language?: string | null;
  symbolType?: string | null;
  file?: string | null;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: "DEFINES" | "IMPORTS" | "CALLS";
}

export interface ArchitectureGraph {
  available: boolean;
  reason: string | null;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export function useRepositoryFiles(repositoryId: string, enabled: boolean) {
  return useQuery<FileEntry[]>({
    queryKey: ["repositories", repositoryId, "files"],
    queryFn: () => apiClient.get<FileEntry[]>(`/repositories/${repositoryId}/files`),
    enabled,
  });
}

export function useFileContent(repositoryId: string, path: string | null) {
  return useQuery<FileContent>({
    queryKey: ["repositories", repositoryId, "files", "content", path],
    queryFn: () =>
      apiClient.get<FileContent>(
        `/repositories/${repositoryId}/files/content?path=${encodeURIComponent(path ?? "")}`,
      ),
    enabled: Boolean(repositoryId) && Boolean(path),
  });
}

export function useSymbols(repositoryId: string, filePath: string | null, enabled: boolean) {
  return useQuery<SymbolEntry[]>({
    queryKey: ["repositories", repositoryId, "symbols", filePath],
    queryFn: () =>
      apiClient.get<SymbolEntry[]>(
        `/repositories/${repositoryId}/symbols${filePath ? `?file_path=${encodeURIComponent(filePath)}` : ""}`,
      ),
    enabled,
  });
}

export function useRepositorySearch(repositoryId: string, query: string) {
  return useQuery<SearchResult[]>({
    queryKey: ["repositories", repositoryId, "search", query],
    queryFn: () =>
      apiClient.get<SearchResult[]>(
        `/repositories/${repositoryId}/search?q=${encodeURIComponent(query)}`,
      ),
    enabled: query.trim().length > 0,
  });
}

export function useArchitectureGraph(repositoryId: string, enabled: boolean) {
  return useQuery<ArchitectureGraph>({
    queryKey: ["repositories", repositoryId, "graph"],
    queryFn: () => apiClient.get<ArchitectureGraph>(`/repositories/${repositoryId}/graph`),
    enabled,
  });
}

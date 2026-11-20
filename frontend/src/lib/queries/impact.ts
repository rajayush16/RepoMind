import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export interface ImpactAnalysis {
  symbol_name: string;
  available: boolean;
  reason: string | null;
  direct_callers: { name: string; file_path: string | null }[];
  dependent_files: { file_path: string }[];
  risk: "low" | "medium" | "high" | "unknown";
}

export function useImpactAnalysis(repositoryId: string, symbol: string) {
  return useQuery<ImpactAnalysis>({
    queryKey: ["repositories", repositoryId, "impact", symbol],
    queryFn: () =>
      apiClient.get<ImpactAnalysis>(
        `/repositories/${repositoryId}/impact?symbol=${encodeURIComponent(symbol)}`,
      ),
    enabled: symbol.trim().length > 0,
  });
}

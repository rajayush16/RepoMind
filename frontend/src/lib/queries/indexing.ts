import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient, ApiError } from "@/lib/api-client";

export interface IndexingJob {
  id: string;
  repository_id: string;
  status: "queued" | "running" | "success" | "failed";
  commit_sha: string | null;
  files_discovered: number;
  files_processed: number;
  symbols_extracted: number;
  graph_relationships_written: number;
  embeddings_generated: number;
  error_message: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

const IN_PROGRESS_STATUSES = new Set(["queued", "running"]);

function indexingJobQueryKey(repositoryId: string) {
  return ["repositories", repositoryId, "indexing-jobs", "latest"];
}

export function useLatestIndexingJob(repositoryId: string, enabled: boolean) {
  return useQuery<IndexingJob | null>({
    queryKey: indexingJobQueryKey(repositoryId),
    queryFn: async () => {
      try {
        return await apiClient.get<IndexingJob>(`/repositories/${repositoryId}/indexing-jobs/latest`);
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
          return null;
        }
        throw error;
      }
    },
    enabled,
    refetchInterval: (query) => (IN_PROGRESS_STATUSES.has(query.state.data?.status ?? "") ? 2000 : false),
  });
}

export function useTriggerIndexing() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (repositoryId: string) => apiClient.post<IndexingJob>(`/repositories/${repositoryId}/index`),
    onSuccess: (_job, repositoryId) => {
      queryClient.invalidateQueries({ queryKey: indexingJobQueryKey(repositoryId) });
      queryClient.invalidateQueries({ queryKey: ["repositories"] });
    },
  });
}

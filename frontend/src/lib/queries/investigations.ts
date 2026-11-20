import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export interface InvestigationStep {
  id: string;
  stage: string;
  summary: string;
  evidence: unknown[] | null;
  created_at: string;
}

export interface Investigation {
  id: string;
  repository_id: string;
  bug_description: string;
  error_message: string | null;
  stack_trace: string | null;
  status: "running" | "complete" | "failed";
  root_cause: string | null;
  confidence_explanation: string | null;
  suggested_fix: string | null;
  potential_side_effects: string | null;
  error_detail: string | null;
  created_at: string;
  steps: InvestigationStep[];
}

const IN_PROGRESS = new Set(["running"]);

export function useInvestigations(repositoryId: string, enabled: boolean) {
  return useQuery<Investigation[]>({
    queryKey: ["repositories", repositoryId, "investigations"],
    queryFn: () => apiClient.get<Investigation[]>(`/repositories/${repositoryId}/investigations`),
    enabled,
  });
}

export function useInvestigation(investigationId: string | null) {
  return useQuery<Investigation>({
    queryKey: ["investigations", investigationId],
    queryFn: () => apiClient.get<Investigation>(`/investigations/${investigationId}`),
    enabled: Boolean(investigationId),
    refetchInterval: (query) => (IN_PROGRESS.has(query.state.data?.status ?? "") ? 2000 : false),
  });
}

export function useStartInvestigation(repositoryId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { bug_description: string; error_message?: string; stack_trace?: string }) =>
      apiClient.post<Investigation>(`/repositories/${repositoryId}/investigations`, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["repositories", repositoryId, "investigations"] });
    },
  });
}

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export interface GeneratedTest {
  id: string;
  repository_id: string;
  symbol_name: string;
  file_path: string;
  framework: string;
  code: string;
  created_at: string;
}

export interface TestExecution {
  id: string;
  generated_test_id: string;
  status: "pending" | "running" | "passed" | "failed" | "sandbox_unavailable" | "unsupported_framework";
  output: string | null;
  duration_ms: number | null;
  created_at: string;
}

const IN_PROGRESS = new Set(["pending", "running"]);

export function useGeneratedTests(repositoryId: string, enabled: boolean) {
  return useQuery<GeneratedTest[]>({
    queryKey: ["repositories", repositoryId, "tests"],
    queryFn: () => apiClient.get<GeneratedTest[]>(`/repositories/${repositoryId}/tests`),
    enabled,
  });
}

export function useGenerateTest(repositoryId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { symbol_name: string; file_path: string; framework: string }) =>
      apiClient.post<GeneratedTest>(`/repositories/${repositoryId}/tests`, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["repositories", repositoryId, "tests"] });
    },
  });
}

export function useLatestExecution(generatedTestId: string | null) {
  return useQuery<TestExecution | null>({
    queryKey: ["generated-tests", generatedTestId, "executions", "latest"],
    queryFn: async () => {
      try {
        return await apiClient.get<TestExecution>(
          `/generated-tests/${generatedTestId}/executions/latest`,
        );
      } catch {
        return null;
      }
    },
    enabled: Boolean(generatedTestId),
    refetchInterval: (query) => (IN_PROGRESS.has(query.state.data?.status ?? "") ? 2000 : false),
  });
}

export function useExecuteTest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (generatedTestId: string) =>
      apiClient.post<TestExecution>(`/generated-tests/${generatedTestId}/execute`),
    onSuccess: (_execution, generatedTestId) => {
      queryClient.invalidateQueries({
        queryKey: ["generated-tests", generatedTestId, "executions", "latest"],
      });
    },
  });
}

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { AvailableGithubRepo, Repository } from "@/lib/types";

const REPOSITORIES_QUERY_KEY = ["repositories"];
const AVAILABLE_GITHUB_REPOS_QUERY_KEY = ["repositories", "github", "available"];

export function useRepositories() {
  return useQuery<Repository[]>({
    queryKey: REPOSITORIES_QUERY_KEY,
    queryFn: () => apiClient.get<Repository[]>("/repositories"),
  });
}

export function useAvailableGithubRepositories(enabled: boolean) {
  return useQuery<AvailableGithubRepo[]>({
    queryKey: AVAILABLE_GITHUB_REPOS_QUERY_KEY,
    queryFn: () => apiClient.get<AvailableGithubRepo[]>("/repositories/github/available"),
    enabled,
    retry: false,
  });
}

export function useConnectRepository() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (repo: AvailableGithubRepo) =>
      apiClient.post<Repository>("/repositories", {
        github_repo_id: repo.github_repo_id,
        owner: repo.owner,
        name: repo.name,
        full_name: repo.full_name,
        description: repo.description,
        default_branch: repo.default_branch,
        primary_language: repo.primary_language,
        is_private: repo.is_private,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: REPOSITORIES_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: AVAILABLE_GITHUB_REPOS_QUERY_KEY });
    },
  });
}

export function useDeleteRepository() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete<void>(`/repositories/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: REPOSITORIES_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: AVAILABLE_GITHUB_REPOS_QUERY_KEY });
    },
  });
}

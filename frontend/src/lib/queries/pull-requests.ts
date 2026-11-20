import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export interface ReviewFinding {
  id: string;
  file_path: string;
  line: number | null;
  severity: "high" | "medium" | "low";
  category: string;
  summary: string;
  explanation: string;
  suggestion: string | null;
}

export interface PullRequestReview {
  id: string;
  repository_id: string;
  pr_number: number;
  pr_title: string;
  pr_url: string;
  status: "pending" | "complete" | "failed";
  summary: string | null;
  published: boolean;
  published_comment_url: string | null;
  error_detail: string | null;
  created_at: string;
  findings: ReviewFinding[];
}

const IN_PROGRESS = new Set(["pending"]);

export function useReviews(repositoryId: string, enabled: boolean) {
  return useQuery<PullRequestReview[]>({
    queryKey: ["repositories", repositoryId, "pull-requests"],
    queryFn: () => apiClient.get<PullRequestReview[]>(`/repositories/${repositoryId}/pull-requests`),
    enabled,
  });
}

export function useReview(reviewId: string | null) {
  return useQuery<PullRequestReview>({
    queryKey: ["pull-requests", reviewId],
    queryFn: () => apiClient.get<PullRequestReview>(`/pull-requests/${reviewId}`),
    enabled: Boolean(reviewId),
    refetchInterval: (query) => (IN_PROGRESS.has(query.state.data?.status ?? "") ? 2000 : false),
  });
}

export function useStartReview(repositoryId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (pr_number: number) =>
      apiClient.post<PullRequestReview>(`/repositories/${repositoryId}/pull-requests`, { pr_number }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["repositories", repositoryId, "pull-requests"] });
    },
  });
}

export function usePublishReview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (reviewId: string) =>
      apiClient.post<PullRequestReview>(`/pull-requests/${reviewId}/publish`, { confirm: true }),
    onSuccess: (review) => {
      queryClient.invalidateQueries({ queryKey: ["pull-requests", review.id] });
    },
  });
}

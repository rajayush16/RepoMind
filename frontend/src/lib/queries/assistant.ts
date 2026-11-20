import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export interface Conversation {
  id: string;
  repository_id: string;
  title: string;
  created_at: string;
}

export interface Citation {
  file_path: string;
  symbol_name: string | null;
  symbol_type: string | null;
  start_line: number | null;
  end_line: number | null;
  sources: string[];
}

export interface AssistantMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[] | null;
  insufficient_evidence: boolean;
  provider: string | null;
  model: string | null;
  created_at: string;
}

export function useConversations(repositoryId: string, enabled: boolean) {
  return useQuery<Conversation[]>({
    queryKey: ["repositories", repositoryId, "conversations"],
    queryFn: () => apiClient.get<Conversation[]>(`/repositories/${repositoryId}/conversations`),
    enabled,
  });
}

export function useCreateConversation(repositoryId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiClient.post<Conversation>(`/repositories/${repositoryId}/conversations`, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["repositories", repositoryId, "conversations"] });
    },
  });
}

export function useMessages(conversationId: string | null) {
  return useQuery<AssistantMessage[]>({
    queryKey: ["conversations", conversationId, "messages"],
    queryFn: () => apiClient.get<AssistantMessage[]>(`/conversations/${conversationId}/messages`),
    enabled: Boolean(conversationId),
  });
}

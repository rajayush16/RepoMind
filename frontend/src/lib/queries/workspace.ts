import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  is_personal: boolean;
}

export function useCurrentWorkspace(enabled: boolean) {
  return useQuery<Workspace>({
    queryKey: ["workspaces", "current"],
    queryFn: () => apiClient.get<Workspace>("/workspaces/current"),
    enabled,
  });
}

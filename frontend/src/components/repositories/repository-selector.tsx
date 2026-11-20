"use client";

import { useEffect } from "react";
import { FolderGit2 } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useRepositories } from "@/lib/queries/repositories";
import { useRepositoryStore } from "@/stores/repository-store";

export function RepositorySelector() {
  const { data: repositories } = useRepositories();
  const selectedRepositoryId = useRepositoryStore((state) => state.selectedRepositoryId);
  const setSelectedRepositoryId = useRepositoryStore((state) => state.setSelectedRepositoryId);

  useEffect(() => {
    if (!selectedRepositoryId && repositories && repositories.length > 0) {
      setSelectedRepositoryId(repositories[0].id);
    }
  }, [repositories, selectedRepositoryId, setSelectedRepositoryId]);

  if (!repositories || repositories.length === 0) {
    return null;
  }

  return (
    <Select value={selectedRepositoryId ?? undefined} onValueChange={setSelectedRepositoryId}>
      <SelectTrigger className="w-64">
        <FolderGit2 className="size-3.5 text-muted-foreground" />
        <SelectValue placeholder="Select a repository" />
      </SelectTrigger>
      <SelectContent>
        {repositories.map((repo) => (
          <SelectItem key={repo.id} value={repo.id}>
            {repo.full_name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

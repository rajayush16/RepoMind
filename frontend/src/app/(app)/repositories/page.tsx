"use client";

import { FolderGit2, Loader2 } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";
import { GithubButton } from "@/components/auth/github-button";
import { RepositoryCard } from "@/components/repositories/repository-card";
import { AvailableRepoRow } from "@/components/repositories/available-repo-row";
import { useCurrentUser } from "@/lib/queries/auth";
import {
  useAvailableGithubRepositories,
  useConnectRepository,
  useDeleteRepository,
  useRepositories,
} from "@/lib/queries/repositories";

export default function RepositoriesPage() {
  const { data: user } = useCurrentUser();
  const githubConnected = Boolean(user?.github_connected);

  const repositories = useRepositories();
  const availableRepos = useAvailableGithubRepositories(githubConnected);
  const connectRepo = useConnectRepository();
  const deleteRepo = useDeleteRepository();

  return (
    <div className="flex flex-1 flex-col gap-8">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Repositories</h1>
        <p className="text-sm text-muted-foreground">
          Connect, index, and manage the GitHub repositories RepoMind understands.
        </p>
      </div>

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold text-muted-foreground">Connected</h2>

        {repositories.isLoading ? (
          <Loader2 className="size-4 animate-spin text-muted-foreground" />
        ) : repositories.data && repositories.data.length > 0 ? (
          <div className="flex flex-col gap-2">
            {repositories.data.map((repo) => (
              <RepositoryCard
                key={repo.id}
                repository={repo}
                onDelete={() => deleteRepo.mutate(repo.id)}
                isDeleting={deleteRepo.isPending && deleteRepo.variables === repo.id}
              />
            ))}
          </div>
        ) : (
          <EmptyState
            icon={FolderGit2}
            title="No repositories connected yet"
            description="Connect a GitHub repository below to start indexing it."
          />
        )}
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold text-muted-foreground">
          Available on GitHub
        </h2>

        {!githubConnected ? (
          <EmptyState
            icon={FolderGit2}
            title="Connect your GitHub account"
            description="Authorize RepoMind to read your repositories so you can browse and connect them here."
          >
            <GithubButton label="Connect GitHub" />
          </EmptyState>
        ) : availableRepos.isLoading ? (
          <Loader2 className="size-4 animate-spin text-muted-foreground" />
        ) : availableRepos.isError ? (
          <p className="text-sm text-destructive">
            Could not load your GitHub repositories. Try reconnecting GitHub.
          </p>
        ) : availableRepos.data && availableRepos.data.length > 0 ? (
          <div className="flex flex-col gap-2">
            {availableRepos.data.map((repo) => (
              <AvailableRepoRow
                key={repo.github_repo_id}
                repo={repo}
                onConnect={() => connectRepo.mutate(repo)}
                isConnecting={
                  connectRepo.isPending &&
                  connectRepo.variables?.github_repo_id === repo.github_repo_id
                }
              />
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            No repositories found on your GitHub account.
          </p>
        )}
      </section>
    </div>
  );
}

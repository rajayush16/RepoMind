"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { GithubButton } from "@/components/auth/github-button";
import { GithubIcon } from "@/components/shared/github-icon";
import { useCurrentUser, useLogout } from "@/lib/queries/auth";

export default function SettingsPage() {
  const router = useRouter();
  const { data: user } = useCurrentUser();
  const logout = useLogout();

  function handleLogout() {
    logout.mutate(undefined, { onSuccess: () => router.replace("/login") });
  }

  return (
    <div className="flex flex-1 flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground">Account and integration settings.</p>
      </div>

      <Card className="max-w-xl">
        <CardHeader>
          <CardTitle className="text-base">Account</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 text-sm">
          <div className="flex justify-between border-b border-border pb-3">
            <span className="text-muted-foreground">Name</span>
            <span>{user?.name ?? "—"}</span>
          </div>
          <div className="flex justify-between border-b border-border pb-3">
            <span className="text-muted-foreground">Email</span>
            <span>{user?.email}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">GitHub</span>
            {user?.github_connected ? (
              <Badge variant="secondary" className="gap-1.5">
                <GithubIcon className="size-3" />@{user.github_username}
              </Badge>
            ) : (
              <GithubButton label="Connect GitHub" />
            )}
          </div>
        </CardContent>
      </Card>

      <div>
        <Button variant="outline" onClick={handleLogout} disabled={logout.isPending}>
          {logout.isPending ? "Signing out..." : "Log out"}
        </Button>
      </div>

      <p className="max-w-xl text-xs text-muted-foreground">
        Workspace management, role-based permissions, and notification preferences are not
        implemented yet (see IMPLEMENTATION_PLAN.md, Phase 3 follow-ups).
      </p>
    </div>
  );
}

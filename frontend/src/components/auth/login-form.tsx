"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { GithubButton } from "@/components/auth/github-button";
import { useLogin } from "@/lib/queries/auth";
import { loginSchema } from "@/lib/validation/auth";
import { ApiError } from "@/lib/api-client";

const OAUTH_ERROR_MESSAGES: Record<string, string> = {
  github_oauth_failed: "GitHub sign-in failed or was cancelled. Please try again.",
  github_email_missing:
    "Your GitHub account has no public email. Add one on GitHub and try again.",
};

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const oauthError = searchParams.get("error");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldError, setFieldError] = useState<string | null>(null);
  const login = useLogin();

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const result = loginSchema.safeParse({ email, password });
    if (!result.success) {
      setFieldError(result.error.issues[0]?.message ?? "Invalid input.");
      return;
    }
    setFieldError(null);
    login.mutate(result.data, {
      onSuccess: () => router.push("/overview"),
    });
  }

  const apiErrorMessage =
    login.error instanceof ApiError ? login.error.message : login.error ? "Something went wrong." : null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Sign in</CardTitle>
        <CardDescription>Welcome back. Sign in to continue to RepoMind.</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {oauthError && (
          <p className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {OAUTH_ERROR_MESSAGES[oauthError] ?? "Sign-in failed. Please try again."}
          </p>
        )}

        <GithubButton label="Continue with GitHub" />

        <div className="flex items-center gap-3">
          <Separator className="flex-1" />
          <span className="text-xs text-muted-foreground">or</span>
          <Separator className="flex-1" />
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="email" className="text-sm font-medium">
              Email
            </label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor="password" className="text-sm font-medium">
              Password
            </label>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          {(fieldError || apiErrorMessage) && (
            <p className="text-sm text-destructive">{fieldError ?? apiErrorMessage}</p>
          )}

          <Button type="submit" disabled={login.isPending} className="mt-1">
            {login.isPending ? "Signing in..." : "Sign in"}
          </Button>
        </form>

        <p className="text-center text-sm text-muted-foreground">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="font-medium text-foreground hover:underline">
            Create one
          </Link>
        </p>
      </CardContent>
    </Card>
  );
}

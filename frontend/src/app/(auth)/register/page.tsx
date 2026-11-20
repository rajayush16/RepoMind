"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { GithubButton } from "@/components/auth/github-button";
import { useRegister } from "@/lib/queries/auth";
import { registerSchema } from "@/lib/validation/auth";
import { ApiError } from "@/lib/api-client";

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldError, setFieldError] = useState<string | null>(null);
  const register = useRegister();

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const result = registerSchema.safeParse({ name: name || undefined, email, password });
    if (!result.success) {
      setFieldError(result.error.issues[0]?.message ?? "Invalid input.");
      return;
    }
    setFieldError(null);
    register.mutate(result.data, {
      onSuccess: () => router.push("/overview"),
    });
  }

  const apiErrorMessage =
    register.error instanceof ApiError
      ? register.error.message
      : register.error
        ? "Something went wrong."
        : null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create your account</CardTitle>
        <CardDescription>Start exploring your codebase with RepoMind.</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <GithubButton label="Sign up with GitHub" />

        <div className="flex items-center gap-3">
          <Separator className="flex-1" />
          <span className="text-xs text-muted-foreground">or</span>
          <Separator className="flex-1" />
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="name" className="text-sm font-medium">
              Name <span className="text-muted-foreground">(optional)</span>
            </label>
            <Input id="name" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
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
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          {(fieldError || apiErrorMessage) && (
            <p className="text-sm text-destructive">{fieldError ?? apiErrorMessage}</p>
          )}

          <Button type="submit" disabled={register.isPending} className="mt-1">
            {register.isPending ? "Creating account..." : "Create account"}
          </Button>
        </form>

        <p className="text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-foreground hover:underline">
            Sign in
          </Link>
        </p>
      </CardContent>
    </Card>
  );
}

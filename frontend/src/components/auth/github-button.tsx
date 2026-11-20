import { Button } from "@/components/ui/button";
import { GithubIcon } from "@/components/shared/github-icon";
import { githubLoginUrl } from "@/lib/api-client";

export function GithubButton({ label }: { label: string }) {
  return (
    <Button variant="outline" className="w-full gap-2" asChild>
      <a href={githubLoginUrl()}>
        <GithubIcon className="size-4" />
        {label}
      </a>
    </Button>
  );
}

import Link from "next/link";
import { Boxes } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-border/60">
      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-6 py-10 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <div className="flex size-6 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Boxes className="size-3.5" />
          </div>
          <span className="text-sm font-medium">RepoMind</span>
          <span className="text-sm text-muted-foreground">
            — Understand. Investigate. Improve.
          </span>
        </div>

        <div className="flex gap-6 text-sm text-muted-foreground">
          <Link href="/login" className="hover:text-foreground">
            Sign in
          </Link>
          <a
            href="https://github.com/rajayush16/RepoMind"
            target="_blank"
            rel="noreferrer"
            className="hover:text-foreground"
          >
            GitHub
          </a>
        </div>
      </div>
    </footer>
  );
}

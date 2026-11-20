import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ProductPreview } from "@/components/marketing/product-preview";
import { githubLoginUrl } from "@/lib/api-client";

export function Hero() {
  return (
    <section className="mx-auto max-w-6xl px-6 pt-20 pb-16 text-center">
      <div className="mx-auto mb-5 inline-flex items-center gap-2 rounded-full border border-border bg-secondary/60 px-3 py-1 text-xs text-muted-foreground">
        AST parsing · knowledge graph · hybrid retrieval · multi-agent reasoning
      </div>

      <h1 className="mx-auto max-w-3xl text-4xl font-semibold tracking-tight sm:text-5xl">
        Your entire codebase.{" "}
        <span className="bg-gradient-to-r from-primary to-brand-cyan bg-clip-text text-transparent">
          Finally understood.
        </span>
      </h1>

      <p className="mx-auto mt-5 max-w-xl text-balance text-base text-muted-foreground sm:text-lg">
        AI-powered code intelligence that maps dependencies, investigates bugs and helps
        developers make safer changes.
      </p>

      <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
        <Button size="lg" asChild>
          <a href={githubLoginUrl()}>
            Connect GitHub
            <ArrowRight className="size-4" />
          </a>
        </Button>
        <Button size="lg" variant="outline" asChild>
          <Link href="/login">Sign in</Link>
        </Button>
      </div>

      <ProductPreview />
    </section>
  );
}

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Cta() {
  return (
    <section className="mx-auto max-w-4xl px-6 py-20 text-center">
      <h2 className="text-3xl font-semibold tracking-tight">
        Stop guessing how your codebase works.
      </h2>
      <p className="mx-auto mt-3 max-w-lg text-muted-foreground">
        Connect a repository and start exploring its real architecture in minutes.
      </p>
      <div className="mt-7 flex flex-col items-center justify-center gap-3 sm:flex-row">
        <Button size="lg" asChild>
          <Link href="/repositories">
            Connect GitHub
            <ArrowRight className="size-4" />
          </Link>
        </Button>
        <Button size="lg" variant="outline" asChild>
          <Link href="/overview">Explore Demo</Link>
        </Button>
      </div>
    </section>
  );
}

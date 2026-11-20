import {
  GitGraph,
  Search,
  Bug,
  Waypoints,
  GitPullRequest,
  FlaskConical,
} from "lucide-react";

const FEATURES = [
  {
    icon: GitGraph,
    title: "Architecture graph",
    description:
      "Files, classes, functions and API endpoints mapped into a real Neo4j dependency graph you can explore visually.",
  },
  {
    icon: Search,
    title: "Hybrid retrieval",
    description:
      "Lexical search, vector similarity, symbol lookup and graph traversal fused together — not naive vector-only RAG.",
  },
  {
    icon: Bug,
    title: "Bug investigation",
    description:
      "A multi-step agent traces stack frames to candidate root causes and shows its evidence at every stage.",
  },
  {
    icon: Waypoints,
    title: "Change impact analysis",
    description:
      "See every caller, dependent, and test affected by a change before you make it, sourced from the code graph.",
  },
  {
    icon: GitPullRequest,
    title: "Pull request review",
    description:
      "Structured, evidence-backed findings on correctness, security and architecture — previewed before anything posts.",
  },
  {
    icon: FlaskConical,
    title: "Test generation",
    description:
      "Generated tests run in an isolated sandbox; results are only ever reported after real execution.",
  },
];

export function Features() {
  return (
    <section id="features" className="mx-auto max-w-6xl px-6 py-20">
      <div className="mx-auto mb-12 max-w-2xl text-center">
        <h2 className="text-3xl font-semibold tracking-tight">
          More than a chatbot over your code
        </h2>
        <p className="mt-3 text-muted-foreground">
          RepoMind combines static analysis, retrieval and multi-agent reasoning to actually
          understand how your codebase works.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map((feature) => (
          <div
            key={feature.title}
            className="rounded-lg border border-border bg-card p-5 transition-colors hover:border-primary/40"
          >
            <div className="mb-3 flex size-9 items-center justify-center rounded-md bg-secondary">
              <feature.icon className="size-5 text-primary" />
            </div>
            <h3 className="text-sm font-semibold">{feature.title}</h3>
            <p className="mt-1.5 text-sm text-muted-foreground">{feature.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

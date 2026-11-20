const STEPS = [
  {
    step: "01",
    title: "Connect a repository",
    description:
      "Authorize GitHub access and select a repository and branch. Public and authorized private repos are supported.",
  },
  {
    step: "02",
    title: "RepoMind indexes it",
    description:
      "Tree-sitter parses every file into symbols, imports and calls. Embeddings go to Qdrant, relationships to Neo4j.",
  },
  {
    step: "03",
    title: "Explore and ask questions",
    description:
      "Browse the architecture graph, navigate symbols, or ask the assistant anything — every answer cites real source.",
  },
  {
    step: "04",
    title: "Investigate and improve",
    description:
      "Trace bugs to root causes, analyse change impact, review pull requests, and generate tests that actually run.",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="border-t border-border/60 bg-surface/40 py-20">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mx-auto mb-12 max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight">How it works</h2>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((item) => (
            <div key={item.step}>
              <span className="text-sm font-mono text-primary">{item.step}</span>
              <h3 className="mt-2 text-sm font-semibold">{item.title}</h3>
              <p className="mt-1.5 text-sm text-muted-foreground">{item.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

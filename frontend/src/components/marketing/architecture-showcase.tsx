const LAYERS = [
  { name: "PostgreSQL", role: "Application metadata: users, workspaces, repos, jobs" },
  { name: "Neo4j", role: "Code knowledge graph: symbols, calls, imports, inheritance" },
  { name: "Qdrant", role: "Vector embeddings for semantic code retrieval" },
  { name: "Redis", role: "Cache and Celery coordination" },
];

export function ArchitectureShowcase() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-20">
      <div className="mx-auto mb-12 max-w-2xl text-center">
        <h2 className="text-3xl font-semibold tracking-tight">
          Built on a real code intelligence stack
        </h2>
        <p className="mt-3 text-muted-foreground">
          Each system owns one source of truth — nothing is duplicated or faked across
          layers.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {LAYERS.map((layer) => (
          <div key={layer.name} className="rounded-lg border border-border bg-card p-5">
            <h3 className="font-mono text-sm font-semibold text-brand-cyan">{layer.name}</h3>
            <p className="mt-2 text-sm text-muted-foreground">{layer.role}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

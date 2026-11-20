const USE_CASES = [
  {
    title: "Onboarding into an unfamiliar codebase",
    description:
      "New engineers get architectural answers with citations instead of grepping blindly through thousands of files.",
  },
  {
    title: "Debugging production incidents",
    description:
      "Paste a stack trace and get a traced, evidence-backed investigation instead of starting from scratch.",
  },
  {
    title: "Reviewing risky changes",
    description:
      "See exactly what a change could break — callers, dependents and affected tests — before you merge it.",
  },
  {
    title: "Maintaining open-source projects",
    description:
      "Review incoming pull requests against the project's real architecture and existing conventions.",
  },
];

export function UseCases() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-20">
      <div className="mx-auto mb-12 max-w-2xl text-center">
        <h2 className="text-3xl font-semibold tracking-tight">Built for real engineering work</h2>
      </div>

      <div className="grid gap-6 sm:grid-cols-2">
        {USE_CASES.map((useCase) => (
          <div key={useCase.title} className="rounded-lg border border-border bg-card p-6">
            <h3 className="text-base font-semibold">{useCase.title}</h3>
            <p className="mt-2 text-sm text-muted-foreground">{useCase.description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

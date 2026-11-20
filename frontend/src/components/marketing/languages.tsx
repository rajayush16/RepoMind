const LANGUAGES = ["Python", "JavaScript", "TypeScript", "Java", "C++", "Go"];

export function Languages() {
  return (
    <section id="languages" className="border-t border-border/60 py-20">
      <div className="mx-auto max-w-6xl px-6 text-center">
        <h2 className="text-3xl font-semibold tracking-tight">
          AST-level support across your stack
        </h2>
        <p className="mx-auto mt-3 max-w-xl text-muted-foreground">
          Tree-sitter parsing ships with these languages today. The parsing system is
          designed so more can be added without reworking the architecture.
        </p>

        <div className="mt-8 flex flex-wrap justify-center gap-3">
          {LANGUAGES.map((lang) => (
            <span
              key={lang}
              className="rounded-full border border-border bg-secondary px-4 py-1.5 text-sm font-medium"
            >
              {lang}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}

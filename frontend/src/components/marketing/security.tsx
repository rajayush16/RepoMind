import { ShieldCheck, Lock, Container, Eye } from "lucide-react";

const POINTS = [
  {
    icon: Lock,
    title: "Encrypted token storage",
    description: "GitHub tokens and LLM credentials never reach the browser.",
  },
  {
    icon: Container,
    title: "Sandboxed execution",
    description:
      "Repository code and generated patches run only in isolated, network-restricted Docker containers.",
  },
  {
    icon: ShieldCheck,
    title: "Workspace-level access control",
    description: "Repository access is scoped per workspace and audited.",
  },
  {
    icon: Eye,
    title: "Prompt-injection resistance",
    description:
      "README files, comments and issue content are treated as untrusted data, never as instructions.",
  },
];

export function Security() {
  return (
    <section id="security" className="border-t border-border/60 bg-surface/40 py-20">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mx-auto mb-12 max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight">Security by default</h2>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {POINTS.map((point) => (
            <div key={point.title} className="text-center">
              <div className="mx-auto mb-3 flex size-10 items-center justify-center rounded-full bg-secondary">
                <point.icon className="size-5 text-primary" />
              </div>
              <h3 className="text-sm font-semibold">{point.title}</h3>
              <p className="mt-1.5 text-sm text-muted-foreground">{point.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

import { Boxes, FolderGit2, Workflow, Sparkles, Bug, FileCode2 } from "lucide-react";

const NAV = [
  { label: "Overview", icon: Boxes, active: false },
  { label: "Repositories", icon: FolderGit2, active: false },
  { label: "Architecture Graph", icon: Workflow, active: false },
  { label: "AI Assistant", icon: Sparkles, active: true },
  { label: "Bug Investigation", icon: Bug, active: false },
];

export function ProductPreview() {
  return (
    <div className="mt-16">
      <div className="mx-auto max-w-4xl overflow-hidden rounded-xl border border-border bg-card shadow-2xl shadow-black/40">
        <div className="flex h-9 items-center gap-1.5 border-b border-border bg-surface px-4">
          <span className="size-2.5 rounded-full bg-destructive/60" />
          <span className="size-2.5 rounded-full bg-warning/60" />
          <span className="size-2.5 rounded-full bg-success/60" />
        </div>

        <div className="flex h-80 text-left">
          <div className="hidden w-48 shrink-0 flex-col gap-0.5 border-r border-border bg-sidebar p-3 sm:flex">
            {NAV.map((item) => (
              <div
                key={item.label}
                className={`flex items-center gap-2 rounded-md px-2.5 py-1.5 text-xs ${
                  item.active
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "text-sidebar-foreground/60"
                }`}
              >
                <item.icon className="size-3.5" />
                {item.label}
              </div>
            ))}
          </div>

          <div className="flex flex-1 flex-col gap-3 overflow-hidden p-5">
            <div className="ml-auto max-w-[80%] rounded-lg bg-secondary px-3 py-2 text-xs">
              How does authentication work in this repo?
            </div>
            <div className="max-w-[85%] rounded-lg border border-border bg-popover px-3 py-2 text-xs leading-relaxed text-foreground/90">
              Requests hit <code className="text-brand-cyan">auth/router.py:42</code>, which
              validates the session via <code className="text-brand-cyan">
                core/security.py:18
              </code>{" "}
              before delegating to the user service.
              <div className="mt-2 flex items-center gap-1.5 rounded-md bg-secondary/60 px-2 py-1 text-[11px] text-muted-foreground">
                <FileCode2 className="size-3" />
                2 citations · auth/router.py, core/security.py
              </div>
            </div>
          </div>
        </div>
      </div>
      <p className="mt-3 text-center text-xs text-muted-foreground">
        Illustrative preview of the AI Assistant interface — built from RepoMind&apos;s real
        design system.
      </p>
    </div>
  );
}

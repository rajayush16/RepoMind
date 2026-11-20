import { CheckCircle2, Loader2, Search, Workflow, GitBranch, FileSearch } from "lucide-react";
import type { InvestigationStep } from "@/lib/queries/investigations";

const STAGE_META: Record<string, { label: string; icon: typeof Search }> = {
  parse_issue: { label: "Understanding issue", icon: FileSearch },
  find_related_symbols: { label: "Finding related symbols", icon: Search },
  trace_execution: { label: "Tracing execution", icon: GitBranch },
  evaluate_causes: { label: "Evaluating root causes", icon: Workflow },
  prepare_findings: { label: "Preparing findings", icon: CheckCircle2 },
};

export function InvestigationTimeline({
  steps,
  isRunning,
}: {
  steps: InvestigationStep[];
  isRunning: boolean;
}) {
  return (
    <ol className="flex flex-col gap-3">
      {steps.map((step) => {
        const meta = STAGE_META[step.stage] ?? { label: step.stage, icon: Search };
        const Icon = meta.icon;
        return (
          <li key={step.id} className="flex gap-3">
            <div className="flex size-6 shrink-0 items-center justify-center rounded-full bg-secondary">
              <Icon className="size-3.5 text-primary" />
            </div>
            <div>
              <p className="text-sm font-medium">{meta.label}</p>
              <p className="text-xs text-muted-foreground">{step.summary}</p>
            </div>
          </li>
        );
      })}
      {isRunning && (
        <li className="flex items-center gap-3">
          <div className="flex size-6 shrink-0 items-center justify-center rounded-full bg-secondary">
            <Loader2 className="size-3.5 animate-spin text-primary" />
          </div>
          <p className="text-sm text-muted-foreground">Working...</p>
        </li>
      )}
    </ol>
  );
}

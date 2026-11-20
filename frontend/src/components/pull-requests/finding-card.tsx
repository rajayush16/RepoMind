import { Badge } from "@/components/ui/badge";
import type { ReviewFinding } from "@/lib/queries/pull-requests";

const SEVERITY_VARIANT: Record<string, "secondary" | "destructive"> = {
  high: "destructive",
  medium: "secondary",
  low: "secondary",
};

export function FindingCard({ finding }: { finding: ReviewFinding }) {
  return (
    <div className="rounded-lg border border-border bg-card p-3">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant={SEVERITY_VARIANT[finding.severity] ?? "secondary"}>{finding.severity}</Badge>
        <Badge variant="outline">{finding.category}</Badge>
        <span className="font-mono text-xs text-muted-foreground">
          {finding.file_path}
          {finding.line ? `:${finding.line}` : ""}
        </span>
      </div>
      <p className="mt-2 text-sm font-medium">{finding.summary}</p>
      <p className="mt-1 text-sm text-muted-foreground">{finding.explanation}</p>
      {finding.suggestion && (
        <p className="mt-2 rounded-md bg-secondary/60 p-2 text-xs">{finding.suggestion}</p>
      )}
    </div>
  );
}

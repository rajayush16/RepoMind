import Link from "next/link";
import { FileCode2 } from "lucide-react";
import type { Citation } from "@/lib/queries/assistant";
import { useRepositoryStore } from "@/stores/repository-store";

export function CitationChip({ citation }: { citation: Citation }) {
  const repositoryId = useRepositoryStore((state) => state.selectedRepositoryId);
  const location = citation.start_line
    ? `${citation.file_path}:${citation.start_line}`
    : citation.file_path;

  const href = `/explorer?repo=${repositoryId ?? ""}&file=${encodeURIComponent(citation.file_path)}${
    citation.start_line ? `&line=${citation.start_line}` : ""
  }`;

  return (
    <Link
      href={href}
      className="inline-flex items-center gap-1 rounded-md border border-border bg-secondary/60 px-2 py-0.5 text-xs text-foreground/80 hover:bg-secondary"
    >
      <FileCode2 className="size-3" />
      {location}
    </Link>
  );
}

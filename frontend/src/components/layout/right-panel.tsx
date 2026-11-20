"use client";

import { Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/ui-store";

export function RightPanel() {
  const open = useUIStore((state) => state.rightPanelOpen);

  return (
    <aside
      className={cn(
        "hidden shrink-0 flex-col border-l border-border bg-surface transition-all duration-200 lg:flex",
        open ? "w-80 opacity-100" : "w-0 overflow-hidden border-l-0 opacity-0",
      )}
    >
      <div className="flex h-14 items-center border-b border-border px-4">
        <span className="text-sm font-medium">AI Insights</span>
      </div>
      <div className="flex flex-1 flex-col items-center justify-center gap-2 px-6 text-center">
        <Sparkles className="size-5 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">
          Insights, related files, and citations will appear here once a repository is
          connected and the AI assistant is active.
        </p>
      </div>
    </aside>
  );
}

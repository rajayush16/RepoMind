import { Braces, Box, Layers, Shapes, Workflow } from "lucide-react";
import type { SymbolEntry } from "@/lib/queries/code";

const ICONS: Record<string, typeof Braces> = {
  function: Braces,
  method: Workflow,
  class: Box,
  interface: Shapes,
  struct: Layers,
};

export function SymbolOutline({
  symbols,
  onJump,
}: {
  symbols: SymbolEntry[];
  onJump: (line: number) => void;
}) {
  if (symbols.length === 0) {
    return <p className="px-3 py-4 text-xs text-muted-foreground">No symbols extracted for this file.</p>;
  }

  return (
    <div className="flex flex-col gap-0.5 py-1">
      {symbols.map((symbol) => {
        const Icon = ICONS[symbol.symbol_type] ?? Braces;
        return (
          <button
            key={symbol.id}
            onClick={() => onJump(symbol.start_line)}
            className="flex items-center gap-2 rounded-md px-3 py-1 text-left text-sm hover:bg-secondary"
          >
            <Icon className="size-3.5 shrink-0 text-muted-foreground" />
            <span className="truncate">
              {symbol.parent_name ? `${symbol.parent_name}.${symbol.name}` : symbol.name}
            </span>
            <span className="ml-auto shrink-0 text-xs text-muted-foreground">
              L{symbol.start_line}
            </span>
          </button>
        );
      })}
    </div>
  );
}

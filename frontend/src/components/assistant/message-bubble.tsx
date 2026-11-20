import { useState } from "react";
import { AlertTriangle, Check, Copy, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { CitationChip } from "@/components/assistant/citation-chip";
import type { Citation } from "@/lib/queries/assistant";
import { cn } from "@/lib/utils";

export interface DisplayMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[] | null;
  insufficientEvidence: boolean;
}

export function MessageBubble({ message }: { message: DisplayMessage }) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === "user";

  async function copy() {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard access can fail (permissions, insecure context) -- non-critical.
    }
  }

  return (
    <div className={cn("flex gap-3", isUser && "flex-row-reverse")}>
      {!isUser && (
        <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-secondary">
          <Sparkles className="size-3.5 text-primary" />
        </div>
      )}

      <div className={cn("flex max-w-[80%] flex-col gap-1.5", isUser && "items-end")}>
        <div
          className={cn(
            "rounded-lg px-3.5 py-2.5 text-sm leading-relaxed whitespace-pre-wrap",
            isUser ? "bg-primary text-primary-foreground" : "border border-border bg-card",
          )}
        >
          {message.insufficientEvidence && (
            <div className="mb-1.5 flex items-center gap-1.5 text-xs text-warning">
              <AlertTriangle className="size-3.5" />
              Insufficient evidence
            </div>
          )}
          {message.content}
        </div>

        {message.citations && message.citations.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {message.citations.map((citation, index) => (
              <CitationChip key={index} citation={citation} />
            ))}
          </div>
        )}

        {!isUser && message.content && (
          <Button variant="ghost" size="sm" className="h-6 gap-1 self-start px-1.5 text-xs text-muted-foreground" onClick={copy}>
            {copied ? <Check className="size-3" /> : <Copy className="size-3" />}
            {copied ? "Copied" : "Copy"}
          </Button>
        )}
      </div>
    </div>
  );
}

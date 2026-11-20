import { Loader2, MessageSquarePlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { Conversation } from "@/lib/queries/assistant";

export function ConversationList({
  conversations,
  isLoading,
  selectedId,
  onSelect,
  onCreate,
  isCreating,
}: {
  conversations: Conversation[] | undefined;
  isLoading: boolean;
  selectedId: string | null;
  onSelect: (id: string) => void;
  onCreate: () => void;
  isCreating: boolean;
}) {
  return (
    <div className="flex h-full w-60 shrink-0 flex-col border-r border-border bg-surface">
      <div className="border-b border-border p-2">
        <Button variant="outline" size="sm" className="w-full gap-1.5" onClick={onCreate} disabled={isCreating}>
          {isCreating ? <Loader2 className="size-3.5 animate-spin" /> : <MessageSquarePlus className="size-3.5" />}
          New conversation
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {isLoading ? (
          <Loader2 className="m-2 size-4 animate-spin text-muted-foreground" />
        ) : conversations && conversations.length > 0 ? (
          <div className="flex flex-col gap-0.5">
            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => onSelect(conv.id)}
                className={cn(
                  "truncate rounded-md px-2 py-1.5 text-left text-sm hover:bg-secondary",
                  conv.id === selectedId ? "bg-sidebar-accent text-sidebar-accent-foreground" : "text-foreground/80",
                )}
              >
                {conv.title}
              </button>
            ))}
          </div>
        ) : (
          <p className="px-2 py-1.5 text-xs text-muted-foreground">No conversations yet.</p>
        )}
      </div>
    </div>
  );
}

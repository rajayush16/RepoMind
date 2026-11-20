import { Sparkles } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";

export default function AssistantPage() {
  return (
    <div className="flex flex-1 flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">AI Assistant</h1>
        <p className="text-sm text-muted-foreground">
          Ask architectural questions about your codebase with streaming, cited answers.
        </p>
      </div>

      <EmptyState
        icon={Sparkles}
        title="Assistant not connected yet"
        description="The codebase assistant needs an indexed repository, a configured LLM provider, and the LangGraph workflow (Phase 6). It will always cite file paths and line numbers for factual claims, and will say so explicitly when it lacks sufficient evidence."
      />
    </div>
  );
}

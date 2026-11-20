"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Loader2, Send, Sparkles } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { EmptyState } from "@/components/shared/empty-state";
import { RepositorySelector } from "@/components/repositories/repository-selector";
import { ConversationList } from "@/components/assistant/conversation-list";
import { MessageBubble, type DisplayMessage } from "@/components/assistant/message-bubble";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { useRepositories } from "@/lib/queries/repositories";
import {
  useConversations,
  useCreateConversation,
  useMessages,
  type Citation,
} from "@/lib/queries/assistant";
import { useRepositoryStore } from "@/stores/repository-store";
import { streamAsk } from "@/lib/stream-ask";

export default function AssistantPage() {
  const { data: repositories } = useRepositories();
  const selectedRepositoryId = useRepositoryStore((state) => state.selectedRepositoryId);
  const repository = repositories?.find((r) => r.id === selectedRepositoryId);
  const hasIndexedRepo = Boolean(repository && repository.indexing_status === "indexed");

  const conversationsQuery = useConversations(selectedRepositoryId ?? "", hasIndexedRepo);
  const createConversation = useCreateConversation(selectedRepositoryId ?? "");
  const [conversationId, setConversationId] = useState<string | null>(null);

  useEffect(() => {
    if (!conversationId && conversationsQuery.data && conversationsQuery.data.length > 0) {
      setConversationId(conversationsQuery.data[0].id);
    }
  }, [conversationsQuery.data, conversationId]);

  const messagesQuery = useMessages(conversationId);
  const queryClient = useQueryClient();

  const [input, setInput] = useState("");
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);
  const [streamingText, setStreamingText] = useState("");
  const [streamingCitations, setStreamingCitations] = useState<Citation[]>([]);
  const [streamingInsufficient, setStreamingInsufficient] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamError, setStreamError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const displayMessages: DisplayMessage[] = useMemo(() => {
    const persisted: DisplayMessage[] = (messagesQuery.data ?? []).map((m) => ({
      id: m.id,
      role: m.role,
      content: m.content,
      citations: m.citations,
      insufficientEvidence: m.insufficient_evidence,
    }));

    if (pendingQuestion) {
      persisted.push({ id: "pending-question", role: "user", content: pendingQuestion, citations: null, insufficientEvidence: false });
      persisted.push({
        id: "pending-answer",
        role: "assistant",
        content: streamingText,
        citations: streamingCitations,
        insufficientEvidence: streamingInsufficient,
      });
    }

    return persisted;
  }, [messagesQuery.data, pendingQuestion, streamingText, streamingCitations, streamingInsufficient]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [displayMessages]);

  async function handleSubmit() {
    const question = input.trim();
    if (!question || !conversationId || isStreaming) return;

    setInput("");
    setPendingQuestion(question);
    setStreamingText("");
    setStreamingCitations([]);
    setStreamingInsufficient(false);
    setStreamError(null);
    setIsStreaming(true);

    await streamAsk(conversationId, question, {
      onToken: (text) => setStreamingText((prev) => prev + text),
      onDone: (data) => {
        setStreamingCitations((data.citations as Citation[]) ?? []);
        setStreamingInsufficient(Boolean(data.insufficient_evidence));
        setIsStreaming(false);
        setPendingQuestion(null);
        queryClient.invalidateQueries({ queryKey: ["conversations", conversationId, "messages"] });
      },
      onError: (detail) => {
        setStreamError(detail);
        setIsStreaming(false);
        setPendingQuestion(null);
      },
    }).catch(() => {
      setStreamError("Something went wrong talking to the model.");
      setIsStreaming(false);
    });

    setIsStreaming(false);
  }

  if (!repositories || repositories.length === 0) {
    return (
      <div className="flex flex-1 flex-col gap-6">
        <PageHeader />
        <EmptyState icon={Sparkles} title="No repository connected yet" description="Connect and index a repository first, from the Repositories page." />
      </div>
    );
  }

  if (!hasIndexedRepo) {
    return (
      <div className="flex flex-1 flex-col gap-6">
        <PageHeader />
        <EmptyState icon={Sparkles} title="This repository hasn't been indexed yet" description="Index it from the Repositories page, then come back here." />
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col gap-4">
      <PageHeader />

      <div className="flex min-h-0 flex-1 overflow-hidden rounded-lg border border-border">
        <ConversationList
          conversations={conversationsQuery.data}
          isLoading={conversationsQuery.isLoading}
          selectedId={conversationId}
          onSelect={setConversationId}
          onCreate={() => createConversation.mutate(undefined, { onSuccess: (c) => setConversationId(c.id) })}
          isCreating={createConversation.isPending}
        />

        <div className="flex min-w-0 flex-1 flex-col">
          {!conversationId ? (
            <EmptyState
              icon={Sparkles}
              title="Start a conversation"
              description="Create a new conversation to ask questions about this repository."
            />
          ) : (
            <>
              <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-4">
                {displayMessages.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    Ask anything about this repository -- answers are grounded in real
                    indexed code, with citations, or an honest &quot;insufficient evidence&quot; if
                    nothing relevant was found.
                  </p>
                ) : (
                  displayMessages.map((message) => <MessageBubble key={message.id} message={message} />)
                )}
                {streamError && <p className="text-sm text-destructive">{streamError}</p>}
              </div>

              <div className="border-t border-border p-3">
                <div className="flex items-end gap-2">
                  <Textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleSubmit();
                      }
                    }}
                    placeholder="Ask about this repository..."
                    className="min-h-10 flex-1 resize-none text-sm"
                    rows={1}
                  />
                  <Button size="icon" onClick={handleSubmit} disabled={isStreaming || !input.trim()}>
                    {isStreaming ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
                  </Button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function PageHeader() {
  return (
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">AI Assistant</h1>
        <p className="text-sm text-muted-foreground">
          Ask architectural questions about your codebase with streaming, cited answers.
        </p>
      </div>
      <RepositorySelector />
    </div>
  );
}

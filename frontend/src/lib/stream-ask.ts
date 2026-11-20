const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

interface StreamCallbacks {
  onToken: (text: string) => void;
  onDone: (data: { citations: unknown[]; insufficient_evidence: boolean }) => void;
  onError: (detail: string) => void;
}

/** EventSource can't do POST with a body, so this parses `event:`/`data:` blocks
 * by hand from a streamed fetch response -- the standard workaround for SSE over
 * a non-GET request. */
export async function streamAsk(
  conversationId: string,
  question: string,
  callbacks: StreamCallbacks,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/conversations/${conversationId}/messages`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  if (!response.ok || !response.body) {
    const body = await response.json().catch(() => null);
    callbacks.onError(body?.detail ?? `Request failed (${response.status})`);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() ?? "";

    for (const block of blocks) {
      const eventLine = block.split("\n").find((l) => l.startsWith("event: "));
      const dataLine = block.split("\n").find((l) => l.startsWith("data: "));
      if (!eventLine || !dataLine) continue;

      const event = eventLine.replace("event: ", "").trim();
      const data = JSON.parse(dataLine.replace("data: ", ""));

      if (event === "token") callbacks.onToken(data.text);
      else if (event === "done") callbacks.onDone(data);
      else if (event === "error") callbacks.onError(data.detail);
    }
  }
}

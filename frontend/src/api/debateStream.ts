import { fetchEventSource } from "@microsoft/fetch-event-source";
import { resolveApiUrl } from "./config";
import type { DebateEvent } from "../types/debate";

export async function streamDebate(
  topic: string,
  onEvent: (event: DebateEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  let receivedAnyEvent = false;

  await fetchEventSource(resolveApiUrl("/api/debate/stream"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ topic }),
    signal,
    openWhenHidden: true,
    async onopen(response) {
      if (!response.ok) {
        throw new Error(`Stream request failed: ${response.status}`);
      }
      const contentType = response.headers.get("content-type") ?? "";
      if (!contentType.includes("text/event-stream")) {
        throw new Error("Expected text/event-stream");
      }
    },
    onmessage(message) {
      if (!message.data) {
        return;
      }
      receivedAnyEvent = true;
      try {
        onEvent(JSON.parse(message.data) as DebateEvent);
      } catch {
        throw new Error("Malformed SSE payload");
      }
    },
    onerror(error) {
      if (signal?.aborted) {
        throw error;
      }
      if (receivedAnyEvent) {
        throw error;
      }
    },
  });
}

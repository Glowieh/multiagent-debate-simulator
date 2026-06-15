import { fetchEventSource } from "@microsoft/fetch-event-source";
import { clearAccessToken, getAccessToken } from "./auth";
import { resolveApiUrl } from "./config";
import type { DebateEvent } from "../types/debate";

export class UnauthorizedError extends Error {
  constructor(message = "Unauthorized") {
    super(message);
    this.name = "UnauthorizedError";
  }
}

export async function streamDebate(
  topic: string,
  onEvent: (event: DebateEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  let receivedAnyEvent = false;
  const token = getAccessToken();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  await fetchEventSource(resolveApiUrl("/api/debate/stream"), {
    method: "POST",
    headers,
    body: JSON.stringify({ topic }),
    signal,
    openWhenHidden: true,
    async onopen(response) {
      if (response.status === 401) {
        clearAccessToken();
        throw new UnauthorizedError();
      }
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

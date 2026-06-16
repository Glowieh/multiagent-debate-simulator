import { useCallback, useEffect, useRef, useState } from "react";
import { getAccessToken, isAuthRequired } from "./api/auth";
import { UnauthorizedError, streamDebate } from "./api/debateStream";
import { DebateStatus } from "./components/DebateStatus";
import { DebateView } from "./components/DebateView";
import { LoginGate } from "./components/LoginGate";
import { TopicForm } from "./components/TopicForm";
import type { DebateEvent } from "./types/debate";
import {
  appendDebateEvent,
  partitionDisplayItems,
  type DisplayItem,
} from "./utils/debateEvents";
import "./App.css";

function App() {
  const [authenticated, setAuthenticated] = useState(
    () => !isAuthRequired() || getAccessToken() !== null,
  );
  const [items, setItems] = useState<DisplayItem[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [abortedByUser, setAbortedByUser] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const eventIndexRef = useRef(0);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  const handleEvent = useCallback((event: DebateEvent) => {
    const index = eventIndexRef.current;
    eventIndexRef.current += 1;
    setItems((prev) => appendDebateEvent(prev, event, index));

    if (event.type === "error") {
      setError(event.message);
      abortRef.current?.abort();
      setIsStreaming(false);
    }

    if (event.type === "debate_completed") {
      setIsStreaming(false);
    }
  }, []);

  const handleAbort = useCallback(() => {
    abortRef.current?.abort();
    setIsStreaming(false);
    setAbortedByUser(true);
  }, []);

  const handleClear = useCallback(() => {
    setItems([]);
    setError(null);
    setAbortedByUser(false);
    eventIndexRef.current = 0;
  }, []);

  const handleSubmit = useCallback(
    async (topic: string) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setItems([]);
      setError(null);
      setAbortedByUser(false);
      setIsStreaming(true);
      eventIndexRef.current = 0;

      try {
        await streamDebate(topic, handleEvent, controller.signal);
      } catch (err) {
        if (controller.signal.aborted) {
          return;
        }
        if (err instanceof UnauthorizedError) {
          setAuthenticated(false);
          setError("Session expired. Please sign in again.");
          return;
        }
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setIsStreaming(false);
      }
    },
    [handleEvent],
  );

  if (isAuthRequired() && !authenticated) {
    return <LoginGate onAuthenticated={() => setAuthenticated(true)} />;
  }

  return (
    <main className="app">
      <header>
        <h1>LangGraph Debate Simulator</h1>
        <p>Stream a multi-agent debate on any topic.</p>
      </header>

      <TopicForm
        onSubmit={handleSubmit}
        onAbort={handleAbort}
        onClear={handleClear}
        isStreaming={isStreaming}
        hasDebateContent={items.length > 0}
      />
      <DebateStatus
        statusEvents={partitionDisplayItems(items).statusEvents}
        isStreaming={isStreaming}
        abortedByUser={abortedByUser}
      />
      {error && <p className="error">{error}</p>}
      <DebateView items={items} isStreaming={isStreaming} />
    </main>
  );
}

export default App;

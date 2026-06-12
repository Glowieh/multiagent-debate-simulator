import type { DebateEvent } from "../types/debate";

type DebateStatusProps = {
  statusEvents: DebateEvent[];
  isStreaming: boolean;
  abortedByUser: boolean;
};

function getTopic(statusEvents: DebateEvent[]): string | null {
  for (let i = statusEvents.length - 1; i >= 0; i -= 1) {
    const event = statusEvents[i];
    if (event.type === "debate_started") {
      return event.topic;
    }
  }
  return null;
}

function isCompleted(statusEvents: DebateEvent[]): boolean {
  return statusEvents.some((event) => event.type === "debate_completed");
}

export function DebateStatus({
  statusEvents,
  isStreaming,
  abortedByUser,
}: DebateStatusProps) {
  const topic = getTopic(statusEvents);
  const completed = isCompleted(statusEvents);

  if (!topic && !isStreaming) {
    return null;
  }

  return (
    <div className="debate-status">
      {topic && <p className="debate-status-topic">Debate started: {topic}</p>}
      {isStreaming && <p className="streaming-indicator">Streaming…</p>}
      {abortedByUser && !isStreaming && (
        <p className="debate-status-aborted">Debate aborted.</p>
      )}
      {completed && !abortedByUser && (
        <p className="debate-status-complete">Debate completed.</p>
      )}
    </div>
  );
}

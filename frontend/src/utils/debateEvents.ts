import type { DebateEvent, Speaker } from "../types/debate";

export type DisplayItem =
  | { kind: "event"; event: DebateEvent; key: string }
  | { kind: "message"; speaker: Speaker; content: string; key: string };

export function appendDebateEvent(
  items: DisplayItem[],
  event: DebateEvent,
  index: number,
): DisplayItem[] {
  if (event.type === "message_chunk") {
    const last = items[items.length - 1];
    if (last?.kind === "message" && last.speaker === event.speaker) {
      return [
        ...items.slice(0, -1),
        {
          kind: "message",
          speaker: event.speaker,
          content: last.content + event.content,
          key: last.key,
        },
      ];
    }
    return [
      ...items,
      {
        kind: "message",
        speaker: event.speaker,
        content: event.content,
        key: `message-${event.speaker}-${index}`,
      },
    ];
  }

  return [
    ...items,
    {
      kind: "event",
      event,
      key: `${event.type}-${index}`,
    },
  ];
}

export type PartitionedItems = {
  statusEvents: DebateEvent[];
  redItems: DisplayItem[];
  greenItems: DisplayItem[];
  summaryContent: string | null;
};

function isTurnEvent(
  event: DebateEvent,
): event is Extract<
  DebateEvent,
  { type: "turn_started" } | { type: "turn_completed" }
> {
  return event.type === "turn_started" || event.type === "turn_completed";
}

function isToolCallEvent(
  event: DebateEvent,
): event is Extract<
  DebateEvent,
  { type: "tool_call_started" } | { type: "tool_call_completed" }
> {
  return (
    event.type === "tool_call_started" || event.type === "tool_call_completed"
  );
}

export function partitionDisplayItems(items: DisplayItem[]): PartitionedItems {
  const statusEvents: DebateEvent[] = [];
  const redItems: DisplayItem[] = [];
  const greenItems: DisplayItem[] = [];
  let summaryStreamContent = "";
  let summaryEventContent: string | null = null;

  for (const item of items) {
    if (item.kind === "message") {
      if (item.speaker === "Red") {
        redItems.push(item);
      } else if (item.speaker === "Green") {
        greenItems.push(item);
      } else if (item.speaker === "summarizer") {
        summaryStreamContent += item.content;
      }
      continue;
    }

    const { event } = item;
    switch (event.type) {
      case "debate_started":
      case "debate_completed":
        statusEvents.push(event);
        break;
      case "turn_started":
      case "turn_completed":
      case "tool_call_started":
      case "tool_call_completed":
        if (event.speaker === "Red") {
          redItems.push(item);
        } else {
          greenItems.push(item);
        }
        break;
      case "summary":
        summaryEventContent = event.content;
        break;
      case "error":
      case "message_chunk":
        break;
    }
  }

  const summaryContent =
    summaryStreamContent.length > 0
      ? summaryStreamContent
      : summaryEventContent;

  return {
    statusEvents,
    redItems,
    greenItems,
    summaryContent,
  };
}

export function speakerClass(speaker: Speaker): string {
  switch (speaker) {
    case "Red":
      return "debater-red";
    case "Green":
      return "debater-green";
    case "summarizer":
      return "debate-summary";
    default: {
      const _exhaustive: never = speaker;
      return _exhaustive;
    }
  }
}

export function turnLabel(event: DebateEvent): string | null {
  if (!isTurnEvent(event)) {
    return null;
  }
  if (event.type === "turn_started") {
    return `Turn ${event.turn}`;
  }
  return null;
}

export function toolCallLabel(event: DebateEvent): string | null {
  if (!isToolCallEvent(event)) {
    return null;
  }
  if (event.type === "tool_call_started") {
    return event.query
      ? `Searching Wikipedia: "${event.query}"`
      : "Searching Wikipedia…";
  }
  return event.query
    ? `Wikipedia: "${event.query}"`
    : "Wikipedia search complete";
}

export function isWaitingForTurnText(items: DisplayItem[]): boolean {
  const last = items[items.length - 1];
  if (last?.kind !== "event") {
    return false;
  }
  return (
    last.event.type === "turn_started" ||
    last.event.type === "tool_call_started" ||
    last.event.type === "tool_call_completed"
  );
}

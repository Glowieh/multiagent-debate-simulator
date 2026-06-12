export type Speaker = "Red" | "Green" | "summarizer";

export type DebateEvent =
  | { type: "debate_started"; topic: string }
  | { type: "turn_started"; speaker: "Red" | "Green"; turn: number }
  | { type: "message_chunk"; speaker: Speaker; content: string }
  | { type: "turn_completed"; speaker: "Red" | "Green"; turn: number }
  | {
      type: "tool_call_started";
      speaker: "Red" | "Green";
      tool: "wikipedia_search";
      query: string;
    }
  | {
      type: "tool_call_completed";
      speaker: "Red" | "Green";
      tool: "wikipedia_search";
      query: string;
    }
  | { type: "summary"; content: string }
  | { type: "debate_completed" }
  | { type: "error"; message: string };

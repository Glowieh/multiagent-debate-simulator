import { z } from "zod";

const DebaterSpeakerSchema = z.enum(["Red", "Green"]);

export const SpeakerSchema = z.enum(["Red", "Green", "summarizer"]);

const WikipediaToolSchema = z.literal("wikipedia_search");

export const DebateEventSchema = z.discriminatedUnion("type", [
  z.object({
    type: z.literal("debate_started"),
    topic: z.string(),
  }),
  z.object({
    type: z.literal("turn_started"),
    speaker: DebaterSpeakerSchema,
    turn: z.number(),
  }),
  z.object({
    type: z.literal("message_chunk"),
    speaker: SpeakerSchema,
    content: z.string(),
  }),
  z.object({
    type: z.literal("turn_completed"),
    speaker: DebaterSpeakerSchema,
    turn: z.number(),
  }),
  z.object({
    type: z.literal("tool_call_started"),
    speaker: DebaterSpeakerSchema,
    tool: WikipediaToolSchema,
    query: z.string(),
  }),
  z.object({
    type: z.literal("tool_call_completed"),
    speaker: DebaterSpeakerSchema,
    tool: WikipediaToolSchema,
    query: z.string(),
  }),
  z.object({
    type: z.literal("summary"),
    content: z.string(),
  }),
  z.object({
    type: z.literal("debate_completed"),
  }),
  z.object({
    type: z.literal("error"),
    message: z.string(),
  }),
]);

export type Speaker = z.infer<typeof SpeakerSchema>;
export type DebateEvent = z.infer<typeof DebateEventSchema>;

export function parseDebateEvent(data: unknown): DebateEvent {
  return DebateEventSchema.parse(data);
}

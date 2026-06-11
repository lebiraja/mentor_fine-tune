import { z } from 'zod';

// ---- WebSocket: server -> client ----

export const serverEventSchema = z.discriminatedUnion('type', [
  z.object({ type: z.literal('session'), session_id: z.string() }),
  z.object({
    type: z.literal('state'),
    state: z.enum(['listening', 'transcribing', 'generating', 'speaking']),
  }),
  z.object({ type: z.literal('user_transcript'), text: z.string() }),
  z.object({ type: z.literal('assistant_delta'), text: z.string() }),
  z.object({ type: z.literal('assistant_done'), text: z.string() }),
  z.object({ type: z.literal('interrupted') }),
  z.object({ type: z.literal('error'), message: z.string() }),
]);

export type ServerEvent = z.infer<typeof serverEventSchema>;
export type ConversationState =
  | 'idle'
  | 'connecting'
  | 'listening'
  | 'transcribing'
  | 'generating'
  | 'speaking';

// ---- REST ----

export const sessionSchema = z.object({
  id: z.string(),
  title: z.string(),
  created_at: z.string(),
  message_count: z.number(),
});

export const messageSchema = z.object({
  role: z.enum(['user', 'assistant']),
  content: z.string(),
  created_at: z.string(),
});

export const sessionsResponseSchema = z.object({ sessions: z.array(sessionSchema) });
export const messagesResponseSchema = z.object({
  session_id: z.string(),
  messages: z.array(messageSchema),
});

export type Session = z.infer<typeof sessionSchema>;
export type Message = z.infer<typeof messageSchema>;

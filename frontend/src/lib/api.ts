import {
  messagesResponseSchema,
  personasResponseSchema,
  sessionsResponseSchema,
  type Message,
  type Persona,
  type Session,
} from '@/types/protocol';

async function get(path: string): Promise<unknown> {
  const res = await fetch(`/api${path}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export const api = {
  async listPersonas(): Promise<Persona[]> {
    return personasResponseSchema.parse(await get('/personas')).personas;
  },

  async listSessions(): Promise<Session[]> {
    return sessionsResponseSchema.parse(await get('/sessions')).sessions;
  },

  async getMessages(sessionId: string): Promise<Message[]> {
    return messagesResponseSchema.parse(await get(`/sessions/${sessionId}/messages`)).messages;
  },

  async deleteSession(sessionId: string): Promise<void> {
    const res = await fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
  },
};

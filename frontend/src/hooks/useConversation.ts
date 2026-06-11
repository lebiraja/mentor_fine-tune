import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '@/lib/api';
import {
  serverEventSchema,
  type ConversationState,
  type Message,
} from '@/types/protocol';

const SESSION_KEY = 'clarity.session';

export interface ChatLine {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

interface Conversation {
  state: ConversationState;
  lines: ChatLine[];
  /** Assistant text currently streaming in (not yet in `lines`). */
  streaming: string;
  sessionId: string | null;
  error: string | null;
  connect: () => void;
  sendAudio: (pcm: ArrayBuffer) => void;
  sendText: (text: string) => void;
  setMuted: (muted: boolean) => void;
  switchSession: (sessionId: string | null) => Promise<void>;
}

interface ConversationCallbacks {
  onAudio: (pcm: ArrayBuffer) => void;
  onInterrupted: () => void;
}

let lineId = 0;
const nextId = () => `line-${++lineId}`;

export function useConversation({ onAudio, onInterrupted }: ConversationCallbacks): Conversation {
  const [state, setState] = useState<ConversationState>('idle');
  const [lines, setLines] = useState<ChatLine[]>([]);
  const [streaming, setStreaming] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectRef = useRef<number | undefined>(undefined);
  const callbacksRef = useRef({ onAudio, onInterrupted });
  callbacksRef.current = { onAudio, onInterrupted };
  const streamingRef = useRef('');

  const loadHistory = useCallback(async (id: string) => {
    try {
      const messages: Message[] = await api.getMessages(id);
      setLines(messages.map((m) => ({ id: nextId(), role: m.role, content: m.content })));
    } catch {
      setLines([]);
    }
  }, []);

  const connect = useCallback(() => {
    const existing = wsRef.current;
    if (existing && (existing.readyState === WebSocket.OPEN || existing.readyState === WebSocket.CONNECTING)) {
      return;
    }
    setState('connecting');

    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${proto}://${window.location.host}/ws/chat`);
    ws.binaryType = 'arraybuffer';
    wsRef.current = ws;

    ws.onopen = () => {
      setError(null);
      const saved = localStorage.getItem(SESSION_KEY);
      ws.send(JSON.stringify({ type: 'set_session', session_id: saved }));
    };

    ws.onmessage = (event: MessageEvent) => {
      if (event.data instanceof ArrayBuffer) {
        callbacksRef.current.onAudio(event.data);
        return;
      }
      const parsed = serverEventSchema.safeParse(JSON.parse(event.data as string));
      if (!parsed.success) return;
      const msg = parsed.data;

      switch (msg.type) {
        case 'session':
          setSessionId(msg.session_id);
          localStorage.setItem(SESSION_KEY, msg.session_id);
          void loadHistory(msg.session_id);
          break;
        case 'state':
          setState(msg.state);
          break;
        case 'user_transcript':
          setLines((prev) => [...prev, { id: nextId(), role: 'user', content: msg.text }]);
          break;
        case 'assistant_delta':
          streamingRef.current += msg.text;
          setStreaming(streamingRef.current);
          break;
        case 'assistant_done':
          streamingRef.current = '';
          setStreaming('');
          setLines((prev) => [...prev, { id: nextId(), role: 'assistant', content: msg.text }]);
          break;
        case 'interrupted':
          if (streamingRef.current) {
            const partial = streamingRef.current;
            setLines((prev) => [...prev, { id: nextId(), role: 'assistant', content: partial }]);
          }
          streamingRef.current = '';
          setStreaming('');
          callbacksRef.current.onInterrupted();
          break;
        case 'error':
          setError(msg.message);
          break;
      }
    };

    ws.onclose = () => {
      setState('idle');
      if (wsRef.current === ws) {
        reconnectRef.current = window.setTimeout(connect, 2000);
      }
    };
  }, [loadHistory]);

  useEffect(() => {
    return () => {
      clearTimeout(reconnectRef.current);
      const ws = wsRef.current;
      wsRef.current = null;
      ws?.close(1000);
    };
  }, []);

  const sendAudio = useCallback((pcm: ArrayBuffer) => {
    const ws = wsRef.current;
    if (ws?.readyState === WebSocket.OPEN) ws.send(pcm);
  }, []);

  const sendText = useCallback((text: string) => {
    const ws = wsRef.current;
    if (ws?.readyState === WebSocket.OPEN && text.trim()) {
      ws.send(JSON.stringify({ type: 'user_text', text: text.trim() }));
    }
  }, []);

  const setMuted = useCallback((muted: boolean) => {
    wsRef.current?.send(JSON.stringify({ type: 'mute', muted }));
  }, []);

  const switchSession = useCallback(
    async (id: string | null) => {
      streamingRef.current = '';
      setStreaming('');
      setLines([]);
      if (id) {
        localStorage.setItem(SESSION_KEY, id);
      } else {
        localStorage.removeItem(SESSION_KEY);
      }
      const ws = wsRef.current;
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'set_session', session_id: id }));
      }
    },
    []
  );

  return {
    state,
    lines,
    streaming,
    sessionId,
    error,
    connect,
    sendAudio,
    sendText,
    setMuted,
    switchSession,
  };
}

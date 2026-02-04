import type { EmotionData } from './api';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  emotion?: EmotionData;
  timestamp: Date;
  isAudio?: boolean;
}

export type ChatMode = 'text' | 'voice';

export interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  currentEmotion?: EmotionData;
  mode: ChatMode;
  sessionId?: string;
}

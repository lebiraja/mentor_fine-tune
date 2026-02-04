import { create } from 'zustand';
import type { ChatMessage, ChatMode } from '@/types/chat';
import type { EmotionData } from '@/types/api';

interface ChatStore {
  messages: ChatMessage[];
  mode: ChatMode;
  sessionId: string | null;
  currentEmotion: EmotionData | null;
  isProcessing: boolean;
  statusMessage: string;
  isRecording: boolean;

  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  setMode: (mode: ChatMode) => void;
  setSessionId: (sessionId: string) => void;
  setCurrentEmotion: (emotion: EmotionData) => void;
  setIsProcessing: (isProcessing: boolean) => void;
  setStatusMessage: (message: string) => void;
  setIsRecording: (isRecording: boolean) => void;
  clearMessages: () => void;
  loadHistory: (messages: ChatMessage[]) => void;
  removeLastMessage: () => void;
  updateLastMessage: (updates: Partial<ChatMessage>) => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  mode: 'text',
  sessionId: null,
  currentEmotion: null,
  isProcessing: false,
  statusMessage: '',
  isRecording: false,

  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          ...message,
          id: crypto.randomUUID(),
          timestamp: new Date(),
        },
      ],
    })),

  setMode: (mode) => set({ mode }),
  setSessionId: (sessionId) => set({ sessionId }),
  setCurrentEmotion: (emotion) => set({ currentEmotion: emotion }),
  setIsProcessing: (isProcessing) => set({ isProcessing }),
  setStatusMessage: (message) => set({ statusMessage: message }),
  setIsRecording: (isRecording) => set({ isRecording }),
  clearMessages: () =>
    set({ messages: [], currentEmotion: null, statusMessage: '' }),
  loadHistory: (messages) => set({ messages }),
  removeLastMessage: () =>
    set((state) => ({
      messages: state.messages.slice(0, -1),
    })),
  updateLastMessage: (updates) =>
    set((state) => {
      const lastIndex = state.messages.length - 1;
      if (lastIndex < 0) return state;

      const newMessages = [...state.messages];
      newMessages[lastIndex] = {
        ...newMessages[lastIndex],
        ...updates,
      };

      return { messages: newMessages };
    }),
}));

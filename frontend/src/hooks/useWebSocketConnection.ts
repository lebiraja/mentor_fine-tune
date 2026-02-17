import { useCallback } from 'react';
import { useWebSocket } from './useWebSocket';
import toast from 'react-hot-toast';
import type { WebSocketMessage, EmotionData } from '@/types/api';

interface UseWebSocketConnectionProps {
  onAudioResponse: (audioData: ArrayBuffer) => void;
  onTranscript: (text: string) => void;
  onResponse: (text: string, emotion?: EmotionData) => void;
  onEmotionUpdate: (emotion: EmotionData) => void;
  onStatusUpdate: (status: string) => void;
  onProcessingUpdate: (isProcessing: boolean) => void;
}

export function useWebSocketConnection({
  onAudioResponse,
  onTranscript,
  onResponse,
  onEmotionUpdate,
  onStatusUpdate,
  onProcessingUpdate,
}: UseWebSocketConnectionProps) {
  const WS_URL = import.meta.env.VITE_WS_URL || 
    `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}://${window.location.host}/ws/voice`;

  const handleWebSocketMessage = useCallback((message: WebSocketMessage | ArrayBuffer) => {
    if (message instanceof ArrayBuffer) {
      onAudioResponse(message);
      onProcessingUpdate(false);
      onStatusUpdate('');
      return;
    }

    switch (message.type) {
      case 'status':
        onStatusUpdate(message.message);
        break;
      case 'transcript':
        onTranscript(message.text);
        break;
      case 'emotion':
        onEmotionUpdate(message.data);
        break;
      case 'response':
        onResponse(message.text, message.data);
        break;
      case 'error':
        toast.error(message.message);
        onProcessingUpdate(false);
        onStatusUpdate('');
        break;
    }
  }, [onAudioResponse, onTranscript, onResponse, onEmotionUpdate, onStatusUpdate, onProcessingUpdate]);

  const { isConnected, sendAudio, disconnect, reconnect } = useWebSocket({
    url: WS_URL,
    autoConnect: false,
    onMessage: handleWebSocketMessage,
    onOpen: () => {
      console.log('Voice WebSocket connected');
      onStatusUpdate('Connected');
    },
    onClose: () => {
      console.log('Voice WebSocket disconnected');
      onStatusUpdate('');
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
      toast.error('Voice connection failed');
    },
  });

  return {
    isConnected,
    sendAudio,
    disconnect,
    reconnect
  };
}

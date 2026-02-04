import { useEffect, useRef, useState, useCallback } from 'react';
import type { WebSocketMessage } from '@/types/api';

interface UseWebSocketOptions {
  url: string;
  onMessage?: (message: WebSocketMessage | ArrayBuffer) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  autoConnect?: boolean;
}

export function useWebSocket({
  url,
  onMessage,
  onOpen,
  onClose,
  onError,
  autoConnect = true,
}: UseWebSocketOptions) {
  const ws = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [reconnectAttempt, setReconnectAttempt] = useState(0);
  const reconnectTimeoutRef = useRef<number | undefined>(undefined);

  const connect = useCallback(() => {
    try {
      if (ws.current?.readyState === WebSocket.OPEN) {
        return; // Already connected
      }

      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setReconnectAttempt(0);
        onOpen?.();
      };

      ws.current.onmessage = (event) => {
        if (event.data instanceof ArrayBuffer) {
          onMessage?.(event.data);
        } else {
          try {
            const message = JSON.parse(event.data) as WebSocketMessage;
            onMessage?.(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        }
      };

      ws.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        onClose?.();

        // Auto-reconnect with exponential backoff (max 30s)
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempt), 30000);
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log(`Reconnecting WebSocket (attempt ${reconnectAttempt + 1})...`);
          setReconnectAttempt((prev) => prev + 1);
        }, delay);
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        onError?.(error);
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
    }
  }, [url, onMessage, onOpen, onClose, onError, reconnectAttempt]);

  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      ws.current?.close();
    };
  }, [connect, reconnectAttempt, autoConnect]);

  const sendAudio = useCallback((audioData: ArrayBuffer) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(audioData);
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  const send = useCallback((message: Record<string, any>) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    ws.current?.close();
    setIsConnected(false);
  }, []);

  return {
    isConnected,
    sendAudio,
    send,
    disconnect,
    reconnect: connect,
    ws: ws.current,
  };
}

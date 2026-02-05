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
  const reconnectTimeoutRef = useRef<number | undefined>(undefined);
  const shouldReconnectRef = useRef(false);

  // Store callbacks in refs to avoid recreating connect on every render
  const onMessageRef = useRef(onMessage);
  const onOpenRef = useRef(onOpen);
  const onCloseRef = useRef(onClose);
  const onErrorRef = useRef(onError);

  // Update refs when callbacks change
  useEffect(() => {
    onMessageRef.current = onMessage;
    onOpenRef.current = onOpen;
    onCloseRef.current = onClose;
    onErrorRef.current = onError;
  }, [onMessage, onOpen, onClose, onError]);

  const connect = useCallback(() => {
    try {
      // Don't connect if already connected or connecting
      if (ws.current?.readyState === WebSocket.OPEN ||
          ws.current?.readyState === WebSocket.CONNECTING) {
        return;
      }

      // Clean up any existing connection
      if (ws.current) {
        ws.current.onclose = null;
        ws.current.onerror = null;
        ws.current.onmessage = null;
        ws.current.onopen = null;
        if (ws.current.readyState !== WebSocket.CLOSED) {
          ws.current.close();
        }
      }

      console.log('Creating new WebSocket connection to:', url);
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        shouldReconnectRef.current = true;
        onOpenRef.current?.();
      };

      ws.current.onmessage = (event) => {
        if (event.data instanceof ArrayBuffer) {
          onMessageRef.current?.(event.data);
        } else {
          try {
            const message = JSON.parse(event.data) as WebSocketMessage;
            onMessageRef.current?.(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        }
      };

      ws.current.onclose = (event) => {
        console.log('WebSocket disconnected, code:', event.code);
        setIsConnected(false);
        onCloseRef.current?.();

        // Only auto-reconnect if we were previously connected and didn't explicitly disconnect
        if (shouldReconnectRef.current && event.code !== 1000) {
          const delay = 2000;
          console.log(`Will attempt reconnection in ${delay}ms...`);
          reconnectTimeoutRef.current = window.setTimeout(() => {
            console.log('Attempting WebSocket reconnection...');
            connect();
          }, delay);
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        onErrorRef.current?.(error);
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
    }
  }, [url]); // Only depend on url, not callbacks

  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      shouldReconnectRef.current = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (ws.current) {
        ws.current.onclose = null; // Prevent reconnect on cleanup
        ws.current.close(1000, 'Component unmounted');
      }
    };
  }, [connect, autoConnect]);

  const sendAudio = useCallback((audioData: ArrayBuffer) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(audioData);
    } else {
      console.warn('WebSocket is not connected, state:', ws.current?.readyState);
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
    shouldReconnectRef.current = false;
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (ws.current) {
      ws.current.onclose = null; // Prevent auto-reconnect
      ws.current.close(1000, 'User disconnected');
      ws.current = null;
    }
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

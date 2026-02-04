// Emotion Types
export type EmotionType =
  | 'neutral'
  | 'joy'
  | 'sadness'
  | 'anger'
  | 'fear'
  | 'surprise'
  | 'confused'
  | 'disgust';

export interface EmotionData {
  primary_emotion: EmotionType;
  confidence: number;
  scores: Record<string, number>;
  source_agreement?: number;
}

// WebSocket Messages
export interface StatusMessage {
  type: 'status';
  message: string;
}

export interface TranscriptMessage {
  type: 'transcript';
  text: string;
}

export interface EmotionMessage {
  type: 'emotion';
  data: EmotionData;
}

export interface ResponseMessage {
  type: 'response';
  text: string;
  data?: EmotionData;
}

export interface ErrorMessage {
  type: 'error';
  message: string;
}

export type WebSocketMessage =
  | StatusMessage
  | TranscriptMessage
  | EmotionMessage
  | ResponseMessage
  | ErrorMessage;

// REST API Types
export interface HealthResponse {
  status: string;
  models_loaded: boolean;
  timestamp: string;
}

export interface SessionResponse {
  session_id: string;
  created_at: string;
}

export interface ConversationTurn {
  role: 'user' | 'assistant';
  content: string;
  emotion?: EmotionData;
  timestamp: string;
}

export interface SessionHistoryResponse {
  session_id: string;
  created_at: string;
  turns: ConversationTurn[];
  emotion_timeline: Array<{
    timestamp: string;
    emotion: EmotionData;
  }>;
}

export interface TextChatRequest {
  text: string;
  session_id?: string;
}

export interface TextChatResponse {
  session_id: string;
  response: string;
  emotion: EmotionData;
}

export interface ErrorResponse {
  error: string;
  details?: string;
  timestamp: string;
}

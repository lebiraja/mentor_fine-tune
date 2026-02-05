import { useState, useEffect, useRef, useCallback } from 'react';
import { GlassCard } from './components/ui/glass-card';
import { GlassButton } from './components/ui/glass-button';
import { GlassInput } from './components/ui/glass-input';
import { api } from './lib/api';
import { useWebSocket } from './hooks/useWebSocket';
import { Toaster } from 'react-hot-toast';
import toast from 'react-hot-toast';
import type { ChatMessage } from './types/chat';
import type { WebSocketMessage, EmotionData } from './types/api';
import { Mic, MicOff, Send, Volume2, VolumeX, MessageSquare, Radio } from 'lucide-react';

const WS_URL = import.meta.env.VITE_WS_URL || (window.location.protocol === 'http:' ? `ws://${window.location.host}/ws/voice` : 'ws://localhost:2323/ws/voice');

function App() {
  const [isHealthy, setIsHealthy] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<'landing' | 'chat'>('landing');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStarting, setIsStarting] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  
  // Voice mode state
  const [mode, setMode] = useState<'text' | 'voice'>('text');
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [currentEmotion, setCurrentEmotion] = useState<EmotionData | null>(null);
  const [isMuted, setIsMuted] = useState(false);
  
  // Audio refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);
  const isMutedRef = useRef(false);

  // Sync muted state to ref
  useEffect(() => {
    isMutedRef.current = isMuted;
  }, [isMuted]);

  // Ref to track latest emotion for message handler
  const currentEmotionRef = useRef<EmotionData | null>(null);
  useEffect(() => {
    currentEmotionRef.current = currentEmotion;
  }, [currentEmotion]);

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((message: WebSocketMessage | ArrayBuffer) => {
    if (message instanceof ArrayBuffer) {
      // Check muted via ref since this callback is memoized
      if (!isMutedRef.current) {
        playAudioResponse(message);
      }
      setIsProcessing(false);
      setStatusMessage('');
      return;
    }

    switch (message.type) {
      case 'status':
        setStatusMessage(message.message);
        break;
      case 'transcript':
        addMessage('user', message.text);
        break;
      case 'emotion':
        setCurrentEmotion(message.data);
        currentEmotionRef.current = message.data;
        break;
      case 'response':
        // Use ref to get latest emotion since state may not have updated yet
        addMessage('assistant', message.text, currentEmotionRef.current || undefined);
        break;
      case 'error':
        toast.error(message.message);
        setIsProcessing(false);
        setStatusMessage('');
        break;
    }
  }, []);

  // WebSocket connection for voice mode
  const { isConnected, sendAudio, disconnect, reconnect } = useWebSocket({
    url: WS_URL,
    autoConnect: false,
    onMessage: handleWebSocketMessage,
    onOpen: () => {
      console.log('Voice WebSocket connected');
      setStatusMessage('Connected');
    },
    onClose: () => {
      console.log('Voice WebSocket disconnected');
      setStatusMessage('');
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
      toast.error('Voice connection failed');
    },
  });

  // Initialize audio context
  useEffect(() => {
    audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    return () => {
      audioContextRef.current?.close();
    };
  }, []);

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const health = await api.health();
        setIsHealthy(health.status === 'healthy');
        setError(null);
      } catch (err) {
        setIsHealthy(false);
        setError('Backend offline. Start it with: ./run_backend.sh');
      } finally {
        setIsLoading(false);
      }
    };

    checkBackend();
    const interval = setInterval(checkBackend, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Connect/disconnect WebSocket when mode changes
  useEffect(() => {
    if (mode === 'voice' && view === 'chat') {
      // Only connect if not already connected
      if (!isConnected) {
        console.log('Voice mode activated, connecting WebSocket...');
        reconnect();
      }
    } else if (mode === 'text') {
      disconnect();
    }
  }, [mode, view, isConnected, reconnect, disconnect]);

  function addMessage(role: 'user' | 'assistant', content: string, emotion?: EmotionData) {
    setMessages((prev) => [...prev, {
      id: crypto.randomUUID(),
      role,
      content,
      emotion,
      timestamp: new Date(),
    }]);
  }

  async function playAudioResponse(audioData: ArrayBuffer) {
    if (!audioContextRef.current) return;

    try {
      const audioBuffer = await audioContextRef.current.decodeAudioData(audioData.slice(0));
      const source = audioContextRef.current.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContextRef.current.destination);
      source.start(0);
    } catch (error) {
      console.error('Audio playback error:', error);
      try {
        const audioBuffer = audioContextRef.current.createBuffer(1, audioData.byteLength / 2, 16000);
        const channelData = audioBuffer.getChannelData(0);
        const view = new Int16Array(audioData);
        for (let i = 0; i < view.length; i++) {
          channelData[i] = view[i] / 32768.0;
        }
        const source = audioContextRef.current.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContextRef.current.destination);
        source.start(0);
      } catch (fallbackError) {
        console.error('Fallback audio failed:', fallbackError);
      }
    }
  }

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
      });

      audioChunksRef.current = [];
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await processAudioBlob(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
      toast.success('Recording... Speak now');
    } catch (error) {
      console.error('Failed to start recording:', error);
      toast.error('Microphone access denied');
    }
  }

  function stopRecording() {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsProcessing(true);
      setStatusMessage('Processing...');
    }
  }

  async function processAudioBlob(blob: Blob) {
    try {
      const arrayBuffer = await blob.arrayBuffer();
      const audioContext = new AudioContext();
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
      
      const offlineContext = new OfflineAudioContext(1, audioBuffer.duration * 16000, 16000);
      const source = offlineContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(offlineContext.destination);
      source.start(0);
      
      const resampled = await offlineContext.startRendering();
      const pcmData = resampled.getChannelData(0);
      
      const int16Array = new Int16Array(pcmData.length);
      for (let i = 0; i < pcmData.length; i++) {
        const s = Math.max(-1, Math.min(1, pcmData[i]));
        int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
      }
      
      sendAudio(int16Array.buffer);
    } catch (error) {
      console.error('Failed to process audio:', error);
      toast.error('Failed to process audio');
      setIsProcessing(false);
      setStatusMessage('');
    }
  }

  const handleStart = async () => {
    if (!isHealthy || isStarting) return;
    setIsStarting(true);
    try {
      const session = await api.createSession();
      setSessionId(session.session_id);
      setView('chat');
      toast.success('Session started');
    } catch (err) {
      toast.error('Failed to start session');
    } finally {
      setIsStarting(false);
    }
  };

  const handleSend = async () => {
    const text = input.trim();
    if (!text || isSending) return;

    addMessage('user', text);
    setInput('');
    setIsSending(true);

    try {
      const response = await api.sendTextMessage({
        text,
        session_id: sessionId ?? undefined,
      });

      if (!sessionId) {
        setSessionId(response.session_id);
      }

      addMessage('assistant', response.response, response.emotion);
      setCurrentEmotion(response.emotion);
    } catch (err) {
      toast.error('Failed to send message');
      addMessage('assistant', 'I had trouble responding. Please try again.');
    } finally {
      setIsSending(false);
    }
  };

  const handleReset = () => {
    setMessages([]);
    setSessionId(null);
    setView('landing');
    setMode('text');
    setCurrentEmotion(null);
    disconnect();
  };

  const toggleMode = () => {
    setMode(mode === 'text' ? 'voice' : 'text');
  };

  const handleVoiceToggle = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const getEmotionEmoji = (emotion?: EmotionData) => {
    if (!emotion) return '😐';
    switch (emotion.primary_emotion) {
      case 'joy': return '😊';
      case 'sadness': return '😢';
      case 'anger': return '😠';
      case 'fear': return '😨';
      case 'surprise': return '😲';
      case 'disgust': return '🤢';
      case 'confused': return '😕';
      default: return '😐';
    }
  };

  const isCtaDisabled = !isHealthy || isLoading || isStarting;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-900 to-purple-900">
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob" />
        <div className="absolute top-40 right-20 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-2000" />
        <div className="absolute -bottom-8 left-1/2 w-96 h-96 bg-pink-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-4000" />
      </div>

      <div className="relative flex items-center justify-center min-h-screen p-4">
        {view === 'landing' ? (
          <GlassCard className="w-full max-w-xl p-10 space-y-8 backdrop-blur-2xl bg-white/10 border border-white/20">
            <div className="text-center space-y-4">
              <div className="flex justify-center mb-4">
                <div className="relative">
                  <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-400 to-purple-600 flex items-center justify-center">
                    <Radio className="w-10 h-10 text-white" />
                  </div>
                  <div className={`absolute -bottom-1 -right-1 w-6 h-6 rounded-full border-4 border-slate-900 ${isHealthy ? 'bg-green-500' : 'bg-red-500'} ${isLoading ? 'animate-pulse' : ''}`} />
                </div>
              </div>
              <h1 className="text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400">
                ClarityMentor
              </h1>
              <p className="text-xl text-slate-300 font-light">
                AI-Powered Mental Health Companion
              </p>
            </div>

            <div className="space-y-3">
              <div
                className={`flex items-center justify-center space-x-3 p-4 rounded-xl border ${
                  isLoading
                    ? 'bg-blue-500/20 border-blue-500/30'
                    : isHealthy
                      ? 'bg-green-500/20 border-green-500/30'
                      : 'bg-red-500/20 border-red-500/30'
                }`}
              >
                <div
                  className={`w-3 h-3 rounded-full ${
                    isLoading
                      ? 'bg-blue-400 animate-pulse'
                      : isHealthy
                        ? 'bg-green-400'
                        : 'bg-red-400 animate-pulse'
                  }`}
                />
                <p className="text-sm font-semibold text-white">
                  {isLoading ? 'Checking backend...' : isHealthy ? 'Backend Online' : 'Backend Offline'}
                </p>
              </div>
              {error && (
                <p className="text-sm text-red-400 text-center px-4">
                  {error}
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-white/5 border border-white/10 backdrop-blur-sm">
                <div className="flex items-center space-x-3 mb-2">
                  <MessageSquare className="w-5 h-5 text-blue-400" />
                  <h3 className="font-semibold text-white">Text Chat</h3>
                </div>
                <p className="text-sm text-slate-300">Natural conversation interface</p>
              </div>
              <div className="p-4 rounded-xl bg-white/5 border border-white/10 backdrop-blur-sm">
                <div className="flex items-center space-x-3 mb-2">
                  <Mic className="w-5 h-5 text-purple-400" />
                  <h3 className="font-semibold text-white">Voice Mode</h3>
                </div>
                <p className="text-sm text-slate-300">Real-time voice chat</p>
              </div>
              <div className="p-4 rounded-xl bg-white/5 border border-white/10 backdrop-blur-sm">
                <div className="flex items-center space-x-3 mb-2">
                  <span className="text-xl">😊</span>
                  <h3 className="font-semibold text-white">Emotion AI</h3>
                </div>
                <p className="text-sm text-slate-300">Detects your feelings</p>
              </div>
              <div className="p-4 rounded-xl bg-white/5 border border-white/10 backdrop-blur-sm">
                <div className="flex items-center space-x-3 mb-2">
                  <span className="text-xl">🔒</span>
                  <h3 className="font-semibold text-white">Private</h3>
                </div>
                <p className="text-sm text-slate-300">Your data stays secure</p>
              </div>
            </div>

            <GlassButton
              disabled={isCtaDisabled}
              isLoading={isStarting}
              className="w-full py-4 text-lg font-semibold bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 hover:from-blue-600 hover:via-purple-600 hover:to-pink-600 text-white shadow-xl"
              onClick={handleStart}
            >
              {isLoading ? 'Initializing...' : isHealthy ? 'Start Conversation' : 'Waiting for Backend'}
            </GlassButton>

            <div className="text-center text-xs text-slate-400 space-y-1 pt-4 border-t border-white/10">
              <p>Powered by ClarityMentor AI • Port 2323</p>
              <p className="text-[10px]">Voice-to-Voice • Emotion Detection • Real-time Response</p>
            </div>
          </GlassCard>
        ) : (
          <GlassCard className="w-full max-w-5xl p-6 space-y-4 backdrop-blur-2xl bg-white/10 border border-white/20">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center gap-4">
                <div>
                  <h2 className="text-2xl font-bold text-white">ClarityMentor</h2>
                  <p className="text-sm text-slate-300">
                    Session {sessionId ? sessionId.slice(0, 8) : 'pending'}
                  </p>
                </div>
                
                {currentEmotion && (
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 border border-white/20">
                    <span className="text-xl">{getEmotionEmoji(currentEmotion)}</span>
                    <span className="text-xs text-white font-medium capitalize">
                      {currentEmotion.primary_emotion}
                    </span>
                    <span className="text-xs text-slate-300">
                      {Math.round(currentEmotion.confidence * 100)}%
                    </span>
                  </div>
                )}
              </div>

              <div className="flex items-center gap-2 flex-wrap">
                <div className="flex items-center gap-1 p-1 rounded-lg bg-white/5 border border-white/10">
                  <button
                    onClick={() => setMode('text')}
                    className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                      mode === 'text'
                        ? 'bg-blue-500 text-white'
                        : 'text-slate-300 hover:text-white'
                    }`}
                  >
                    <MessageSquare className="w-4 h-4 inline mr-1" />
                    Text
                  </button>
                  <button
                    onClick={toggleMode}
                    className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                      mode === 'voice'
                        ? 'bg-purple-500 text-white'
                        : 'text-slate-300 hover:text-white'
                    }`}
                  >
                    <Mic className="w-4 h-4 inline mr-1" />
                    Voice
                  </button>
                </div>

                {mode === 'voice' && (
                  <GlassButton
                    variant="ghost"
                    size="icon"
                    onClick={() => setIsMuted(!isMuted)}
                    className="border border-white/10 text-white"
                  >
                    {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
                  </GlassButton>
                )}

                <GlassButton variant="danger" onClick={handleReset} size="sm">
                  End Session
                </GlassButton>
              </div>
            </div>

            {mode === 'voice' && (
              <div className="flex items-center justify-between px-4 py-2 rounded-lg bg-white/5 border border-white/10">
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'} animate-pulse`} />
                  <span className="text-sm text-slate-300">
                    {isConnected ? 'Voice Connected' : 'Connecting...'}
                  </span>
                </div>
                {statusMessage && (
                  <span className="text-sm text-blue-400 animate-pulse">{statusMessage}</span>
                )}
              </div>
            )}

            <div className="h-[55vh] overflow-y-auto rounded-xl bg-black/20 backdrop-blur-sm p-4 space-y-4 border border-white/10">
              {messages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center space-y-4">
                  <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                    {mode === 'voice' ? (
                      <Mic className="w-8 h-8 text-white" />
                    ) : (
                      <MessageSquare className="w-8 h-8 text-white" />
                    )}
                  </div>
                  <div>
                    <p className="text-lg text-white font-medium mb-2">
                      {mode === 'voice' ? 'Ready to listen' : 'Start your conversation'}
                    </p>
                    <p className="text-sm text-slate-400 max-w-md">
                      {mode === 'voice'
                        ? 'Click the microphone button below and speak. I\'ll listen, understand your emotions, and respond with voice.'
                        : 'Share what\'s on your mind. I\'m here to listen and help.'}
                    </p>
                  </div>
                </div>
              ) : (
                messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${
                      message.role === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    <div
                      className={`max-w-[75%] rounded-2xl px-4 py-3 space-y-2 ${
                        message.role === 'user'
                          ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white'
                          : 'bg-white/10 backdrop-blur-md text-white border border-white/20'
                      }`}
                    >
                      <p className="text-sm leading-relaxed">{message.content}</p>
                      {message.emotion && (
                        <div className="flex items-center gap-2 text-xs opacity-75">
                          <span>{getEmotionEmoji(message.emotion)}</span>
                          <span className="capitalize">{message.emotion.primary_emotion}</span>
                          <span>·</span>
                          <span>{Math.round(message.emotion.confidence * 100)}%</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {mode === 'text' ? (
              <div className="flex items-center gap-3">
                <GlassInput
                  placeholder="Type your message..."
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' && !event.shiftKey) {
                      event.preventDefault();
                      handleSend();
                    }
                  }}
                  disabled={isSending}
                  className="bg-white/5 border-white/10 text-white placeholder:text-slate-400"
                />
                <GlassButton
                  onClick={handleSend}
                  isLoading={isSending}
                  disabled={isSending || input.trim().length === 0}
                  className="px-6 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600"
                >
                  <Send className="w-4 h-4 mr-2" />
                  Send
                </GlassButton>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-4">
                <div className="flex items-center gap-6">
                  <button
                    onClick={handleVoiceToggle}
                    disabled={isProcessing}
                    className={`relative w-20 h-20 rounded-full flex items-center justify-center transition-all transform hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed ${
                      isRecording
                        ? 'bg-red-500 shadow-2xl shadow-red-500/50 animate-pulse'
                        : 'bg-gradient-to-br from-blue-500 to-purple-600 shadow-xl shadow-purple-500/30'
                    }`}
                  >
                    {isRecording ? (
                      <MicOff className="w-8 h-8 text-white" />
                    ) : (
                      <Mic className="w-8 h-8 text-white" />
                    )}
                    
                    {isRecording && (
                      <>
                        <span className="absolute inset-0 rounded-full bg-red-500 animate-ping opacity-30" />
                        <span className="absolute inset-0 rounded-full bg-red-500 animate-pulse opacity-50" />
                      </>
                    )}
                  </button>
                </div>

                <div className="text-center">
                  <p className="text-sm font-medium text-white">
                    {isRecording
                      ? 'Recording... Click to stop'
                      : isProcessing
                        ? 'Processing your voice...'
                        : 'Click to start speaking'}
                  </p>
                  {isProcessing && (
                    <p className="text-xs text-slate-400 mt-1">
                      This may take a few seconds
                    </p>
                  )}
                </div>
              </div>
            )}
          </GlassCard>
        )}
      </div>

      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: 'rgba(30, 41, 59, 0.9)',
            backdropFilter: 'blur(10px)',
            color: '#fff',
            border: '1px solid rgba(255, 255, 255, 0.1)',
          },
        }}
      />
    </div>
  );
}

export default App;

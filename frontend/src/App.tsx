import { useState, useEffect } from 'react';
import toast, { Toaster } from 'react-hot-toast';
import { api } from './lib/api';
import { useAudioRecording } from './hooks/useAudioRecording';
import { useVoiceProcessing } from './hooks/useVoiceProcessing';
import { useWebSocketConnection } from './hooks/useWebSocketConnection';
import { RootLayout } from './components/layout/RootLayout';
import { Sidebar } from './components/layout/Sidebar';
import { ChatInterface } from './components/chat/ChatInterface';
import { VoiceMode } from './components/voice/VoiceMode';
import { EmotionDashboard } from './components/emotion/EmotionDashboard';
import { LandingPage } from './components/layout/LandingPage';
import type { ChatMessage } from './types/chat';
import type { EmotionData } from './types/api';

function App() {
  // --- State ---
  const [view, setView] = useState<'landing' | 'chat' | 'voice'>('landing');
  const [isHealthy, setIsHealthy] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStarting, setIsStarting] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [currentEmotion, setCurrentEmotion] = useState<EmotionData | null>(null);
  const [statusMessage, setStatusMessage] = useState('');
  const [isMuted, setIsMuted] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);

  // --- Hooks ---
  const { playAudioResponse, setMuted: setVoiceMuted, isPlaying } = useVoiceProcessing();

  const {
    isRecording,
    isProcessing: isRecordingProcessing,
    stopRecording,
    toggleRecording
  } = useAudioRecording({
    onAudioData: (data) => {
      if (isConnected) {
        sendAudio(data);
      } else {
        toast.error('Voice connection lost'); // removed unused toast import? No, I see imports.
      }
    }
  });

  const { isConnected, sendAudio, reconnect } = useWebSocketConnection({
    onAudioResponse: playAudioResponse,
    onTranscript: (text) => addMessage('user', text),
    onResponse: (text, emotion) => {
      addMessage('assistant', text, emotion);
      if (emotion) setCurrentEmotion(emotion);
    },
    onEmotionUpdate: (emotion) => setCurrentEmotion(emotion),
    onStatusUpdate: setStatusMessage,
    onProcessingUpdate: () => { /* handled by local state if needed */ }
  });

  // --- Effects ---

  // Backend Health Check
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

  // Sync mute state
  useEffect(() => {
    setVoiceMuted(isMuted);
  }, [isMuted, setVoiceMuted]);

  // Handle View/Mode Switching
  useEffect(() => {
    if (view === 'voice') {
      if (!isConnected) reconnect();
    } else {
      // Optional: disconnect if moving away from voice view?
      // Keeping it connected might be better for seamless switching.
      if (isRecording) stopRecording();
    }
  }, [view, isConnected, reconnect, isRecording, stopRecording]);


  // --- Handlers ---

  const addMessage = (role: 'user' | 'assistant', content: string, emotion?: EmotionData) => {
    setMessages((prev) => [...prev, {
      id: crypto.randomUUID(),
      role,
      content,
      emotion,
      timestamp: new Date(),
    }]);
  };

  const handleStartSession = async () => {
    if (!isHealthy || isStarting) return;
    setIsStarting(true);
    try {
      const session = await api.createSession();
      setSessionId(session.session_id);
      setView('chat');
      toast.success('Session started'); // toast is imported
    } catch (err) {
      toast.error('Failed to start session');
    } finally {
      setIsStarting(false);
    }
  };

  const handleSendMessage = async () => {
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

      if (!sessionId) setSessionId(response.session_id);

      addMessage('assistant', response.response, response.emotion);
      setCurrentEmotion(response.emotion);
    } catch (err) {
      toast.error('Failed to send message');
      addMessage('assistant', 'I had trouble responding. Please try again.');
    } finally {
      setIsSending(false);
    }
  };

  // Mock audio level for visualization (real implementation would use AnalyserNode)
  useEffect(() => {
    if (isRecording || isPlaying) {
      const interval = setInterval(() => {
        setAudioLevel(Math.random() * 0.5 + 0.3);
      }, 100);
      return () => clearInterval(interval);
    } else {
      setAudioLevel(0);
    }
  }, [isRecording, isPlaying]);


  // --- Render ---

  if (view === 'landing') {
    return (
      <RootLayout>
         <LandingPage
            onConnect={handleStartSession}
            isHealthy={isHealthy}
            isLoading={isLoading}
            isStarting={isStarting}
            error={error}
         />
         <Toaster position="top-right" toastOptions={{
             className: '!bg-slate-900 !text-white !border !border-white/10',
         }} />
      </RootLayout>
    );
  }

  return (
    <RootLayout>
      <div className="flex h-[85vh] gap-6 relative">
        {/* Sidebar Navigation */}
        <div className="hidden md:flex h-full">
             <Sidebar
               currentView={view}
               setCurrentView={setView}
             />
        </div>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col relative min-w-0">
          {view === 'chat' ? (
            <ChatInterface
              messages={messages}
              input={input}
              setInput={setInput}
              onSend={handleSendMessage}
              isSending={isSending}
              isRecording={isRecording}
              onToggleVoice={() => setView('voice')}
              isLoading={isSending} // repurposed loading state
            />
          ) : (
            <VoiceMode
              isRecording={isRecording}
              isProcessing={isRecordingProcessing || (!isRecording && isPlaying)} // simplified processing state
              isPlaying={isPlaying}
              onToggleRecording={toggleRecording}
              isMuted={isMuted}
              onToggleMute={() => setIsMuted(!isMuted)}
              statusMessage={statusMessage}
              audioLevel={audioLevel}
            />
          )}
        </div>

        {/* Right Sidebar: Emotion Dashboard (Desktop) */}
        <div className="hidden lg:block w-80">
          <EmotionDashboard currentEmotion={currentEmotion} />
        </div>
      </div>

      <Toaster position="top-right" toastOptions={{
         className: '!bg-slate-900 !text-white !border !border-white/10',
      }} />
    </RootLayout>
  );
}

export default App;

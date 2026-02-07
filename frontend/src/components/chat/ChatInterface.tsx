import React, { useRef, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Mic, MessageSquare } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ChatMessage } from '@/types/chat';
import type { EmotionData } from '@/types/api';
import { motion, AnimatePresence } from 'framer-motion';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  input: string;
  setInput: (value: string) => void;
  onSend: () => void;
  isSending: boolean;
  isRecording: boolean;
  onToggleVoice: () => void;
  isLoading?: boolean;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  input,
  setInput,
  onSend,
  isSending,
  isRecording,
  onToggleVoice,
  isLoading = false,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  const getEmotionEmoji = (emotion?: EmotionData) => {
    if (!emotion) return null;
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

  return (
    <Card className="flex flex-col h-[70vh] md:h-[80vh] w-full max-w-4xl mx-auto glass-panel overflow-hidden relative">
      <div className="flex items-center justify-between p-4 border-b border-white/10 bg-white/5 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-primary/20 text-primary">
            <MessageSquare className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-display font-semibold text-lg text-white">ClarityMentor</h2>
            <p className="text-xs text-muted-foreground">AI Mental Health Companion</p>
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleVoice}
          className={cn(
            "rounded-full w-10 h-10 transition-all",
            isRecording ? "bg-red-500/20 text-red-500 hover:bg-red-500/30" : "hover:bg-white/10 text-muted-foreground hover:text-white"
          )}
        >
          <Mic className={cn("w-5 h-5", isRecording && "animate-pulse")} />
        </Button>
      </div>

      <ScrollArea className="flex-1 p-4">
        <div className="space-y-6 pb-4">
          <AnimatePresence initial={false}>
            {messages.length === 0 ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                className="h-full flex flex-col items-center justify-center text-center space-y-4 opacity-50 min-h-[400px]"
              >
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center backdrop-blur-sm border border-white/10">
                  <MessageSquare className="w-8 h-8 text-white/50" />
                </div>
                <p className="text-lg font-medium text-white/70">Start a conversation</p>
                <p className="text-sm text-muted-foreground max-w-xs">
                  I'm here to listen. Share what's on your mind.
                </p>
              </motion.div>
            ) : (
              messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 20, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  transition={{ duration: 0.3 }}
                  className={cn(
                    "flex w-full",
                    message.role === 'user' ? "justify-end" : "justify-start"
                  )}
                >
                  <div
                    className={cn(
                      "max-w-[80%] md:max-w-[70%] rounded-2xl px-5 py-3 shadow-lg backdrop-blur-sm transition-all duration-300",
                      message.role === 'user'
                        ? "bg-primary/20 text-white border border-primary/30 rounded-tr-sm"
                        : "bg-white/10 text-white border border-white/10 rounded-tl-sm"
                    )}
                  >
                    <p className="leading-relaxed text-sm md:text-base">{message.content}</p>
                    {message.emotion && (
                      <div className="mt-2 flex items-center gap-2 text-xs opacity-60 font-medium">
                        <span>{getEmotionEmoji(message.emotion)}</span>
                        <span className="capitalize">{message.emotion.primary_emotion}</span>
                        <span className="w-1 h-1 rounded-full bg-white/30" />
                        <span>{Math.round(message.emotion.confidence * 100)}%</span>
                      </div>
                    )}
                  </div>
                </motion.div>
              ))
            )}
          </AnimatePresence>
          {isLoading && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
            >
              <div className="bg-white/5 border border-white/10 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </motion.div>
          )}
        </div>
        <div ref={messagesEndRef} />
      </ScrollArea>

      <div className="p-4 border-t border-white/10 bg-white/5 backdrop-blur-md">
        <div className="flex items-center gap-3 relative">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
            disabled={isSending}
            className="glass-input pr-12 text-white placeholder:text-muted-foreground/50 border-white/10 focus:border-primary/50"
          />
          <Button
            size="icon"
            variant="default"
            onClick={onSend}
            disabled={!input.trim() || isSending}
            className="absolute right-0 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full shadow-[0_0_10px_rgba(255,0,204,0.3)] hover:shadow-[0_0_20px_rgba(255,0,204,0.5)]"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </Card>
  );
};

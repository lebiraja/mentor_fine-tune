import React, { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Mic, MicOff, Volume2, VolumeX } from 'lucide-react';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';

interface VoiceModeProps {
  isRecording: boolean;
  isProcessing: boolean;
  isPlaying: boolean;
  onToggleRecording: () => void;
  isMuted: boolean;
  onToggleMute: () => void;
  statusMessage?: string;
  audioLevel?: number; // 0-1
}

export const VoiceMode: React.FC<VoiceModeProps> = ({
  isRecording,
  isProcessing,
  isPlaying,
  onToggleRecording,
  isMuted,
  onToggleMute,
  statusMessage,
  audioLevel = 0,
}) => {
  const [visualLevel, setVisualLevel] = useState(0);

  // Smooth out audio level visualization
  useEffect(() => {
    const target = isRecording || isPlaying ? Math.max(0.2, audioLevel) : 0.1;
    const interval = setInterval(() => {
      setVisualLevel(prev => {
        const diff = target - prev;
        return prev + diff * 0.1;
      });
    }, 16);
    return () => clearInterval(interval);
  }, [audioLevel, isRecording, isPlaying]);

  return (
    <Card className="flex flex-col items-center justify-center h-[70vh] md:h-[80vh] w-full max-w-4xl mx-auto glass-panel relative overflow-hidden p-8">

      {/* Dynamic Background Glow */}
      <motion.div
        className={cn(
          "absolute inset-0 transition-colors duration-1000",
          isRecording ? "bg-primary/20" :
          isProcessing ? "bg-secondary/20" :
          isPlaying ? "bg-accent/20" : "bg-transparent"
        )}
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.3 }}
      />

      <div className="relative z-10 flex flex-col items-center gap-12">

        {/* Main Orb Visualization */}
        <div className="relative">
          {/* Outer Glow Rings */}
          <motion.div
            className={cn(
              "absolute inset-0 rounded-full blur-3xl",
              isRecording ? "bg-red-500/40" :
              isProcessing ? "bg-blue-500/40" :
              isPlaying ? "bg-purple-500/40" : "bg-white/5"
            )}
            animate={{
              scale: 1 + visualLevel * 2,
              opacity: [0.5, 0.8, 0.5]
            }}
            transition={{
              scale: { duration: 0.1, ease: "linear" },
              opacity: { duration: 2, repeat: Infinity }
            }}
          />

          {/* Core Orb */}
          <motion.div
            className={cn(
              "w-48 h-48 rounded-full flex items-center justify-center shadow-2xl border border-white/10 backdrop-blur-md",
              isRecording ? "bg-gradient-to-br from-red-500/80 to-orange-600/80" :
              isProcessing ? "bg-gradient-to-br from-blue-500/80 to-cyan-600/80" :
              isPlaying ? "bg-gradient-to-br from-purple-500/80 to-pink-600/80" :
              "bg-white/10"
            )}
            animate={{
              boxShadow: `0 0 ${20 + visualLevel * 50}px rgba(255,255,255,0.2)`,
              scale: isRecording || isPlaying ? [1, 1.05, 1] : 1
            }}
            transition={{
              boxShadow: { duration: 0.1 },
              scale: { duration: 2, repeat: Infinity, ease: "easeInOut" }
            }}
          >
            <AnimatePresence mode="wait">
              {isRecording ? (
                <motion.div
                  key="mic"
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0, opacity: 0 }}
                >
                  <Mic className="w-16 h-16 text-white drop-shadow-lg" />
                </motion.div>
              ) : isProcessing ? (
                <motion.div
                  key="processing"
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0, opacity: 0 }}
                >
                   <div className="w-12 h-12 border-4 border-white border-t-transparent rounded-full animate-spin" />
                </motion.div>
              ) : isPlaying ? (
                <motion.div
                  key="playing"
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0, opacity: 0 }}
                >
                  <Volume2 className="w-16 h-16 text-white drop-shadow-lg" />
                </motion.div>
              ) : (
                <motion.div
                  key="idle"
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0, opacity: 0 }}
                >
                  <MicOff className="w-16 h-16 text-white/50" />
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>

        {/* Status Text */}
        <div className="text-center space-y-2 h-20">
          <motion.h2
            key={isRecording ? "listening" : isProcessing ? "processing" : isPlaying ? "speaking" : "ready"}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-3xl font-display font-bold text-white tracking-tight"
          >
            {isRecording ? "Listening..." :
             isProcessing ? "Thinking..." :
             isPlaying ? "Speaking..." : "Ready"}
          </motion.h2>
          <motion.p
            className="text-muted-foreground text-lg"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            {statusMessage || (isRecording ? "I'm listening to you" : "Tap the mic to start")}
          </motion.p>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-6">
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggleMute}
            className="w-14 h-14 rounded-full glass-button hover:bg-white/20"
          >
            {isMuted ? <VolumeX className="w-6 h-6" /> : <Volume2 className="w-6 h-6" />}
          </Button>

          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Button
              size="icon"
              onClick={onToggleRecording}
              className={cn(
                "w-20 h-20 rounded-full shadow-xl border-4 transition-colors duration-300",
                isRecording
                  ? "bg-red-500 hover:bg-red-600 border-red-300/30 shadow-red-500/30"
                  : "bg-primary hover:bg-primary/90 border-white/20 shadow-primary/30"
              )}
            >
              <AnimatePresence mode="wait">
                {isRecording ? (
                  <motion.div
                    key="stop"
                    initial={{ opacity: 0, scale: 0.5 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.5 }}
                  >
                    <MicOff className="w-8 h-8" />
                  </motion.div>
                ) : (
                  <motion.div
                    key="start"
                    initial={{ opacity: 0, scale: 0.5 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.5 }}
                  >
                    <Mic className="w-8 h-8" />
                  </motion.div>
                )}
              </AnimatePresence>
            </Button>
          </motion.div>
        </div>
      </div>
    </Card>
  );
};

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import type { EmotionData } from '@/types/api';
import { cn } from '@/lib/utils';

interface EmotionDashboardProps {
  currentEmotion: EmotionData | null;
}

export const EmotionDashboard: React.FC<EmotionDashboardProps> = ({ currentEmotion }) => {
  if (!currentEmotion) {
    return (
      <Card className="glass-panel w-full h-full flex items-center justify-center p-6 min-h-[200px]">
        <div className="text-center text-muted-foreground">
          <p>No emotion detected yet.</p>
          <p className="text-sm opacity-50">Start speaking or chatting.</p>
        </div>
      </Card>
    );
  }

  const getEmoji = (emotion: string) => {
    switch (emotion) {
      case 'joy': return '😊';
      case 'sadness': return '😢';
      case 'anger': return '😠';
      case 'fear': return '😨';
      case 'surprise': return '😲';
      case 'disgust': return '🤢';
      case 'confused': return '😕';
      case 'neutral': return '😐';
      default: return '😐';
    }
  };

  const getColor = (emotion: string) => {
    switch (emotion) {
        case 'joy': return 'bg-yellow-400';
        case 'sadness': return 'bg-blue-500';
        case 'anger': return 'bg-red-500';
        case 'fear': return 'bg-purple-500';
        case 'surprise': return 'bg-pink-500';
        case 'disgust': return 'bg-green-500';
        case 'confused': return 'bg-cyan-500';
        default: return 'bg-slate-400';
    }
  };

  return (
    <Card className="glass-panel w-full h-full p-4 overflow-hidden flex flex-col gap-4">
      <CardHeader className="p-0 pb-2 border-b border-white/10">
        <CardTitle className="text-lg font-display text-white">Emotional State</CardTitle>
      </CardHeader>

      <CardContent className="p-0 flex flex-col gap-6 flex-1">

        {/* Primary Emotion Display */}
        <div className="flex flex-col items-center justify-center py-4 relative">
          <div className={cn(
            "w-24 h-24 rounded-full flex items-center justify-center text-6xl shadow-2xl transition-all duration-500 border border-white/10 backdrop-blur-md",
            getColor(currentEmotion.primary_emotion) + "/20"
          )}>
            {getEmoji(currentEmotion.primary_emotion)}
          </div>
          <div className={cn(
            "absolute inset-0 rounded-full blur-3xl opacity-20 -z-10",
             getColor(currentEmotion.primary_emotion)
          )} />

          <h3 className="mt-4 text-2xl font-bold text-white capitalize">
            {currentEmotion.primary_emotion}
          </h3>
          <p className="text-sm text-white/60">
            {Math.round(currentEmotion.confidence * 100)}% Confidence
          </p>
        </div>

      </CardContent>
    </Card>
  );
};

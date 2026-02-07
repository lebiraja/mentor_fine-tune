import React from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Radio, Mic, MessageSquare, Activity, ShieldCheck } from 'lucide-react';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';

interface LandingPageProps {
  onConnect: () => void;
  isHealthy: boolean;
  isLoading: boolean;
  isStarting: boolean;
  error: string | null;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  onConnect,
  isHealthy,
  isLoading,
  isStarting,
  error,
}) => {
  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
  };

  return (
    <div className="flex items-center justify-center min-h-[80vh] w-full">
      <Card className="glass-panel w-full max-w-2xl p-8 md:p-12 flex flex-col items-center text-center gap-8 relative overflow-hidden">

        {/* decorative background elements inside card */}
        <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-primary via-secondary to-accent opacity-50" />
        <div className="absolute -top-20 -right-20 w-64 h-64 bg-primary/20 blur-[80px] rounded-full pointer-events-none" />
        <div className="absolute -bottom-20 -left-20 w-64 h-64 bg-secondary/20 blur-[80px] rounded-full pointer-events-none" />

        <motion.div
          className="space-y-4 z-10"
          variants={container}
          initial="hidden"
          animate="show"
        >
          <motion.div variants={item} className="mx-auto w-24 h-24 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center shadow-lg shadow-primary/30 mb-6 relative group">
            <Radio className="w-10 h-10 text-white group-hover:scale-110 transition-transform duration-500" />
            <div className={cn(
              "absolute -bottom-1 -right-1 w-6 h-6 rounded-full border-4 border-black/50 transition-colors duration-300",
              isLoading ? "bg-yellow-500 animate-pulse" : isHealthy ? "bg-green-500" : "bg-red-500"
            )} />
          </motion.div>

          <motion.h1 variants={item} className="text-5xl md:text-6xl font-display font-bold bg-clip-text text-transparent bg-gradient-to-r from-white via-white to-white/70 tracking-tight">
            ClarityMentor
          </motion.h1>
          <motion.p variants={item} className="text-xl text-muted-foreground font-light max-w-md mx-auto">
            AI-Powered Mental Health Companion with Real-time Emotion Analysis
          </motion.p>
        </motion.div>

        <motion.div
          className="grid grid-cols-2 gap-4 w-full max-w-lg z-10"
          variants={container}
          initial="hidden"
          animate="show"
        >
          {[
            { icon: MessageSquare, label: "Text Chat", desc: "Natural conversation" },
            { icon: Mic, label: "Voice Mode", desc: "Real-time voice AI" },
            { icon: Activity, label: "Emotion AI", desc: "Adaptive responses" },
            { icon: ShieldCheck, label: "Private", desc: "Secure & confidential" },
          ].map((feature, i) => (
            <motion.div
              key={i}
              variants={item}
              className="p-4 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors text-left flex flex-col gap-2 group"
            >
              <div className="flex items-center gap-2 text-primary group-hover:text-accent transition-colors">
                <feature.icon className="w-5 h-5" />
                <span className="font-semibold text-white">{feature.label}</span>
              </div>
              <p className="text-xs text-muted-foreground">{feature.desc}</p>
            </motion.div>
          ))}
        </motion.div>

        <motion.div
          className="w-full max-w-md space-y-4 z-10 mt-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          <Button
            size="lg"
            className="w-full h-14 text-lg font-semibold shadow-xl shadow-primary/20 hover:shadow-primary/40 transition-all duration-300 relative overflow-hidden group"
            onClick={onConnect}
            disabled={!isHealthy || isLoading || isStarting}
          >
            <div className="absolute inset-0 bg-gradient-to-r from-primary via-accent to-primary opacity-0 group-hover:opacity-100 transition-opacity duration-500 animate-glass-shine" />
            <span className="relative z-10 flex items-center justify-center gap-2">
              {isLoading ? 'Initializing...' : isStarting ? 'Starting Session...' : 'Start Session'}
              {!isLoading && !isStarting && <Radio className="w-5 h-5" />}
            </span>
          </Button>

          <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
             <div className={cn("w-2 h-2 rounded-full", isHealthy ? "bg-green-500" : "bg-red-500")} />
             <span>{isLoading ? "Checking System..." : isHealthy ? "System Online" : "System Offline"}</span>
             {error && <span className="text-red-400 ml-2">• {error}</span>}
          </div>
        </motion.div>

      </Card>
    </div>
  );
};

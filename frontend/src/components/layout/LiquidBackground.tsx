import React from 'react';

export const LiquidBackground: React.FC = () => {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none -z-50 bg-background">
      <div className="absolute top-[-20%] left-[-10%] w-[50vw] h-[50vw] rounded-full bg-primary/20 blur-[120px] animate-blob mix-blend-screen" />
      <div className="absolute top-[20%] right-[-10%] w-[40vw] h-[40vw] rounded-full bg-secondary/20 blur-[100px] animate-blob animation-delay-2000 mix-blend-screen" />
      <div className="absolute bottom-[-20%] left-[20%] w-[60vw] h-[60vw] rounded-full bg-accent/10 blur-[140px] animate-blob animation-delay-4000 mix-blend-screen" />

      {/* Overlay for noise/texture if needed */}
      <div className="absolute inset-0 bg-noise opacity-[0.03]" />
    </div>
  );
};

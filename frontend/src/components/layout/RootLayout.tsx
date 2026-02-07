import React from 'react';
import { LiquidBackground } from './LiquidBackground';

interface RootLayoutProps {
  children: React.ReactNode;
}

export const RootLayout: React.FC<RootLayoutProps> = ({ children }) => {
  return (
    <div className="relative min-h-screen text-foreground font-sans selection:bg-primary/30 selection:text-white overflow-hidden">
      <LiquidBackground />
      <main className="relative z-10 container mx-auto px-4 py-8 md:py-12 min-h-screen flex flex-col">
        {children}
      </main>
    </div>
  );
};

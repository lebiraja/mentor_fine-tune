import React from 'react';
import { Button } from '@/components/ui/button';
import { MessageSquare, Mic, Activity, Home, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SidebarProps {
  currentView: 'landing' | 'chat' | 'voice';
  setCurrentView: (view: 'landing' | 'chat' | 'voice') => void;
  className?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentView, setCurrentView, className }) => {
  const navItems = [
    { id: 'landing', label: 'Home', icon: Home, view: 'landing' },
    { id: 'chat', label: 'Chat', icon: MessageSquare, view: 'chat' },
    { id: 'voice', label: 'Voice', icon: Mic, view: 'voice' },
  ];

  return (
    <div className={cn("flex flex-col h-full w-16 md:w-20 glass-panel border-r border-white/10 items-center py-6 gap-4 z-50", className)}>
      <div className="mb-6">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center shadow-lg shadow-primary/20">
            <Activity className="w-6 h-6 text-white" />
        </div>
      </div>

      <nav className="flex flex-col gap-4 w-full px-2">
        {navItems.map((item) => (
          <Button
            key={item.id}
            variant="ghost"
            size="icon"
            onClick={() => setCurrentView(item.view as any)}
            className={cn(
              "w-full aspect-square rounded-xl transition-all duration-300",
              currentView === item.view
                ? "bg-primary/20 text-primary shadow-inner shadow-primary/10 border border-primary/20"
                : "text-muted-foreground hover:bg-white/5 hover:text-white"
            )}
            title={item.label}
          >
            <item.icon className={cn("w-5 h-5", currentView === item.view && "stroke-[2.5px]")} />
          </Button>
        ))}
      </nav>

      <div className="mt-auto flex flex-col gap-4 w-full px-2">
        <Button
            variant="ghost"
            size="icon"
            className="w-full aspect-square rounded-xl text-muted-foreground hover:bg-white/5 hover:text-white"
        >
            <Settings className="w-5 h-5" />
        </Button>
      </div>
    </div>
  );
};

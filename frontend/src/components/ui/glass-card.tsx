import * as React from 'react';
import { cn } from '@/lib/utils';

export interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'subtle' | 'default' | 'strong';
  blur?: 'sm' | 'md' | 'lg' | 'xl';
}

const GlassCard = React.forwardRef<HTMLDivElement, GlassCardProps>(
  ({ className, variant = 'default', blur = 'md', ...props }, ref) => {
    const variants = {
      subtle: 'bg-white/5 dark:bg-black/10',
      default: 'bg-white/15 dark:bg-black/25',
      strong: 'bg-white/25 dark:bg-black/40',
    };

    const blurs = {
      sm: 'backdrop-blur-sm',
      md: 'backdrop-blur-md',
      lg: 'backdrop-blur-lg',
      xl: 'backdrop-blur-xl',
    };

    return (
      <div
        ref={ref}
        className={cn(
          'rounded-glass border border-white/20 dark:border-white/10',
          'shadow-glass',
          'overflow-hidden isolate',
          'backdrop-saturate-150',
          variants[variant],
          blurs[blur],
          className
        )}
        {...props}
      />
    );
  }
);
GlassCard.displayName = 'GlassCard';

export { GlassCard };

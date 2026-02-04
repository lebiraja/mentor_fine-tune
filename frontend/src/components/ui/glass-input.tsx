import * as React from 'react';
import { cn } from '@/lib/utils';

export interface GlassInputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  variant?: 'default' | 'subtle';
  error?: boolean;
}

const GlassInput = React.forwardRef<HTMLInputElement, GlassInputProps>(
  ({ className, variant = 'default', error, ...props }, ref) => {
    const variants = {
      default:
        'bg-white/10 dark:bg-black/20 border-white/20 dark:border-white/10 placeholder-slate-500 dark:placeholder-slate-400',
      subtle:
        'bg-transparent border-white/10 dark:border-white/5 placeholder-slate-400 dark:placeholder-slate-600',
    };

    return (
      <input
        ref={ref}
        className={cn(
          'w-full',
          'rounded-lg border',
          'px-4 py-2',
          'text-slate-900 dark:text-white',
          'transition-colors duration-200',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:border-transparent',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          error && 'border-red-500 focus-visible:ring-red-500',
          variants[variant],
          className
        )}
        {...props}
      />
    );
  }
);
GlassInput.displayName = 'GlassInput';

export { GlassInput };

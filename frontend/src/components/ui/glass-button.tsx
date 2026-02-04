import * as React from 'react';
import { cn } from '@/lib/utils';

export interface GlassButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'secondary' | 'accent' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg' | 'icon';
  isLoading?: boolean;
}

const GlassButton = React.forwardRef<HTMLButtonElement, GlassButtonProps>(
  (
    { className, variant = 'default', size = 'md', isLoading, ...props },
    ref
  ) => {
    const variants = {
      default:
        'bg-primary-500 text-white hover:bg-primary-600 active:bg-primary-700',
      secondary:
        'bg-secondary-500 text-white hover:bg-secondary-600 active:bg-secondary-700',
      accent:
        'bg-accent-500 text-white hover:bg-accent-600 active:bg-accent-700',
      ghost:
        'bg-white/5 text-slate-900 dark:text-white hover:bg-white/10 dark:hover:bg-white/20',
      danger: 'bg-red-500 text-white hover:bg-red-600 active:bg-red-700',
    };

    const sizes = {
      sm: 'px-3 py-1.5 text-sm rounded-md',
      md: 'px-4 py-2 text-base rounded-lg',
      lg: 'px-6 py-3 text-lg rounded-lg',
      icon: 'p-2 rounded-lg',
    };

    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center font-medium',
          'transition-colors duration-200',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary-500',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          variants[variant],
          sizes[size],
          className
        )}
        disabled={isLoading || props.disabled}
        {...props}
      >
        {isLoading && (
          <svg
            className="mr-2 h-4 w-4 animate-spin"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        {props.children}
      </button>
    );
  }
);
GlassButton.displayName = 'GlassButton';

export { GlassButton };

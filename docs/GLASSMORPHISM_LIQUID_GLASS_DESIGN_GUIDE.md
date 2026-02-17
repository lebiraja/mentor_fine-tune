# Glassmorphism & Apple Liquid Glass Design System

## Complete Knowledge Base for Frontend Development (React + TypeScript + Vite)

---

## Table of Contents

1. [Overview & History](#overview--history)
2. [Core Design Principles](#core-design-principles)
3. [Apple's Liquid Glass Specifics](#apples-liquid-glass-specifics)
4. [Technical Implementation](#technical-implementation)
5. [CSS Properties Reference](#css-properties-reference)
6. [Tailwind CSS Implementation](#tailwind-css-implementation)
7. [shadcn/ui Integration](#shadcnui-integration)
8. [Component Patterns](#component-patterns)
9. [Accessibility Guidelines](#accessibility-guidelines)
10. [Performance Optimization](#performance-optimization)
11. [Browser Compatibility](#browser-compatibility)
12. [Design Tokens & Variables](#design-tokens--variables)
13. [Code Examples](#code-examples)
14. [Best Practices Checklist](#best-practices-checklist)

---

## Overview & History

### What is Glassmorphism?

Glassmorphism is a visual design style that creates a **frosted glass effect** using:
- **Transparency** - Semi-transparent backgrounds
- **Background blur** - Blurring content behind elements
- **Subtle borders** - Light borders to define edges
- **Layered depth** - Creating visual hierarchy through stacking

### Historical Context

| Era | Design Language | Key Features |
|-----|----------------|--------------|
| 2001 | Apple Aqua (Mac OS X) | Translucent window elements |
| 2006 | Windows Vista Aero | Glass-like window chrome |
| 2013 | iOS 7 | Gaussian blur, flat design |
| 2020 | macOS Big Sur | Modern glassmorphism |
| 2021 | Windows 11 Fluent Design | Mica & Acrylic materials |
| 2025 | Apple Liquid Glass (iOS 26) | Dynamic refraction & lensing |

### Apple Liquid Glass (2025)

Announced at **WWDC 2025 (June 9, 2025)**, Liquid Glass is Apple's unified design language across:
- iOS 26
- iPadOS 26
- macOS Tahoe 26
- watchOS 26
- tvOS 26
- visionOS 26

> "A dynamic material that combines the optical properties of glass with a sense of fluidity" — Apple Human Interface Guidelines

---

## Core Design Principles

### The Three Pillars (Apple HIG)

#### 1. Hierarchy
> "Establish a clear visual hierarchy where controls and interface elements elevate and distinguish the content beneath them."

- Content is **primary**; UI controls are **secondary**
- Glass effects create separation between layers
- Navigation floats above content as a distinct functional layer
- Use varying levels of transparency to communicate importance

#### 2. Harmony
> "Align with the concentric design of the hardware and software to create harmony between interface elements, system experiences, and devices."

- Shapes follow hardware (rounded corners match device bezels)
- Software design reflects physical device design
- Consistent material usage across the interface
- Capsule shapes for touch-friendly layouts

#### 3. Consistency
> "Adopt platform conventions to maintain a consistent design that continuously adapts across window sizes and displays."

- Universal design across all Apple platforms
- Behavior remains predictable even as appearance adapts
- Standard icons for standard actions
- Predictable control placement

### Glassmorphism Core Characteristics

```
┌─────────────────────────────────────────────────────────┐
│  GLASSMORPHISM FORMULA                                  │
├─────────────────────────────────────────────────────────┤
│  1. Semi-transparent background (10-30% opacity)        │
│  2. Background blur (8-20px)                            │
│  3. Subtle border (white/black at 10-25% opacity)       │
│  4. Soft shadow for depth                               │
│  5. Rounded corners (soft, organic feel)                │
│  6. Vibrant/colorful background behind the glass        │
└─────────────────────────────────────────────────────────┘
```

---

## Apple's Liquid Glass Specifics

### Key Features

| Feature | Description |
|---------|-------------|
| **Lensing** | Bends and concentrates light in real-time (vs traditional blur that scatters light) |
| **Refraction** | Background content subtly bends through glass layers, simulating physical optics |
| **Specular Highlights** | Highlights move with device motion, reinforcing realism |
| **Adaptive Contrast** | Material adapts automatically between Light/Dark mode |
| **Motion Response** | Reacts to device movement on iOS/iPadOS |
| **Materialization** | Elements appear by gradually modulating light bending |

### Material Variants

```typescript
// Apple's Glass Variants (SwiftUI reference)
type GlassVariant = {
  regular: {
    transparency: 'Medium',
    adaptivity: 'Full - adapts to any content',
    useCase: 'Default for most UI'
  },
  clear: {
    transparency: 'High',
    adaptivity: 'Limited - requires dimming layer',
    useCase: 'Media-rich backgrounds'
  },
  identity: {
    transparency: 'None',
    adaptivity: 'N/A - no effect applied',
    useCase: 'Conditional disable'
  }
}
```

### Design Philosophy

```
┌─────────────────────────────────────────────────────────┐
│  LIQUID GLASS USAGE RULE                                │
├─────────────────────────────────────────────────────────┤
│  "Liquid Glass is best reserved for the navigation      │
│   layer that floats above the content of your app."     │
│                                                         │
│  ✓ DO: Apply to navigation, toolbars, controls          │
│  ✗ DON'T: Apply to content (lists, tables, media)       │
└─────────────────────────────────────────────────────────┘
```

---

## Technical Implementation

### Core CSS Properties

```css
/* Essential Glassmorphism Properties */
.glass-element {
  /* 1. Semi-transparent background */
  background: rgba(255, 255, 255, 0.15);
  /* Alternative with CSS color functions */
  background: hsl(0 0% 100% / 0.15);
  background: oklch(1 0 0 / 0.15);
  
  /* 2. Background blur - THE KEY PROPERTY */
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px); /* Safari support */
  
  /* 3. Subtle border */
  border: 1px solid rgba(255, 255, 255, 0.2);
  
  /* 4. Soft shadow */
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  
  /* 5. Rounded corners */
  border-radius: 16px;
}
```

### Blur Intensity Guide

| Blur Value | Effect | Use Case |
|------------|--------|----------|
| `4px` | Very subtle | Minimal separation |
| `8px` | Light frost | Cards, small overlays |
| `12px` | Medium frost | Navigation bars |
| `16px` | Standard glass | Modals, sidebars |
| `20px` | Heavy frost | Hero sections |
| `32px+` | Intense blur | Special effects |

### Background Opacity Guide

| Opacity | Effect | Readability |
|---------|--------|-------------|
| `0.05-0.10` | Very transparent | Requires high contrast text |
| `0.15-0.25` | Balanced | Good for most use cases |
| `0.30-0.40` | Semi-opaque | Better text readability |
| `0.50+` | Heavy tint | Best accessibility |

---

## CSS Properties Reference

### backdrop-filter Functions

```css
/* Individual filters */
backdrop-filter: blur(10px);
backdrop-filter: brightness(0.9);
backdrop-filter: contrast(1.1);
backdrop-filter: grayscale(0.1);
backdrop-filter: saturate(1.2);
backdrop-filter: sepia(0.1);
backdrop-filter: hue-rotate(10deg);
backdrop-filter: invert(0.1);
backdrop-filter: opacity(0.9);
backdrop-filter: drop-shadow(0 0 10px rgba(0,0,0,0.1));

/* Combined filters for richer effect */
backdrop-filter: blur(10px) saturate(1.5) brightness(1.1);
```

### Complete Glass Card Example

```css
.glass-card {
  /* Background */
  background: rgba(255, 255, 255, 0.15);
  
  /* Blur effect */
  backdrop-filter: blur(10px) saturate(1.2);
  -webkit-backdrop-filter: blur(10px) saturate(1.2);
  
  /* Border for definition */
  border: 1px solid rgba(255, 255, 255, 0.2);
  
  /* Shadow for depth */
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  
  /* Rounded corners */
  border-radius: 16px;
  
  /* Padding */
  padding: 24px;
  
  /* Prevent overflow issues */
  overflow: hidden;
  
  /* Isolation for stacking context */
  isolation: isolate;
}
```

### Dark Mode Variant

```css
/* Light mode */
:root {
  --glass-bg: rgba(255, 255, 255, 0.15);
  --glass-border: rgba(255, 255, 255, 0.2);
  --glass-shadow: rgba(0, 0, 0, 0.1);
}

/* Dark mode */
.dark {
  --glass-bg: rgba(0, 0, 0, 0.3);
  --glass-border: rgba(255, 255, 255, 0.1);
  --glass-shadow: rgba(0, 0, 0, 0.3);
}

.glass-card {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  box-shadow: 0 8px 32px var(--glass-shadow);
}
```

---

## Tailwind CSS Implementation

### Built-in Utilities

```html
<!-- Basic Glassmorphism with Tailwind -->
<div class="
  bg-white/15
  backdrop-blur-md
  border border-white/20
  rounded-2xl
  shadow-lg
  p-6
">
  Content here
</div>
```

### Backdrop Blur Classes

| Class | CSS | Blur Value |
|-------|-----|------------|
| `backdrop-blur-none` | `backdrop-filter: blur(0)` | 0px |
| `backdrop-blur-sm` | `backdrop-filter: blur(4px)` | 4px |
| `backdrop-blur` | `backdrop-filter: blur(8px)` | 8px |
| `backdrop-blur-md` | `backdrop-filter: blur(12px)` | 12px |
| `backdrop-blur-lg` | `backdrop-filter: blur(16px)` | 16px |
| `backdrop-blur-xl` | `backdrop-filter: blur(24px)` | 24px |
| `backdrop-blur-2xl` | `backdrop-filter: blur(40px)` | 40px |
| `backdrop-blur-3xl` | `backdrop-filter: blur(64px)` | 64px |

### Background Opacity

```html
<!-- Using color with opacity -->
<div class="bg-white/10">10% white</div>
<div class="bg-white/20">20% white</div>
<div class="bg-white/30">30% white</div>

<!-- Dark mode variants -->
<div class="bg-black/20 dark:bg-white/10">Adaptive</div>
```

### Extended Tailwind Configuration

```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss'

const config: Config = {
  theme: {
    extend: {
      // Custom blur values
      backdropBlur: {
        xs: '2px',
        '4xl': '80px',
      },
      
      // Glass-specific colors
      colors: {
        glass: {
          light: 'rgba(255, 255, 255, 0.15)',
          dark: 'rgba(0, 0, 0, 0.3)',
          border: 'rgba(255, 255, 255, 0.2)',
        },
      },
      
      // Custom shadows for glass
      boxShadow: {
        glass: '0 8px 32px rgba(0, 0, 0, 0.1)',
        'glass-lg': '0 16px 48px rgba(0, 0, 0, 0.15)',
        'glass-inset': 'inset 0 1px 0 rgba(255, 255, 255, 0.2)',
      },
      
      // Border radius for glass elements
      borderRadius: {
        'glass': '16px',
        'glass-lg': '24px',
        'glass-xl': '32px',
      },
    },
  },
  plugins: [],
}

export default config
```

### Complete Tailwind Glass Component

```html
<!-- Glass Card Component -->
<div class="
  relative
  bg-white/15
  dark:bg-black/25
  backdrop-blur-lg
  backdrop-saturate-150
  border
  border-white/20
  dark:border-white/10
  rounded-2xl
  shadow-[0_8px_32px_rgba(0,0,0,0.1)]
  p-6
  overflow-hidden
  isolate
">
  <!-- Optional: Inner glow effect -->
  <div class="
    absolute
    inset-0
    bg-gradient-to-br
    from-white/10
    to-transparent
    pointer-events-none
  "></div>
  
  <!-- Content -->
  <div class="relative z-10">
    <h3 class="text-xl font-semibold">Glass Card</h3>
    <p class="mt-2 opacity-80">Your content here</p>
  </div>
</div>
```

---

## shadcn/ui Integration

### Option 1: Custom Glass Theme via CSS Variables

```css
/* globals.css */
@import "tailwindcss";

@layer base {
  :root {
    /* Standard shadcn variables */
    --background: oklch(1 0 0);
    --foreground: oklch(0.145 0 0);
    
    /* Glass-specific variables */
    --glass-background: oklch(1 0 0 / 0.15);
    --glass-background-strong: oklch(1 0 0 / 0.25);
    --glass-border: oklch(1 0 0 / 0.2);
    --glass-shadow: oklch(0 0 0 / 0.1);
    --glass-blur: 16px;
    
    /* Card with glass support */
    --card: oklch(1 0 0);
    --card-foreground: oklch(0.145 0 0);
  }

  .dark {
    --background: oklch(0.145 0 0);
    --foreground: oklch(0.985 0 0);
    
    /* Dark mode glass */
    --glass-background: oklch(0 0 0 / 0.3);
    --glass-background-strong: oklch(0 0 0 / 0.4);
    --glass-border: oklch(1 0 0 / 0.1);
    --glass-shadow: oklch(0 0 0 / 0.3);
  }
}

/* Glass utility class */
@layer utilities {
  .glass {
    background: var(--glass-background);
    backdrop-filter: blur(var(--glass-blur));
    -webkit-backdrop-filter: blur(var(--glass-blur));
    border: 1px solid var(--glass-border);
    box-shadow: 0 8px 32px var(--glass-shadow);
  }
  
  .glass-strong {
    background: var(--glass-background-strong);
    backdrop-filter: blur(calc(var(--glass-blur) * 1.5));
    -webkit-backdrop-filter: blur(calc(var(--glass-blur) * 1.5));
    border: 1px solid var(--glass-border);
    box-shadow: 0 8px 32px var(--glass-shadow);
  }
}
```

### Option 2: glasscn-ui Library

```bash
# Install glasscn-ui
npm install glasscn-ui
```

```typescript
// tailwind.config.ts
import { createTailwindPreset } from 'glasscn-ui'

const glasscnPreset = createTailwindPreset({
  baseRadius: '0.5em',
  colors: {
    primary: 'blue',
    secondary: 'purple',
    gray: 'slate',
  },
})

export default {
  presets: [glasscnPreset],
  // ... rest of config
}
```

### Option 3: shadcn-glass-ui

```bash
# Add via shadcn CLI
npx shadcn@latest add @shadcn-glass-ui/button-glass
npx shadcn@latest add @shadcn-glass-ui/card-glass
npx shadcn@latest add @shadcn-glass-ui/modal-glass
```

```tsx
// Usage
import { ButtonGlass } from '@/components/glass/ui/button-glass';
import { GlassCard } from 'shadcn-glass-ui';

function App() {
  return (
    <GlassCard variant="glass" intensity="medium" padding="default">
      <ButtonGlass variant="default">
        Click me
      </ButtonGlass>
    </GlassCard>
  );
}
```

### Custom shadcn Glass Card Component

```tsx
// components/ui/glass-card.tsx
import * as React from "react"
import { cn } from "@/lib/utils"

export interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'subtle' | 'default' | 'strong'
  blur?: 'sm' | 'md' | 'lg' | 'xl'
}

const GlassCard = React.forwardRef<HTMLDivElement, GlassCardProps>(
  ({ className, variant = 'default', blur = 'md', ...props }, ref) => {
    const variants = {
      subtle: 'bg-white/5 dark:bg-black/10',
      default: 'bg-white/15 dark:bg-black/25',
      strong: 'bg-white/25 dark:bg-black/40',
    }
    
    const blurs = {
      sm: 'backdrop-blur-sm',
      md: 'backdrop-blur-md',
      lg: 'backdrop-blur-lg',
      xl: 'backdrop-blur-xl',
    }
    
    return (
      <div
        ref={ref}
        className={cn(
          "rounded-xl border border-white/20 dark:border-white/10",
          "shadow-[0_8px_32px_rgba(0,0,0,0.1)]",
          "overflow-hidden isolate",
          variants[variant],
          blurs[blur],
          className
        )}
        {...props}
      />
    )
  }
)
GlassCard.displayName = "GlassCard"

export { GlassCard }
```

---

## Component Patterns

### Navigation Bar

```tsx
// components/glass-navbar.tsx
import { cn } from "@/lib/utils"

export function GlassNavbar({ className, children }: {
  className?: string
  children: React.ReactNode
}) {
  return (
    <nav
      className={cn(
        "fixed top-4 left-1/2 -translate-x-1/2 z-50",
        "px-6 py-3",
        "bg-white/10 dark:bg-black/20",
        "backdrop-blur-lg backdrop-saturate-150",
        "border border-white/20 dark:border-white/10",
        "rounded-full",
        "shadow-[0_8px_32px_rgba(0,0,0,0.1)]",
        className
      )}
    >
      {children}
    </nav>
  )
}
```

### Modal/Dialog

```tsx
// components/glass-modal.tsx
import * as Dialog from "@radix-ui/react-dialog"
import { cn } from "@/lib/utils"

export function GlassModal({ 
  open, 
  onOpenChange, 
  children 
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  children: React.ReactNode
}) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        {/* Backdrop */}
        <Dialog.Overlay 
          className={cn(
            "fixed inset-0 z-50",
            "bg-black/40 backdrop-blur-sm",
            "data-[state=open]:animate-in data-[state=closed]:animate-out",
            "data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0"
          )} 
        />
        
        {/* Content */}
        <Dialog.Content
          className={cn(
            "fixed left-1/2 top-1/2 z-50",
            "-translate-x-1/2 -translate-y-1/2",
            "w-full max-w-lg p-6",
            "bg-white/15 dark:bg-black/30",
            "backdrop-blur-xl backdrop-saturate-150",
            "border border-white/20 dark:border-white/10",
            "rounded-2xl",
            "shadow-[0_16px_48px_rgba(0,0,0,0.15)]",
            "data-[state=open]:animate-in data-[state=closed]:animate-out",
            "data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
            "data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95"
          )}
        >
          {children}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
```

### Glass Button

```tsx
// components/ui/glass-button.tsx
import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const glassButtonVariants = cva(
  [
    "inline-flex items-center justify-center",
    "rounded-xl font-medium",
    "transition-all duration-200",
    "focus-visible:outline-none focus-visible:ring-2",
    "focus-visible:ring-white/50 focus-visible:ring-offset-2",
    "disabled:pointer-events-none disabled:opacity-50",
    "backdrop-blur-md",
    "border border-white/20 dark:border-white/10",
  ].join(" "),
  {
    variants: {
      variant: {
        default: [
          "bg-white/20 dark:bg-white/10",
          "hover:bg-white/30 dark:hover:bg-white/20",
          "text-foreground",
        ].join(" "),
        primary: [
          "bg-primary/80",
          "hover:bg-primary/90",
          "text-primary-foreground",
          "backdrop-blur-md",
        ].join(" "),
        ghost: [
          "bg-transparent",
          "hover:bg-white/10",
          "border-transparent",
        ].join(" "),
      },
      size: {
        sm: "h-9 px-4 text-sm",
        md: "h-10 px-5 text-sm",
        lg: "h-11 px-6 text-base",
        xl: "h-12 px-8 text-base",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "md",
    },
  }
)

export interface GlassButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof glassButtonVariants> {
  asChild?: boolean
}

const GlassButton = React.forwardRef<HTMLButtonElement, GlassButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(glassButtonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
GlassButton.displayName = "GlassButton"

export { GlassButton, glassButtonVariants }
```

### Sidebar

```tsx
// components/glass-sidebar.tsx
export function GlassSidebar({ children }: { children: React.ReactNode }) {
  return (
    <aside
      className={cn(
        "fixed left-0 top-0 h-screen w-64",
        "bg-white/10 dark:bg-black/20",
        "backdrop-blur-xl backdrop-saturate-150",
        "border-r border-white/10",
        "p-4"
      )}
    >
      {children}
    </aside>
  )
}
```

---

## Accessibility Guidelines

### WCAG Contrast Requirements

| Element Type | Minimum Ratio | Target |
|--------------|---------------|--------|
| Body text | 4.5:1 | AA |
| Large text (18pt+) | 3:1 | AA |
| UI components | 3:1 | AA |
| Body text (enhanced) | 7:1 | AAA |

### Critical Rules for Glassmorphism

```
┌─────────────────────────────────────────────────────────┐
│  ACCESSIBILITY CHECKLIST                                │
├─────────────────────────────────────────────────────────┤
│  ✓ Never place text directly on glass without overlay   │
│  ✓ Use semi-opaque fills behind text                    │
│  ✓ Test contrast against ALL possible backgrounds       │
│  ✓ Respect prefers-reduced-transparency                 │
│  ✓ Provide solid fallbacks for older browsers           │
│  ✓ Maintain 4.5:1 contrast for all body text            │
│  ✓ Test in both light AND dark modes                    │
│  ✓ Test with screen readers (VoiceOver, NVDA)           │
│  ✓ Ensure focus indicators are visible                  │
└─────────────────────────────────────────────────────────┘
```

### Reduced Transparency Support

```css
/* Respect user preferences */
@media (prefers-reduced-transparency: reduce) {
  .glass-element {
    background: var(--background);
    backdrop-filter: none;
    border: 1px solid var(--border);
  }
}

/* Alternative: CSS custom property approach */
:root {
  --glass-opacity: 0.15;
}

@media (prefers-reduced-transparency: reduce) {
  :root {
    --glass-opacity: 0.9;
  }
}
```

### Focus State Enhancement

```css
.glass-button:focus-visible {
  outline: 2px solid white;
  outline-offset: 2px;
  box-shadow: 
    0 0 0 4px rgba(255, 255, 255, 0.3),
    0 8px 32px rgba(0, 0, 0, 0.1);
}
```

### High Contrast Mode

```css
@media (prefers-contrast: high) {
  .glass-element {
    background: var(--background);
    backdrop-filter: none;
    border: 2px solid var(--foreground);
  }
}
```

---

## Performance Optimization

### Performance Impact

| Property | GPU Impact | Recommendations |
|----------|------------|-----------------|
| `backdrop-filter: blur()` | HIGH | Limit to 2-3 elements per viewport |
| `box-shadow` | MEDIUM | Use simpler shadows on mobile |
| `border-radius` | LOW | No restrictions needed |
| `opacity` | LOW | No restrictions needed |

### Optimization Strategies

```css
/* 1. Use will-change sparingly */
.glass-element {
  will-change: backdrop-filter;
}

/* 2. Reduce blur on mobile */
@media (max-width: 768px) {
  .glass-element {
    backdrop-filter: blur(8px); /* Reduced from 16px */
  }
}

/* 3. Use transform for animations instead of backdrop-filter */
.glass-element {
  transition: transform 0.2s, opacity 0.2s;
}

.glass-element:hover {
  transform: translateY(-2px);
  /* Don't animate backdrop-filter! */
}

/* 4. Hardware acceleration hint */
.glass-element {
  transform: translateZ(0);
}
```

### React Performance Tips

```tsx
// Use memo for glass components
import { memo } from 'react'

export const GlassCard = memo(function GlassCard({ 
  children 
}: { 
  children: React.ReactNode 
}) {
  return (
    <div className="glass-card">
      {children}
    </div>
  )
})

// Avoid inline styles that cause re-renders
// ❌ Bad
<div style={{ backdropFilter: `blur(${blur}px)` }} />

// ✅ Good - Use CSS variables
<div 
  className="glass-card" 
  style={{ '--blur': `${blur}px` } as React.CSSProperties} 
/>
```

---

## Browser Compatibility

### Support Matrix

| Browser | Version | Support |
|---------|---------|---------|
| Chrome | 76+ | ✅ Full |
| Safari | 9+ | ✅ Full (with `-webkit-` prefix) |
| Firefox | 103+ | ✅ Full |
| Edge | 79+ | ✅ Full |
| Opera | 63+ | ✅ Full |
| iOS Safari | 9+ | ✅ Full |
| Chrome Android | 76+ | ✅ Full |

### Fallback Strategy

```css
/* Progressive enhancement approach */
.glass-card {
  /* Fallback: solid background */
  background: rgba(255, 255, 255, 0.9);
}

@supports (backdrop-filter: blur(10px)) {
  .glass-card {
    background: rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
  }
}
```

### Firefox-Specific Handling

```typescript
// tailwind.config.ts - Firefox variant
import plugin from 'tailwindcss/plugin'

export default {
  plugins: [
    plugin(function({ addVariant }) {
      addVariant('firefox', '@-moz-document url-prefix()')
    }),
  ],
}
```

```html
<!-- Usage -->
<div class="bg-white/15 backdrop-blur-lg firefox:bg-white/50">
  Increased opacity for Firefox fallback
</div>
```

---

## Design Tokens & Variables

### Complete Token System

```css
/* Glass Design Tokens */
:root {
  /* === BLUR TOKENS === */
  --blur-xs: 4px;
  --blur-sm: 8px;
  --blur-md: 16px;
  --blur-lg: 24px;
  --blur-xl: 32px;
  
  /* === GLASS BACKGROUND TOKENS === */
  --glass-subtle-bg: rgba(255, 255, 255, 0.08);
  --glass-medium-bg: rgba(255, 255, 255, 0.15);
  --glass-strong-bg: rgba(255, 255, 255, 0.25);
  
  /* === GLASS BORDER TOKENS === */
  --glass-border-subtle: rgba(255, 255, 255, 0.1);
  --glass-border-medium: rgba(255, 255, 255, 0.2);
  --glass-border-strong: rgba(255, 255, 255, 0.3);
  
  /* === SHADOW TOKENS === */
  --glass-shadow-sm: 0 4px 16px rgba(0, 0, 0, 0.08);
  --glass-shadow-md: 0 8px 32px rgba(0, 0, 0, 0.12);
  --glass-shadow-lg: 0 16px 48px rgba(0, 0, 0, 0.16);
  
  /* === RADIUS TOKENS === */
  --glass-radius-sm: 8px;
  --glass-radius-md: 16px;
  --glass-radius-lg: 24px;
  --glass-radius-full: 9999px;
  
  /* === TEXT SHADOW FOR GLASS === */
  --text-shadow-glass: 0 1px 2px rgba(0, 0, 0, 0.4), 
                       0 2px 6px rgba(0, 0, 0, 0.2);
  
  /* === SATURATION === */
  --glass-saturate: 1.5;
}

/* Dark Mode Tokens */
.dark {
  --glass-subtle-bg: rgba(0, 0, 0, 0.2);
  --glass-medium-bg: rgba(0, 0, 0, 0.35);
  --glass-strong-bg: rgba(0, 0, 0, 0.5);
  
  --glass-border-subtle: rgba(255, 255, 255, 0.05);
  --glass-border-medium: rgba(255, 255, 255, 0.1);
  --glass-border-strong: rgba(255, 255, 255, 0.15);
  
  --glass-shadow-sm: 0 4px 16px rgba(0, 0, 0, 0.3);
  --glass-shadow-md: 0 8px 32px rgba(0, 0, 0, 0.4);
  --glass-shadow-lg: 0 16px 48px rgba(0, 0, 0, 0.5);
}

/* Aurora Theme (Gradient Glow) */
.theme-aurora {
  --glass-subtle-bg: rgba(255, 255, 255, 0.1);
  --glass-medium-bg: rgba(255, 255, 255, 0.18);
  --glass-strong-bg: rgba(255, 255, 255, 0.25);
}
```

---

## Code Examples

### Complete Vite + React + TypeScript Setup

```bash
# Create project
npm create vite@latest glass-app -- --template react-ts

# Install dependencies
cd glass-app
npm install
npm install -D tailwindcss postcss autoprefixer
npm install class-variance-authority clsx tailwind-merge
npm install @radix-ui/react-dialog @radix-ui/react-slot
npm install lucide-react

# Initialize Tailwind
npx tailwindcss init -p
```

### Project Structure

```
src/
├── components/
│   ├── ui/
│   │   ├── glass-card.tsx
│   │   ├── glass-button.tsx
│   │   ├── glass-input.tsx
│   │   └── glass-modal.tsx
│   └── layout/
│       ├── glass-navbar.tsx
│       └── glass-sidebar.tsx
├── lib/
│   └── utils.ts
├── styles/
│   └── globals.css
├── App.tsx
└── main.tsx
```

### utils.ts

```typescript
// src/lib/utils.ts
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

### Complete App Example

```tsx
// src/App.tsx
import { useState } from 'react'
import { GlassCard } from './components/ui/glass-card'
import { GlassButton } from './components/ui/glass-button'
import { GlassNavbar } from './components/layout/glass-navbar'
import { Moon, Sun, Menu } from 'lucide-react'

function App() {
  const [darkMode, setDarkMode] = useState(false)

  return (
    <div className={darkMode ? 'dark' : ''}>
      {/* Vibrant Background - ESSENTIAL for glassmorphism */}
      <div className="min-h-screen bg-gradient-to-br from-purple-500 via-pink-500 to-orange-400 dark:from-slate-900 dark:via-purple-900 dark:to-slate-900">
        
        {/* Decorative blobs */}
        <div className="fixed inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-20 left-20 w-72 h-72 bg-blue-400 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob" />
          <div className="absolute top-40 right-20 w-72 h-72 bg-purple-400 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-2000" />
          <div className="absolute bottom-20 left-1/2 w-72 h-72 bg-pink-400 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-4000" />
        </div>

        {/* Glass Navbar */}
        <GlassNavbar>
          <div className="flex items-center gap-4">
            <Menu className="w-5 h-5" />
            <span className="font-semibold">Glass UI</span>
          </div>
          <GlassButton
            variant="ghost"
            size="sm"
            onClick={() => setDarkMode(!darkMode)}
          >
            {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </GlassButton>
        </GlassNavbar>

        {/* Main Content */}
        <main className="relative pt-24 px-6 pb-12">
          <div className="max-w-4xl mx-auto grid gap-6 md:grid-cols-2">
            
            <GlassCard variant="default" blur="lg" className="p-6">
              <h2 className="text-xl font-bold mb-4">Glassmorphism Card</h2>
              <p className="opacity-80 mb-4">
                This card demonstrates the frosted glass effect with
                backdrop blur and semi-transparent backgrounds.
              </p>
              <GlassButton>Learn More</GlassButton>
            </GlassCard>

            <GlassCard variant="strong" blur="xl" className="p-6">
              <h2 className="text-xl font-bold mb-4">Strong Glass</h2>
              <p className="opacity-80 mb-4">
                A stronger glass effect with more opacity for
                better text readability.
              </p>
              <GlassButton variant="primary">Get Started</GlassButton>
            </GlassCard>

          </div>
        </main>
      </div>
    </div>
  )
}

export default App
```

### Animation Keyframes

```css
/* Add to globals.css */
@keyframes blob {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  25% {
    transform: translate(20px, -30px) scale(1.1);
  }
  50% {
    transform: translate(-20px, 20px) scale(0.9);
  }
  75% {
    transform: translate(30px, 10px) scale(1.05);
  }
}

.animate-blob {
  animation: blob 8s infinite ease-in-out;
}

.animation-delay-2000 {
  animation-delay: 2s;
}

.animation-delay-4000 {
  animation-delay: 4s;
}
```

---

## Best Practices Checklist

### Design Checklist

- [ ] **Background**: Use vibrant, colorful backgrounds (gradients, images, or animated blobs)
- [ ] **Hierarchy**: Glass should be used for navigation/controls, NOT content
- [ ] **Blur intensity**: 8-16px for most use cases
- [ ] **Opacity**: 15-25% for balanced transparency
- [ ] **Borders**: Subtle white/black borders at 10-25% opacity
- [ ] **Shadows**: Soft shadows for depth perception
- [ ] **Rounded corners**: Use consistent radius (16px recommended)
- [ ] **Dark mode**: Test and adjust opacity/blur for dark backgrounds

### Accessibility Checklist

- [ ] Text contrast meets 4.5:1 minimum (use WebAIM Contrast Checker)
- [ ] UI components meet 3:1 contrast minimum
- [ ] Supports `prefers-reduced-transparency`
- [ ] Supports `prefers-contrast: high`
- [ ] Focus indicators are clearly visible
- [ ] Tested with screen readers
- [ ] No text placed directly on glass without background overlay

### Performance Checklist

- [ ] Limited to 2-3 glass elements per viewport
- [ ] Reduced blur on mobile devices
- [ ] No animation of `backdrop-filter` property
- [ ] Use `will-change` sparingly
- [ ] Tested on lower-end devices

### Browser Compatibility Checklist

- [ ] Include `-webkit-backdrop-filter` prefix
- [ ] Provide solid color fallback
- [ ] Use `@supports` for progressive enhancement
- [ ] Test on Firefox, Safari, Chrome, Edge

---

## Resources & References

### Official Documentation
- [Apple Human Interface Guidelines - Materials](https://developer.apple.com/design/human-interface-guidelines/materials)
- [Apple Liquid Glass Documentation](https://developer.apple.com/documentation/TechnologyOverviews/liquid-glass)
- [Tailwind CSS Backdrop Blur](https://tailwindcss.com/docs/backdrop-blur)
- [shadcn/ui Theming](https://ui.shadcn.com/docs/theming)

### Tools
- [Glass UI Generator](https://ui.glass/generator/)
- [CSS Glass Generator](https://css.glass/)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)

### Libraries
- [glasscn-ui](https://github.com/itsjavi/glasscn-ui) - shadcn/ui with glassmorphism
- [shadcn-glass-ui](https://github.com/Yhooi2/shadcn-glass-ui-library) - Glass components for shadcn

### WCAG Guidelines
- [WCAG 2.2 Contrast Requirements](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
- [Non-text Contrast (1.4.11)](https://www.w3.org/WAI/WCAG21/Understanding/non-text-contrast.html)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | February 2026 | Initial comprehensive guide |

---

*This guide is intended as a reference for AI agents (Claude) and developers building glassmorphism/Liquid Glass interfaces with React, TypeScript, Tailwind CSS, and shadcn/ui.*

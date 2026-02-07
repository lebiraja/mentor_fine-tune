# Frontend Redesign: Cosmic Liquid Glass Theme

## Overview
The frontend of ClarityMentor has been completely redesigned with a modern **"Cosmic Liquid Glass"** aesthetic. The codebase has been refactored from a monolithic structure into a modular, maintainable architecture using React best practices.

## Visual Style
- **Theme**: Deep space backgrounds (`#0f0c29`, `#302b63`) with vibrant neon accents (`#ff00cc`).
- **Glassmorphism**: Extensive use of semi-transparent backgrounds (`bg-white/5`), backdrop blurs, and subtle white borders to create a depth effect.
- **Animations**:
  - **Liquid Background**: A continuously moving, blurred background animation.
  - **Page Transitions**: Smooth fades and slides when switching between Landing, Chat, and Voice modes.
  - **Micro-interactions**: Hover effects, pulsating voice indicators, and animated entry for chat bubbles.

## Architecture

### Components (`src/components/`)
- **Layout**: `RootLayout`, `Sidebar`, `LandingPage`, `LiquidBackground`.
- **Chat**: `ChatInterface` - Handles text messaging with animated history.
- **Voice**: `VoiceMode` - A dedicated full-screen mode for voice interaction with a visual "orb" indicator.
- **Emotion**: `EmotionDashboard` - Displays real-time emotion detection confidence and type.
- **UI**: Reusable Shadcn UI components (Button, Card, Input, etc.) customized for the theme.

### Hooks (`src/hooks/`)
- **`useAudioRecording`**: Encapsulates MediaRecorder logic, permission handling, and audio chunk processing.
- **`useVoiceProcessing`**: Manages audio context for playback and visualization data.
- **`useWebSocketConnection`**: Handles the WebSocket lifecycle (connect, disconnect, reconnect) and message routing.

### Technologies
- **Framework**: React 19 + Vite
- **Styling**: Tailwind CSS v4 + Shadcn UI
- **Animations**: Framer Motion
- **Icons**: Lucide React

## Usage
The application can be built and run using standard commands:

```bash
# Install dependencies (if not already done)
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Next Steps
- Implement the backend logic for specific emotion breakdowns in the dashboard if granular data becomes available.
- Add user settings to customize the theme intensity or toggle animations for accessibility.

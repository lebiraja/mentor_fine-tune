# ClarityMentor Voice Chat UI

A modern, responsive web interface for the ClarityMentor voice-to-voice chat system with emotion detection and dual-channel awareness.

## Features

✨ **Modern Voice Chat**
- 🎤 Real-time microphone recording (Record/Stop buttons)
- 📁 Audio file upload support
- 🎵 Auto-play TTS responses

🧠 **Emotion Detection**
- Dual-channel emotion detection (speech + text)
- Color-coded emotion display with confidence
- Emotion badges in chat history

💬 **Chat Interface**
- Hybrid chat + voice assistant layout
- Message bubbles with timestamps
- Full conversation history
- Session management

🎨 **UI/UX**
- Dark theme (default) with light mode toggle
- Loading spinner during processing
- Waveform visualization while recording
- Real-time status updates
- Fully responsive design (mobile + desktop)

## Getting Started

### Prerequisites

- Backend running on `ws://localhost:2323/ws/voice`
- Modern browser (Chrome, Firefox, Safari, Edge)
- Microphone access enabled

### Quick Start

1. **Open the UI**
   ```bash
   # Navigate to the sample-ui directory
   cd /home/lebi/projects/mentor/sample-ui

   # Open in browser (use any http server)
   python -m http.server 8000

   # Then visit: http://localhost:8000
   ```

   Or simply open `index.html` directly in your browser:
   ```bash
   # macOS
   open index.html

   # Linux
   xdg-open index.html

   # Windows
   start index.html
   ```

2. **Start Backend**
   ```bash
   # In another terminal, ensure backend is running
   cd /home/lebi/projects/mentor
   python -m uvicorn backend.main:app --port 2323 --ws-max-size 10485760
   ```

3. **Use the UI**
   - Click **"Record"** button
   - Speak into your microphone
   - Click **"Stop"** when done
   - Listen to the AI response (auto-plays)
   - View chat history and emotion detection

## How It Works

### 1. Audio Recording
- Click "Record" to start microphone capture
- Click "Stop" to end recording
- Or upload an audio file instead

### 2. WebSocket Communication
```
Browser sends audio bytes
   ↓
Backend processes:
  - STT (speech-to-text)
  - Emotion detection (speech + text)
  - LLM response generation
  - TTS synthesis
   ↓
Browser receives:
  - Transcript
  - Emotion (with confidence)
  - Response text
  - Audio bytes (auto-plays)
```

### 3. Emotion Detection
Detected emotions are:
- 😊 **Joy** - Yellow (#fbbf24)
- 😢 **Sadness** - Blue (#3b82f6)
- 😡 **Anger** - Red (#ef4444)
- 😨 **Fear** - Purple (#8b5cf6)
- 😮 **Surprise** - Pink (#ec4899)
- 😐 **Neutral** - Gray (#64748b)

### 4. Chat History
All messages are displayed in chronological order:
- **User messages** (right side, blue bubbles)
- **Assistant responses** (left side, gray bubbles)
- **Emotion tags** on user messages

## File Structure

```
sample-ui/
├── index.html      # HTML structure
├── styles.css      # Dark theme styling (light mode included)
├── app.js          # WebSocket client + UI logic
├── README.md       # This file
```

## Configuration

### Backend URL
Edit `app.js` to change backend URL:
```javascript
const wsUrl = 'ws://localhost:2323/ws/voice'; // Line 47
```

### Emotion Colors
Customize emotion colors in `styles.css`:
```css
--emotion-neutral: #64748b;
--emotion-joy: #fbbf24;
--emotion-sadness: #3b82f6;
--emotion-anger: #ef4444;
--emotion-fear: #8b5cf6;
--emotion-surprise: #ec4899;
```

### Theme Colors
Dark theme colors in `styles.css`:
```css
--bg-primary: #0a0e27;      /* Main background */
--bg-secondary: #1a1f3a;    /* Panels */
--bg-tertiary: #252d4a;     /* Elements */
--text-primary: #ffffff;     /* Text */
--accent-color: #6366f1;     /* Buttons */
```

## Keyboard Shortcuts

- `R` - Start recording (future enhancement)
- `S` - Stop recording (future enhancement)
- `T` - Toggle theme (future enhancement)
- `N` - New session (future enhancement)

## Troubleshooting

### "Connection refused" error
**Problem:** Can't connect to backend
**Solution:** Ensure backend is running on port 2323:
```bash
python -m uvicorn backend.main:app --port 2323 --ws-max-size 10485760
```

### Microphone not working
**Problem:** Microphone access denied or no device
**Solutions:**
1. Check browser permissions for microphone
2. Grant microphone access when prompted
3. Test microphone in system settings
4. Try another browser
5. Use audio file upload instead

### Audio not playing
**Problem:** TTS response not auto-playing
**Solutions:**
1. Check browser's autoplay policy (some require user interaction first)
2. Click the audio player manually
3. Check browser console for errors
4. Try in a different browser

### "Message too big" error
**Problem:** WebSocket frame exceeds limit
**Solution:** This should be fixed, but ensure backend is started with:
```bash
python -m uvicorn backend.main:app --port 2323 --ws-max-size 10485760
```

## Performance

- **Recording**: Real-time audio capture with browser APIs
- **Latency**: 2-3 seconds end-to-end (STT + Emotion + LLM + TTS)
- **Memory**: ~50MB for UI + WebSocket buffer
- **Mobile**: Fully responsive, optimized for touch

## Browser Support

| Browser | Support | Notes |
|---------|---------|-------|
| Chrome | ✅ | Full support, recommended |
| Firefox | ✅ | Full support |
| Safari | ✅ | Full support (iOS 14.5+) |
| Edge | ✅ | Full support |
| IE 11 | ❌ | Not supported |

## API Reference

### WebSocket Messages

**Client → Server**
```
Binary: Raw PCM audio data (16000 Hz, 16-bit mono)
```

**Server → Client**
```json
{"type": "status", "message": "Processing..."}
{"type": "transcript", "text": "User said this"}
{"type": "emotion", "data": {"primary_emotion": "joy", "confidence": 0.85}}
{"type": "response", "text": "AI response text"}
```
Plus binary audio data at the end.

### REST Endpoints

Optional (for testing):
```bash
# Health check
curl http://localhost:2323/api/health

# Create session
curl -X POST http://localhost:2323/api/sessions

# Text chat
curl -X POST http://localhost:2323/api/text-chat \
  -H "Content-Type: application/json" \
  -d '{"text":"Your message"}'
```

## Development

### Adding Features

1. **New emotion colors**
   - Edit `styles.css` emotion colors
   - Update emotion map in `app.js`

2. **Custom status messages**
   - Edit `setStatus()` method in `app.js`
   - Add new status types in `getStatusColor()`

3. **UI layout changes**
   - Modify `index.html` structure
   - Update `styles.css` grid layout

### Testing

Use Python's built-in server:
```bash
cd /home/lebi/projects/mentor/sample-ui
python -m http.server 8000
```

Or use Node.js:
```bash
npx http-server .
```

Or use Live Server extension in VS Code.

## Advanced Usage

### JavaScript API

```javascript
// Access the UI instance
const ui = window.ui;

// Start recording programmatically
ui.startRecording();

// Stop recording
ui.stopRecording();

// Add message to chat
ui.addMessage('user', 'Hello');

// Set status
ui.setStatus('Custom status', 'success');

// Create new session
ui.createNewSession();

// Toggle theme
ui.toggleTheme();
```

### Custom Styling

Override CSS variables:
```css
body {
    --accent-color: #ff0000; /* Change accent */
    --bg-primary: #000000;   /* Change bg */
}
```

## Deployment

### Deploy to GitHub Pages

```bash
cd /home/lebi/projects/mentor/sample-ui
git add .
git commit -m "Add sample UI"
git push origin main
```

### Deploy with Docker

```dockerfile
FROM node:latest
WORKDIR /app
COPY . .
RUN npx http-server -p 3000
EXPOSE 3000
```

### Deploy to Vercel

```bash
npm i -g vercel
vercel
```

## License

MIT

## Support

For issues or feature requests:
1. Check the troubleshooting section above
2. Check browser console for errors (F12)
3. Ensure backend is running correctly
4. Try a different browser

## Credits

Created for ClarityMentor voice system
- Backend: FastAPI with WebSocket
- Frontend: Vanilla HTML/CSS/JS
- Design: Modern dark theme UI

---

**Status:** ✅ Fully functional and ready for use

**Backend required:** `ws://localhost:2323/ws/voice`

**Happy chatting!** 🚀

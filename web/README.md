# AI Eyes - Vietnamese Vision Assistant Web Client

A modern React TypeScript web application for real-time object detection with Vietnamese speech synthesis. This frontend connects to a Python backend running YOLOv5 inference and provides an intuitive interface for vision assistance.

## 🚀 Features

- **Real-time Object Detection**: Camera capture with live YOLOv5 inference
- **Vietnamese Speech Synthesis**: Text-to-speech with Web Speech API and backend fallback
- **Anti-spam Speech Logic**: Intelligent deduplication and throttling
- **Dark Theme UI**: Modern glassmorphism design with Tailwind CSS
- **Keyboard Shortcuts**: Full keyboard navigation support
- **Responsive Design**: Works on desktop and mobile devices
- **Accessibility**: ARIA labels and focus management
- **Real-time Transcript**: History of spoken descriptions
- **Snapshot Gallery**: Captured frames with annotations

## 🛠 Tech Stack

- **Frontend**: React 18 + TypeScript + Vite
- **Styling**: Tailwind CSS with glassmorphism effects
- **Animations**: Framer Motion
- **Icons**: Lucide React
- **State Management**: React Context + Custom Hooks
- **Speech**: Web Speech API with backend TTS fallback
- **Camera**: getUserMedia API

## 📦 Installation

```bash
# Navigate to the web directory
cd web

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the `web/` directory:

```bash
VITE_API_BASE=http://localhost:8000
```

### API Proxy

The Vite dev server is configured to proxy `/api` requests to the backend:

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
```

## 🎮 Usage

### Starting the Application

1. **Start the Python backend** (from the parent directory):
   ```bash
   streamlit run main.py
   ```

2. **Start the React frontend**:
   ```bash
   cd web
   npm run dev
   ```

3. **Open browser** to `http://localhost:5173`

### Basic Controls

- **Start/Stop Camera**: Click the Start/Stop button or press `S`
- **Continuous Mode**: Toggle automatic scene descriptions with `C`
- **Describe Now**: Single-shot analysis with `D` or the button
- **Mute/Unmute**: Control speech output with `M` or the header button
- **Settings**: Click the gear icon to configure options
- **Help**: Press `?` to see all keyboard shortcuts

### Settings Panel

- **API Base URL**: Configure backend endpoint
- **Confidence Threshold**: Adjust detection sensitivity (0-100%)
- **Object Classes**: Select which objects to detect
- **Speech Settings**: Configure TTS and timing
- **Min Speech Interval**: Throttle between utterances (500-3000ms)
- **Deduplication Window**: Prevent repeated speech (1-10s)

## 🔌 API Integration

### Backend Endpoints

The frontend expects these endpoints from the Python backend:

#### POST /api/infer
```typescript
// Request (multipart/form-data)
{
  file?: Blob,           // JPEG frame
  conf: number,          // 0-1 confidence
  classes: string[],     // Object classes to detect
  continuous: boolean,   // Continuous mode flag
  pull?: boolean         // Let backend capture frame
}

// Response
{
  sentences: string[],           // Vietnamese descriptions
  annotatedImage?: string,       // Base64 encoded image
  metrics?: {
    fps?: number,
    infer_ms?: number,
    queue?: number
  },
  speak?: boolean               // Whether to speak the result
}
```

#### POST /api/tts (optional)
```typescript
// Request
{
  text: string,
  lang: string
}

// Response
{
  url: string  // Audio file URL
}
```

#### GET /health
Health check endpoint for monitoring backend availability.

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `S` | Start/Stop camera |
| `C` | Toggle continuous mode |
| `D` | Describe current scene |
| `M` | Mute/Unmute voice |
| `?` | Show keyboard shortcuts |
| `Esc` | Close modals/drawers |

## 🎨 UI Components

### Header
- Status indicators (camera, voice, API health)
- Real-time metrics (FPS, inference time, confidence)
- Settings and mute controls

### Controls
- Primary action buttons with visual feedback
- Mode toggles with clear state indication
- Loading states and progress indicators

### Live View
- Video stream with overlay canvas
- Center grid for composition reference
- Error handling and permission prompts

### Transcript
- Chronological list of Vietnamese descriptions
- Replay and copy functionality
- Visual distinction for spoken vs. unspoken text

### Snapshots
- Grid of captured frames with captions
- Download annotated images
- Automatic cleanup (max 12 snapshots)

### Settings Drawer
- Comprehensive configuration options
- Real-time setting updates
- Reset to defaults functionality

## 🚨 Error Handling

- **Camera Permission**: Clear instructions for enabling access
- **API Connectivity**: Health checks with retry mechanisms
- **Network Errors**: Toast notifications with actionable feedback
- **Speech Failures**: Automatic fallback between TTS methods
- **Validation**: Input validation with user-friendly messages

## 📱 Accessibility

- **ARIA Labels**: All interactive elements properly labeled
- **Keyboard Navigation**: Full keyboard support with focus management
- **Screen Readers**: Semantic HTML and live regions
- **High Contrast**: Dark theme with sufficient color contrast
- **Motion Preferences**: Respects `prefers-reduced-motion`

## 🔧 Development

### Project Structure

```
web/src/
├── components/        # React components
│   ├── Header.tsx
│   ├── Controls.tsx
│   ├── LiveView.tsx
│   ├── Transcript.tsx
│   ├── Snapshots.tsx
│   ├── SettingsDrawer.tsx
│   ├── ShortcutHelp.tsx
│   └── Toast.tsx
├── hooks/            # Custom React hooks
│   ├── useCamera.ts
│   ├── useSpeech.ts
│   └── useLocalStorage.ts
├── lib/             # Utility functions
│   ├── api.ts
│   ├── speech.ts
│   ├── throttle.ts
│   ├── draw.ts
│   └── types.ts
├── state/           # Context providers
│   ├── SettingsContext.tsx
│   └── SessionContext.tsx
├── App.tsx          # Main application
├── main.tsx         # Entry point
└── index.css        # Global styles
```

### Building

```bash
# Development build
npm run dev

# Production build
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## 🐛 Troubleshooting

### Camera Issues
- Check browser permissions
- Ensure HTTPS or localhost
- Try different browsers
- Check camera hardware

### API Connection
- Verify backend is running on correct port
- Check CORS configuration
- Validate API base URL in settings
- Monitor network tab for errors

### Speech Problems
- Enable browser TTS in settings
- Check audio permissions
- Try backend TTS fallback
- Verify Vietnamese language support

### Performance
- Lower confidence threshold
- Reduce object classes
- Increase speech intervals
- Check browser performance

## 📄 License

This project is part of the AI Eyes Vietnamese Vision Assistant system.

---

**Built with ❤️ for the visually impaired community**
// Core TypeScript interfaces for the AI Eyes application

export interface InferResponse {
  sentences: string[];
  annotatedImage?: string; // base64 encoded JPEG
  metrics?: {
    fps?: number;
    infer_ms?: number;
    queue?: number;
  };
  speak?: boolean;
}

export interface TTSResponse {
  url: string;
}

export interface Settings {
  apiBase: string;
  confidence: number; // 0..1
  classes: string[]; // e.g., ["person", "car"]
  continuous: boolean;
  autoInterval: number; // Auto capture interval in milliseconds
  minIntervalMs: number; // throttle between requests
  dedupeWindowSec: number; // do not repeat same sentence within N seconds
  browserTTS: boolean; // if false, try /api/tts
  muted: boolean;
}

export interface TranscriptEntry {
  id: string;
  text: string;
  timestamp: Date;
  spoken: boolean;
}

export interface SnapshotEntry {
  id: string;
  image: string; // base64 or blob URL
  annotatedImage?: string; // base64 encoded
  caption: string;
  timestamp: Date;
}

export interface CameraState {
  isActive: boolean;
  stream: MediaStream | null;
  error: string | null;
}

export interface SpeechState {
  isMuted: boolean;
  isSupported: boolean;
  lastSpokenTime: number;
  dedupeCache: Map<string, number>;
}

export const DEFAULT_SETTINGS: Settings = {
  apiBase: import.meta.env.VITE_API_BASE || 'http://localhost:8000',
  confidence: 0.35,
  classes: ['person', 'car', 'bus', 'bicycle', 'motorcycle', 'dog', 'cat'],
  continuous: false,
  autoInterval: 5000, // 5 seconds default for auto capture
  minIntervalMs: 1200,
  dedupeWindowSec: 3.0,
  browserTTS: true,
  muted: false,
};

export const AVAILABLE_CLASSES = [
  'person', 'car', 'bus', 'bicycle', 'motorcycle', 
  'dog', 'cat', 'bird', 'truck', 'boat'
] as const;

export type AvailableClass = typeof AVAILABLE_CLASSES[number];
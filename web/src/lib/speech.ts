// Speech synthesis utilities with Vietnamese support and anti-spam

let viVoice: SpeechSynthesisVoice | null = null;
let lastSpoken = '';
let lastAt = 0;
const MIN_GAP_MS = 1500;

function normalize(s: string) {
  return s.toLowerCase().replace(/\s+/g, ' ').trim();
}

function loadVoicesOnce(): Promise<SpeechSynthesisVoice[]> {
  const have = window.speechSynthesis.getVoices();
  if (have.length) return Promise.resolve(have);
  return new Promise(res => {
    const h = () => { 
      const v = window.speechSynthesis.getVoices(); 
      if (v.length) { 
        window.speechSynthesis.removeEventListener('voiceschanged', h); 
        res(v); 
      }
    };
    window.speechSynthesis.addEventListener('voiceschanged', h);
  });
}

export async function initVietnameseVoice() {
  try {
    const voices = await loadVoicesOnce();
    viVoice =
      voices.find(v => v.lang?.toLowerCase().startsWith('vi')) ||
      voices.find(v => /vietnam/i.test(v.name)) ||
      voices.find(v => /microsoft.*an/i.test(v.name)) || // Microsoft An - Vietnamese voice
      null;
    console.log('✅ VN voice initialized:', viVoice?.name ?? 'none available');
    console.log('📋 Available voices:', voices.map(v => `${v.name} (${v.lang})`));
  } catch (error) {
    console.error('❌ Failed to init Vietnamese voice:', error);
  }
}

export function speakVi(text: string, opt: {force?: boolean} = {}) {
  const now = Date.now();
  const norm = normalize(text);
  
  console.log('🗣️ speakVi called:', { text, norm, force: opt.force, viVoice: viVoice?.name });
  
  // If no Vietnamese voice loaded, try to init again
  if (!viVoice) {
    console.warn('⚠️ No Vietnamese voice available, attempting re-init...');
    initVietnameseVoice().then(() => {
      if (viVoice) {
        console.log('✅ Voice loaded, retrying speech...');
        speakVi(text, opt); // Retry once
      }
    });
    return;
  }
  
  if (!opt.force) {
    if (norm === normalize(lastSpoken)) {
      console.log('⚠️ Blocked: same as last spoken');
      return;
    }
    if (now - lastAt < MIN_GAP_MS) {
      console.log('⚠️ Blocked: too soon, gap:', now - lastAt);
      return;
    }
  }
  
  lastSpoken = text;
  lastAt = now;

  const u = new SpeechSynthesisUtterance(text);
  u.lang = 'vi-VN';
  if (viVoice) u.voice = viVoice;
  u.rate = 1.0; 
  u.pitch = 1.0; 
  u.volume = 1.0;

  console.log('🔊 Speaking:', { text, lang: u.lang, voice: u.voice?.name });
  
  window.speechSynthesis.cancel(); // cắt câu trước nếu còn đang phát
  window.speechSynthesis.speak(u);
}

/**
 * Speech synthesis manager with deduplication and throttling (legacy compatibility)
 */
export class SpeechManager {
  private synthesis: SpeechSynthesis;
  private voices: SpeechSynthesisVoice[] = [];
  private vietnameseVoice: SpeechSynthesisVoice | null = null;
  private lastSpokenTime = 0;
  private dedupeCache = new Map<string, number>();
  private minIntervalMs: number;
  private dedupeWindowMs: number;
  private isMuted = false;

  constructor(minIntervalMs = 1200, dedupeWindowMs = 3000) {
    this.synthesis = window.speechSynthesis;
    this.minIntervalMs = minIntervalMs;
    this.dedupeWindowMs = dedupeWindowMs;
    this.loadVoices();
    
    // Handle voice loading (Chrome loads voices asynchronously)
    if (this.synthesis.onvoiceschanged !== undefined) {
      this.synthesis.onvoiceschanged = () => this.loadVoices();
    }
  }

  private loadVoices() {
    this.voices = this.synthesis.getVoices();
    
    // Find Vietnamese voice with multiple fallback patterns
    this.vietnameseVoice = this.voices.find(voice => {
      const lang = voice.lang.toLowerCase();
      const name = voice.name.toLowerCase();
      return (
        lang.includes('vi-vn') ||
        lang.includes('vi') ||
        lang.includes('vietnam') ||
        name.includes('vietnam') ||
        name.includes('vietnamese') ||
        name.includes('vi-vn')
      );
    }) || null;

    console.log('Available voices:', this.voices.length);
    if (this.vietnameseVoice) {
      console.log('Vietnamese voice found:', this.vietnameseVoice.name);
    } else if (this.voices.length === 0) {
      console.log('No voices loaded yet, will retry...');
      // Retry after a short delay
      setTimeout(() => this.loadVoices(), 100);
    } else {
      console.warn('No Vietnamese voice found, using default');
    }
  }

  /**
   * Check if speech synthesis is supported
   */
  isSupported(): boolean {
    return 'speechSynthesis' in window;
  }

  /**
   * Check if should speak based on throttling and deduplication
   */
  private shouldSpeak(text: string): boolean {
    const now = Date.now();
    
    // Check mute status
    if (this.isMuted) {
      return false;
    }

    // Check minimum interval throttling
    if (now - this.lastSpokenTime < this.minIntervalMs) {
      console.log('Speech throttled: too soon after last utterance');
      return false;
    }

    // Check deduplication
    const lastSpokenTime = this.dedupeCache.get(text);
    if (lastSpokenTime && (now - lastSpokenTime) < this.dedupeWindowMs) {
      console.log('Speech deduplicated: same text spoken recently');
      return false;
    }

    return true;
  }

  /**
   * Speak text with Vietnamese voice
   */
  speak(text: string): Promise<boolean> {
    return new Promise((resolve) => {
      if (!this.isSupported()) {
        console.error('Speech synthesis not supported');
        resolve(false);
        return;
      }

      // If no voices loaded yet, try to reload
      if (this.voices.length === 0) {
        this.loadVoices();
      }

      if (!this.shouldSpeak(text)) {
        resolve(false);
        return;
      }

      // Cancel any ongoing speech
      this.synthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      
      // Use Vietnamese voice if available
      if (this.vietnameseVoice) {
        utterance.voice = this.vietnameseVoice;
        utterance.lang = 'vi-VN';
      } else {
        // Try to find Vietnamese voice again
        this.loadVoices();
        if (this.vietnameseVoice) {
          utterance.voice = this.vietnameseVoice;
        }
        utterance.lang = 'vi-VN';
      }

      // Configure speech parameters
      utterance.rate = 0.9;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;

      utterance.onstart = () => {
        const now = Date.now();
        this.lastSpokenTime = now;
        this.dedupeCache.set(text, now);
        console.log('Speaking:', text);
      };

      utterance.onend = () => {
        resolve(true);
      };

      utterance.onerror = (event) => {
        console.error('Speech synthesis error:', event.error);
        resolve(false);
      };

      this.synthesis.speak(utterance);
    });
  }

  /**
   * Stop current speech
   */
  stop() {
    this.synthesis.cancel();
  }

  /**
   * Set muted state
   */
  setMuted(muted: boolean) {
    this.isMuted = muted;
  }

  /**
   * Update settings
   */
  updateSettings(minIntervalMs: number, dedupeWindowMs: number) {
    this.minIntervalMs = minIntervalMs;
    this.dedupeWindowMs = dedupeWindowMs;
  }
}

/**
 * Play TTS audio from backend URL
 */
export async function playTTSFromBackend(url: string): Promise<boolean> {
  try {
    const audio = new Audio(url);
    await audio.play();
    return true;
  } catch (error) {
    console.error('Failed to play TTS audio:', error);
    return false;
  }
}
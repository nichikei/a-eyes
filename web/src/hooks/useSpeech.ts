// Speech synthesis hook with Vietnamese support and anti-spam logic

import { useState, useEffect, useRef, useCallback } from 'react';
import { SpeechManager, playTTSFromBackend } from '../lib/speech';
import { getAPIClient } from '../lib/api';
import type { SpeechState, Settings } from '../lib/types';

export function useSpeech(settings: Settings) {
  const [state, setState] = useState<SpeechState>({
    isMuted: settings.muted,
    isSupported: 'speechSynthesis' in window,
    lastSpokenTime: 0,
    dedupeCache: new Map(),
  });

  const speechManagerRef = useRef<SpeechManager | null>(null);

  // Initialize speech manager
  useEffect(() => {
    if (state.isSupported) {
      speechManagerRef.current = new SpeechManager(
        settings.minIntervalMs,
        settings.dedupeWindowSec * 1000
      );
    }

    return () => {
      if (speechManagerRef.current) {
        speechManagerRef.current.stop();
      }
    };
  }, [settings.minIntervalMs, settings.dedupeWindowSec, state.isSupported]);

  // Update settings
  useEffect(() => {
    if (speechManagerRef.current) {
      speechManagerRef.current.updateSettings(
        settings.minIntervalMs,
        settings.dedupeWindowSec * 1000
      );
      speechManagerRef.current.setMuted(settings.muted);
    }
    
    setState(prev => ({ ...prev, isMuted: settings.muted }));
  }, [settings.minIntervalMs, settings.dedupeWindowSec, settings.muted]);

  /**
   * Speak text using browser TTS or backend fallback
   */
  const speak = useCallback(async (text: string): Promise<boolean> => {
    if (!text.trim()) return false;

    try {
      // Use browser TTS if enabled and supported
      if (settings.browserTTS && speechManagerRef.current) {
        const success = await speechManagerRef.current.speak(text);
        if (success) {
          setState(prev => ({
            ...prev,
            lastSpokenTime: Date.now(),
          }));
          return true;
        }
      }

      // Fallback to backend TTS
      if (!settings.browserTTS || !state.isSupported) {
        try {
          const apiClient = getAPIClient(settings);
          const response = await apiClient.textToSpeech(text, 'vi');
          const success = await playTTSFromBackend(response.url);
          
          if (success) {
            setState(prev => ({
              ...prev,
              lastSpokenTime: Date.now(),
            }));
            return true;
          }
        } catch (error) {
          console.error('Backend TTS failed:', error);
          
          // Last resort: try browser TTS even if not preferred
          if (speechManagerRef.current && !settings.browserTTS) {
            console.log('Falling back to browser TTS');
            const success = await speechManagerRef.current.speak(text);
            if (success) {
              setState(prev => ({
                ...prev,
                lastSpokenTime: Date.now(),
              }));
              return true;
            }
          }
        }
      }

      return false;
    } catch (error) {
      console.error('Speech synthesis failed:', error);
      return false;
    }
  }, [settings, state.isSupported]);

  /**
   * Stop current speech
   */
  const stop = useCallback(() => {
    if (speechManagerRef.current) {
      speechManagerRef.current.stop();
    }
  }, []);

  /**
   * Toggle mute state
   */
  const toggleMute = useCallback(() => {
    const newMuted = !state.isMuted;
    
    if (speechManagerRef.current) {
      speechManagerRef.current.setMuted(newMuted);
    }
    
    setState(prev => ({ ...prev, isMuted: newMuted }));
    
    return newMuted;
  }, [state.isMuted]);

  /**
   * Check if text should be spoken (for external validation)
   */
  const shouldSpeak = useCallback((text: string): boolean => {
    const now = Date.now();
    
    // Check mute status
    if (state.isMuted) return false;
    
    // Check minimum interval
    if (now - state.lastSpokenTime < settings.minIntervalMs) {
      return false;
    }
    
    // Check deduplication
    const dedupeWindowMs = settings.dedupeWindowSec * 1000;
    const lastSpokenTime = state.dedupeCache.get(text);
    if (lastSpokenTime && (now - lastSpokenTime) < dedupeWindowMs) {
      return false;
    }
    
    return true;
  }, [state.isMuted, state.lastSpokenTime, state.dedupeCache, settings.minIntervalMs, settings.dedupeWindowSec]);

  /**
   * Get speech status
   */
  const getStatus = useCallback(() => {
    return {
      ...state,
      managerStatus: null, // SpeechManager doesn't expose getStatus()
    };
  }, [state]);

  return {
    ...state,
    speak,
    stop,
    toggleMute,
    shouldSpeak,
    getStatus,
  };
}
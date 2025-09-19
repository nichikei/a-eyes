// Settings context for managing application configuration

import React, { createContext, useContext, useCallback } from 'react';
import { useLocalStorage } from '../hooks/useLocalStorage';
import type { Settings, AvailableClass } from '../lib/types';
import { DEFAULT_SETTINGS } from '../lib/types';

interface SettingsContextType {
  settings: Settings;
  updateSettings: (updates: Partial<Settings>) => void;
  resetSettings: () => void;
  toggleClass: (className: AvailableClass) => void;
  updateApiBase: (url: string) => void;
  toggleContinuous: () => void;
  toggleMute: () => void;
  toggleBrowserTTS: () => void;
}

const SettingsContext = createContext<SettingsContextType | null>(null);

export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const [settings, setSettings] = useLocalStorage<Settings>('ai-eyes-settings', DEFAULT_SETTINGS);

  const updateSettings = useCallback((updates: Partial<Settings>) => {
    setSettings(prev => ({
      ...prev,
      ...updates,
    }));
  }, [setSettings]);

  const resetSettings = useCallback(() => {
    setSettings(DEFAULT_SETTINGS);
  }, [setSettings]);

  const toggleClass = useCallback((className: AvailableClass) => {
    setSettings(prev => ({
      ...prev,
      classes: prev.classes.includes(className)
        ? prev.classes.filter(c => c !== className)
        : [...prev.classes, className],
    }));
  }, [setSettings]);

  const updateApiBase = useCallback((url: string) => {
    setSettings(prev => ({
      ...prev,
      apiBase: url,
    }));
  }, [setSettings]);

  const toggleContinuous = useCallback(() => {
    setSettings(prev => ({
      ...prev,
      continuous: !prev.continuous,
    }));
  }, [setSettings]);

  const toggleMute = useCallback(() => {
    setSettings(prev => ({
      ...prev,
      muted: !prev.muted,
    }));
  }, [setSettings]);

  const toggleBrowserTTS = useCallback(() => {
    setSettings(prev => ({
      ...prev,
      browserTTS: !prev.browserTTS,
    }));
  }, [setSettings]);

  const value: SettingsContextType = {
    settings,
    updateSettings,
    resetSettings,
    toggleClass,
    updateApiBase,
    toggleContinuous,
    toggleMute,
    toggleBrowserTTS,
  };

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings(): SettingsContextType {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
}
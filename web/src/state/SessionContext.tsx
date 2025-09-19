// Session context for managing application state and data

import React, { createContext, useContext, useState, useCallback } from 'react';
import type { TranscriptEntry, SnapshotEntry } from '../lib/types';
import { generateId } from '../lib/throttle';

interface SessionState {
  transcript: TranscriptEntry[];
  snapshots: SnapshotEntry[];
  isLoading: boolean;
  lastError: string | null;
  metrics: {
    fps?: number;
    infer_ms?: number;
    queue?: number;
  };
}

interface SessionContextType {
  state: SessionState;
  addTranscriptEntry: (text: string, spoken?: boolean) => void;
  addSnapshot: (image: string, caption: string, annotatedImage?: string) => void;
  clearTranscript: () => void;
  clearSnapshots: () => void;
  clearAll: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  updateMetrics: (metrics: SessionState['metrics']) => void;
  replayTranscript: (entry: TranscriptEntry) => void;
}

const initialState: SessionState = {
  transcript: [],
  snapshots: [],
  isLoading: false,
  lastError: null,
  metrics: {},
};

const SessionContext = createContext<SessionContextType | null>(null);

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<SessionState>(initialState);

  const addTranscriptEntry = useCallback((text: string, spoken = false) => {
    const entry: TranscriptEntry = {
      id: generateId(),
      text,
      timestamp: new Date(),
      spoken,
    };

    setState(prev => ({
      ...prev,
      transcript: [entry, ...prev.transcript].slice(0, 100), // Keep last 100 entries
    }));
  }, []);

  const addSnapshot = useCallback((image: string, caption: string, annotatedImage?: string) => {
    const entry: SnapshotEntry = {
      id: generateId(),
      image,
      annotatedImage,
      caption,
      timestamp: new Date(),
    };

    setState(prev => ({
      ...prev,
      snapshots: [entry, ...prev.snapshots].slice(0, 12), // Keep last 12 snapshots
    }));
  }, []);

  const clearTranscript = useCallback(() => {
    setState(prev => ({
      ...prev,
      transcript: [],
    }));
  }, []);

  const clearSnapshots = useCallback(() => {
    setState(prev => ({
      ...prev,
      snapshots: [],
    }));
  }, []);

  const clearAll = useCallback(() => {
    setState(initialState);
  }, []);

  const setLoading = useCallback((loading: boolean) => {
    setState(prev => ({
      ...prev,
      isLoading: loading,
    }));
  }, []);

  const setError = useCallback((error: string | null) => {
    setState(prev => ({
      ...prev,
      lastError: error,
    }));
  }, []);

  const updateMetrics = useCallback((metrics: SessionState['metrics']) => {
    setState(prev => ({
      ...prev,
      metrics,
    }));
  }, []);

  const replayTranscript = useCallback((entry: TranscriptEntry) => {
    // This will be handled by the parent component
    // Just dispatch a custom event for now
    window.dispatchEvent(new CustomEvent('replay-transcript', { 
      detail: { text: entry.text } 
    }));
  }, []);

  const value: SessionContextType = {
    state,
    addTranscriptEntry,
    addSnapshot,
    clearTranscript,
    clearSnapshots,
    clearAll,
    setLoading,
    setError,
    updateMetrics,
    replayTranscript,
  };

  return (
    <SessionContext.Provider value={value}>
      {children}
    </SessionContext.Provider>
  );
}

export function useSession(): SessionContextType {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
}
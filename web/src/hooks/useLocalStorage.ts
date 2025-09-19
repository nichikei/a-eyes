// Local storage hook for persisting settings

import { useState, useEffect } from 'react';

/**
 * Hook for managing localStorage with JSON serialization
 */
export function useLocalStorage<T>(key: string, defaultValue: T) {
  const [value, setValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error);
      return defaultValue;
    }
  });

  useEffect(() => {
    try {
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error);
    }
  }, [key, value]);

  return [value, setValue] as const;
}

/**
 * Hook for managing localStorage with automatic cleanup
 */
export function useLocalStorageWithCleanup<T>(
  key: string, 
  defaultValue: T,
  maxAge?: number // milliseconds
) {
  const [value, setValue] = useLocalStorage(key, defaultValue);

  useEffect(() => {
    if (!maxAge) return;

    const cleanup = () => {
      try {
        const stored = window.localStorage.getItem(key);
        if (stored) {
          const parsed = JSON.parse(stored);
          if (parsed._timestamp && Date.now() - parsed._timestamp > maxAge) {
            window.localStorage.removeItem(key);
            setValue(defaultValue);
          }
        }
      } catch (error) {
        console.error(`Error during localStorage cleanup for "${key}":`, error);
      }
    };

    cleanup();
    const interval = setInterval(cleanup, maxAge);
    
    return () => clearInterval(interval);
  }, [key, defaultValue, maxAge, setValue]);

  const setValueWithTimestamp = (newValue: T) => {
    if (maxAge) {
      setValue({
        ...newValue,
        _timestamp: Date.now(),
      } as T);
    } else {
      setValue(newValue);
    }
  };

  return [value, setValueWithTimestamp] as const;
}
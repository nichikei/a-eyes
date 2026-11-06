// Utility functions for throttling and performance

/**
 * Creates a throttled version of a function that only executes once per interval
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout | null = null;
  let lastExecTime = 0;

  return (...args: Parameters<T>) => {
    const currentTime = Date.now();

    if (currentTime - lastExecTime > delay) {
      // Execute immediately if enough time has passed
      lastExecTime = currentTime;
      func(...args);
    } else {
      // Schedule execution for later
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      
      timeoutId = setTimeout(() => {
        lastExecTime = Date.now();
        func(...args);
        timeoutId = null;
      }, delay - (currentTime - lastExecTime));
    }
  };
}

/**
 * Creates a debounced version of a function that delays execution
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout | null = null;

  return (...args: Parameters<T>) => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    
    timeoutId = setTimeout(() => {
      func(...args);
      timeoutId = null;
    }, delay);
  };
}

/**
 * Creates a rate-limited queue that processes items at a fixed interval
 */
export class RateLimitedQueue<T> {
  private queue: T[] = [];
  private processing = false;
  private intervalMs: number;
  private processor: (item: T) => void | Promise<void>;

  constructor(intervalMs: number, processor: (item: T) => void | Promise<void>) {
    this.intervalMs = intervalMs;
    this.processor = processor;
  }

  enqueue(item: T) {
    this.queue.push(item);
    this.startProcessing();
  }

  clear() {
    this.queue.length = 0;
  }

  size() {
    return this.queue.length;
  }

  private async startProcessing() {
    if (this.processing) return;
    
    this.processing = true;
    
    while (this.queue.length > 0) {
      const item = this.queue.shift()!;
      
      try {
        await this.processor(item);
      } catch (error) {
        console.error('Queue processor error:', error);
      }
      
      // Wait for the specified interval before processing next item
      if (this.queue.length > 0) {
        await new Promise(resolve => setTimeout(resolve, this.intervalMs));
      }
    }
    
    this.processing = false;
  }
}

/**
 * Format timestamp for display
 */
export function formatTimestamp(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(date);
}

/**
 * Generate unique ID
 */
export function generateId(): string {
  return Math.random().toString(36).substring(2) + Date.now().toString(36);
}

/**
 * Convert blob to base64 string
 */
export function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

/**
 * Download data as file
 */
export function downloadFile(data: string, filename: string, mimeType: string = 'application/octet-stream') {
  const blob = new Blob([data], { type: mimeType });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Download base64 image
 */
export function downloadBase64Image(base64: string, filename: string) {
  const link = document.createElement('a');
  link.href = base64;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
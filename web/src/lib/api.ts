/// API client for communicating with the Python backend

import type { InferResponse, TTSResponse, Settings } from './types';

export class APIClient {
  private baseURL: string;
  private abortController: AbortController | null = null;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  updateBaseURL(url: string) {
    this.baseURL = url;
  }

  // Cancel any in-flight requests
  abort() {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
  }

  /**
   * Submit inference request to backend
   * @param options - Inference options
   * @returns Promise with inference response
   */
  async infer(options: {
    file?: Blob;
    conf: number;
    classes: string[];
    continuous: boolean;
    pull?: boolean;
  }): Promise<InferResponse> {
    // Cancel previous request
    this.abort();
    this.abortController = new AbortController();

    const formData = new FormData();
    
    if (options.file) {
      formData.append('file', options.file, 'frame.jpg');
    } else if (options.pull) {
      formData.append('pull', '1');
    }

    formData.append('conf', options.conf.toString());
    formData.append('continuous', options.continuous.toString());
    
    // Add class filters
    options.classes.forEach(cls => {
      formData.append('classes[]', cls);
    });

    try {
      const response = await fetch(`${this.baseURL}/api/infer`, {
        method: 'POST',
        body: formData,
        signal: this.abortController.signal,
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      const result: InferResponse = await response.json();
      return result;
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Request cancelled');
      }
      throw error;
    } finally {
      this.abortController = null;
    }
  }

  /**
   * Request TTS audio from backend
   * @param text - Text to synthesize
   * @param lang - Language code (default: 'vi')
   * @returns Promise with TTS response
   */
  async textToSpeech(text: string, lang: string = 'vi'): Promise<TTSResponse> {
    try {
      const response = await fetch(`${this.baseURL}/api/tts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text, lang }),
      });

      if (!response.ok) {
        throw new Error(`TTS API Error: ${response.status} ${response.statusText}`);
      }

      const result: TTSResponse = await response.json();
      return result;
    } catch (error) {
      throw new Error(`TTS request failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Health check for the API
   * @returns Promise<boolean> - true if API is healthy
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseURL}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000), // 5 second timeout
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}

// Singleton instance
let apiClient: APIClient;

export function getAPIClient(settings?: Settings): APIClient {
  const baseURL = settings?.apiBase || import.meta.env.VITE_API_BASE || 'http://localhost:8000';
  
  if (!apiClient) {
    apiClient = new APIClient(baseURL);
  } else {
    apiClient.updateBaseURL(baseURL);
  }
  
  return apiClient;
}
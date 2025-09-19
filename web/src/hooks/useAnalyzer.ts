// Analyzer hook with requestAnimationFrame throttling and anti-spam speech

import { useEffect, useRef } from 'react';
import { speakVi } from '../lib/speech';

export function useAnalyzer(running: boolean, canvasRef: React.RefObject<HTMLCanvasElement>) {
  const lastTextRef = useRef('');

  useEffect(() => {
    if (!running) return;
    let alive = true;
    let lastCall = 0;

    const tick = async () => {
      if (!alive) return;
      const now = performance.now();
      if (now - lastCall < 500) { 
        requestAnimationFrame(tick); 
        return; 
      } // 2fps mô tả
      lastCall = now;

      try {
        // Get current frame from canvas if needed
        let blob: Blob | null = null;
        if (canvasRef.current) {
          blob = await new Promise<Blob>(r => 
            canvasRef.current!.toBlob(b => r(b!), 'image/jpeg', 0.8)
          );
        }

        // Call backend API (adjust URL to match your backend)
        const formData = new FormData();
        if (blob) {
          formData.append('file', blob);
        }
        formData.append('conf', '0.5');
        formData.append('continuous', 'true');

        const resp = await fetch('/api/infer', { 
          method: 'POST',
          body: formData
        });
        
        const data = await resp.json();
        
        // Extract text from response
        const text = (data?.sentences?.[0] ?? '').trim();

        // Only speak if text is new and different
        if (text && text !== lastTextRef.current) {
          lastTextRef.current = text;
          speakVi(text); // chống spam đã xử lý trong speech.ts
        }
      } catch (e) {
        console.warn('analyze error', e);
      }
      requestAnimationFrame(tick);
    };

    requestAnimationFrame(tick);
    return () => { alive = false; };
  }, [running, canvasRef]);
}
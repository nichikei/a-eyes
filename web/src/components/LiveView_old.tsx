// Live video view with overlay canvas for annotations

import { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { drawCenterGrid, drawStatusText, clearCanvas, resizeCanvas } from '../lib/draw';

interface LiveViewProps {
  videoRef: React.RefObject<HTMLVideoElement>;
  canvasRef: React.RefObject<HTMLCanvasElement>;
  isActive: boolean;
  isLoading: boolean;
  error: string | null;
}

export function LiveView({ videoRef, canvasRef, isActive, isLoading, error }: LiveViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Handle canvas overlay updates
  useEffect(() => {
    if (!canvasRef.current || !videoRef.current) return;

    const canvas = canvasRef.current;
    const video = videoRef.current;

    const updateOverlay = () => {
      // Resize canvas to match video
      resizeCanvas(canvas, video);
      
      // Clear previous drawings
      clearCanvas(canvas);
      
      // Draw center grid
      drawCenterGrid(canvas, {
        color: '#ffffff',
        opacity: 0.3,
        lineWidth: 1,
      });

      // Draw status
      if (isLoading) {
        drawStatusText(canvas, 'Analyzing...', 'top-left', {
          color: '#60a5fa',
          backgroundColor: 'rgba(59, 130, 246, 0.2)',
        });
      }
    };

    // Update overlay when video dimensions change
    const handleVideoLoad = () => {
      updateOverlay();
    };

    const handleVideoResize = () => {
      updateOverlay();
    };

    video.addEventListener('loadedmetadata', handleVideoLoad);
    video.addEventListener('resize', handleVideoResize);
    
    // Initial draw
    if (video.videoWidth > 0) {
      updateOverlay();
    }

    // Animation frame for continuous updates
    let animationId: number;
    const animate = () => {
      if (isActive && video.videoWidth > 0) {
        updateOverlay();
      }
      animationId = requestAnimationFrame(animate);
    };
    animate();

    return () => {
      video.removeEventListener('loadedmetadata', handleVideoLoad);
      video.removeEventListener('resize', handleVideoResize);
      cancelAnimationFrame(animationId);
    };
  }, [videoRef, canvasRef, isActive, isLoading]);

  return (
    <div className="glass rounded-2xl overflow-hidden border border-slate-700/50">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-700/50 bg-slate-800/50">
        <h2 className="font-semibold text-white">Live View</h2>
        <p className="text-sm text-slate-400">
          {isActive ? 'Camera active' : 'Camera inactive'}
        </p>
      </div>

      {/* Video container */}
      <div 
        ref={containerRef}
        className="relative aspect-video bg-slate-900 flex items-center justify-center min-h-[400px]"
      >
        {/* Video element */}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className={`
            w-full h-full object-cover
            ${isActive ? 'opacity-100' : 'opacity-50'}
            transition-opacity duration-300
          `}
        />

        {/* Overlay canvas */}
        <canvas
          ref={canvasRef}
          className="absolute inset-0 pointer-events-none"
          style={{ mixBlendMode: 'normal' }}
        />

        {/* Placeholder/Error overlay */}
        {(!isActive || error) && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="absolute inset-0 flex flex-col items-center justify-center bg-slate-900/80 backdrop-blur-sm"
          >
            {error ? (
              <div className="text-center text-red-400">
                <div className="text-4xl mb-4">⚠️</div>
                <h3 className="text-lg font-semibold mb-2">Camera Error</h3>
                <p className="text-sm text-red-300 max-w-md mx-auto">
                  {error}
                </p>
                <p className="text-xs text-slate-400 mt-2">
                  Please check camera permissions and try again
                </p>
              </div>
            ) : (
              <div className="text-center text-slate-400">
                <div className="text-4xl mb-4">📷</div>
                <h3 className="text-lg font-semibold mb-2">Camera Inactive</h3>
                <p className="text-sm">
                  Click "Start" to begin video capture
                </p>
              </div>
            )}
          </motion.div>
        )}

        {/* Loading overlay */}
        {isLoading && isActive && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="absolute top-4 left-4 flex items-center gap-2 bg-blue-500/20 border border-blue-500/30 rounded-lg px-3 py-2"
          >
            <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
            <span className="text-sm text-blue-200">Analyzing...</span>
          </motion.div>
        )}
      </div>

      {/* Footer with video info */}
      {isActive && videoRef.current && (
        <div className="px-4 py-2 border-t border-slate-700/50 bg-slate-800/30">
          <div className="flex justify-between text-xs text-slate-400">
            <span>
              Resolution: {videoRef.current.videoWidth || 0}×{videoRef.current.videoHeight || 0}
            </span>
            <span>
              Format: {videoRef.current.srcObject ? 'Live Camera' : 'No Source'}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
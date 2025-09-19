// Enhanced Live video view with modern design and advanced overlays

import { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { drawCenterGrid, drawStatusText, clearCanvas, resizeCanvas } from '../lib/draw';
import { Camera, AlertTriangle, Zap, Activity, Monitor } from 'lucide-react';

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
      
      // Draw center grid with enhanced style
      drawCenterGrid(canvas, {
        color: '#06b6d4',
        opacity: 0.4,
        lineWidth: 2,
      });

      // Draw status
      if (isLoading) {
        drawStatusText(canvas, '🔍 AI Analyzing Scene...', 'top-left', {
          color: '#06b6d4',
          backgroundColor: 'rgba(6, 182, 212, 0.15)',
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
    <motion.div 
      className="relative overflow-hidden bg-gradient-to-br from-slate-800/90 via-slate-800/80 to-slate-900/90 backdrop-blur-xl rounded-3xl border border-slate-700/50 shadow-2xl"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
    >
      {/* Background effects */}
      <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/5 via-blue-500/5 to-purple-500/5 rounded-3xl"></div>
      
      {/* Header */}
      <div className="relative px-6 py-4 border-b border-slate-700/50 bg-gradient-to-r from-slate-800/80 to-slate-800/60">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <motion.div 
              className="p-2 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-500/30"
              animate={isActive ? { scale: [1, 1.1, 1] } : {}}
              transition={{ repeat: isActive ? Infinity : 0, duration: 2 }}
            >
              <Camera className="h-5 w-5 text-cyan-400" />
            </motion.div>
            <div>
              <h2 className="font-bold text-white text-lg">Live Vision Feed</h2>
              <p className="text-sm text-slate-300">
                {isActive ? (
                  <span className="flex items-center gap-1">
                    <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                    Camera streaming
                  </span>
                ) : (
                  <span className="flex items-center gap-1">
                    <span className="w-2 h-2 bg-red-400 rounded-full"></span>
                    Camera offline
                  </span>
                )}
              </p>
            </div>
          </div>
          
          {/* Activity indicator */}
          {isActive && (
            <motion.div 
              className="flex items-center gap-2 px-3 py-1 rounded-lg bg-green-500/20 border border-green-500/30"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
            >
              <Activity className="h-4 w-4 text-green-400" />
              <span className="text-xs text-green-400 font-medium">LIVE</span>
            </motion.div>
          )}
        </div>
      </div>

      {/* Video container */}
      <div 
        ref={containerRef}
        className="relative aspect-video bg-gradient-to-br from-slate-900 to-slate-800 flex items-center justify-center min-h-[400px] overflow-hidden"
      >
        {/* Video element */}
        <motion.video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className={`
            w-full h-full object-cover
            ${isActive ? 'opacity-100' : 'opacity-30'}
            transition-all duration-500
          `}
          initial={{ scale: 1.1 }}
          animate={{ scale: isActive ? 1 : 1.05 }}
          transition={{ duration: 0.5 }}
        />

        {/* Enhanced overlay canvas */}
        <canvas
          ref={canvasRef}
          className="absolute inset-0 pointer-events-none"
          style={{ mixBlendMode: 'normal' }}
        />

        {/* Corner indicators */}
        {isActive && (
          <>
            <div className="absolute top-2 left-2 w-4 h-4 border-l-2 border-t-2 border-cyan-400/60 rounded-tl-lg"></div>
            <div className="absolute top-2 right-2 w-4 h-4 border-r-2 border-t-2 border-cyan-400/60 rounded-tr-lg"></div>
            <div className="absolute bottom-2 left-2 w-4 h-4 border-l-2 border-b-2 border-cyan-400/60 rounded-bl-lg"></div>
            <div className="absolute bottom-2 right-2 w-4 h-4 border-r-2 border-b-2 border-cyan-400/60 rounded-br-lg"></div>
          </>
        )}

        {/* Placeholder/Error overlay */}
        {(!isActive || error) && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="absolute inset-0 flex flex-col items-center justify-center bg-slate-900/90 backdrop-blur-sm"
          >
            {error ? (
              <motion.div 
                className="text-center"
                initial={{ scale: 0.9 }}
                animate={{ scale: 1 }}
              >
                <motion.div 
                  className="flex items-center justify-center w-16 h-16 mb-6 mx-auto bg-red-500/20 border border-red-500/30 rounded-2xl"
                  animate={{ rotate: [0, -5, 5, 0] }}
                  transition={{ repeat: Infinity, duration: 2 }}
                >
                  <AlertTriangle className="h-8 w-8 text-red-400" />
                </motion.div>
                <h3 className="text-xl font-bold text-red-400 mb-3">Camera Error</h3>
                <p className="text-slate-300 max-w-md mx-auto mb-2 leading-relaxed">
                  {error}
                </p>
                <p className="text-xs text-slate-500">
                  Please check camera permissions and try again
                </p>
              </motion.div>
            ) : (
              <motion.div 
                className="text-center"
                initial={{ scale: 0.9 }}
                animate={{ scale: 1 }}
              >
                <motion.div 
                  className="flex items-center justify-center w-16 h-16 mb-6 mx-auto bg-slate-700/30 border border-slate-600/50 rounded-2xl"
                  animate={{ scale: [1, 1.05, 1] }}
                  transition={{ repeat: Infinity, duration: 3 }}
                >
                  <Camera className="h-8 w-8 text-slate-400" />
                </motion.div>
                <h3 className="text-xl font-bold text-slate-300 mb-3">Camera Inactive</h3>
                <p className="text-slate-400 mb-4">
                  Click "Start Camera" to begin live vision assistance
                </p>
                <motion.div 
                  className="flex items-center justify-center gap-2 text-sm text-slate-500"
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ repeat: Infinity, duration: 2 }}
                >
                  <Zap className="h-4 w-4" />
                  <span>Ready to analyze</span>
                </motion.div>
              </motion.div>
            )}
          </motion.div>
        )}

        {/* Enhanced loading overlay */}
        {isLoading && isActive && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="absolute top-4 left-4 flex items-center gap-3 bg-cyan-500/20 border border-cyan-500/40 rounded-xl px-4 py-3 backdrop-blur-sm"
          >
            <motion.div 
              className="w-3 h-3 bg-cyan-400 rounded-full"
              animate={{ scale: [1, 1.3, 1], opacity: [1, 0.7, 1] }}
              transition={{ repeat: Infinity, duration: 1.5 }}
            />
            <span className="text-sm text-cyan-200 font-medium">AI Processing...</span>
          </motion.div>
        )}

        {/* Quality indicator */}
        {isActive && videoRef.current && (
          <motion.div
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            className="absolute top-4 right-4 flex items-center gap-2 bg-slate-800/80 border border-slate-600/50 rounded-lg px-3 py-2 backdrop-blur-sm"
          >
            <Monitor className="h-4 w-4 text-green-400" />
            <span className="text-xs text-green-400 font-mono">
              {videoRef.current.videoWidth || 0}×{videoRef.current.videoHeight || 0}
            </span>
          </motion.div>
        )}
      </div>

      {/* Enhanced footer with video info */}
      {isActive && videoRef.current && (
        <motion.div 
          className="px-6 py-3 border-t border-slate-700/50 bg-gradient-to-r from-slate-800/60 to-slate-800/40"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-4 text-slate-300">
              <span className="flex items-center gap-2">
                <Monitor className="h-4 w-4 text-cyan-400" />
                {videoRef.current.videoWidth || 0}×{videoRef.current.videoHeight || 0}
              </span>
              <span className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-green-400" />
                Live Stream
              </span>
            </div>
            <div className="text-slate-400 text-xs">
              Vietnamese AI Vision • Ready
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
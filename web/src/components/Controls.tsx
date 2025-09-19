// Modern control buttons with enhanced animations and styling

import { motion } from 'framer-motion';
import { 
  Square, 
  Repeat, 
  RotateCcw,
  Eye,
  Zap,
  Camera
} from 'lucide-react';
import { useSettings } from '../state/SettingsContext';

interface ControlsProps {
  cameraActive: boolean;
  onStartCamera: () => void;
  onStopCamera: () => void;
  onDescribeNow: () => void;
  isLoading: boolean;
}

export function Controls({ 
  cameraActive, 
  onStartCamera, 
  onStopCamera, 
  onDescribeNow,
  isLoading 
}: ControlsProps) {
  const { settings, toggleContinuous } = useSettings();

  const buttonVariants = {
    idle: { scale: 1, y: 0 },
    hover: { scale: 1.05, y: -2 },
    tap: { scale: 0.95, y: 0 }
  };

  const glowVariants = {
    idle: { opacity: 0 },
    hover: { opacity: 1 }
  };

  return (
    <motion.div 
      className="relative overflow-hidden bg-gradient-to-br from-slate-800/90 via-slate-800/80 to-slate-900/90 backdrop-blur-xl rounded-3xl p-8 border border-slate-700/50 shadow-2xl"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Background effects */}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 via-purple-500/5 to-cyan-500/5 rounded-3xl"></div>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(59,130,246,0.1),transparent_70%)]"></div>
      
      <div className="relative">
        {/* Header */}
        <div className="text-center mb-6">
          <motion.h2 
            className="text-xl font-bold bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent mb-2"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            Camera Controls
          </motion.h2>
          <motion.p 
            className="text-sm text-slate-400"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            Manage your AI vision assistant
          </motion.p>
        </div>

        <div className="flex items-center justify-center gap-6">
          {/* Start/Stop Camera */}
          <motion.button
            variants={buttonVariants}
            initial="idle"
            whileHover="hover"
            whileTap="tap"
            onClick={cameraActive ? onStopCamera : onStartCamera}
            disabled={isLoading}
            className={`
              relative flex items-center gap-3 px-8 py-4 rounded-2xl font-semibold text-lg
              transition-all duration-300 focus-ring shadow-lg
              ${cameraActive 
                ? 'bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white shadow-red-500/25' 
                : 'bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white shadow-green-500/25'
              }
              ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}
            `}
            aria-label={cameraActive ? 'Stop camera' : 'Start camera'}
          >
            <motion.div
              variants={glowVariants}
              className={`absolute inset-0 rounded-2xl blur-lg ${
                cameraActive ? 'bg-red-500/50' : 'bg-green-500/50'
              }`}
            />
            <div className="relative flex items-center gap-3">
              {cameraActive ? (
                <>
                  <Square className="h-6 w-6" />
                  Stop Camera
                </>
              ) : (
                <>
                  <Camera className="h-6 w-6" />
                  Start Camera
                </>
              )}
            </div>
          </motion.button>

          {/* Continuous Mode Toggle */}
          <motion.button
            variants={buttonVariants}
            initial="idle"
            whileHover="hover"
            whileTap="tap"
            onClick={toggleContinuous}
            disabled={isLoading}
            className={`
              relative flex items-center gap-3 px-6 py-4 rounded-2xl font-semibold
              transition-all duration-300 focus-ring border-2 shadow-lg
              ${settings.continuous
                ? 'bg-gradient-to-r from-blue-500 to-blue-600 border-blue-400 hover:from-blue-600 hover:to-blue-700 text-white shadow-blue-500/25' 
                : 'bg-slate-800/50 border-blue-500/50 hover:bg-blue-500/10 hover:border-blue-400 text-blue-400 shadow-blue-500/10'
              }
              ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}
            `}
            aria-label={`${settings.continuous ? 'Disable' : 'Enable'} continuous mode`}
          >
            <motion.div
              variants={glowVariants}
              className="absolute inset-0 rounded-2xl blur-lg bg-blue-500/30"
            />
            <div className="relative flex items-center gap-3">
              <motion.div
                animate={settings.continuous ? { rotate: 360 } : { rotate: 0 }}
                transition={{ duration: 2, repeat: settings.continuous ? Infinity : 0, ease: "linear" }}
              >
                <Repeat className="h-5 w-5" />
              </motion.div>
              <span>Auto Mode</span>
              {settings.continuous && (
                <motion.div
                  className="w-2 h-2 bg-green-400 rounded-full"
                  animate={{ scale: [1, 1.5, 1], opacity: [1, 0.5, 1] }}
                  transition={{ repeat: Infinity, duration: 1.5 }}
                />
              )}
            </div>
          </motion.button>

          {/* Describe Now */}
          <motion.button
            variants={buttonVariants}
            initial="idle"
            whileHover="hover"
            whileTap="tap"
            onClick={onDescribeNow}
            disabled={!cameraActive || isLoading}
            className={`
              relative flex items-center gap-3 px-6 py-4 rounded-2xl font-semibold
              transition-all duration-300 focus-ring border-2 shadow-lg
              ${cameraActive && !isLoading
                ? 'bg-slate-800/50 border-purple-500/50 hover:bg-purple-500/10 hover:border-purple-400 text-purple-400 shadow-purple-500/10' 
                : 'opacity-50 cursor-not-allowed text-gray-500 border-gray-600/30'
              }
            `}
            aria-label="Describe current scene"
          >
            <motion.div
              variants={glowVariants}
              className="absolute inset-0 rounded-2xl blur-lg bg-purple-500/30"
            />
            <div className="relative flex items-center gap-3">
              <Eye className="h-5 w-5" />
              <span>Describe Now</span>
              <Zap className="h-4 w-4" />
            </div>
          </motion.button>
        </div>

        {/* Loading indicator */}
        {isLoading && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center justify-center gap-3 mt-6 p-4 rounded-xl bg-blue-500/10 border border-blue-500/30"
          >
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            >
              <RotateCcw className="h-5 w-5 text-blue-400" />
            </motion.div>
            <span className="text-blue-400 font-medium">Processing vision data...</span>
          </motion.div>
        )}

        {/* Status text */}
        <motion.div 
          className="mt-6 text-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
        >
          <div className="text-slate-300 font-medium mb-2">
            {!cameraActive ? (
              '🔴 Camera is offline - Press "Start Camera" to begin'
            ) : settings.continuous ? (
              '🟢 Auto mode active - Continuous scene analysis'
            ) : (
              '🟡 Manual mode - Click "Describe Now" for analysis'
            )}
          </div>
        </motion.div>

        {/* Keyboard shortcuts */}
        <motion.div 
          className="mt-4 flex justify-center gap-2 text-xs text-slate-500"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          <kbd className="px-2 py-1 bg-slate-700/50 rounded-md border border-slate-600/50 font-mono">Space</kbd>
          <span>Start/Stop</span>
          <span className="text-slate-600">•</span>
          <kbd className="px-2 py-1 bg-slate-700/50 rounded-md border border-slate-600/50 font-mono">C</kbd>
          <span>Continuous</span>
          <span className="text-slate-600">•</span>
          <kbd className="px-2 py-1 bg-slate-700/50 rounded-md border border-slate-600/50 font-mono">D</kbd>
          <span>Describe</span>
        </motion.div>
      </div>
    </motion.div>
  );
}
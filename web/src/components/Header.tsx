// Modern Header component with professional design

import { motion } from 'framer-motion';
import { 
  Camera, 
  CameraOff, 
  Mic, 
  MicOff, 
  Repeat, 
  Square,
  Settings,
  Wifi,
  WifiOff,
  Eye
} from 'lucide-react';
import { useSettings } from '../state/SettingsContext';
import { useSession } from '../state/SessionContext';

interface HeaderProps {
  cameraActive: boolean;
  onToggleSettings: () => void;
  apiHealthy: boolean;
}

export function Header({ cameraActive, onToggleSettings, apiHealthy }: HeaderProps) {
  const { settings, toggleMute } = useSettings();
  const { state } = useSession();

  return (
    <header className="relative overflow-hidden bg-gradient-to-r from-slate-900 via-blue-900/20 to-purple-900/20 border-b border-slate-700/50 px-6 py-4">
      {/* Background pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#334155_1px,transparent_1px),linear-gradient(to_bottom,#334155_1px,transparent_1px)] bg-[size:24px_24px] opacity-20"></div>
      
      <div className="relative flex items-center justify-between">
        {/* Logo and title */}
        <div className="flex items-center gap-4">
          <motion.div
            initial={{ rotate: 0 }}
            animate={{ rotate: cameraActive ? 360 : 0 }}
            transition={{ duration: 0.8, ease: "easeInOut" }}
            className="relative p-3 rounded-xl bg-gradient-to-br from-blue-500/30 to-purple-500/30 border border-blue-500/50 shadow-lg backdrop-blur-sm"
          >
            <Eye className="h-7 w-7 text-white drop-shadow-md" />
            {cameraActive && (
              <motion.div 
                className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full border-2 border-slate-900"
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ repeat: Infinity, duration: 2 }}
              />
            )}
          </motion.div>
          <div>
            <motion.h1 
              className="text-2xl font-bold bg-gradient-to-r from-white via-blue-100 to-purple-100 bg-clip-text text-transparent"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              AI Eyes
            </motion.h1>
            <motion.p 
              className="text-sm text-slate-300/80 font-medium"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.7, delay: 0.2 }}
            >
              Vietnamese Vision Assistant
            </motion.p>
          </div>
        </div>

        {/* Status indicators */}
        <div className="flex items-center gap-3">
          {/* Camera status */}
          <motion.div 
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800/80 border border-slate-600/50 backdrop-blur-sm"
            whileHover={{ scale: 1.02 }}
            transition={{ duration: 0.2 }}
          >
            {cameraActive ? (
              <Camera className="h-4 w-4 text-green-400" />
            ) : (
              <CameraOff className="h-4 w-4 text-red-400" />
            )}
            <span className="text-sm font-medium text-white">
              {cameraActive ? 'ON' : 'OFF'}
            </span>
          </motion.div>

          {/* Continuous mode indicator */}
          <motion.div 
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800/80 border border-slate-600/50 backdrop-blur-sm"
            whileHover={{ scale: 1.02 }}
          >
            {settings.continuous ? (
              <Repeat className="h-4 w-4 text-blue-400" />
            ) : (
              <Square className="h-4 w-4 text-slate-400" />
            )}
            <span className="text-sm font-medium text-white">
              {settings.continuous ? 'Auto' : 'Manual'}
            </span>
          </motion.div>

          {/* Voice status */}
          <motion.button
            onClick={toggleMute}
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800/80 border border-slate-600/50 backdrop-blur-sm hover:bg-slate-700/80 focus-ring transition-all duration-200"
            aria-label={settings.muted ? 'Unmute voice' : 'Mute voice'}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {settings.muted ? (
              <MicOff className="h-4 w-4 text-red-400" />
            ) : (
              <Mic className="h-4 w-4 text-green-400" />
            )}
            <span className="text-sm font-medium text-white">
              {settings.muted ? 'Muted' : 'Voice'}
            </span>
          </motion.button>

          {/* API health */}
          <motion.div 
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800/80 border border-slate-600/50 backdrop-blur-sm"
            whileHover={{ scale: 1.02 }}
          >
            {apiHealthy ? (
              <Wifi className="h-4 w-4 text-green-400" />
            ) : (
              <WifiOff className="h-4 w-4 text-orange-400" />
            )}
            <span className="text-sm font-medium text-white">
              {apiHealthy ? 'Online' : 'Offline'}
            </span>
          </motion.div>

          {/* Performance metrics */}
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800/80 border border-slate-600/50 backdrop-blur-sm">
            <div className="flex flex-col items-center">
              {state.metrics.fps && (
                <div className="text-xs font-mono text-green-400 leading-tight">
                  {state.metrics.fps.toFixed(1)} FPS
                </div>
              )}
              {state.metrics.infer_ms && (
                <div className="text-xs font-mono text-blue-400 leading-tight">
                  {state.metrics.infer_ms}ms
                </div>
              )}
            </div>
          </div>

          {/* Confidence indicator */}
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800/80 border border-slate-600/50 backdrop-blur-sm">
            <div className="text-xs font-mono text-purple-400">
              Conf: {(settings.confidence * 100).toFixed(0)}%
            </div>
          </div>

          {/* Settings button */}
          <motion.button
            onClick={onToggleSettings}
            className="p-2 rounded-lg bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-500/50 hover:from-blue-500/30 hover:to-purple-500/30 focus-ring transition-all duration-200"
            aria-label="Open settings"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Settings className="h-5 w-5 text-white" />
          </motion.button>
        </div>
      </div>

      {/* Error display with enhanced styling */}
      {state.lastError && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="relative mt-3 p-3 rounded-lg bg-red-500/10 border border-red-500/30 backdrop-blur-sm"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-red-500/5 to-orange-500/5 rounded-lg"></div>
          <p className="relative text-sm text-red-200">
            <strong>⚠️ Error:</strong> {state.lastError}
          </p>
        </motion.div>
      )}
    </header>
  );
}
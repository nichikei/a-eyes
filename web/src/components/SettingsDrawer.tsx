// Settings drawer for configuring the application

import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, 
  Settings, 
  Sliders,
  Volume2,
  Filter,
  Globe,
  HelpCircle,
  RotateCcw
} from 'lucide-react';
import { useSettings } from '../state/SettingsContext';
import { AVAILABLE_CLASSES } from '../lib/types';

interface SettingsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onShowHelp: () => void;
}

export function SettingsDrawer({ isOpen, onClose, onShowHelp }: SettingsDrawerProps) {
  const { 
    settings, 
    updateSettings, 
    resetSettings, 
    toggleClass, 
    updateApiBase,
    toggleBrowserTTS 
  } = useSettings();

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
          />

          {/* Drawer */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed right-0 top-0 h-full w-96 bg-slate-900 border-l border-slate-700 z-50 flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-slate-700">
              <div className="flex items-center gap-3">
                <Settings className="h-5 w-5 text-blue-400" />
                <h2 className="text-lg font-semibold text-white">Settings</h2>
              </div>
              <button
                onClick={onClose}
                className="p-2 rounded-lg hover:bg-white/10 focus-ring transition-colors"
                aria-label="Close settings"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* API Configuration */}
              <section>
                <div className="flex items-center gap-2 mb-3">
                  <Globe className="h-4 w-4 text-blue-400" />
                  <h3 className="font-medium text-white">API Configuration</h3>
                </div>
                
                <div className="space-y-3">
                  <div>
                    <label htmlFor="apiBase" className="block text-sm font-medium text-slate-300 mb-1">
                      Base URL
                    </label>
                    <input
                      id="apiBase"
                      type="url"
                      value={settings.apiBase}
                      onChange={(e) => updateApiBase(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="http://localhost:8000"
                    />
                  </div>
                </div>
              </section>

              {/* Detection Settings */}
              <section>
                <div className="flex items-center gap-2 mb-3">
                  <Sliders className="h-4 w-4 text-green-400" />
                  <h3 className="font-medium text-white">Detection</h3>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <label htmlFor="confidence" className="block text-sm font-medium text-slate-300 mb-2">
                      Confidence Threshold: {(settings.confidence * 100).toFixed(0)}%
                    </label>
                    <input
                      id="confidence"
                      type="range"
                      min="0"
                      max="1"
                      step="0.05"
                      value={settings.confidence}
                      onChange={(e) => updateSettings({ confidence: parseFloat(e.target.value) })}
                      className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer slider"
                    />
                    <div className="flex justify-between text-xs text-slate-400 mt-1">
                      <span>0%</span>
                      <span>50%</span>
                      <span>100%</span>
                    </div>
                  </div>
                </div>
              </section>

              {/* Object Classes */}
              <section>
                <div className="flex items-center gap-2 mb-3">
                  <Filter className="h-4 w-4 text-purple-400" />
                  <h3 className="font-medium text-white">Object Classes</h3>
                </div>
                
                <div className="grid grid-cols-2 gap-2">
                  {AVAILABLE_CLASSES.map((className) => (
                    <label
                      key={className}
                      className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-800 cursor-pointer transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={settings.classes.includes(className)}
                        onChange={() => toggleClass(className)}
                        className="w-4 h-4 text-blue-600 bg-slate-700 border-slate-600 rounded focus:ring-blue-500 focus:ring-2"
                      />
                      <span className="text-sm text-slate-300 capitalize">
                        {className}
                      </span>
                    </label>
                  ))}
                </div>
              </section>

              {/* Speech Settings */}
              <section>
                <div className="flex items-center gap-2 mb-3">
                  <Volume2 className="h-4 w-4 text-yellow-400" />
                  <h3 className="font-medium text-white">Speech</h3>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.browserTTS}
                        onChange={toggleBrowserTTS}
                        className="w-4 h-4 text-blue-600 bg-slate-700 border-slate-600 rounded focus:ring-blue-500 focus:ring-2"
                      />
                      <span className="text-sm text-slate-300">
                        Use browser TTS
                      </span>
                    </label>
                    <p className="text-xs text-slate-400 ml-6">
                      {settings.browserTTS 
                        ? 'Using Web Speech API with fallback to backend'
                        : 'Using backend TTS only'
                      }
                    </p>
                  </div>

                  <div>
                    <label htmlFor="minInterval" className="block text-sm font-medium text-slate-300 mb-2">
                      Min Speech Interval: {settings.minIntervalMs}ms
                    </label>
                    <input
                      id="minInterval"
                      type="range"
                      min="500"
                      max="3000"
                      step="100"
                      value={settings.minIntervalMs}
                      onChange={(e) => updateSettings({ minIntervalMs: parseInt(e.target.value) })}
                      className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer slider"
                    />
                    <div className="flex justify-between text-xs text-slate-400 mt-1">
                      <span>500ms</span>
                      <span>1.5s</span>
                      <span>3s</span>
                    </div>
                  </div>

                  <div>
                    <label htmlFor="autoInterval" className="block text-sm font-medium text-slate-300 mb-2">
                      Auto Capture Interval: {settings.autoInterval / 1000}s
                    </label>
                    <input
                      id="autoInterval"
                      type="range"
                      min="3000"
                      max="15000"
                      step="1000"
                      value={settings.autoInterval}
                      onChange={(e) => updateSettings({ autoInterval: parseInt(e.target.value) })}
                      className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer slider"
                    />
                    <div className="flex justify-between text-xs text-slate-400 mt-1">
                      <span>3s</span>
                      <span>9s</span>
                      <span>15s</span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">
                      How often to automatically capture and analyze when in continuous mode
                    </p>
                  </div>

                  <div>
                    <label htmlFor="dedupe" className="block text-sm font-medium text-slate-300 mb-2">
                      Deduplication Window: {settings.dedupeWindowSec}s
                    </label>
                    <input
                      id="dedupe"
                      type="range"
                      min="1"
                      max="10"
                      step="0.5"
                      value={settings.dedupeWindowSec}
                      onChange={(e) => updateSettings({ dedupeWindowSec: parseFloat(e.target.value) })}
                      className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer slider"
                    />
                    <div className="flex justify-between text-xs text-slate-400 mt-1">
                      <span>1s</span>
                      <span>5s</span>
                      <span>10s</span>
                    </div>
                  </div>
                </div>
              </section>
            </div>

            {/* Footer */}
            <div className="p-6 border-t border-slate-700 space-y-3">
              <button
                onClick={onShowHelp}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-500/20 border border-blue-500/30 rounded-lg text-blue-300 hover:bg-blue-500/30 focus-ring transition-colors"
              >
                <HelpCircle className="h-4 w-4" />
                Keyboard Shortcuts
              </button>

              <button
                onClick={resetSettings}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-red-500/20 border border-red-500/30 rounded-lg text-red-300 hover:bg-red-500/30 focus-ring transition-colors"
              >
                <RotateCcw className="h-4 w-4" />
                Reset to Defaults
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
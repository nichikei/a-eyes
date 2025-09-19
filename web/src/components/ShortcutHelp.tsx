// Keyboard shortcuts help modal

import { motion, AnimatePresence } from 'framer-motion';
import { X, Keyboard } from 'lucide-react';

interface ShortcutHelpProps {
  isOpen: boolean;
  onClose: () => void;
}

const shortcuts = [
  { key: 'S', description: 'Start/Stop camera' },
  { key: 'C', description: 'Toggle continuous mode' },
  { key: 'D', description: 'Describe current scene' },
  { key: 'M', description: 'Mute/Unmute voice' },
  { key: '?', description: 'Show this help' },
  { key: 'Esc', description: 'Close modals/drawers' },
];

export function ShortcutHelp({ isOpen, onClose }: ShortcutHelpProps) {
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
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none"
          >
            <div className="glass-strong rounded-2xl p-6 w-full max-w-md pointer-events-auto border border-slate-600">
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <Keyboard className="h-5 w-5 text-blue-400" />
                  <h2 className="text-lg font-semibold text-white">Keyboard Shortcuts</h2>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 rounded-lg hover:bg-white/10 focus-ring transition-colors"
                  aria-label="Close help"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Shortcuts list */}
              <div className="space-y-3">
                {shortcuts.map((shortcut) => (
                  <div
                    key={shortcut.key}
                    className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50 border border-slate-700/50"
                  >
                    <span className="text-slate-300">{shortcut.description}</span>
                    <kbd className="px-3 py-1 text-sm font-mono bg-slate-700 border border-slate-600 rounded-lg text-slate-200">
                      {shortcut.key}
                    </kbd>
                  </div>
                ))}
              </div>

              {/* Footer */}
              <div className="mt-6 pt-4 border-t border-slate-700/50">
                <p className="text-xs text-slate-400 text-center">
                  Press any key to activate shortcuts when focused on the page
                </p>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}